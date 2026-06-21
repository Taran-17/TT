from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple


INTENT_BUCKETS = [
    "ready_to_buy",
    "exploring",
    "researching_styles",
    "corporate_lead",
    "customer_support",
]


@dataclass(frozen=True)
class WorkflowSpec:
    id: str
    title: str
    intent_bucket: str
    summary: str
    trigger_phrases: List[str]
    questions: List[str]
    recommended_actions: List[str]
    upsells: List[str]
    follow_up: str


def _slug(value: str) -> str:
    return (
        value.lower()
        .replace("&", " and ")
        .replace("/", " ")
        .replace("-", " ")
        .replace("'", "")
        .replace("  ", " ")
        .strip()
        .replace(" ", "_")
    )


def _variant_workflow(
    domain: str,
    label: str,
    intent_bucket: str,
    summary: str,
    trigger_phrases: List[str],
    questions: List[str],
    recommended_actions: List[str],
    upsells: List[str],
) -> WorkflowSpec:
    return WorkflowSpec(
        id=f"{_slug(domain)}__{_slug(label)}",
        title=f"{domain.title()} - {label.replace('_', ' ').title()}",
        intent_bucket=intent_bucket,
        summary=summary,
        trigger_phrases=trigger_phrases,
        questions=questions,
        recommended_actions=recommended_actions,
        upsells=upsells,
        follow_up="Capture the minimum information needed, then guide the customer to the next best action.",
    )


BASE_WORKFLOWS: List[WorkflowSpec] = [
    WorkflowSpec("master_entry", "Master Entry Router", "exploring", "Route new visitors into the right journey.", ["hello", "hi", "start", "browse", "explore"], ["What brings you here today?"], ["capture_lead", "show_workflow_summary"], ["offer_style_quiz"], "Classify the visitor quickly."),
    WorkflowSpec("doc_custom_shirt", "Custom Shirt", "ready_to_buy", "Guide shirt buyers through occasion, fabric, fit, style, measurements, and checkout.", ["shirt", "custom shirt", "tailored shirt"], ["What is the occasion?", "Which fabric family do you prefer?"], ["show_size_guide", "request_measurements", "capture_lead"], ["add_tie", "add_pocket_square"], "Ask only the missing slots."),
    WorkflowSpec("doc_custom_suit", "Custom Suit", "ready_to_buy", "Handle suit requests across interview, business, wedding, tuxedo, and special event use cases.", ["suit", "custom suit", "tailored suit", "blazer"], ["What is the purpose of the suit?", "Do you want ready or custom sizing?"], ["navigate_men", "show_fabric_options", "request_measurements"], ["add_shirt", "add_cufflinks"], "Recommend lapel, button, and lining choices once purpose is known."),
    WorkflowSpec("doc_wedding_groom", "Wedding Groom Consultation", "ready_to_buy", "Plan groom wear and companion looks around date, venue, and tradition.", ["wedding", "groom", "reception", "marriage"], ["When is the wedding?", "Are you the groom or a guest?"], ["capture_lead", "request_measurements", "show_bundle"], ["add_shoes", "add_turban"], "Drive toward a complete event wardrobe."),
    WorkflowSpec("doc_groomsmen_bundle", "Bridegroom Party Bundle", "corporate_lead", "Quote bulk outfits for a wedding party or groomsmen group.", ["groomsmen", "wedding party", "group outfit"], ["How many people are in the party?", "What is the theme color?"], ["create_quote", "capture_lead", "show_bundle"], ["add_accessories_bundle"], "Prioritize bulk pricing and lead capture."),
    WorkflowSpec("doc_corporate_uniform_buyer", "Corporate Uniform Buyer", "corporate_lead", "Collect company, industry, headcount, location, and branding for uniform proposals.", ["company", "uniform", "corporate"], ["What industry are you in?", "How many employees need uniforms?"], ["create_quote", "capture_lead", "handoff_human"], ["embroidery", "fabric_swatches"], "Treat this as a procurement flow."),
    WorkflowSpec("doc_hospital_admin", "Hospital Procurement", "corporate_lead", "Support hospital buyers requesting coats, scrubs, gowns, or linen quotes.", ["hospital", "doctor coat", "scrubs", "patient gown"], ["What items do you need?", "What quantity is required?"], ["create_quote", "capture_lead", "handoff_human"], ["sample_swatches", "bulk_discount"], "Convert the request into a service ticket or quote."),
    WorkflowSpec("doc_hotel_owner", "Hotel Operations Apparel", "corporate_lead", "Collect hotel department needs like chef, steward, housekeeping, and front office wear.", ["hotel", "chef uniform", "housekeeping", "front office"], ["Which departments need uniforms?", "What quantities are you planning?"], ["create_quote", "capture_lead", "handoff_human"], ["sample_kit", "bulk_pricing"], "Keep the conversation organized by department."),
    WorkflowSpec("doc_accessories_only", "Accessories Only", "ready_to_buy", "Fast checkout path for ties, pocket squares, belts, wallets, and cufflinks.", ["tie", "belt", "wallet", "cufflinks", "accessory"], ["Which accessory are you looking for?"], ["navigate_accessories", "open_cart", "capture_lead"], ["gift_wrap", "bundle_accessories"], "Avoid measurement questions."),
    WorkflowSpec("doc_discovery_mode", "Discovery Mode", "exploring", "Help undecided customers with gender, age group, occasion, and budget.", ["not sure", "help me choose", "recommend"], ["Who is this for?", "What is the occasion?"], ["show_recommendations", "compare_products", "capture_lead"], ["style_quiz", "fabric_compare"], "Turn uncertainty into one confident recommendation."),
    WorkflowSpec("doc_virtual_try_on", "Virtual Try-On", "researching_styles", "Handle experimentation requests around photos, color changes, and style previews.", ["try on", "photo", "preview", "see on me"], ["Do you want a shirt, suit, or ethnic look?", "Do you want to upload a photo?"], ["request_photo", "show_style_preview", "capture_lead"], ["multiple_color_preview", "fabric_swap"], "Keep the session visual and lightweight."),
    WorkflowSpec("doc_price_sensitive", "Price-Sensitive Customer", "exploring", "Offer alternate fabrics, simplified styling, and bundles to protect the sale.", ["expensive", "too much", "cheaper", "discount"], ["What budget are you comfortable with?"], ["set_budget", "offer_alternative", "show_bundle"], ["seasonal_offer", "entry_fabric"], "Reframe value instead of arguing price."),
    WorkflowSpec("doc_abandoned_cart", "Abandoned Cart Recovery", "customer_support", "Track cart contents and propose follow-up for incomplete orders.", ["left in cart", "forgot", "checkout later", "abandoned"], ["Would you like me to summarize your bag?"], ["open_cart", "capture_lead", "save_preferences"], ["reminder_followup", "coupon_offer"], "Recover the order without being pushy."),
    WorkflowSpec("doc_repeat_customer", "Repeat Customer", "ready_to_buy", "Reuse prior measurements, orders, fabrics, and preferred colors.", ["reorder", "again", "same as before", "last time"], ["Should I reuse your previous measurements?"], ["save_preferences", "open_cart", "capture_lead"], ["wardrobe_refresh", "new_color_variant"], "Reduce friction and skip needless questions."),
    WorkflowSpec("doc_alteration", "Alteration Request", "customer_support", "Collect garment type, issue, urgency, and pickup scheduling for alterations.", ["alteration", "resize", "waist", "shorten sleeve"], ["What garment needs alteration?", "What needs to be changed?"], ["capture_lead", "request_measurements", "handoff_human"], ["pickup_schedule", "express_service"], "Turn the issue into a service ticket."),
    WorkflowSpec("doc_international_customer", "International Customer", "researching_styles", "Show international shipping, delivery timelines, and mandatory measurement guidance.", ["outside india", "international", "ship to", "usa", "uk", "uae"], ["Which country are you shipping to?", "Do you need size guidance?"], ["show_shipping", "request_measurements", "capture_lead"], ["video_consultation", "currency_display"], "Flag shipping limitations early."),
    WorkflowSpec("doc_hnwi", "High Net Worth Client", "ready_to_buy", "Route premium clients to stylist consultation, exclusive fabrics, and home or video appointments.", ["premium", "luxury", "private", "concierge"], ["Would you like a stylist consultation?", "Would you prefer a video or home appointment?"], ["start_consultation", "capture_lead", "handoff_human"], ["exclusive_fabric", "bespoke_package"], "Keep the tone elevated and direct."),
    WorkflowSpec("doc_festival_wear", "Festival Wear", "researching_styles", "Suggest kurta, Nehru jacket, sherwani, or bandhgala for festivals.", ["diwali", "eid", "festival", "navratri", "sherwani"], ["Which festival or occasion is this for?", "Traditional or modern styling?"], ["navigate_men", "show_recommendations", "capture_lead"], ["ethnic_bundle", "festival_accessories"], "Recommend outfits by occasion."),
    WorkflowSpec("doc_student_customer", "Student Customer", "exploring", "Create affordable packages for graduation, placements, or college events.", ["student", "graduation", "interview", "placement", "college"], ["What is the event?", "What budget range should I stay within?"], ["set_budget", "show_bundle", "capture_lead"], ["entry_package", "accessory_bundle"], "Balance affordability with polish."),
    WorkflowSpec("doc_gift_buyer", "Gift Buyer", "exploring", "Help shoppers buy for another person using occasion, budget, and recipient details.", ["gift", "present", "for him", "for her", "birthday"], ["Who is the gift for?", "What is the occasion?"], ["show_recommendations", "capture_lead", "open_cart"], ["gift_wrap", "gift_voucher"], "Avoid size questions unless needed."),
    WorkflowSpec("doc_customer_service", "Customer Service Desk", "customer_support", "Support tracking, address changes, delivery status, corrections, returns, and rework.", ["track order", "change address", "return", "status", "delivery"], ["What order or issue are you referring to?"], ["handoff_human", "capture_lead", "save_preferences"], ["resolution_followup", "service_ticket"], "Keep the user informed and minimize back and forth."),
]


EXPANSION_GROUPS: List[Tuple[str, List[Tuple[str, str, str]], List[str], List[str], List[str], List[str], List[str]]] = [
    (
        "custom shirt",
        [
            ("office", "ready_to_buy", "A formal office shirt with crisp fabric and conservative styling."),
            ("casual", "exploring", "A relaxed casual shirt for daily wear or smart-casual dressing."),
            ("party", "ready_to_buy", "A party shirt with stronger color and elevated styling."),
            ("wedding_guest", "researching_styles", "A refined shirt for a wedding guest look."),
            ("travel", "exploring", "A travel shirt focused on comfort and wrinkle resistance."),
            ("premium_luxury", "ready_to_buy", "An elevated luxury shirt with premium fabric and finishing."),
            ("summer_linen", "researching_styles", "A linen shirt for breathable warm-weather wear."),
            ("winter_layering", "researching_styles", "A shirt intended for layering under jackets or knits."),
            ("interview", "ready_to_buy", "A polished shirt for interviews and first impressions."),
            ("date_night", "exploring", "A sharp shirt for evening social events or date night."),
        ],
        ["shirt", "{label}"],
        ["What occasion is this shirt for?", "Which fabric family do you prefer?"],
        ["navigate_men", "show_fabric_options", "show_size_guide"],
        ["add_tie", "add_pocket_square"],
        ["shirt", "button down", "collar", "cuff"],
    ),
    (
        "custom suit",
        [
            ("business", "ready_to_buy", "A business suit for office and client meetings."),
            ("interview", "ready_to_buy", "A polished interview suit that communicates confidence."),
            ("wedding", "ready_to_buy", "A suit tailored for wedding season and receptions."),
            ("tuxedo", "ready_to_buy", "A tuxedo-driven formalwear path for black-tie events."),
            ("special_event", "exploring", "A special-event suit for parties, launches, or ceremonies."),
            ("conference", "exploring", "A conference suit that looks sharp across long travel days."),
            ("investment_pitch", "ready_to_buy", "A high-confidence suit for investor or board presentations."),
            ("award_night", "ready_to_buy", "A sharp suit for ceremonies and awards."),
            ("destination_wedding", "researching_styles", "A suit suited for travel, weather, and destination events."),
            ("photoshoot", "researching_styles", "A suit designed to photograph well under controlled light."),
        ],
        ["suit", "{label}", "blazer"],
        ["What is the purpose of the suit?", "Do you want ready or custom sizing?"],
        ["navigate_men", "show_fabric_options", "request_measurements"],
        ["add_shirt", "add_cufflinks"],
        ["lapel", "buttons", "lining", "trouser"],
    ),
    (
        "wedding",
        [
            ("groom_reception", "ready_to_buy", "Reception outfit planning with a formal and refined finish."),
            ("groom_haldi", "researching_styles", "A bright ceremonial outfit for haldi or pre-wedding events."),
            ("groom_sangeet", "researching_styles", "A festive look for sangeet, dance, and celebration."),
            ("groom_mehendi", "researching_styles", "An outfit for mehendi with ease of movement and color."),
            ("wedding_guest_formal", "exploring", "A guest outfit that stays festive without overshadowing the wedding party."),
            ("father_of_bride", "ready_to_buy", "A dignified look for the father of the bride."),
            ("father_of_groom", "ready_to_buy", "A dignified look for the father of the groom."),
            ("sibling_of_bride", "exploring", "A complementary look for the bride's sibling."),
            ("sibling_of_groom", "exploring", "A complementary look for the groom's sibling."),
            ("registry_ceremony", "ready_to_buy", "A clean formal outfit for registry or courthouse ceremonies."),
        ],
        ["wedding", "{label}", "groom", "guest"],
        ["Who is this outfit for?", "What event date or ceremony is this for?"],
        ["capture_lead", "request_measurements", "show_bundle"],
        ["add_accessories_bundle", "book_home_visit"],
        ["venue", "day time", "traditional", "modern"],
    ),
    (
        "ethnic wear",
        [
            ("kurta_diwali", "researching_styles", "A kurta-led look for Diwali and festive gatherings."),
            ("kurta_eid", "researching_styles", "A refined kurta outfit for Eid celebrations."),
            ("nehru_jacket", "ready_to_buy", "A Nehru jacket path for layering over kurta or shirt looks."),
            ("bandhgala", "ready_to_buy", "A bandhgala path for formal ethnic styling."),
            ("sherwani", "ready_to_buy", "A sherwani path for ceremonial and wedding wear."),
            ("festival_family_photo", "exploring", "A coordinated festive outfit for family portraits."),
            ("religious_ceremony", "researching_styles", "A respectful outfit for temple, mosque, or ceremonial visits."),
            ("navratri_garba", "exploring", "An outfit that works for movement and color during garba or dandiya."),
            ("pongal_celebration", "researching_styles", "A festive look suitable for Pongal gatherings."),
            ("wedding_season_ethnic", "ready_to_buy", "A versatile ethnic piece for an entire wedding season."),
        ],
        ["kurta", "{label}", "sherwani", "bandhgala"],
        ["Which festive event is this for?", "Traditional or modern styling?"],
        ["navigate_men", "show_recommendations", "capture_lead"],
        ["add_accessories_bundle", "show_fabric_options"],
        ["festival", "celebration", "ethnic", "formal"],
    ),
    (
        "accessory",
        [
            ("tie_only", "ready_to_buy", "Fast path for a single tie purchase."),
            ("pocket_square", "ready_to_buy", "Fast path for a pocket square purchase."),
            ("belt_gift", "exploring", "A belt purchase for gifting or everyday wear."),
            ("cufflinks_formal", "ready_to_buy", "Cufflinks for formal shirts and event dressing."),
            ("wallet_gift", "exploring", "A wallet selection path that can be bought as a gift."),
            ("scarf_winter", "exploring", "A scarf or wrap for colder weather styling."),
            ("tie_bar", "ready_to_buy", "A tie bar or tie clip accessory path."),
            ("sock_bundle", "exploring", "A sock bundle for wardrobe completion."),
            ("lapel_pin", "ready_to_buy", "A lapel pin or boutonniere accessory path."),
            ("accessory_gift_set", "ready_to_buy", "A bundled accessory gift set."),
        ],
        ["accessory", "{label}", "tie", "belt", "cufflinks"],
        ["Is this for yourself or as a gift?"],
        ["navigate_accessories", "open_cart"],
        ["gift_wrap", "bundle_accessories"],
        ["gift", "formal", "everyday", "bundle"],
    ),
    (
        "discovery",
        [
            ("color_confused", "exploring", "A shopper who needs help choosing a color family."),
            ("fabric_compare", "researching_styles", "A shopper comparing fabrics or weaves."),
            ("budget_low", "exploring", "A shopper with a constrained budget who still wants a polished look."),
            ("budget_mid", "exploring", "A shopper in a moderate budget range."),
            ("budget_high", "ready_to_buy", "A shopper comfortable with a premium spend."),
            ("fit_confused", "exploring", "A shopper unsure about fit or silhouette."),
            ("style_quiz", "exploring", "A guided style quiz to improve recommendation quality."),
            ("wardrobe_refresh", "ready_to_buy", "A wardrobe refresh or closet reset conversation."),
            ("capsule_wardrobe", "researching_styles", "A minimal capsule wardrobe build."),
            ("sale_hunter", "exploring", "A deal-seeking customer looking for offers."),
        ],
        ["help me choose", "not sure", "{label}"],
        ["What is the occasion?", "What budget should I stay within?"],
        ["show_recommendations", "compare_products", "capture_lead"],
        ["style_quiz", "fabric_compare"],
        ["budget", "compare", "recommend", "help"],
    ),
    (
        "customer support",
        [
            ("track_order", "customer_support", "A customer checking order status or delivery progress."),
            ("change_address", "customer_support", "A customer wants to change the delivery address."),
            ("measurement_correction", "customer_support", "A correction to previously captured measurements."),
            ("return_request", "customer_support", "A return or refund request."),
            ("rework_request", "customer_support", "A rework or remake request due to fit or finish issues."),
            ("delivery_delay", "customer_support", "A complaint about delayed delivery."),
            ("damaged_item", "customer_support", "A damaged or defective item complaint."),
            ("exchange_request", "customer_support", "An exchange request for a different item or size."),
            ("reschedule_visit", "customer_support", "A request to reschedule a technician or consultation."),
            ("cancel_order", "customer_support", "An order cancellation request."),
        ],
        ["order", "delivery", "{label}"],
        ["What order or issue are you referring to?"],
        ["handoff_human", "capture_lead", "save_preferences"],
        ["service_ticket", "resolution_followup"],
        ["track", "delivery", "return", "change"],
    ),
    (
        "corporate uniform",
        [
            ("hospital_doctors", "corporate_lead", "Doctor coats and clinical apparel for hospital teams."),
            ("hospital_scrubs", "corporate_lead", "Scrubs and softwear for clinical staff."),
            ("hotel_chef", "corporate_lead", "Chef uniforms for hospitality kitchens."),
            ("hotel_housekeeping", "corporate_lead", "Housekeeping uniforms for hotel operations."),
            ("restaurant_staff", "corporate_lead", "Front-of-house and back-of-house restaurant uniforms."),
            ("bank_formalwear", "corporate_lead", "Uniform or dress code solutions for bank teams."),
            ("it_company", "corporate_lead", "Formal wear or branded attire for IT teams and events."),
            ("security_agency", "corporate_lead", "Security or guard uniforms with practical requirements."),
            ("manufacturing_plant", "corporate_lead", "Uniforms for manufacturing and industrial sites."),
            ("school_staff", "corporate_lead", "Attire for teachers, admin staff, or school events."),
        ],
        ["uniform", "corporate", "{label}"],
        ["What industry are you in?", "How many people need uniforms?"],
        ["create_quote", "capture_lead", "handoff_human"],
        ["bulk_pricing", "sample_kit"],
        ["company", "staff", "bulk", "quote"],
    ),
    (
        "international and vip",
        [
            ("international_shipping", "researching_styles", "A customer shipping outside India needs international logistics details."),
            ("customs_vat", "customer_support", "A customer needs customs, VAT, or duty guidance."),
            ("remote_measurement", "researching_styles", "A customer wants measurement help without in-person access."),
            ("video_consult", "ready_to_buy", "A customer wants a video consultation with a stylist."),
            ("home_visit", "ready_to_buy", "A customer wants a home visit in a serviced city."),
            ("vip_concierge", "ready_to_buy", "A premium concierge flow with white-glove service."),
            ("corporate_gift", "exploring", "A gift buyer purchasing for clients or partners."),
            ("anniversary_gift", "exploring", "A gift buyer shopping for an anniversary occasion."),
            ("father_gift", "exploring", "A gift buyer shopping for a father or father figure."),
            ("luxury_wardrobe_refresh", "ready_to_buy", "A premium wardrobe refresh with curated recommendations."),
        ],
        ["international", "luxury", "{label}"],
        ["Which country or city should I account for?", "Would you like a stylist consultation?"],
        ["capture_lead", "request_measurements", "start_consultation"],
        ["exclusive_fabric", "video_consultation"],
        ["vip", "global", "premium", "international"],
    ),
    (
        "loyalty and upsell",
        [
            ("measurement_recall", "ready_to_buy", "Reuse stored measurements for a fast reorder."),
            ("seasonal_refresh", "ready_to_buy", "A seasonal refresh for a customer who already owns the core wardrobe."),
            ("wardrobe_audit", "exploring", "Review a customer's current closet and identify gaps."),
            ("bundle_builder", "ready_to_buy", "Build a multi-item order around a single anchor garment."),
            ("shirt_restock", "ready_to_buy", "A repeat shirt order with a likely same-size recommendation."),
            ("suit_update", "ready_to_buy", "Refresh an existing suit order with a new color or fabric."),
            ("event_upsell", "exploring", "Add finishing pieces for an event outfit."),
            ("gift_followup", "exploring", "A gift buyer returning for a second purchase."),
            ("vip_closet_refresh", "ready_to_buy", "A high-touch closet refresh for a premium client."),
            ("membership_offer", "exploring", "Present loyalty or repeat-customer perks."),
        ],
        ["repeat", "loyalty", "membership", "{label}"],
        ["Would you like me to reuse past measurements or preferences?", "What is the main garment or occasion?"],
        ["save_preferences", "open_cart", "capture_lead"],
        ["bundle_accessories", "wardrobe_refresh"],
        ["reorder", "repeat", "membership", "refresh"],
    ),
]


def _generate_workflows() -> List[WorkflowSpec]:
    workflows = list(BASE_WORKFLOWS)
    for domain, variants, triggers, questions, actions, upsells, keywords in EXPANSION_GROUPS:
        for label, intent_bucket, summary in variants:
            trigger_phrases = [t.format(label=label.replace("_", " ")) for t in triggers]
            question_set = [q for q in questions]
            action_set = [a for a in actions]
            upsell_set = [u for u in upsells]
            trigger_set = list(dict.fromkeys(trigger_phrases + keywords + [label.replace("_", " ")]))
            workflows.append(
                _variant_workflow(
                    domain,
                    label,
                    intent_bucket,
                    summary,
                    trigger_set,
                    question_set,
                    action_set,
                    upsell_set,
                )
            )
    return workflows


WORKFLOWS: List[WorkflowSpec] = _generate_workflows()
WORKFLOW_INDEX: Dict[str, WorkflowSpec] = {workflow.id: workflow for workflow in WORKFLOWS}


def workflow_to_dict(workflow: WorkflowSpec) -> Dict[str, object]:
    return asdict(workflow)


def catalog_to_dicts() -> List[Dict[str, object]]:
    return [workflow_to_dict(workflow) for workflow in WORKFLOWS]


def _score_workflow(text: str, workflow: WorkflowSpec) -> int:
    haystack = f"{text} {workflow.title} {workflow.summary} {' '.join(workflow.trigger_phrases)}".lower()
    score = 0
    for phrase in workflow.trigger_phrases:
        if phrase.lower() in text:
            score += 6
    for token in text.split():
        if token and token in haystack:
            score += 1
    return score


def classify_workflow(user_text: str) -> WorkflowSpec:
    text = (user_text or "").lower()
    if not text.strip():
        return WORKFLOW_INDEX["master_entry"]
    ranked = sorted(WORKFLOWS, key=lambda workflow: _score_workflow(text, workflow), reverse=True)
    best = ranked[0]
    if _score_workflow(text, best) <= 1:
        return WORKFLOW_INDEX["master_entry"]
    return best


def related_workflows(selected: WorkflowSpec, limit: int = 4) -> List[WorkflowSpec]:
    scored: List[Tuple[int, WorkflowSpec]] = []
    for workflow in WORKFLOWS:
        if workflow.id == selected.id:
            continue
        score = 0
        if workflow.intent_bucket == selected.intent_bucket:
            score += 5
        if any(trigger in selected.summary.lower() for trigger in workflow.trigger_phrases):
            score += 2
        if any(trigger in workflow.summary.lower() for trigger in selected.trigger_phrases):
            score += 2
        scored.append((score, workflow))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [workflow for score, workflow in scored[:limit] if score > 0]


def render_workflow_brief(workflow: WorkflowSpec) -> str:
    lines = [
        f"- Workflow ID: `{workflow.id}`",
        f"- Title: {workflow.title}",
        f"- Intent bucket: `{workflow.intent_bucket}`",
        f"- Summary: {workflow.summary}",
        f"- Ask next: {workflow.questions[0] if workflow.questions else 'Clarify the goal'}",
        f"- Recommended actions: {', '.join(workflow.recommended_actions)}",
        f"- Upsells: {', '.join(workflow.upsells) if workflow.upsells else 'None'}",
    ]
    return "\n".join(lines)


def render_catalog_summary(max_items: int = 25) -> str:
    grouped: Dict[str, List[WorkflowSpec]] = {bucket: [] for bucket in INTENT_BUCKETS}
    for workflow in WORKFLOWS:
        grouped.setdefault(workflow.intent_bucket, []).append(workflow)
    lines: List[str] = []
    for bucket in INTENT_BUCKETS:
        items = grouped.get(bucket, [])[:max_items]
        if not items:
            continue
        lines.append(f"{bucket}:")
        for workflow in items:
            lines.append(f"- {workflow.title} ({workflow.id})")
    return "\n".join(lines)
