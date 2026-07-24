from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from groq import Groq

from agent_store import get_session_snapshot, record_event, upsert_session
from workflow_catalog import classify_workflow, related_workflows, render_workflow_brief


SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}

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


def _session_fallback(session_id: str, selected_workflow) -> Any:
    previous = SESSION_MEMORY.get(session_id)
    if not previous:
        snapshot = get_session_snapshot(session_id)
        if snapshot and snapshot.get("workflow_id"):
            from workflow_catalog import WORKFLOW_INDEX

            stored = WORKFLOW_INDEX.get(snapshot["workflow_id"])
            if stored:
                previous = {"workflow": stored}
                SESSION_MEMORY[session_id] = previous
        if not previous:
            return selected_workflow

    if selected_workflow.id == "master_entry":
        return previous["workflow"]

    if previous["workflow"].intent_bucket == selected_workflow.intent_bucket:
        return previous["workflow"]

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

    return slots


def _build_system_prompt(workflow, related, branch: str, messages: List[Dict[str, str]] = None) -> str:
    related_text = "\n".join([f"- {item.title} ({item.id})" for item in related]) if related else "- None"
    messages = messages or []
    slots = _extract_session_slots(messages)
    turn_count = len([m for m in messages if m.get("role") == "user"])

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

STRICT SHOPPING AGENT RULES:
1. PROGRESS THE SHOPPING FUNNEL: Do NOT ask the same question twice if details are already in 'Already Identified Details'. Move directly to the next stage (e.g., Occasion -> Fabric/Product Recommendation -> Sizing/Measurements -> Add to Bag).
2. ALWAYS PROVIDE CLICKABLE OPTIONS: Whenever you ask a question or offer choices, you MUST include a `present_options` action in your JSON `actions` array with 3 to 5 clear options.
   Example action: `{{"type": "present_options", "title": "Choose Occasion", "options": ["Office Formal", "Wedding Reception", "Casual Weekend", "Party Wear"]}}`
3. VISUAL PRODUCT & FABRIC RECOMMENDATIONS: When recommending suits or garments, output a `show_recommendations` action with product IDs (`silver-slate`, `pearl-white`, `umber-pinstripe`, `soot-black`, `misty-aqua`, `printed-tie-combo`, `mens-belt`). When discussing fabrics, output a `customize_fabric` action.
4. SIZING & TAILORING: Offer `request_measurements` or `schedule_technician` (cities: Mumbai, Bangalore, Gurgaon) actions when sizing is discussed.
5. DRIVE TO CART: When customer expresses interest in buying or ordering, output `add_to_bag` or `open_cart` action to complete the purchase flow.
6. Keep text responses concise (2-4 sentences max), polite, and action-driven.

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
        temperature=0.2,
    )
    content = response.choices[0].message.content or "{}"
    return _parse_json_blob(content)


def _model_candidates() -> List[str]:
    configured = os.getenv("GROQ_MODEL", "").strip()
    candidates = [configured] if configured else []
    candidates.extend([
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ])
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

    workflow = WORKFLOW_INDEX[workflow_id]
    related = related_workflows(workflow)
    system_prompt = state.get("system_prompt") or _build_system_prompt(workflow, related, branch, state.get("messages", []))
    api_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for message in state["messages"]:
        role = message.get("role")
        content = message.get("content", "")
        if role in {"user", "assistant", "system"}:
            api_messages.append({"role": role, "content": content})

    response_json: Dict[str, Any]
    last_error: Optional[Exception] = None
    for model_name in _model_candidates():
        try:
            response_json = _call_model(api_messages, model_name)
            break
        except Exception as exc:
            last_error = exc
    else:
        return {
            "response": "I could not generate a structured response from the model right now. Please try again.",
            "actions": [],
            "error": str(last_error) if last_error else "Unknown Groq error",
        }

    if not isinstance(response_json, dict):
        response_json = {"response": str(response_json), "actions": []}

    response_text = response_json.get("response", "")
    actions = _normalize_actions(response_json.get("actions", []), workflow.id)
    return {
        "response": response_text,
        "actions": actions,
    }


def _route_workflow(state: AgentState) -> AgentState:
    from workflow_catalog import WORKFLOW_INDEX

    session_id = state.get("session_id") or "default"
    last_user = _last_user_message(state["messages"])
    selected = classify_workflow(last_user)
    selected = _session_fallback(session_id, selected)
    branch = _branch_for_bucket(selected.intent_bucket)
    SESSION_MEMORY[session_id] = {"workflow": selected}
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
    previous = SESSION_MEMORY.get(session_id, {})
    if state.get("workflow_id"):
        previous["workflow_id"] = state["workflow_id"]
        previous["workflow_title"] = state.get("workflow_title", "")
        previous["intent_bucket"] = state.get("intent_bucket", "")
        previous["workflow_summary"] = state.get("workflow_summary", "")
    SESSION_MEMORY[session_id] = previous
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
