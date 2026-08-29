from __future__ import annotations

"""
Redis layer: shared session state, an exact-match LLM response cache, and a
pub/sub broadcaster for live events (stock changes, new leads, etc).

Everything here degrades gracefully to an in-process equivalent when
REDIS_URL isn't set, so local dev / a single quick demo still works with zero
external services. In any multi-worker or multi-dyno deployment the in-memory
fallback is NOT shared across processes - that's exactly the bug this file
fixes for the real deployment (the original code kept session state in a
plain Python dict, which silently breaks as soon as you run more than one
uvicorn worker or the process restarts).
"""

import hashlib
import json
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

REDIS_URL = os.getenv("REDIS_URL", "").strip()

_redis_client = None
if REDIS_URL:
    try:
        import redis as _redis  # type: ignore

        _redis_client = _redis.Redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
    except Exception:
        # Bad URL / Redis unreachable at boot - fail open to the in-memory
        # fallback rather than crashing the whole app.
        _redis_client = None

USING_REDIS = _redis_client is not None

# --- Fallbacks used only when Redis is unavailable --------------------------
_LOCAL_LOCK = threading.Lock()
_LOCAL_SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}
_LOCAL_CACHE: Dict[str, Any] = {}
_LOCAL_SUBSCRIBERS: List[Callable[[Dict[str, Any]], None]] = []

SESSION_TTL_SECONDS = 60 * 60 * 6  # 6 hours of idle session memory
CACHE_TTL_SECONDS = 60 * 15  # short TTL: cheap win on repeat/greeting turns
                              # without risking stale answers for a live convo
CACHE_NAMESPACE = "techtailor:llmcache:"
SESSION_NAMESPACE = "techtailor:session:"
EVENTS_CHANNEL = "techtailor:events"


# --- Session memory (replaces the old bare `SESSION_MEMORY` dict) -----------

def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    if USING_REDIS:
        raw = _redis_client.get(SESSION_NAMESPACE + session_id)
        return json.loads(raw) if raw else None
    with _LOCAL_LOCK:
        return _LOCAL_SESSION_MEMORY.get(session_id)


def set_session_state(session_id: str, state: Dict[str, Any]) -> None:
    if USING_REDIS:
        _redis_client.set(
            SESSION_NAMESPACE + session_id,
            json.dumps(state, default=str),
            ex=SESSION_TTL_SECONDS,
        )
        return
    with _LOCAL_LOCK:
        _LOCAL_SESSION_MEMORY[session_id] = state


# --- LLM response cache -------------------------------------------------

def _cache_key(model: str, system_prompt: str, messages: List[Dict[str, str]]) -> str:
    """Exact-match cache key. This intentionally does NOT do semantic/fuzzy
    matching - only byte-identical (model, system prompt, message history)
    tuples share a cache entry. That keeps it safe (never returns an answer
    that doesn't fit the actual conversation) while still saving real API
    spend on the extremely common repeat cases: identical greetings ("hi",
    "hello"), FAQ-style questions, and a user re-sending the same message
    after a network hiccup.
    """
    payload = json.dumps({"model": model, "system": system_prompt, "messages": messages}, sort_keys=True)
    return CACHE_NAMESPACE + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_cached_response(model: str, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    key = _cache_key(model, system_prompt, messages)
    if USING_REDIS:
        raw = _redis_client.get(key)
        return json.loads(raw) if raw else None
    with _LOCAL_LOCK:
        entry = _LOCAL_CACHE.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if expires_at < time.time():
            _LOCAL_CACHE.pop(key, None)
            return None
        return value


def set_cached_response(model: str, system_prompt: str, messages: List[Dict[str, str]], value: Dict[str, Any]) -> None:
    key = _cache_key(model, system_prompt, messages)
    if USING_REDIS:
        _redis_client.set(key, json.dumps(value, default=str), ex=CACHE_TTL_SECONDS)
        return
    with _LOCAL_LOCK:
        _LOCAL_CACHE[key] = (value, time.time() + CACHE_TTL_SECONDS)


# --- Pub/sub (the "Kafka" ask, done with the Redis instance we already have) -

def publish_event(event_type: str, payload: Dict[str, Any]) -> None:
    message = json.dumps({"event_type": event_type, "payload": payload, "ts": time.time()}, default=str)
    if USING_REDIS:
        _redis_client.publish(EVENTS_CHANNEL, message)
        return
    with _LOCAL_LOCK:
        subscribers = list(_LOCAL_SUBSCRIBERS)
    for callback in subscribers:
        try:
            callback(json.loads(message))
        except Exception:
            pass


def subscribe_events_blocking(on_message: Callable[[Dict[str, Any]], None], stop_flag: Callable[[], bool]) -> None:
    """Blocking subscribe loop, intended to be run in a background thread/task
    per connected WebSocket client. `stop_flag()` should return True once the
    caller wants to stop listening (e.g. the socket disconnected).
    """
    if USING_REDIS:
        pubsub = _redis_client.pubsub()
        pubsub.subscribe(EVENTS_CHANNEL)
        try:
            while not stop_flag():
                message = pubsub.get_message(timeout=1.0)
                if message and message.get("type") == "message":
                    try:
                        on_message(json.loads(message["data"]))
                    except Exception:
                        pass
        finally:
            pubsub.close()
        return

    # In-memory fallback: register a callback and just idle until stopped.
    with _LOCAL_LOCK:
        _LOCAL_SUBSCRIBERS.append(on_message)
    try:
        while not stop_flag():
            time.sleep(0.5)
    finally:
        with _LOCAL_LOCK:
            if on_message in _LOCAL_SUBSCRIBERS:
                _LOCAL_SUBSCRIBERS.remove(on_message)
