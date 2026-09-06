# TechTailor — Project Deep-Dive for Interviews

This isn't a features list. It's the reasoning you should be able to produce
on demand: why each piece exists, what would break without it, and what an
interviewer is actually testing when they ask about it. Read it once
top-to-bottom, then use the Q&A section at the end to drill.

---

## 1. The 30-second version (open with this)

"TechTailor is a conversational shopping assistant for a custom-tailoring
business — a customer chats with it about what they want (a suit for a
wedding, a shirt for the office, whatever), and it routes them through a
LangGraph-based agent that classifies intent, asks the right follow-up
questions, and surfaces product/fabric recommendations and a checkout flow.
I inherited it as a working prototype with three real problems: the
conversation quality was poor (terse answers, UI elements firing on nearly
every message), the persistence layer (SQLite, in-process memory) wouldn't
survive being deployed for real, and there was no cost control on the LLM
calls. I fixed all three, and I can walk through exactly what was wrong and
why each fix is the right one, not just 'I added Redis.'"

That last sentence is the whole point of this document. Anyone can say "I
integrated Postgres and Redis." The interview is about whether you can
explain *why*, in terms of failure modes, not features.

---

## 2. What the system actually does, architecturally

```
Browser (static/app.js)
   │  POST /api/chat  { messages, session_id }
   ▼
FastAPI (server.py)
   │
   ▼
LangGraph agent (agent_graph.py)
   ├─ route node: classify intent from conversation → pick a "workflow"
   │              (one of ~120 pre-defined conversation templates: custom
   │              shirt, wedding groom, corporate uniform buyer, etc.)
   ├─ branch node (sales/support/corporate/research/explore): builds a
   │              system prompt for that workflow + branch, calls Groq
   │              (Llama models via Groq's fast inference API), gets back
   │              structured JSON: { response, actions }
   └─ persist node: writes to Postgres, publishes events over Redis
   │
   ▼
Postgres (sessions, messages, events, stock)     Redis (session state,
                                                   LLM cache, pub/sub)
```

The key architectural idea worth stating explicitly: **the LLM never talks
to the frontend directly, and it never emits free-form UI.** It emits a
small, closed vocabulary of typed "actions" (`present_options`,
`show_recommendations`, `add_to_bag`, etc.) that the frontend interprets.
This is a deliberate separation — the model handles *what to say and what
to suggest*, the frontend handles *how to render it*. That separation is
also exactly where the biggest bug was hiding (section 3.1).

---

## 3. The real engineering problems, and why each fix is correct

This is the part to actually rehearse — it's evidence you can debug a
system, not just add technologies to it.

### 3.1 The frontend was inferring intent from prose, not from data

**Symptom:** almost every assistant reply triggered a product carousel, a
fabric swatch gallery, and an option-card grid, regardless of what the
message actually needed.

**Root cause:** `addMessageToChat()` in the frontend didn't only render
based on the typed `actions` array the backend sent — it *also* ran
substring checks on the assistant's own text (`content.includes('fabric')`,
`content.includes('recommend')`, etc.) and rendered widgets on a match. Since
the system prompt's own branch policies used words like "fabric" and
"recommend" constantly, nearly every reply tripped at least one heuristic —
independent of whether an actual `show_recommendations` or `customize_fabric`
action existed.

**Why this is a *design* bug, not a copy-editing bug:** it's a violation of
having a single source of truth for "what should render." Once the view
layer has its own opinion about intent that can diverge from the model's
declared intent, the two will drift, and you get exactly this: visual noise
that has no relationship to what's actually being asked. The fix wasn't
"tune the keyword list" — it was deleting the parallel inference path
entirely, so rendering is a pure function of the actions array.

**What to say if pushed on this:** "This is the kind of bug you only find by
reading the actual rendering code, not by reading the prompt. The prompt
looked reasonable in isolation — the bug was in how two independently-built
layers (prompt design and frontend rendering) both tried to infer the same
thing and disagreed."

### 3.2 Conversational context was one message wide

**Symptom:** the agent felt like it kept "forgetting" the conversation —
short replies like "yes" or "the blue one" would sometimes bounce the whole
conversation to an unrelated topic.

**Root cause:** intent classification (`classify_workflow`) scored only the
single latest user message against ~120 workflow templates, and the
session-continuity logic switched the active workflow (and therefore the
*entire* system prompt) the instant the newly classified bucket differed at
all from the previous turn's — with no confidence threshold.

**The fix, and the concept behind it:** this is a hysteresis problem. A
system that reclassifies its own state on every weak signal will oscillate.
The fix has two parts: (1) score against a short window of recent turns,
weighted toward the latest one, so a low-content reply inherits context from
what was actually said a turn or two earlier; (2) only actually switch
state when the new classification is a *strong* match — a weak or ambiguous
read keeps the system in its current state. This is the same idea behind
debouncing in UI code, or a schmitt trigger in circuit design: don't let
noise flip a state machine.

**Interview framing:** "This is a state-management bug that happened to be
inside an LLM pipeline — the fix isn't prompt engineering, it's applying a
basic hysteresis/confidence-threshold pattern to a classifier that was
being treated as ground truth on every single call."

### 3.3 SQLite in a container that isn't guaranteed to persist

**Root cause:** the original store was a SQLite file sitting on the
container's local disk. On both Hugging Face Spaces and most PaaS free
tiers, that disk is not guaranteed to survive a restart or redeploy — so
session/message history could silently vanish. SQLite also serializes
writes at the file level, which becomes a real bottleneck (and a
correctness risk) the moment there's more than one worker process.

**Fix:** SQLAlchemy models against Postgres (`DATABASE_URL`), with SQLite
kept only as a zero-config local-dev fallback. This is a durability fix,
not a "nicer database" preference — say that explicitly if asked, because
"I switched to Postgres because it's more standard" is a weak answer; "I
switched because the previous store could lose all history on a routine
redeploy" is a strong one.

### 3.4 Session state lived in a bare Python dict

**Root cause:** `SESSION_MEMORY: Dict[str, Dict] = {}` at module scope. This
works by accident with exactly one worker process. The moment you run more
than one (multiple uvicorn workers, multiple container replicas, a
restart), each process has its own independent copy, and a user's session
state randomly desyncs depending on which process handles which request.

**Fix:** moved this into Redis (`redis_layer.py`), so state is shared across
however many processes are actually running. **This is the correctness
argument for Redis that matters most, and it has nothing to do with
performance** — the bug it fixes is a horizontal-scaling correctness bug,
not a speed problem. Be precise about that distinction in an interview:
Redis here is not "for speed," it's for having one shared truth about
session state across processes that don't share memory.

### 3.5 Cost control without correctness risk: the LLM cache

**The naive-wrong approach** would be a semantic/fuzzy cache — cache "similar
enough" prompts and serve a similar answer. That's dangerous here: two
customers asking something that *sounds* similar can be at completely
different points in their own conversation, and returning someone else's
cached answer would be visibly, confidently wrong.

**What was actually built:** an *exact-match* cache — key is a hash of
`(model, full system prompt, full message history)`, short TTL (15 min).
It only ever returns a cached answer when the input is byte-identical to a
previous call. That means it can never return an answer that doesn't fit
the live conversation — it only saves a real API call on genuine repeats:
identical greetings, a client retry after a network blip, common FAQ
openers. **This is the answer to "isn't caching an LLM risky" — the design
explicitly trades away most of the possible cache-hit-rate to guarantee
zero risk of a wrong answer.** That trade-off, stated explicitly, is exactly
what a senior engineer is expected to reason about before reaching for a
cache in front of anything non-deterministic.

### 3.6 Real-time stock visibility: Redis pub/sub + WebSocket (see section 4 for the Kafka angle)

There was no inventory concept in the app at all originally — the product
catalog was static frontend data with no backend quantity. Added a minimal
`stock` table, decremented on `add_to_bag`, and broadcast the change over a
Redis pub/sub channel that a `/ws/updates` WebSocket endpoint fans out to
every connected browser tab — so if customer A buys the last unit, customer
B's tab reflects it without a refresh. This is a basic event-driven pattern:
a state change produces an event, the event is published once, and any
number of subscribers react to it without the publisher knowing or caring
who's listening. That decoupling is the actual concept being demonstrated —
Kafka or Redis are just two different implementations of the same pattern
at different scales, which is exactly the next section.

### 3.7 Upstream API drift: don't hardcode a vendor's model names

**What happened live:** the app broke in production because
`llama-3.1-8b-instant` had been retired/renamed on Groq's side, and the code
had that name (and one other) hardcoded with no way to notice it had gone
stale.

**Fix:** query Groq's own `/models` endpoint at runtime, cache the result
for 10 minutes, and rank whatever's actually available by preference —
falling back to the old hardcoded guesses only if the discovery call itself
fails. **The general principle, good for any interview:** never hardcode a
third-party vendor's resource identifiers as if they're permanent constants
— discover what's actually available and degrade gracefully, because
vendor-side renames/deprecations are a "when," not an "if."

---

## 4. "Imagine if Kafka had been used" — the section to actually nail

This is the question worth being able to answer better than most
candidates, because most people either (a) don't know the difference
between Kafka and Redis pub/sub beyond "Kafka is for big data," or (b) add
Kafka reflexively because it's the resume-recognizable answer. You should be
the person who can explain *precisely* what changes and argue the actual
scale threshold.

**What Redis pub/sub actually is:** fire-and-forget. A publisher sends a
message to a channel; only subscribers connected *at that exact moment*
receive it. Nothing is stored. If your WebSocket client reconnects a second
after a stock update was published, that update is gone — the client has to
re-fetch current state (`GET /api/stock`) to catch up. There's no replay,
no consumer groups, no partitioning, no durability guarantee, no ordering
guarantee across multiple publishers.

**What Kafka would add:**
- **Durability + replay.** Kafka is a distributed, partitioned, append-only
  log. Messages are persisted to disk (with configurable retention) and a
  new consumer joining late can replay history from any offset. If you
  needed "show me every stock change in the last 24 hours" as a real
  feature (e.g. a merchandising dashboard), Kafka gives you that for free;
  Redis pub/sub gives you nothing — you'd have to build your own event
  store on top of it (which, incidentally, is close to reinventing Kafka
  badly).
- **Consumer groups and horizontal scaling of consumers.** Multiple
  instances of the same service can share a topic's partitions and each
  message is processed exactly once across the group. Redis pub/sub
  broadcasts to *every* subscriber — there's no built-in concept of "one of
  these N workers should handle this," so you'd hand-roll a leader-election
  or locking scheme to get equivalent behavior.
- **Ordering guarantees within a partition,** which matters if event order
  is load-bearing (e.g. "reserve stock" must be processed before "release
  reservation" for the same product). At this app's current scale that's
  not a real risk — but it becomes one the moment you have concurrent
  writers you don't fully control (e.g. a separate warehouse-management
  system also decrementing stock).
- **Schema evolution and multi-team consumption.** Kafka's ecosystem (schema
  registry, Kafka Connect, ksqlDB) is built for the scenario where many
  different services/teams need to consume the same event stream
  independently, potentially written in different languages, over a long
  time horizon. That's an organizational scaling problem, not a technical
  one — it matters when you have multiple teams, not multiple browser tabs.

**What Kafka would cost, concretely, for this project right now:**
- An operational dependency with real setup: brokers (or a managed service
  — Confluent Cloud, Upstash Kafka, Redpanda Cloud — since neither Render
  nor Hugging Face Spaces can host a broker as a sidecar container), topic
  provisioning, partition count decisions, consumer group management,
  offset commit strategy, and monitoring for consumer lag.
- A new production dependency and likely a bill, for a system currently
  broadcasting to a handful of browser tabs — the durability/replay/
  ordering guarantees above solve problems this app doesn't have yet.
- The Redis instance already exists in the stack for caching and session
  state — pub/sub on that same instance is marginal cost; Kafka would be a
  wholly new piece of infrastructure to operate.

**The actual engineering answer, if asked "why didn't you use Kafka":**
"Because the job here — broadcast an ephemeral event to whoever happens to
be looking right now — doesn't need durability or replay, and Redis pub/sub
already does that job with infrastructure I was already running for other
reasons. I know exactly where the line is, though: the moment this needs
event replay, multiple independent consumer services, or ordering
guarantees across concurrent writers — for example, if inventory
reservations moved to a separate service, or if analytics needed to
reprocess historical stock events — that's the point where Redis Streams
(a middle ground: persisted, consumer-group-aware, but still one Redis
instance) or actual Kafka becomes the right call, not before. Adding it
preemptively here would be solving a scaling problem the product doesn't
have yet, at the cost of real operational complexity it would have today."

That answer demonstrates the thing interviewers are actually screening for:
not "have you used Kafka" but "do you reach for infrastructure because a
problem demands it, or because it's familiar/impressive." The second
instinct is the one senior engineers are trained out of.

---

## 5. Trade-off table (good for a whiteboard-style follow-up)

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Persistence | Postgres | SQLite (original) | Concurrent writers, survives container restarts |
| Session state | Redis (shared) | In-process dict (original) | Correctness across multiple worker processes, not speed |
| LLM cost control | Exact-match cache | Semantic/fuzzy cache | Zero risk of returning an answer that doesn't fit the live conversation |
| Real-time fan-out | Redis pub/sub + WebSocket | Kafka | No durability/replay/ordering need yet; avoids a new managed-service dependency |
| Classification | Multi-turn, confidence-gated | Single-message, always-switch (original) | Prevents state oscillation on weak/ambiguous signals |
| Model selection | Runtime discovery via Groq API | Hardcoded model names (original) | Survives vendor-side renames/deprecations without a code change |

---

## 6. Q&A drill — say these out loud once before the interview

**Q: What's the single biggest bug you found, and how did you find it?**
A: The frontend rendering widgets based on keyword-matching the assistant's
own text instead of only the typed actions array. I found it by tracing
*why* a specific reply produced a fabric gallery when the model hadn't
asked for one — reading `addMessageToChat()` line by line rather than
assuming the prompt was the whole story.

**Q: Isn't caching LLM responses dangerous — how do you know it won't go
stale or wrong?**
A: It's exact-match only — same model, same system prompt, same full
message history, hashed. It can't return an answer that fits a different
conversation because it will never match a different conversation. The
trade is a lower hit rate in exchange for zero correctness risk, which is
the right trade for a customer-facing agent.

**Q: How would two customers adding the last unit of the same product at
the same time be handled — is there a race condition?**
A: Yes, worth being honest about this one: the current `decrement_stock`
does a read-then-write inside one DB transaction per call, which is safe
against corruption (Postgres serializes the row-level update) but not
against a mild overselling race under high concurrency without an
additional `CHECK (quantity >= 0)` constraint or a `SELECT ... FOR UPDATE`.
At current scale (dozens of concurrent shoppers, not thousands) this hasn't
been a practical problem, but it's the honest next hardening step, not
something I'd claim is already bulletproof.

**Q: Why not just use a vector DB / semantic search for the workflow
routing instead of keyword scoring?**
A: The current classifier is a fast, fully deterministic, explainable
scoring function over ~120 hand-authored workflow templates — you can
always say exactly why a message routed where it did, which matters for
debugging a customer complaint ("why did the bot ask me that"). A
vector/embedding approach would generalize better to phrasing the templates
don't anticipate, at the cost of losing that explainability and adding an
embedding-model dependency and latency per turn. Worth doing if the
template library stops covering real traffic — not clearly worth it yet.

**Q: What would you do next if you had another week?**
A: Streaming responses (currently the frontend waits for the full JSON
body — streaming would make the same-quality answers feel much more
responsive), surfacing when the app has silently fallen back to a weaker
model so degraded quality is diagnosable instead of invisible, rate
limiting on the chat endpoint (there's currently none, and the Groq calls
are the real cost driver), and the stock-race hardening mentioned above.

---

## 7. One thing to actually believe, not just say

Every fix above followed the same method: don't add infrastructure because
it's the "correct-sounding" answer — find the actual failure mode first
(a bug reproduced, a cost line item, a vendor API breaking in production),
then pick the smallest thing that fixes that specific failure mode. That's
the throughline across Postgres, Redis, the caching design, and the Kafka
non-decision. If an interviewer asks about any piece of this stack, that's
the frame to answer from — not "I used X," but "X fixed this specific,
demonstrable problem, and here's what would have to change for a different
answer to become correct."
