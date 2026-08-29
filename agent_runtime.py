from __future__ import annotations

import json
import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from groq import Groq
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from agent_store import record_event, upsert_session
from sqlite_checkpoint_saver import SqliteSaver
from workflow_catalog import classify_workflow, related_workflows, render_workflow_brief


BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_DB_PATH = str(BASE_DIR / "techtailor_checkpoints.db")


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
ALLOWED_PRODUCT_IDS = {
    "silver-slate",
    "pearl-white",
    "umber-pinstripe",
    "soot-black",
    "misty-aqua",
    "charcoal-blazer",
    "printed-tie-combo",
    "mens-belt",
}
ALLOWED_FABRIC_TYPES = {"same", "catalog", "own"}
ALLOWED_HEIGHTS = {"short", "regular", "tall"}
ALLOWED_BODY_TYPES = {"ectomorph_men", "mesomorph_men", "endomorph_men"}
ALLOWED_SIZE_METHODS = {"ready", "custom"}
ALLOWED_FITTINGS = {"regular_fit", "slim_fit", "loose_fit"}
ALLOWED_CITIES = {"Mumbai", "Bangalore", "Gurgaon"}
MUTATING_ACTION_TYPES = {"add_to_bag", "schedule_technician"}

ProductId = Literal[
    "silver-slate",
    "pearl-white",
    "umber-pinstripe",
    "soot-black",
    "misty-aqua",
    "charcoal-blazer",
    "printed-tie-combo",
    "mens-belt",
]
PageId = Literal["home", "men", "women", "accessories"]
FabricType = Literal["same", "catalog", "own"]
HeightType = Literal["short", "regular", "tall"]
BodyType = Literal["ectomorph_men", "mesomorph_men", "endomorph_men"]
SizeMethod = Literal["ready", "custom"]
FitType = Literal["regular_fit", "slim_fit", "loose_fit"]
CityType = Literal["Mumbai", "Bangalore", "Gurgaon"]


RECOMMENDATION_BLUEPRINTS = [
    {
        "name": "boardroom bundle",
        "keywords": {"office", "business", "interview", "meeting", "pitch", "executive", "board"},
        "product_ids": ["silver-slate", "printed-tie-combo", "mens-belt"],
        "reason": "Silver Slate gives a clean office silhouette, while the tie and belt complete the look without overpowering it.",
        "cross_sells": ["white shirt", "navy or silver tie", "minimal pocket square"],
    },
    {
        "name": "power suit bundle",
        "keywords": {"pinstripe", "authority", "power", "premium", "ceo", "boardroom", "investor"},
        "product_ids": ["umber-pinstripe", "printed-tie-combo", "mens-belt"],
        "reason": "Umber Pinstripe reads more authoritative and structured, which works well for high-stakes meetings and premium tailoring.",
        "cross_sells": ["white shirt", "dark leather shoes", "subtle cufflinks"],
    },
    {
        "name": "wedding reception bundle",
        "keywords": {"wedding", "groom", "reception", "ceremony", "marriage", "guest"},
        "product_ids": ["pearl-white", "printed-tie-combo", "mens-belt"],
        "reason": "Pearl White photographs well for wedding settings and the matching accessories make the outfit feel complete.",
        "cross_sells": ["cufflinks", "pocket square", "light-toned shirt"],
    },
    {
        "name": "black-tie bundle",
        "keywords": {"tuxedo", "black tie", "evening", "formal", "party", "night"},
        "product_ids": ["soot-black", "printed-tie-combo", "mens-belt"],
        "reason": "Soot Black is the strongest formal option in the catalog, and the accessories keep the outfit intentional rather than plain.",
        "cross_sells": ["cufflinks", "satin shirt", "formal shoes"],
    },
    {
        "name": "value comparison bundle",
        "keywords": {"budget", "cheap", "cheaper", "value", "student", "affordable", "discount"},
        "product_ids": ["silver-slate", "umber-pinstripe", "printed-tie-combo"],
        "reason": "This comparison keeps the decision focused on value and use case, not just price.",
        "cross_sells": ["choose one suit first", "add belt only if needed"],
    },
    {
        "name": "accessory finishing bundle",
        "keywords": {"tie", "belt", "cufflinks", "accessory", "gift", "bundle"},
        "product_ids": ["printed-tie-combo", "mens-belt"],
        "reason": "These are the two easiest finishing pieces to match with most formal outfits.",
        "cross_sells": ["pocket square", "gift wrap", "reversible belt option"],
    },
]

QUESTION_PATTERNS = {
    "occasion": ["what is the occasion", "which occasion", "choose occasion", "occasion"],
    "fabric": ["which fabric", "fabric family", "fabric choice", "choose fabric"],
    "fit": ["which fit", "fit preference", "sizing preference", "what fit", "measurements"],
    "city": ["which city", "schedule a technician", "city should", "visit in"],
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
    pending_actions: List[Dict[str, Any]]
    retry_count: int
    validation_failed: bool
    validation_reason: str
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


def _branch_prompt(branch: str) -> str:
    prompts = {
        "sales": (
            "Guide the customer through selecting fabric, fit, and sizing step-by-step using interactive options in chat. "
            "Do not rush to finalize suit or checkout until options are selected or requested."
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
            "Help the customer narrow choices step-by-step without pushing too early."
        ),
        "explore": (
            "Act like a premium stylist and discovery assistant. "
            "Ask one clear question at a time and present clickable option choices in chat."
        ),
    }
    return prompts[branch]


def _extract_session_slots(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    text = " ".join([m.get("content", "").lower() for m in messages if m.get("role") == "user"])
    slots: Dict[str, Any] = {}

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

    for color in ["black", "white", "navy", "blue", "grey", "gray", "brown", "beige", "burgundy", "green", "aqua", "pink", "ivory", "charcoal", "silver"]:
        if color in text:
            slots["color"] = color.title()
            break

    budget_match = re.search(r"(?:under|within|around|below|up to|upto)\s*(?:rs\.?|inr|₹)?\s*([0-9][0-9,]*)", text)
    if budget_match:
        slots["budget"] = budget_match.group(1)
    elif "budget" in text:
        slots["budget"] = "open"

    return slots


def _recommendation_context(workflow, user_text: str, slots: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = (user_text or "").lower()
    haystack = f"{workflow.id} {workflow.title} {workflow.summary} {text}"
    for blueprint in RECOMMENDATION_BLUEPRINTS:
        if any(keyword in haystack for keyword in blueprint["keywords"]):
            reason = blueprint["reason"]
            if slots.get("color"):
                reason = f"{reason} The customer also mentioned {slots['color'].lower()} preferences, so the palette can be tuned around that."
            if slots.get("budget") and slots.get("budget") != "open":
                reason = f"{reason} The target budget around {slots['budget']} keeps the recommendation practical."
            return {
                "title": blueprint["name"].replace("_", " ").title(),
                "product_ids": blueprint["product_ids"],
                "reason": reason,
                "cross_sells": blueprint["cross_sells"],
            }
    return None


def _enrich_actions_with_recommendations(
    actions: List[Dict[str, Any]],
    workflow,
    user_text: str,
    slots: Dict[str, Any],
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    recommendation_present = False
    recommendation_context = _recommendation_context(workflow, user_text, slots)

    for action in actions:
        if action.get("type") in {"show_recommendations", "compare_products", "offer_alternative"}:
            recommendation_present = True
            if recommendation_context:
                action.setdefault("title", recommendation_context["title"])
                action.setdefault("reason", recommendation_context["reason"])
                action.setdefault("cross_sells", recommendation_context["cross_sells"])
                if not action.get("product_ids"):
                    action["product_ids"] = recommendation_context["product_ids"]
        enriched.append(action)

    if not recommendation_present and recommendation_context:
        enriched.append(
            {
                "type": "show_recommendations",
                "title": recommendation_context["title"],
                "product_ids": recommendation_context["product_ids"],
                "reason": recommendation_context["reason"],
                "cross_sells": recommendation_context["cross_sells"],
            }
        )

    return enriched


def _split_pending_actions(actions: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    normal: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []
    for action in actions:
        if action.get("type") in MUTATING_ACTION_TYPES:
            pending.append(action)
        else:
            normal.append(action)
    return normal, pending


def _message(role: str, content: str):
    if role == "user":
        return HumanMessage(content=content)
    if role == "assistant":
        return AIMessage(content=content)
    return SystemMessage(content=content)


def _build_system_prompt(
    workflow,
    related,
    branch: str,
    messages: List[Dict[str, str]] | None = None,
    validation_reason: str | None = None,
    retry_count: int = 0,
) -> str:
    related_text = "\n".join([f"- {item.title} ({item.id})" for item in related]) if related else "- None"
    messages = messages or []
    slots = _extract_session_slots(messages)
    turn_count = len([m for m in messages if m.get("role") == "user"])
    validation_note = f"\nValidation note: {validation_reason}" if validation_reason else ""

    return f"""You are the TechTailor AI Concierge & Executive Shopping Assistant.
You are operating inside a LangGraph workflow to guide customers through bespoke tailoring selection and purchasing.
Assume the user has no prior knowledge unless they clearly show it. Explain ideas from first principles and build up slowly.

Selected workflow:
{render_workflow_brief(workflow)}

Branch policy:
{_branch_prompt(branch)}

Related workflows:
{related_text}

Session memory already observed in this conversation:
- Turn Count: {turn_count}
- Already Identified Details: {json.dumps(slots) if slots else "None yet"}
- Retry Count: {retry_count}{validation_note}

Conversation rules:
1. Step by step is better than rushing. Ask only for the next missing choice.
2. When a choice is needed, use the available tools instead of inventing a custom format.
3. If the user mentions budget, color combinations, occasion, body type, or styling preferences, reflect that in the recommendation.
4. Recommending a product is not enough. Prefer complete outfit combinations with matching accessories and explain why they work.
5. Do not repeat a question for a slot that is already known from the conversation.
6. Keep responses concise, polite, and action-driven.

Teaching mode:
- If the user asks how the system works, why LangGraph is used, or what state/nodes/edges mean, explain it slowly from first principles.
- Start with the problem, then explain plain Python, then explain state/nodes/edges, then explain why the graph helps, then map it back to TechTailor.
- Use short numbered sections or bullets. Do not assume the user knows LangGraph, checkpointers, or tool calling.

Tool calling rules:
- Use a tool whenever a structured UI action is needed.
- Never invent unsupported pages, cities, or product IDs.
- If the model needs to recommend an outfit, call show_recommendations with a complete combination.
- If the model needs to schedule a visit or add an item to the bag, the graph will ask the user for confirmation before executing it.

Return a short, natural response in plain text. Use tools when needed."""


def _tool_identity_response(name: str) -> str:
    return f"{name} action prepared."


@tool("navigate", description="Navigate the storefront to a specific page.")
def navigate(page: PageId) -> str:
    return _tool_identity_response(f"navigate:{page}")


@tool("select_product", description="Select a specific product by product id.")
def select_product(product_id: ProductId) -> str:
    return _tool_identity_response(f"select_product:{product_id}")


@tool("customize_fabric", description="Choose fabric type and optional fabric name.")
def customize_fabric(fabric_type: FabricType, fabric_name: str | None = None) -> str:
    suffix = f":{fabric_name}" if fabric_name else ""
    return _tool_identity_response(f"customize_fabric:{fabric_type}{suffix}")


@tool("customize_measurements", description="Store sizing preferences and measurement inputs.")
def customize_measurements(
    height: HeightType | None = None,
    body_type: BodyType | None = None,
    size_method: SizeMethod | None = None,
    ready_jacket_size: str | None = None,
    ready_trouser_size: str | None = None,
    fitting: FitType | None = None,
    custom_measurements: dict[str, Any] | None = None,
) -> str:
    return _tool_identity_response("customize_measurements")


@tool("schedule_technician", description="Schedule a measurement technician visit in a city.")
def schedule_technician(city: CityType, date: str | None = None) -> str:
    suffix = f":{date}" if date else ""
    return _tool_identity_response(f"schedule_technician:{city}{suffix}")


@tool("add_to_bag", description="Add the current selection to the shopping bag.")
def add_to_bag() -> str:
    return _tool_identity_response("add_to_bag")


@tool("open_cart", description="Open the shopping cart.")
def open_cart() -> str:
    return _tool_identity_response("open_cart")


@tool("show_workflow_summary", description="Show the active workflow summary.")
def show_workflow_summary(workflow_id: str | None = None) -> str:
    return _tool_identity_response("show_workflow_summary")


@tool("capture_lead", description="Capture a lead for follow-up.")
def capture_lead() -> str:
    return _tool_identity_response("capture_lead")


@tool("show_recommendations", description="Recommend a complete outfit combination.")
def show_recommendations(
    product_ids: list[ProductId],
    title: str = "Recommended outfit combination",
    reason: str = "",
    cross_sells: list[str] | None = None,
) -> str:
    return _tool_identity_response("show_recommendations")


@tool("compare_products", description="Compare recommended products side by side.")
def compare_products(
    product_ids: list[ProductId],
    title: str = "Compare options",
    reason: str = "",
    cross_sells: list[str] | None = None,
) -> str:
    return _tool_identity_response("compare_products")


@tool("request_photo", description="Request a customer photo for styling preview.")
def request_photo() -> str:
    return _tool_identity_response("request_photo")


@tool("show_style_preview", description="Show a styling preview.")
def show_style_preview() -> str:
    return _tool_identity_response("show_style_preview")


@tool("set_budget", description="Capture a budget target.")
def set_budget(budget: str) -> str:
    return _tool_identity_response("set_budget")


@tool("offer_alternative", description="Offer alternative outfit options.")
def offer_alternative(
    product_ids: list[ProductId],
    title: str = "Alternative options",
    reason: str = "",
    cross_sells: list[str] | None = None,
) -> str:
    return _tool_identity_response("offer_alternative")


@tool("show_shipping", description="Explain shipping details.")
def show_shipping() -> str:
    return _tool_identity_response("show_shipping")


@tool("request_measurements", description="Ask the customer to provide measurements.")
def request_measurements() -> str:
    return _tool_identity_response("request_measurements")


@tool("create_quote", description="Create a quote request.")
def create_quote() -> str:
    return _tool_identity_response("create_quote")


@tool("handoff_human", description="Route the conversation to a human.")
def handoff_human() -> str:
    return _tool_identity_response("handoff_human")


@tool("save_preferences", description="Save customer preferences.")
def save_preferences() -> str:
    return _tool_identity_response("save_preferences")


@tool("start_consultation", description="Start a stylist consultation.")
def start_consultation() -> str:
    return _tool_identity_response("start_consultation")


@tool("present_options", description="Present clickable options in chat.")
def present_options(title: str, options: list[str]) -> str:
    return _tool_identity_response("present_options")


AVAILABLE_TOOLS = [
    navigate,
    select_product,
    customize_fabric,
    customize_measurements,
    schedule_technician,
    add_to_bag,
    open_cart,
    show_workflow_summary,
    capture_lead,
    show_recommendations,
    compare_products,
    request_photo,
    show_style_preview,
    set_budget,
    offer_alternative,
    show_shipping,
    request_measurements,
    create_quote,
    handoff_human,
    save_preferences,
    start_consultation,
    present_options,
]


@lru_cache(maxsize=8)
def _accessible_groq_models(api_key: str) -> List[str]:
    api_key = api_key.strip()
    if not api_key:
        return []

    try:
        client = Groq(api_key=api_key)
        response = client.models.list()
    except Exception:
        return []

    models: List[str] = []
    for item in getattr(response, "data", []) or []:
        model_id = getattr(item, "id", None)
        is_active = getattr(item, "active", True)
        if model_id and is_active:
            models.append(model_id)
    return models


def _model_candidates() -> List[str]:
    configured = os.getenv("GROQ_MODEL", "").strip()
    preferred = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "llama-3.1-8b-instant",
    ]

    api_key = os.getenv("GROQ_API_KEY", "")
    accessible = _accessible_groq_models(api_key)
    pool = accessible or preferred

    candidates = [configured] if configured else []
    candidates.extend(pool)

    seen = set()
    ordered: List[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _call_model(messages: List[Any], model_name: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = ChatGroq(api_key=api_key, model=model_name, temperature=0.2)
    tool_bound = client.bind_tools(AVAILABLE_TOOLS)
    return tool_bound.invoke(messages)


def _extract_tool_calls(message: Any) -> List[Dict[str, Any]]:
    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls and getattr(message, "additional_kwargs", None):
        tool_calls = message.additional_kwargs.get("tool_calls", []) or []

    normalized: List[Dict[str, Any]] = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name") or call.get("function", {}).get("name")
        raw_args = call.get("args") or call.get("function", {}).get("arguments") or {}
        if isinstance(raw_args, str):
            try:
                raw_args = json.loads(raw_args) if raw_args.strip() else {}
            except Exception:
                raw_args = {}
        if not name:
            continue
        normalized.append({"name": name, "args": raw_args})
    return normalized


def _tool_call_to_action(tool_call: Dict[str, Any], workflow) -> Dict[str, Any] | None:
    name = tool_call.get("name")
    args = tool_call.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    if name == "navigate":
        page = args.get("page")
        if page in ALLOWED_PAGES:
            return {"type": "navigate", "page": page}
        return None

    if name == "select_product":
        product_id = args.get("product_id")
        if product_id in ALLOWED_PRODUCT_IDS:
            return {"type": "select_product", "product_id": product_id}
        return None

    if name == "customize_fabric":
        fabric_type = args.get("fabric_type")
        if fabric_type not in ALLOWED_FABRIC_TYPES:
            return None
        action = {"type": "customize_fabric", "fabric_type": fabric_type}
        if args.get("fabric_name"):
            action["fabric_name"] = args["fabric_name"]
        return action

    if name == "customize_measurements":
        action = {"type": "customize_measurements"}
        for field in ["height", "body_type", "size_method", "ready_jacket_size", "ready_trouser_size", "fitting", "custom_measurements"]:
            if field in args and args[field] is not None:
                action[field] = args[field]
        return action

    if name == "schedule_technician":
        city = args.get("city")
        if city not in ALLOWED_CITIES:
            return None
        action = {"type": "schedule_technician", "city": city}
        if args.get("date"):
            action["date"] = args["date"]
        return action

    if name == "add_to_bag":
        return {"type": "add_to_bag"}

    if name == "open_cart":
        return {"type": "open_cart"}

    if name == "show_workflow_summary":
        action = {"type": "show_workflow_summary"}
        if args.get("workflow_id"):
            action["workflow_id"] = args["workflow_id"]
        return action

    if name == "capture_lead":
        return {"type": "capture_lead"}

    if name in {"show_recommendations", "compare_products", "offer_alternative"}:
        product_ids = [pid for pid in args.get("product_ids", []) if pid in ALLOWED_PRODUCT_IDS]
        recommendation_context = _recommendation_context(workflow, "", {})
        if not product_ids and recommendation_context:
            product_ids = recommendation_context["product_ids"]
        action = {"type": name, "product_ids": product_ids}
        if args.get("title"):
            action["title"] = args["title"]
        if args.get("reason"):
            action["reason"] = args["reason"]
        if args.get("cross_sells"):
            action["cross_sells"] = [str(item) for item in args["cross_sells"]]
        return action

    if name == "request_photo":
        return {"type": "request_photo"}

    if name == "show_style_preview":
        return {"type": "show_style_preview"}

    if name == "set_budget":
        return {"type": "set_budget", "budget": str(args.get("budget", "")).strip()}

    if name == "show_shipping":
        return {"type": "show_shipping"}

    if name == "request_measurements":
        return {"type": "request_measurements"}

    if name == "create_quote":
        return {"type": "create_quote"}

    if name == "handoff_human":
        return {"type": "handoff_human"}

    if name == "save_preferences":
        return {"type": "save_preferences"}

    if name == "start_consultation":
        return {"type": "start_consultation"}

    if name == "present_options":
        title = str(args.get("title", "Select an option"))
        options = [str(option) for option in args.get("options", []) if str(option).strip()]
        return {"type": "present_options", "title": title, "options": options}

    return None


def _normalize_actions(actions: Any, workflow) -> List[Dict[str, Any]]:
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
            if page in ALLOWED_PAGES:
                normalized["page"] = page
        elif action_type == "select_product":
            product_id = item.get("product_id")
            if product_id in ALLOWED_PRODUCT_IDS:
                normalized["product_id"] = product_id
        elif action_type == "customize_fabric":
            fabric_type = item.get("fabric_type")
            if fabric_type in ALLOWED_FABRIC_TYPES:
                normalized["fabric_type"] = fabric_type
            if item.get("fabric_name"):
                normalized["fabric_name"] = item["fabric_name"]
        elif action_type == "customize_measurements":
            for field in ["height", "body_type", "size_method", "ready_jacket_size", "ready_trouser_size", "fitting", "custom_measurements"]:
                if field in item:
                    normalized[field] = item[field]
        elif action_type == "schedule_technician":
            if item.get("city") in ALLOWED_CITIES:
                normalized["city"] = item["city"]
            if item.get("date"):
                normalized["date"] = item["date"]
        elif action_type == "present_options":
            normalized["title"] = item.get("title", "Select an option:")
            opts = item.get("options", [])
            if isinstance(opts, list):
                normalized["options"] = [str(o) for o in opts if str(o).strip()]
        elif action_type in {"show_recommendations", "compare_products", "offer_alternative"}:
            ids = item.get("product_ids", [])
            if isinstance(ids, list):
                normalized["product_ids"] = [pid for pid in ids if pid in ALLOWED_PRODUCT_IDS]
            if item.get("title"):
                normalized["title"] = item["title"]
            if item.get("reason"):
                normalized["reason"] = item["reason"]
            if item.get("cross_sells") and isinstance(item["cross_sells"], list):
                normalized["cross_sells"] = [str(x) for x in item["cross_sells"]]
        else:
            for k, v in item.items():
                normalized[k] = v

        cleaned.append(normalized)
    return cleaned


def _response_content(response: Any) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content or "")


def _build_present_options_for_fallback(slots: Dict[str, Any]) -> Dict[str, Any]:
    if not slots.get("fabric"):
        return {
            "type": "present_options",
            "title": "Choose fabric direction",
            "options": ["Show fabric swatches", "Recommend a complete outfit", "Compare wool and linen"],
        }
    if not slots.get("fit"):
        return {
            "type": "present_options",
            "title": "Choose fit and sizing",
            "options": ["Slim Fit", "Regular Fit", "Ready Size M", "Book measurements"],
        }
    if not slots.get("city"):
        return {
            "type": "present_options",
            "title": "Choose a visit city",
            "options": ["Mumbai", "Bangalore", "Gurgaon"],
        }
    return {
        "type": "present_options",
        "title": "Choose the next step",
        "options": ["Show complete looks", "Compare options", "Add accessories"],
    }


def _build_validation_fallback(state: AgentState, reason: str, slots: Dict[str, Any]) -> AgentState:
    fallback_action = _build_present_options_for_fallback(slots)
    if "occasion" in slots and any(pattern in reason.lower() for pattern in QUESTION_PATTERNS["occasion"]):
        response = "You already told me the occasion, so I’m moving to the next step instead."
    elif "fabric" in slots and any(pattern in reason.lower() for pattern in QUESTION_PATTERNS["fabric"]):
        response = "You already gave me the fabric direction, so I’ll move to the next styling choice."
    elif "fit" in slots and any(pattern in reason.lower() for pattern in QUESTION_PATTERNS["fit"]):
        response = "You already told me the fit preference, so I’m moving on."
    elif "city" in slots and any(pattern in reason.lower() for pattern in QUESTION_PATTERNS["city"]):
        response = "You already gave me the city, so I’m moving forward with the visit details."
    else:
        response = "I’ve corrected the response to skip the repeated question and move the conversation forward."
    return {"response": response, "actions": [fallback_action]}


def _validate_output(state: AgentState) -> AgentState:
    messages = state.get("messages", [])
    response = state.get("response", "")
    actions = state.get("actions", [])
    slots = _extract_session_slots(messages)

    lower_response = response.lower()
    question_text = lower_response
    for action in actions:
        if action.get("type") == "present_options":
            question_text += " " + str(action.get("title", "")).lower()
            question_text += " " + " ".join([str(opt).lower() for opt in action.get("options", [])])

    for slot, patterns in QUESTION_PATTERNS.items():
        if slot in slots and any(pattern in question_text for pattern in patterns):
            retry_count = int(state.get("retry_count", 0)) + 1
            reason = f"Repeated {slot} question even though the slot is already known."
            if retry_count < 2:
                return {
                    "validation_failed": True,
                    "validation_reason": reason,
                    "retry_count": retry_count,
                }
            fallback = _build_validation_fallback(state, reason, slots)
            return {
                **fallback,
                "validation_failed": False,
                "validation_reason": "",
                "retry_count": 0,
            }

    for action in actions:
        action_type = action.get("type")
        if action_type == "navigate" and action.get("page") not in ALLOWED_PAGES:
            reason = "Invalid page in navigate action."
            retry_count = int(state.get("retry_count", 0)) + 1
            if retry_count < 2:
                return {"validation_failed": True, "validation_reason": reason, "retry_count": retry_count}
            return {
                **_build_validation_fallback(state, reason, slots),
                "validation_failed": False,
                "validation_reason": "",
                "retry_count": 0,
            }
        if action_type == "select_product" and action.get("product_id") not in ALLOWED_PRODUCT_IDS:
            reason = "Invalid product id in select_product action."
            retry_count = int(state.get("retry_count", 0)) + 1
            if retry_count < 2:
                return {"validation_failed": True, "validation_reason": reason, "retry_count": retry_count}
            return {
                **_build_validation_fallback(state, reason, slots),
                "validation_failed": False,
                "validation_reason": "",
                "retry_count": 0,
            }
        if action_type == "schedule_technician" and action.get("city") not in ALLOWED_CITIES:
            reason = "Invalid city in schedule_technician action."
            retry_count = int(state.get("retry_count", 0)) + 1
            if retry_count < 2:
                return {"validation_failed": True, "validation_reason": reason, "retry_count": retry_count}
            return {
                **_build_validation_fallback(state, reason, slots),
                "validation_failed": False,
                "validation_reason": "",
                "retry_count": 0,
            }
        if action_type in {"show_recommendations", "compare_products", "offer_alternative"}:
            product_ids = action.get("product_ids", [])
            if not isinstance(product_ids, list) or not product_ids:
                reason = "Recommendation action did not include valid product ids."
                retry_count = int(state.get("retry_count", 0)) + 1
                if retry_count < 2:
                    return {"validation_failed": True, "validation_reason": reason, "retry_count": retry_count}
                return {
                    **_build_validation_fallback(state, reason, slots),
                    "validation_failed": False,
                    "validation_reason": "",
                    "retry_count": 0,
                }

    return {
        "validation_failed": False,
        "validation_reason": "",
        "retry_count": 0,
    }


def _call_llm(state: AgentState, branch: str) -> AgentState:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "response": "No Groq API Key is configured yet. Set it in the top-right panel to activate the agent.",
            "actions": [],
            "pending_actions": [],
        }

    from workflow_catalog import DEFAULT_WORKFLOW, WORKFLOW_INDEX

    workflow_id = state.get("workflow_id") or "master_entry"
    workflow = WORKFLOW_INDEX.get(workflow_id, DEFAULT_WORKFLOW)
    related = related_workflows(workflow)
    messages = state.get("messages", [])
    system_prompt = _build_system_prompt(
        workflow,
        related,
        branch,
        messages,
        validation_reason=state.get("validation_reason") or None,
        retry_count=int(state.get("retry_count", 0)),
    )
    if state.get("system_prompt"):
        system_prompt = f"{system_prompt}\n\nAdditional runtime instructions:\n{state['system_prompt']}"

    api_messages: List[Any] = [SystemMessage(content=system_prompt)]
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role in {"user", "assistant", "system"}:
            api_messages.append(_message(role, content))

    response_message = None
    last_error: Optional[Exception] = None
    for model_name in _model_candidates():
        try:
            response_message = _call_model(api_messages, model_name)
            break
        except Exception as exc:
            last_error = exc

    if response_message is None:
        accessible = _accessible_groq_models(os.getenv("GROQ_API_KEY", ""))
        if accessible:
            error_hint = f"Available Groq models for this key: {', '.join(accessible[:10])}"
        else:
            error_hint = "No accessible Groq models were discovered for the current API key."
        return {
            "response": f"I could not generate a structured response from the model right now. Please try again.\n\n{error_hint}",
            "actions": [],
            "pending_actions": [],
            "error": str(last_error) if last_error else "Unknown Groq error",
        }

    response_text = _response_content(response_message)
    tool_calls = _extract_tool_calls(response_message)
    actions = [_tool_call_to_action(call, workflow) for call in tool_calls]
    actions = [action for action in actions if action is not None]
    actions = _normalize_actions(actions, workflow)

    slots = _extract_session_slots(messages)
    actions = _enrich_actions_with_recommendations(actions, workflow, _last_user_message(messages), slots)

    if not response_text.strip():
        if actions:
            response_text = "I have prepared the next step for you."
        else:
            response_text = "I’m ready to help. Tell me the occasion, style, or budget and I’ll guide you step by step."

    non_mutating_actions, pending_actions = _split_pending_actions(actions)
    return {
        "response": response_text.strip(),
        "actions": non_mutating_actions,
        "pending_actions": pending_actions,
    }


def _route_workflow(state: AgentState) -> AgentState:
    from workflow_catalog import DEFAULT_WORKFLOW, WORKFLOW_INDEX

    session_id = state.get("session_id") or "default"
    last_user = _last_user_message(state.get("messages", []))
    selected = classify_workflow(last_user)
    current_workflow = WORKFLOW_INDEX.get(state.get("workflow_id", ""), DEFAULT_WORKFLOW)

    if state.get("workflow_id") and (
        selected.id == "master_entry" or selected.intent_bucket == current_workflow.intent_bucket
    ):
        selected = current_workflow

    branch = _branch_for_bucket(selected.intent_bucket)
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
        "retry_count": 0,
        "validation_failed": False,
        "validation_reason": "",
        "pending_actions": [],
    }


def _sales_node(state: AgentState) -> AgentState:
    return _call_llm(state, "sales")


def _support_node(state: AgentState) -> AgentState:
    return _call_llm(state, "support")


def _corporate_node(state: AgentState) -> AgentState:
    return _call_llm(state, "corporate")


def _research_node(state: AgentState) -> AgentState:
    return _call_llm(state, "research")


def _explore_node(state: AgentState) -> AgentState:
    return _call_llm(state, "explore")


def _validation_router(state: AgentState) -> str:
    if state.get("validation_failed"):
        return state.get("branch") or "explore"
    return "mutation_gate"


def _mutation_confirmation_router(state: AgentState) -> AgentState:
    pending_actions = state.get("pending_actions", [])
    if not pending_actions:
        return {"pending_actions": []}

    action_types = ", ".join(action.get("type", "") for action in pending_actions)
    prompt = {
        "title": "Confirm before I change your order",
        "message": f"You asked me to run: {action_types}. Reply confirm to continue or cancel to stop.",
        "pending_actions": pending_actions,
    }
    decision = interrupt(prompt)
    normalized = str(decision or "").strip().lower()

    if normalized in {"cancel", "no", "stop", "abort"}:
        return {
            "response": "Canceled. I left your bag and scheduling unchanged.",
            "actions": state.get("actions", []),
            "pending_actions": [],
        }

    if normalized in {"confirm", "yes", "continue", "ok", "okay", "proceed"}:
        return {
            "actions": list(state.get("actions", [])) + list(pending_actions),
            "pending_actions": [],
            "response": state.get("response", ""),
        }

    return {
        "response": "Please confirm or cancel.",
        "actions": state.get("actions", []),
        "pending_actions": pending_actions,
    }


def _persist_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id") or "default"
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
            "pending_actions": state.get("pending_actions", []),
            "error": state.get("error"),
        },
    )
    return state


def build_agent_graph():
    saver = SqliteSaver.from_conn_string(f"sqlite:///{CHECKPOINT_DB_PATH}")
    graph = StateGraph(AgentState)
    graph.add_node("route", _route_workflow)
    graph.add_node("sales", _sales_node)
    graph.add_node("support", _support_node)
    graph.add_node("corporate", _corporate_node)
    graph.add_node("research", _research_node)
    graph.add_node("explore", _explore_node)
    graph.add_node("validate", _validate_output)
    graph.add_node("mutation_gate", _mutation_confirmation_router)
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
    graph.add_edge("sales", "validate")
    graph.add_edge("support", "validate")
    graph.add_edge("corporate", "validate")
    graph.add_edge("research", "validate")
    graph.add_edge("explore", "validate")
    graph.add_conditional_edges(
        "validate",
        _validation_router,
        {
            "sales": "sales",
            "support": "support",
            "corporate": "corporate",
            "research": "research",
            "explore": "explore",
            "mutation_gate": "mutation_gate",
        },
    )
    graph.add_edge("mutation_gate", "persist")
    graph.add_edge("persist", END)
    return graph.compile(checkpointer=saver)


AGENT_GRAPH = build_agent_graph()
