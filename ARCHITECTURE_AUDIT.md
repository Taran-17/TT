# TechTailor Prototype - Architecture Audit & Changes

Repo: https://github.com/Taran-17/TT
Stack before this pass: FastAPI + LangGraph + Groq, SQLite file, no cache/queue, deployed to Hugging Face Spaces (Docker). (The repo also has a `render.yaml` from an earlier/alternate deploy path - not the one actually in use, see README for the real HF Spaces deploy steps.)

## What was actually wrong with the agent's conversation quality

These were the real causes behind "responses were pretty one-wordish" and
"images/recommendations popping up overwhelmingly" - not vague vibes, specific
lines of code:

1. **The frontend was hallucinating widgets from keyword matching, independent
   of what the model asked for.** In `static/app.js` `addMessageToChat()`,
   any assistant reply containing the word "fabric" rendered a full fabric
   swatch gallery; any reply containing "recommend"/"suit"/"collection"
   rendered product cards; any reply containing "occasion"/"fit"/"measure"
   rendered an option-card grid - all regardless of whether an actual
   `present_options`/`show_recommendations`/`customize_fabric` action was
   present. Since the system prompt's branch policies actively encourage
   those words ("guide the customer to fabric choice", "surface the best
   next options"), nearly every assistant turn tripped at least one of these
   heuristics. **Fixed:** all five widget blocks now render strictly off the
   `actions` array the backend returned; the keyword fallbacks are removed.

2. **The system prompt mandated a widget on almost every turn.** Rule 2 said
   "whenever you ask a question... you MUST include `present_options`" and
   rule 3 said to attach `show_recommendations`/`customize_fabric` whenever
   suits/fabrics were mentioned at all, with no "only when it's a real
   decision point" carve-out. **Fixed:** rewrote the rules to be conditional
   - only attach a visual action when the reply is actually presenting a
   concrete choice, and explicitly says not to stack multiple visual actions
   in a single reply.

3. **Rule 6 hard-capped every reply at "2-4 sentences max," with no
   distinction between a one-word confirmation and a reply the customer
   explicitly asked for an explanation on.** Combined with `temperature=0.2`
   and a JSON-mode small model as a silent fallback (`llama-3.1-8b-instant`
   when the 70B model's call fails), this reliably produced clipped,
   fragment-like answers. **Fixed:** replaced the blanket sentence cap with
   guidance to match length to the moment, bumped temperature to `0.4` for
   more natural phrasing, and kept the model fallback order but it's now
   easier to see when it's happening (see "still worth doing" below).

4. **Classification only ever looked at the single latest user message**
   (`classify_workflow(last_user_message)` in the old `agent_graph.py`), and
   `_session_fallback` switched the active workflow/branch (and therefore the
   entire system prompt) the instant the newly classified intent bucket
   differed at all from the previous turn's. A short reply like "yes", "the
   blue one", or "how much?" scores weakly against every workflow, so it
   would frequently get reclassified to `master_entry` or a wrong workflow,
   silently changing the agent's whole frame of reference mid-conversation -
   a big contributor to the assistant feeling like it kept "forgetting" the
   conversation and answering tersely/generically. **Fixed:**
   `workflow_catalog.classify_conversation()` now scores against the last few
   user turns (latest weighted most heavily, not exclusively), and
   `_session_fallback` only actually switches workflows on a *strong* new
   match - a weak/ambiguous signal keeps the customer on their current
   workflow instead of bouncing them.

## Infrastructure changes

### SQLite -> Postgres (`agent_store.py`)
Rewritten on SQLAlchemy. Uses `DATABASE_URL` when set (Postgres in
production - `render.yaml` now provisions a managed Postgres instance and
wires the URL automatically); falls back to a local SQLite file with zero
config so a quick local run still needs nothing installed. This also fixes a
real bug, not just a "nicer DB" preference: on Render/HF Spaces the
container filesystem is not guaranteed to survive a restart or redeploy, so
the old SQLite file's session/message/event history could silently
disappear. Postgres also handles concurrent writers correctly, which one
SQLite file does not once there's more than one worker process.

### Redis (`redis_layer.py`)
One new module, three jobs, all with an in-process fallback when `REDIS_URL`
is unset (so nothing breaks locally without Docker):

- **Session state** - replaces the old bare `SESSION_MEMORY: Dict[...] = {}`
  module-level dict. That dict only worked by accident with exactly one
  worker process; with more than one (multiple Render instances, multiple
  uvicorn workers, a restart) each process had its own copy and sessions
  would desync in ways that'd look exactly like "the agent forgot what we
  were talking about." Redis makes this state actually shared.
- **LLM response cache** - `get_cached_response`/`set_cached_response`, keyed
  by an exact hash of `(model, system_prompt, message_history)`, short TTL
  (15 min). This is deliberately *exact-match*, not semantic/fuzzy: it will
  never hand back an answer that doesn't fit the live conversation, it only
  saves a real Groq call on genuine repeats - identical greetings ("hi"),
  a resend after a network blip, common FAQ-style openers. That's where
  redundant API spend was actually happening; this is a safe way to cut it
  without risking a wrong or stale-sounding reply.
- **Pub/sub** (`publish_event`/`subscribe_events_blocking`) over a single
  Redis channel, used by a new `/ws/updates` WebSocket endpoint in
  `server.py`. This is the answer to "if multiple people are chatting at the
  same time they need to know the state of stock" - which, worth flagging
  directly: **there was no inventory/stock concept anywhere in the original
  app at all** (the storefront catalog in `static/app.js` is static frontend
  data with no backend quantity). Added a minimal `stock` table
  (`agent_store.py`), decremented on `add_to_bag`, broadcast over Redis
  pub/sub the instant it changes, and a WebSocket client
  (`connectLiveUpdates()` in `app.js`) that shows a toast when stock gets low
  or sells out - confirmed end-to-end in testing (see below).

### Why Redis pub/sub instead of Kafka
Render has no native Kafka service; real Kafka would mean signing up for and
paying for an external managed broker (Confluent Cloud, Upstash Kafka, etc)
just for this. At this app's actual scale - broadcasting stock/session
events to browser tabs - Redis pub/sub (already needed for caching and
session state) does the same job with no new vendor, no extra cost, and one
less moving part to operate. If usage ever grows to genuinely needing
partitioned, replayable, multi-consumer-group streaming, Redis Streams
(rather than plain pub/sub) is the next step up before reaching for Kafka -
worth revisiting if/when that's real, not preemptively.

## What was tested

Ran the full stack locally against real Postgres 16 and Redis (not just the
fallback path): confirmed `/api/chat`, `/api/stock`, `/api/analytics` all
work with `backend: "postgres"` in the analytics response, confirmed a
message written by one process is visible via a fresh DB read, confirmed
`redis_layer` round-trips session state, exact-match cache entries, and
pub/sub events, and connected an actual WebSocket client to `/ws/updates`
and received a `stock_update` event published from a separate process.
Also ran with no `DATABASE_URL`/`REDIS_URL` set at all (the zero-config
path) to confirm nothing regressed for a plain local run.

## Still worth doing (not done in this pass - flagging so it's a choice, not a surprise)

- **Streaming responses.** The frontend waits for the full JSON body before
  showing anything; a streaming response (even just the `response` text
  field) would make the agent feel much more responsive, especially on the
  slower fallback model.
- **Surface which model actually answered.** The silent fallback from the
  70B model to the 8B model on any error means a customer can get a
  noticeably worse reply with no visible indication why. Worth logging/
  exposing this (e.g. in `/api/analytics` or the dev-facing monitor panel)
  so degraded quality is diagnosable instead of just "the agent seems worse
  today."
- **Stock badges in the actual product UI.** The live pipe
  (`/ws/updates` -> `handleStockUpdate()`) is wired and confirmed working,
  but the product/customizer cards in `static/index.html` don't yet render
  a `data-product-id`/`.stock-badge` element for it to update - right now
  the visible effect is the low-stock/sold-out toast. Wiring the badges into
  the actual product cards is a frontend markup change, not a backend one.
- **Rate limiting / abuse protection** on `/api/chat` - there isn't any
  currently, and the Groq calls are the actual cost driver here.
