from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "techtailor_agent.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_store() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                workflow_title TEXT,
                intent_bucket TEXT,
                workflow_summary TEXT,
                branch TEXT,
                turn_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                workflow_id TEXT,
                intent_bucket TEXT,
                branch TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def upsert_session(
    session_id: str,
    workflow_id: Optional[str] = None,
    workflow_title: Optional[str] = None,
    intent_bucket: Optional[str] = None,
    workflow_summary: Optional[str] = None,
    branch: Optional[str] = None,
) -> None:
    now = _utc_now()
    with _connect() as conn:
        existing = conn.execute(
            "SELECT session_id, turn_count, created_at FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE sessions
                SET workflow_id = COALESCE(?, workflow_id),
                    workflow_title = COALESCE(?, workflow_title),
                    intent_bucket = COALESCE(?, intent_bucket),
                    workflow_summary = COALESCE(?, workflow_summary),
                    branch = COALESCE(?, branch),
                    updated_at = ?,
                    turn_count = turn_count + 1
                WHERE session_id = ?
                """,
                (workflow_id, workflow_title, intent_bucket, workflow_summary, branch, now, session_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, workflow_id, workflow_title, intent_bucket, workflow_summary, branch,
                    turn_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (session_id, workflow_id, workflow_title, intent_bucket, workflow_summary, branch, now, now),
            )


def record_message(
    session_id: str,
    role: str,
    content: str,
    workflow_id: Optional[str] = None,
    intent_bucket: Optional[str] = None,
    branch: Optional[str] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, workflow_id, intent_bucket, branch, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, role, content, workflow_id, intent_bucket, branch, _utc_now()),
        )


def record_event(session_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (session_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (session_id, event_type, json.dumps(payload, ensure_ascii=True), _utc_now()),
        )


def get_session_snapshot(session_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        return dict(row)


def get_recent_messages(session_id: str, limit: int = 12) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content, workflow_id, intent_bucket, branch, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [dict(row) for row in reversed(rows)]


def get_analytics() -> Dict[str, Any]:
    with _connect() as conn:
        session_count = conn.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"]
        message_count = conn.execute("SELECT COUNT(*) AS count FROM messages").fetchone()["count"]
        event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
        bucket_rows = conn.execute(
            """
            SELECT COALESCE(intent_bucket, 'unknown') AS bucket, COUNT(*) AS count
            FROM sessions
            GROUP BY COALESCE(intent_bucket, 'unknown')
            ORDER BY count DESC
            """
        ).fetchall()
        event_rows = conn.execute(
            """
            SELECT event_type, COUNT(*) AS count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
            """
        ).fetchall()
        return {
            "sessions": session_count,
            "messages": message_count,
            "events": event_count,
            "intent_buckets": [dict(row) for row in bucket_rows],
            "event_types": [dict(row) for row in event_rows],
        }


init_store()

