from __future__ import annotations

import json
import os
import re
import time
from datetime import date
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from groq import Groq

import fashion_knowledge
import fulfillment
import outfit_planner
import product_catalog
from agent_store import (
    decrement_stock,
    get_customer_profile,
    get_order_history,
    get_session_snapshot,
    record_event,
    record_order,
    upsert_customer_profile,
    upsert_session,
)
from redis_layer import get_cached_response, get_session_state, publish_event, set_cached_response, set_session_state
from workflow_catalog import classify_conversation, related_workflows, render_workflow_brief


def _get_session_memory(session_id: str) -> Dict[str, Any]:
    return get_session_state(session_id) or {}


def _set_session_memory(session_id: str, value: Dict[str, Any]) -> None:
    set_session_state(session_id, value)

ALLOWED_ACTION_TYPES = {
    "navigate",
    "select_product",
    "customize_fabric",
    "customize_measurements",
    "schedule_technician",
    "add_to_bag",
    "open_cart",
    "show_workflow_summary",
    "capture_lead",
    "show_recommendations",
    "compare_products",
    "request_photo",
    "show_style_preview",
    "set_budget",
    "offer_alternative",
    "show_shipping",
    "request_measurements",
    "create_quote",
    "handoff_human",
    "save_preferences",
    "start_consultation",
    "present_options",
    "outfit_plan",  # deterministic, backend-computed - see _maybe_attach_outfit_plan
    "delivery_estimate",  # deterministic, backend-computed - see fulfillment.py
}

ALLOWED_PAGES = {"home", "men", "women", "accessories"}
ALLOWED_PRODUCT_IDS = {"silver-slate", "pearl-white", "umber-pinstripe", "soot-black", "misty-aqua", "charcoal-blazer", "printed-tie-combo", "mens-belt"}
ALLOWED_FABRIC_TYPES = {"same", "catalog", "own"}
ALLOWED_HEIGHTS = {"short", "regular", "tall"}
ALLOWED_BODY_TYPES = {"ectomorph_men", "mesomorph_men", "endomorph_men"}
ALLOWED_SIZE_METHODS = {"ready", "custom"}
ALLOWED_FITTINGS = {"regular_fit", "slim_fit", "loose_fit"}
ALLOWED_CITIES = {"Mumbai", "Bangalore", "Gurgaon"}
FABRIC_NAMES = {
    "D 963/1 - Suit Soft stone",
    "AC 103/1 - Suit Pearl",
    "AC 103/2 - Suit Navy",
    "AC 103/8 - Suit Beige",
    "AW 267/3 - Jacket Fawn",
    "AW 268/1 - Jacket Cobalt blue",
    "CHARCOAL DUSK TWILL - PDW40",
    "D 922/3 - Suit Steal blue",
    "D 936/2 - Suit Burnt maroon",
    "D 959/2 - Suit Hunter green",
    "DRIFTWOOD BEIGE - PDW13",
    "ICY SKY MIST - PDW04",
    "MISTY AQUA - PDW06",
    "STEEL SHADOW TWILL - S15",
    "V 712/11 - Jacket Soft Pink",
    "V 712/12 - Jacket Pistachio",
    "V 712/13 - Jacket Mauve Grey",
    "V 712/3 - Bandhgala Burgundy",
    "WD 201/2 - Suit Royal blue",
    "WL 212/1 - Jacket Blush",
}


class AgentState(TypedDict, total=False):
    session_id: str
    messages: List[Dict[str, str]]
    workflow_id: str
    workflow_title: str
    intent_bucket: str
    workflow_summary: str
    branch: str
    system_prompt: str
    response: str
    actions: List[Dict[str, Any]]
    error: str


def _last_user_message(messages: List[Dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _branch_for_bucket(intent_bucket: str) -> str:
    if intent_bucket in {"ready_to_buy", "exploring"}:
        return "sales"
    if intent_bucket == "corporate_lead":
        return "corporate"
    if intent_bucket == "customer_support":
        return "support"
    if intent_bucket == "researching_styles":
        return "research"
    return "explore"


def _session_fallback(session_id: str, selected_workflow, selected_score: int) -> Any:
    """Decide whether to keep the customer on their existing workflow or move
    them to the newly classified one.

    The original version switched workflows the instant the newly classified
    intent_bucket differed at all from the previous turn's bucket. Since
    classification only ever looked at the single latest user message, one
    short reply like "yes", "ok", or "the blue one" (which scores weakly
    against every workflow) was enough to bounce the conversation to a
    different branch/system-prompt every turn - this is a big part of why
    conversations felt disjointed and answers felt clipped: the agent kept
    restarting its own frame of reference.

    Now we only actually switch when the new classification is a *strong*
    match (comfortably above the "no confident match" floor) - a weak/ambiguous
    signal keeps the customer on their current workflow instead of yanking
    them somewhere new.
    """
    previous = _get_session_memory(session_id)
    previous_workflow = previous.get("workflow_id")
    if not previous_workflow:
        snapshot = get_session_snapshot(session_id)
        if snapshot and snapshot.get("workflow_id"):
            previous_workflow = snapshot["workflow_id"]

    if not previous_workflow:
        return selected_workflow

    from workflow_catalog import WORKFLOW_INDEX

    previous = WORKFLOW_INDEX.get(previous_workflow)
    if not previous:
        return selected_workflow

    if selected_workflow.id == "master_entry":
        return previous

    STRONG_MATCH_THRESHOLD = 6  # matches one full trigger-phrase hit (see _score_workflow)
    if selected_score < STRONG_MATCH_THRESHOLD and previous.intent_bucket == selected_workflow.intent_bucket:
        return previous
    if selected_score < STRONG_MATCH_THRESHOLD and selected_workflow.id != previous.id:
        # Weak signal and a different workflow than before - stay put rather
        # than flip-flopping on a low-confidence read of one message.
        return previous

    return selected_workflow


def _branch_prompt(branch: str) -> str:
    prompts = {
        "sales": (
            "Drive toward selection, sizing, fabric choice, and checkout. "
            "Be concise, guide the customer to the next conversion step, and present clear options or product cards."
        ),
        "support": (
            "Handle the issue with empathy and operational clarity. "
            "Collect the minimum details needed for a resolution or human handoff."
        ),
        "corporate": (
            "Treat the request as a B2B quote or procurement workflow. "
            "Ask for quantities, locations, deadlines, and branding details."
        ),
        "research": (
            "Focus on education, comparison, and preference gathering. "
            "Help the customer narrow choices without pushing too early."
        ),
        "explore": (
            "Act like a premium stylist and discovery assistant. "
            "Classify intent, ask one good question, and surface the best next options."
        ),
    }
    return prompts[branch]


def _extract_session_slots(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    text = " ".join([m.get("content", "").lower() for m in messages if m.get("role") == "user"])
    slots = {}
    if "shirt" in text:
        slots["garment"] = "Custom Shirt"
    elif "suit" in text or "tuxedo" in text or "blazer" in text:
        slots["garment"] = "Custom Suit"
    elif "trouser" in text or "pant" in text or "chino" in text:
        slots["garment"] = "Trousers"
    elif "wedding" in text or "groom" in text:
        slots["garment"] = "Wedding Wear"
    elif "ethnic" in text or "kurta" in text or "sherwani" in text:
        slots["garment"] = "Ethnic Wear"
    elif "accessory" in text or "tie" in text or "belt" in text:
        slots["garment"] = "Accessories"

    for occ in ["office", "wedding", "party", "casual", "interview", "travel", "diwali", "reception"]:
        if occ in text:
            slots["occasion"] = occ.title()
            break

    for fab in ["wool", "cashmere", "linen", "cotton", "silk", "soft stone", "pearl", "navy", "cobalt"]:
        if fab in text:
            slots["fabric"] = fab.title()
            break

    for fit in ["slim", "regular", "relaxed", "loose"]:
        if fit in text:
            slots["fit"] = fit.title()
            break

    for city in ["mumbai", "bangalore", "gurgaon"]:
        if city in text:
            slots["city"] = city.title()
            break

    budget = _extract_budget(text)
    if budget:
        slots["budget"] = budget
    else:
        # No number given, but the customer may still have signaled that
        # budget matters to them ("low on budget", "keep it cheap"). This
        # used to fall through silently - the model had nothing telling it
        # budget was even relevant, so it kept asking about fabric/style and
        # only circled back to budget as an afterthought near the end.
        # Surfacing this as its own slot lets the system prompt explicitly
        # tell the model to pin down a real number *now*, not later.
        for phrase in ["low budget", "low on budget", "tight budget", "keep it cheap", "cheap", "affordable", "budget friendly", "budget-friendly", "inexpensive", "economical", "not expensive"]:
            if phrase in text:
                slots["budget_sensitivity"] = "price-conscious (no number given yet)"
                break

    event_date = _extract_event_date(messages)
    if event_date:
        slots["event_date"] = event_date

    return slots


_BUDGET_PATTERN = re.compile(
    r"(?:budget|under|within|below|less than|around|about)?\s*(?:rs\.?|inr|₹)?\s*"
    r"(\d[\d,]*)\s*(k|000)?",
    re.IGNORECASE,
)


def _extract_budget(text: str) -> Optional[int]:
    """Best-effort extraction of a stated budget figure, e.g. "under 25k",
    "budget is around 30000", "₹20,000". Deliberately conservative - only
    fires near an actual budget-signaling word or a rupee marker, so it
    doesn't misfire on unrelated numbers (a phone number, a date)."""
    if not any(marker in text for marker in ["budget", "₹", "rs.", "rs ", "inr", "afford", "spend"]):
        return None
    for match in _BUDGET_PATTERN.finditer(text):
        digits, thousands_suffix = match.group(1), match.group(2)
        if not digits:
            continue
        value = int(digits.replace(",", ""))
        if thousands_suffix and thousands_suffix.lower() == "k":
            value *= 1000
        if 500 <= value <= 2_000_000:  # sane range for this catalog; filters out stray small numbers
            return value
    return None


_MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_MONTH_ALTERNATION = "|".join(sorted(_MONTH_NAMES.keys(), key=len, reverse=True))

_DATE_WITH_MONTH_PATTERN = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_ALTERNATION})\b"
    rf"|\b({_MONTH_ALTERNATION})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b",
    re.IGNORECASE,
)

_BARE_ORDINAL_PATTERN = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b")

# Phrases in an assistant message that mean "what date is your event",
# so a bare ordinal reply right after one of these ("12th") can be read as
# the event date rather than requiring the customer to spell out a month.
_DATE_QUESTION_MARKERS = [
    "when is your wedding", "when is the wedding", "when's your wedding",
    "when is your event", "when is your function", "what date",
    "which date", "what's the date", "date is it", "date works for you",
]


def _resolve_day_to_date(day: int, month: Optional[int] = None) -> Optional[str]:
    """Turn a stated day (and optional month) into a concrete ISO date,
    always resolving to the next real future occurrence - customers state
    an event date relative to "soon", never a date that already passed."""
    today = date.today()
    year = today.year
    target_month = month or today.month
    try:
        candidate = date(year, target_month, day)
    except ValueError:
        return None
    if candidate < today:
        if month:
            candidate = date(year + 1, target_month, day)
        else:
            next_month = target_month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            try:
                candidate = date(next_year, next_month, day)
            except ValueError:
                return None
    return candidate.isoformat()


def _extract_event_date(messages: List[Dict[str, str]]) -> Optional[str]:
    """Best-effort extraction of a stated event date (a wedding, a function,
    a travel date) so delivery/lead-time math (see fulfillment.py) has
    something concrete to check against. Without this, "schedule a visit"
    had no idea a wedding was 3 days away and stitching alone takes longer
    than that."""
    full_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")

    match = _DATE_WITH_MONTH_PATTERN.search(full_text)
    if match:
        if match.group(1):
            day, month_name = int(match.group(1)), match.group(2)
        else:
            month_name, day = match.group(3), int(match.group(4))
        month = _MONTH_NAMES.get(month_name.lower())
        if month:
            resolved = _resolve_day_to_date(day, month)
            if resolved:
                return resolved

    # A bare ordinal ("12th") given as a reply right after the assistant
    # asked specifically when the event is - the common real case ("When is
    # your wedding?" -> "12th"). Scan every adjacent pair, not just the most
    # recent, so this stays known on later turns of the same conversation.
    for i in range(1, len(messages)):
        if messages[i].get("role") != "user" or messages[i - 1].get("role") != "assistant":
            continue
        prior_text = messages[i - 1].get("content", "").lower()
        if any(marker in prior_text for marker in _DATE_QUESTION_MARKERS):
            ordinal_match = _BARE_ORDINAL_PATTERN.search(messages[i].get("content", ""))
            if ordinal_match:
                resolved = _resolve_day_to_date(int(ordinal_match.group(1)))
                if resolved:
                    return resolved

    return None


_BUDGET_HINT_CACHE: Optional[str] = None


def _budget_band_hint() -> str:
    """Real-terms guardrail for rule 1's budget-range prompting. The model
    was previously left to invent its own example bands ("Under ₹2,000",
    "₹2,000-₹4,000" ...) which are off by roughly an order of magnitude from
    what anything in the catalog actually costs (₹18,000-₹38,000 for a main
    garment) - so a customer picking any of those "budget" bands was really
    picking a fantasy number the recommendations then ignored entirely.
    Computing real bands from product_catalog means the example the model
    sees is always anchored to what's actually for sale."""
    global _BUDGET_HINT_CACHE
    if _BUDGET_HINT_CACHE is not None:
        return _BUDGET_HINT_CACHE

    prices = []
    for gender in ("men", "women"):
        for pid in product_catalog.main_garments(gender):
            product = product_catalog.get_product(pid)
            if product:
                prices.append(product["price"])

    if not prices:
        _BUDGET_HINT_CACHE = ""
        return _BUDGET_HINT_CACHE

    lo, hi = min(prices), max(prices)
    third = max((hi - lo) // 3, 1)
    q1, q2 = lo + third, lo + 2 * third

    def fmt(n: int) -> str:
        return f"₹{n:,}"

    _BUDGET_HINT_CACHE = (
        f"Our garments actually run about {fmt(lo)}-{fmt(hi)} - so realistic bands look like "
        f'"Under {fmt(q1)}", "{fmt(q1)}-{fmt(q2)}", "{fmt(q2)}-{fmt(hi)}", "Above {fmt(hi)}" '
        f"(adjust to the specific item category, e.g. accessories are far cheaper). Never propose "
        f'bands like "Under ₹2,000" for a garment - that is off by an order of magnitude from what '
        f"anything here costs and makes every recommendation look like it ignored the stated budget."
    )
    return _BUDGET_HINT_CACHE


def _build_system_prompt(
    workflow,
    related,
    branch: str,
    messages: List[Dict[str, str]] = None,
    session_id: Optional[str] = None,
) -> str:
    related_text = "\n".join([f"- {item.title} ({item.id})" for item in related]) if related else "- None"
    messages = messages or []
    slots = _extract_session_slots(messages)
    turn_count = len([m for m in messages if m.get("role") == "user"])

    profile = get_customer_profile(session_id) if session_id else None
    body_type = profile.get("body_type") if profile else None
    order_history = get_order_history(session_id, limit=5) if session_id else []

    fashion_context = fashion_knowledge.build_fashion_context(slots, body_type=body_type)

    profile_lines = []
    if profile:
        known = {k: v for k, v in profile.items() if v and k not in {"session_id", "updated_at"}}
        if known:
            profile_lines.append(f"- Returning customer profile on file: {json.dumps(known)}")
    if order_history:
        past_items = ", ".join(
            f"{o['product_name'] or o['product_id']} (₹{o['price']})" for o in order_history if o.get("product_id")
        )
        if past_items:
            profile_lines.append(f"- Past purchases on this device: {past_items}")
    profile_section = "\n".join(profile_lines) if profile_lines else "- No returning-customer data on file yet."

    return f"""You are the TechTailor AI Concierge & Executive Shopping Assistant.
You are operating inside a LangGraph workflow to guide customers from discovery to customization, sizing, and checkout.

Selected workflow:
{render_workflow_brief(workflow)}

Branch policy:
{_branch_prompt(branch)}

Related workflows:
{related_text}

Session Memory State:
- Turn Count: {turn_count}
- Already Identified Details: {json.dumps(slots) if slots else "None yet"}

Customer History (from previous visits on this device, if any - use it, don't ask for what's already known here):
{profile_section}

{fashion_context if fashion_context else ""}

SHOPPING AGENT RULES:
1. PROGRESS THE SHOPPING FUNNEL, IN THIS ORDER - Garment -> Occasion -> Budget -> Fabric/Product Recommendation -> Sizing/Measurements -> Add to Bag. Budget comes BEFORE fabric/style choices, not after - narrowing down fabric or styling options before you know the budget means you may walk the customer through choices they can't actually afford, then have to backtrack. Do NOT ask the same question twice if details are already in 'Already Identified Details' or 'Customer History'. If a returning customer's body type, fit, or past purchases are on file, reuse them by default and only ask if they want something different this time. If 'Already Identified Details' shows a `budget_sensitivity` value (the customer said something like "low budget" or "keep it cheap" without giving an actual number), treat that as a signal to ask for a concrete budget range right now with a `present_options` action BEFORE moving on to fabric or style - don't let it sit unresolved until the end of the conversation. {_budget_band_hint()}
2. CLICKABLE OPTIONS, WHEN THEY ACTUALLY HELP: If your reply asks the customer to pick between a small set of concrete choices (an occasion, a fabric family, a size), include a `present_options` action with 3-5 options.
   Example action: `{{"type": "present_options", "title": "Choose Occasion", "options": ["Office Formal", "Wedding Reception", "Casual Weekend", "Party Wear"]}}`
   Do NOT attach `present_options` to a reply that isn't actually posing that kind of choice (a plain answer, an acknowledgement, small talk) - forcing a widget onto every message is what makes the chat feel cluttered.
3. VISUAL PRODUCT & FABRIC RECOMMENDATIONS, ON REQUEST OR AT A REAL DECISION POINT: When you are recommending specific garments for the customer to choose between, output one `show_recommendations` action with product IDs (`silver-slate`, `pearl-white`, `umber-pinstripe`, `soot-black`, `misty-aqua`, `printed-tie-combo`, `mens-belt`). When you're actually walking them through fabric choices, output one `customize_fabric` action. Merely using the word "fabric" or "recommend" in a sentence is not itself a reason to attach one of these - only attach it when you are presenting products/fabrics for them to pick from right now, and don't stack more than one visual action in a single reply.
4. GROUND RECOMMENDATIONS IN THE FASHION KNOWLEDGE ABOVE, WHEN PRESENT: if a "Fashion Knowledge" section is included, use its specific facts (formality level, fabric warmth, body-type fit guidance) to explain *why* something suits the customer, instead of a generic assertion like "this looks great on you." If there's no Fashion Knowledge section, don't invent styling facts you're not confident are true.
5. SIZING & TAILORING - ALWAYS OFFER ALL THREE PATHS, NOT JUST A VISIT: The first time sizing/fit/measurements comes up in a conversation, do not jump straight to `schedule_technician`. Instead present the customer a real choice with a `present_options` action titled "How would you like to get sized?" and exactly these three options: "Enter Measurements Manually", "Schedule a Doorstep Visit", "Try It On Virtually (Beta)". Then, based on which one they pick on their next message:
   - "Enter Measurements Manually" -> output `request_measurements`.
   - "Schedule a Doorstep Visit" -> if you don't yet know the city, ask with `present_options` (options: "Mumbai", "Bangalore", "Gurgaon"); once you know the city, output `schedule_technician` with that city.
   - "Try It On Virtually (Beta)" -> output `request_photo`. This feature is a placeholder today (say so plainly - "virtual try-on is in beta, here's a placeholder preview for now" - don't overpromise a live camera/AR experience), but still acknowledge the choice and keep the conversation moving (e.g. ask what garment they'd like previewed, or offer to continue with manual sizing instead).
   Whichever path they pick, always continue the conversation naturally afterward - don't treat any of these three as a dead end.
5b. ASK FOR AN EVENT DATE WHENEVER THE OCCASION IMPLIES ONE: if the occasion is tied to a specific date (a wedding, a reception, any function - not "office wear" or "casual weekend"), ask when it is if you don't already know, e.g. "When is the wedding/reception?" - a plain day or day+month answer is fine, don't demand a full formatted date. This is what makes rule 5c possible.
5c. RESPECT THE `delivery_estimate` ACTION WHEN IT APPEARS: the backend attaches this automatically once you know both a sizing method (from rule 5) and an event date (from rule 5b) - it tells you the earliest realistic delivery date for that method and, if `can_make_it` is `false`, that the finished garment likely won't arrive before the stated event. When you see `can_make_it: false`, say so plainly and honestly (don't bury it or soften it into nothing) and proactively suggest a faster path - e.g. a doorstep visit takes longer than manual measurements because of technician scheduling, so recommend manual measurements or an in-stock ready-to-wear option instead if the event is close. When `can_make_it` is `true`, you don't need to dwell on it - a brief one-line reassurance ("that'll comfortably reach you before the 12th") is enough.
6. DRIVE TO CART: When the customer expresses clear interest in buying or ordering a specific item, output `add_to_bag` or `open_cart`.
7. RESPONSE LENGTH SHOULD MATCH THE MOMENT: a confirmation or a direct answer can be one short sentence; a recommendation or an explanation the customer asked for deserves the room to actually say something useful (a real sentence or two of reasoning, not just a label). Never pad, but never clip a genuinely useful answer down to a fragment just to "be concise" - a one-word reply to a real question reads as broken, not efficient. Sound like a knowledgeable, warm human stylist having a conversation, not a form generating field prompts.
8. Note: a complete outfit plan (garment + accessory, styled to the occasion and any budget mentioned) is computed automatically by the backend when enough is known - you do not need to build one yourself; just keep the conversation natural.

Return valid JSON with keys: response and actions."""


def _call_model(messages: List[Any], model_name: str) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        messages=messages,
        model=model_name,
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    content = response.choices[0].message.content or "{}"
    return _parse_json_blob(content)


_MODEL_CACHE: Dict[str, Any] = {"ids": None, "fetched_at": 0.0}
_MODEL_CACHE_TTL_SECONDS = 600  # Groq's lineup shifts periodically; re-check
                                  # every 10 minutes rather than hardcoding
                                  # names that quietly go stale/get retired.

# Preferred substrings, in priority order, used to pick a sensible default
# out of whatever Groq is actually serving right now. This is a *preference*,
# not a requirement - if none of these match anything available, we just use
# whatever the account does have access to rather than failing outright.
_PREFERRED_MODEL_HINTS = ["versatile", "70b", "instant", "8b"]


def _fetch_available_model_ids() -> List[str]:
    """Ask Groq what this account can actually use right now, instead of
    trusting a hardcoded model name that may have been renamed or retired
    since this code was written (this is exactly what broke: the app kept
    trying `llama-3.1-8b-instant`/`llama-3.3-70b-versatile` even after Groq
    stopped serving them for this account, and had no way to notice)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return []
    try:
        client = Groq(api_key=api_key)
        response = client.models.list()
        return [m.id for m in getattr(response, "data", []) if getattr(m, "id", None)]
    except Exception:
        return []


def _model_candidates() -> List[str]:
    configured = os.getenv("GROQ_MODEL", "").strip()

    now = time.time()
    if _MODEL_CACHE["ids"] is None or (now - _MODEL_CACHE["fetched_at"]) > _MODEL_CACHE_TTL_SECONDS:
        fetched = _fetch_available_model_ids()
        if fetched:
            _MODEL_CACHE["ids"] = fetched
            _MODEL_CACHE["fetched_at"] = now

    available = _MODEL_CACHE["ids"] or []

    candidates: List[str] = []
    if configured:
        candidates.append(configured)

    if available:
        # Rank whatever's actually available by our preference hints, most
        # preferred first, then append anything left over as a last resort.
        def _rank(model_id: str) -> int:
            lowered = model_id.lower()
            for i, hint in enumerate(_PREFERRED_MODEL_HINTS):
                if hint in lowered:
                    return i
            return len(_PREFERRED_MODEL_HINTS)

        candidates.extend(sorted(available, key=_rank))
    else:
        # Discovery failed (no key yet, or Groq unreachable) - fall back to
        # the last known-good names as a best-effort guess rather than
        # having zero candidates at all.
        candidates.extend(["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])

    seen = set()
    ordered: List[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _parse_json_blob(content: str) -> Dict[str, Any]:
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise


def _normalize_actions(actions: Any, workflow_id: str) -> List[Dict[str, Any]]:
    if not isinstance(actions, list):
        return []

    cleaned: List[Dict[str, Any]] = []
    for item in actions:
        if not isinstance(item, dict):
            continue
        action_type = item.get("type")
        if action_type not in ALLOWED_ACTION_TYPES:
            continue

        normalized: Dict[str, Any] = {"type": action_type}

        if action_type == "navigate":
            page = item.get("page")
            normalized["page"] = page if page in ALLOWED_PAGES else "men"
        elif action_type == "select_product":
            product_id = item.get("product_id")
            normalized["product_id"] = product_id if product_id in ALLOWED_PRODUCT_IDS else "silver-slate"
        elif action_type == "customize_fabric":
            normalized["fabric_type"] = item.get("fabric_type", "catalog")
            if item.get("fabric_name"):
                normalized["fabric_name"] = item["fabric_name"]
        elif action_type == "customize_measurements":
            for field in ["height", "body_type", "size_method", "ready_jacket_size", "ready_trouser_size", "fitting", "custom_measurements"]:
                if field in item:
                    normalized[field] = item[field]
        elif action_type == "schedule_technician":
            if item.get("city"):
                normalized["city"] = item["city"]
            if item.get("date"):
                normalized["date"] = item["date"]
        elif action_type == "present_options":
            normalized["title"] = item.get("title", "Select an option:")
            opts = item.get("options", [])
            if isinstance(opts, list):
                normalized["options"] = [str(o) for o in opts]
        elif action_type in {"show_recommendations", "compare_products", "offer_alternative"}:
            if item.get("product_ids") and isinstance(item["product_ids"], list):
                normalized["product_ids"] = item["product_ids"]
            elif item.get("product_id"):
                normalized["product_ids"] = [item["product_id"]]
            else:
                normalized["product_ids"] = ["silver-slate", "pearl-white"]
            if item.get("title"):
                normalized["title"] = item["title"]
        else:
            for k, v in item.items():
                normalized[k] = v

        cleaned.append(normalized)
    return cleaned


def _generate_response(state: AgentState, branch: str) -> AgentState:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "response": "No Groq API Key is configured yet. Set it in the top-right panel to activate the agent.",
            "actions": [],
        }

    workflow_id = state["workflow_id"]
    from workflow_catalog import WORKFLOW_INDEX

    session_id = state.get("session_id") or "default"
    workflow = WORKFLOW_INDEX[workflow_id]
    related = related_workflows(workflow)
    system_prompt = state.get("system_prompt") or _build_system_prompt(
        workflow, related, branch, state.get("messages", []), session_id=session_id
    )
    api_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for message in state["messages"]:
        role = message.get("role")
        content = message.get("content", "")
        if role in {"user", "assistant", "system"}:
            api_messages.append({"role": role, "content": content})

    primary_model = _model_candidates()[0] if _model_candidates() else "unknown"
    cached = get_cached_response(primary_model, system_prompt, api_messages)
    if cached is not None:
        response_json = cached
    else:
        response_json = None
        last_error: Optional[Exception] = None
        for model_name in _model_candidates():
            try:
                response_json = _call_model(api_messages, model_name)
                break
            except Exception as exc:
                last_error = exc
        if response_json is None:
            return {
                "response": "I could not generate a structured response from the model right now. Please try again.",
                "actions": [],
                "error": str(last_error) if last_error else "Unknown Groq error",
            }
        set_cached_response(primary_model, system_prompt, api_messages, response_json)

    if not isinstance(response_json, dict):
        response_json = {"response": str(response_json), "actions": []}

    response_text = response_json.get("response", "")
    actions = _normalize_actions(response_json.get("actions", []), workflow.id)
    actions = _enrich_actions(session_id, state.get("messages", []), actions)
    return {
        "response": response_text,
        "actions": actions,
    }


def _enrich_actions(session_id: str, messages: List[Dict[str, str]], actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Everything in this function is deterministic arithmetic against
    product_catalog/fashion_knowledge/outfit_planner - none of it is another
    LLM call. This is where "the model said to recommend X" turns into "and
    here's a grounded, rule-based score for why X suits them," and where a
    customer's stated measurements get persisted for next time."""
    slots = _extract_session_slots(messages)

    # 0. Deterministic backstop for the sizing-path choice. The model is
    #    told (rule 5) to honor whichever of "Enter Measurements Manually" /
    #    "Schedule a Doorstep Visit" / "Try It On Virtually" the customer
    #    just picked, but in practice it sometimes attaches the wrong action
    #    anyway (seen live: customer picks "Enter Measurements Manually" and
    #    still gets the doorstep-visit widget). Since the customer's last
    #    message is one of a handful of literal button labels/city names in
    #    this flow, it's cheap to just check it directly and correct the
    #    action list rather than trust the model got it right.
    last_user_text = _last_user_message(messages).lower() if messages else ""
    _CITY_WORDS = ["mumbai", "bangalore", "gurgaon"]
    wants_manual = any(p in last_user_text for p in ["enter measurements manually", "manually", "enter my measurements"])
    wants_visit = any(p in last_user_text for p in ["doorstep", "schedule a visit", "schedule visit", "technician visit"]) or any(
        c in last_user_text for c in _CITY_WORDS
    )
    wants_virtual = any(p in last_user_text for p in ["try it on virtually", "virtual try-on", "virtually"])

    if wants_manual and not wants_visit:
        actions = [a for a in actions if a.get("type") != "schedule_technician"]
        if not any(a.get("type") == "request_measurements" for a in actions):
            actions.append({"type": "request_measurements"})
    elif wants_visit and not wants_manual:
        actions = [a for a in actions if a.get("type") != "request_measurements"]
        if not any(a.get("type") == "schedule_technician" for a in actions):
            city = next((c for c in _CITY_WORDS if c in last_user_text), None)
            visit_action: Dict[str, Any] = {"type": "schedule_technician"}
            if city:
                visit_action["city"] = city.capitalize()
            actions.append(visit_action)
    elif wants_virtual:
        actions = [a for a in actions if a.get("type") not in {"request_measurements", "schedule_technician"}]
        if not any(a.get("type") in {"request_photo", "show_style_preview"} for a in actions):
            actions.append({"type": "request_photo"})

    # 0b. Delivery/lead-time reality check. Whichever sizing method just got
    #     confirmed above (manual measurements, a doorstep visit, virtual
    #     try-on), and if the customer has stated an event date, compute
    #     whether a finished garment can actually get to them in time - and
    #     say so, rather than silently confirming a visit/method that can't
    #     possibly make it. Only attached once per distinct (method,
    #     event_date) combination so it doesn't repeat every turn.
    sizing_action = next(
        (a for a in actions if a.get("type") in {"request_measurements", "schedule_technician", "request_photo", "show_style_preview"}),
        None,
    )
    if sizing_action:
        method = fulfillment.method_for_action(sizing_action["type"])
        if method:
            event_date = slots.get("event_date")
            signature = f"{method}:{event_date}"
            session_memory = _get_session_memory(session_id)
            if session_memory.get("delivery_estimate_signature") != signature:
                estimate = fulfillment.estimate(method, event_date)
                actions.append({"type": "delivery_estimate", **estimate})
                session_memory["delivery_estimate_signature"] = signature
                _set_session_memory(session_id, session_memory)

    # 1. Persist measurements the moment they're given, so a *future* visit
    #    (see get_customer_profile in _build_system_prompt) doesn't have to
    #    ask again.
    for action in actions:
        if action.get("type") == "customize_measurements":
            upsert_customer_profile(
                session_id,
                body_type=action.get("body_type"),
                height=action.get("height"),
                fitting=action.get("fitting"),
                size_method=action.get("size_method"),
                measurements=action.get("custom_measurements"),
            )

    profile = get_customer_profile(session_id)
    body_type = profile.get("body_type") if profile else None
    occasion = slots.get("occasion")

    # 2. Attach a grounded style score to every product a recommendation
    #    action surfaces, plus a compatibility score across the set.
    for action in actions:
        if action.get("type") in {"show_recommendations", "compare_products", "offer_alternative"}:
            product_ids = action.get("product_ids") or []
            scores = {}
            for pid in product_ids:
                score, rationale = fashion_knowledge.style_score(pid, occasion=occasion, body_type=body_type)
                scores[pid] = {"style_score": score, "rationale": rationale}
            if scores:
                action["product_scores"] = scores
            if len(product_ids) > 1:
                compat_score, compat_rationale = fashion_knowledge.compatibility_score(product_ids)
                action["compatibility_score"] = compat_score
                action["compatibility_rationale"] = compat_rationale
        elif action.get("type") == "add_to_bag" and action.get("product_id"):
            score, rationale = fashion_knowledge.style_score(action["product_id"], occasion=occasion, body_type=body_type)
            action["style_score"] = score
            action["style_rationale"] = rationale

    # 3. Auto-plan a complete outfit once we know enough (occasion + a
    #    garment category that isn't accessories-only), whether or not a
    #    budget was ever stated - this is the actual fix for "doesn't plan
    #    an outfit within budget when one isn't specified." Only attach it
    #    once per distinct (occasion, budget) combination for this session,
    #    so it doesn't repeat on every turn once shown.
    garment = slots.get("garment")
    if occasion and garment and garment != "Accessories":
        budget = slots.get("budget")
        signature = f"{occasion}:{budget}"
        session_memory = _get_session_memory(session_id)
        if session_memory.get("outfit_plan_signature") != signature:
            # No gender slot is extracted from chat text today, and the
            # catalog is men-led (2 of 8 SKUs are women's, with no women's
            # accessories yet) - defaulting to "men" here is an honest
            # limitation of the current catalog, not a hidden assumption;
            # worth revisiting once gender is captured as its own slot.
            gender = "men"
            plan = outfit_planner.plan_outfit(
                occasion=occasion.lower(), budget=budget, gender=gender, body_type=body_type
            )
            if plan.get("items"):
                actions.append({"type": "outfit_plan", **plan})
            session_memory["outfit_plan_signature"] = signature
            _set_session_memory(session_id, session_memory)

    return actions


def _route_workflow(state: AgentState) -> AgentState:
    session_id = state.get("session_id") or "default"
    last_user = _last_user_message(state["messages"])
    recent_user_messages = [m.get("content", "") for m in state["messages"] if m.get("role") == "user"]
    selected, score = classify_conversation(recent_user_messages)
    selected = _session_fallback(session_id, selected, score)
    branch = _branch_for_bucket(selected.intent_bucket)
    session_memory = _get_session_memory(session_id)
    session_memory["workflow_id"] = selected.id
    _set_session_memory(session_id, session_memory)
    upsert_session(
        session_id=session_id,
        workflow_id=selected.id,
        workflow_title=selected.title,
        intent_bucket=selected.intent_bucket,
        workflow_summary=selected.summary,
        branch=branch,
    )
    record_event(
        session_id,
        "route_decision",
        {
            "workflow_id": selected.id,
            "workflow_title": selected.title,
            "intent_bucket": selected.intent_bucket,
            "branch": branch,
            "last_user_message": last_user[:500],
        },
    )
    return {
        "workflow_id": selected.id,
        "workflow_title": selected.title,
        "intent_bucket": selected.intent_bucket,
        "workflow_summary": selected.summary,
        "branch": branch,
    }


def _sales_node(state: AgentState) -> AgentState:
    return _generate_response(state, "sales")


def _support_node(state: AgentState) -> AgentState:
    return _generate_response(state, "support")


def _corporate_node(state: AgentState) -> AgentState:
    return _generate_response(state, "corporate")


def _research_node(state: AgentState) -> AgentState:
    return _generate_response(state, "research")


def _explore_node(state: AgentState) -> AgentState:
    return _generate_response(state, "explore")


def _persist_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id") or "default"
    previous = _get_session_memory(session_id)
    if state.get("workflow_id"):
        previous["workflow_id"] = state["workflow_id"]
        previous["workflow_title"] = state.get("workflow_title", "")
        previous["intent_bucket"] = state.get("intent_bucket", "")
        previous["workflow_summary"] = state.get("workflow_summary", "")
    _set_session_memory(session_id, previous)
    upsert_session(
        session_id=session_id,
        workflow_id=state.get("workflow_id"),
        workflow_title=state.get("workflow_title"),
        intent_bucket=state.get("intent_bucket"),
        workflow_summary=state.get("workflow_summary"),
        branch=state.get("branch"),
    )
    record_event(
        session_id,
        "assistant_turn",
        {
            "workflow_id": state.get("workflow_id"),
            "branch": state.get("branch"),
            "response": state.get("response", "")[:1500],
            "actions": state.get("actions", []),
            "error": state.get("error"),
        },
    )

    # Fan out anything a *different, concurrently-connected* shopper would
    # actually want to know about in real time. Stock is the clear case: if
    # two people are looking at the same product and one adds it to their
    # bag, the other's page should reflect the new quantity without a reload.
    for action in state.get("actions", []) or []:
        if action.get("type") == "add_to_bag" and action.get("product_id"):
            remaining = decrement_stock(action["product_id"])
            action["remaining_stock"] = remaining
            publish_event(
                "stock_update",
                {"product_id": action["product_id"], "remaining_stock": remaining, "session_id": session_id},
            )
            # Recorded here (not in _generate_response) because this is
            # where we already know the final workflow_id for this turn -
            # this is the raw fact a *future* visit's "Customer History"
            # section (see _build_system_prompt) reads back.
            product = product_catalog.get_product(action["product_id"])
            record_order(
                session_id,
                product_id=action["product_id"],
                product_name=product["name"] if product else None,
                price=product["price"] if product else None,
                workflow_id=state.get("workflow_id"),
            )

    publish_event(
        "session_update",
        {
            "session_id": session_id,
            "workflow_id": state.get("workflow_id"),
            "workflow_title": state.get("workflow_title"),
            "branch": state.get("branch"),
        },
    )
    return state


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route", _route_workflow)
    graph.add_node("sales", _sales_node)
    graph.add_node("support", _support_node)
    graph.add_node("corporate", _corporate_node)
    graph.add_node("research", _research_node)
    graph.add_node("explore", _explore_node)
    graph.add_node("persist", _persist_node)

    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        lambda state: state["branch"],
        {
            "sales": "sales",
            "support": "support",
            "corporate": "corporate",
            "research": "research",
            "explore": "explore",
        },
    )
    graph.add_edge("sales", "persist")
    graph.add_edge("support", "persist")
    graph.add_edge("corporate", "persist")
    graph.add_edge("research", "persist")
    graph.add_edge("explore", "persist")
    graph.add_edge("persist", END)
    return graph.compile()


AGENT_GRAPH = build_agent_graph()
