---
title: TechTailor Prototype
emoji: 👔
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# TechTailor Customer Experience Agent Prototype

A Virtual Tailoring Consultant + Style Advisor + Measurement Assistant prototype built with FastAPI and LangGraph, running in a Docker container.

## Local Setup (full stack, matches production)
```bash
cp .env.example .env   # fill in GROQ_API_KEY
docker compose up --build
```
This runs the app plus Postgres and Redis. Visit http://localhost:8000.

## Local Setup (no external services)
The app also runs standalone with zero infra - it falls back to a local
SQLite file and in-process session/cache state when `DATABASE_URL`/`REDIS_URL`
aren't set. Good for a quick check, not for anything beyond one process.
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY, leave DATABASE_URL/REDIS_URL blank
python -m uvicorn server:app --port 8000
```

## What Postgres/Redis are actually for here

- **Postgres** (`agent_store.py`) replaces SQLite for session/message/event
  history and product stock counts. SQLite was a file on the container's
  local disk - on Render/HF Spaces that disk isn't guaranteed to persist
  across restarts or redeploys, so history could silently vanish. Postgres
  also handles concurrent writers correctly, which a single SQLite file does
  not once you have more than one worker process.
- **Redis** (`redis_layer.py`) does three jobs:
  1. **Session state** - the workflow/branch the LangGraph agent has decided
     a customer is in. This used to live in a plain Python dict inside the
     process; it worked by accident with exactly one worker and would
     silently desync as soon as you ran more than one (each dyno/worker has
     its own dict). Redis makes it shared.
  2. **LLM response cache** - an *exact-match* cache (same model + same
     system prompt + same message history -> same cached answer, short TTL).
     This is deliberately not fuzzy/semantic caching, so it never returns an
     answer that doesn't fit the live conversation - it only saves a real
     Groq call on genuine repeats (identical greetings, a resend after a
     network blip, etc), which is where the API cost was going.
  3. **Pub/sub** for live events (`/ws/updates`) - e.g. broadcasting a stock
     change the instant one shopper adds the last unit to their bag, so any
     other browser tab looking at the same product finds out without a
     reload. This is the same job "Kafka" was requested for; at this
     traffic scale a dedicated broker is unnecessary operational weight -
     the Redis instance already in the stack handles it.

See `ARCHITECTURE_AUDIT.md` for the full list of what was found and fixed,
including the agent-behavior issues (one-word replies, images/recommendation
widgets firing on nearly every turn).

## Deploying to Hugging Face Spaces (this is what we actually use)
A Space runs your `Dockerfile` as a single container - there's no sidecar
service the way Render's blueprint provides, so Postgres and Redis both need
to be *externally hosted* and reached over the network by connection string.
Both of the below have a free tier that's plenty for a prototype:

1. Create a Postgres database - [Neon](https://neon.tech) or
   [Supabase](https://supabase.com) both work - and copy its connection
   string.
2. Create a Redis database - [Upstash](https://upstash.com) - and copy its
   connection string (use the `rediss://` TLS one Upstash gives you).
3. In your Space, go to **Settings -> Variables and secrets** and add three
   **secrets**: `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`. Nothing else
   changes - the app already reads these three from the environment.
4. Push/restart the Space. `techtailor_agent.db` (the SQLite fallback) is
   only ever used if `DATABASE_URL` is unset, and a Space's local disk isn't
   guaranteed to survive a restart anyway - so for anything beyond a quick
   throwaway test, set the secrets above rather than leaving them blank.

`docker-compose.yml` and `render.yaml` are both still in the repo (useful if
you ever want to run the full stack locally, or if you add a Render
deployment alongside HF later) but neither is needed for the HF Spaces path
above - ignore them for now.
