from __future__ import annotations

"""
A small, explicit styling knowledge base plus deterministic (non-LLM)
scoring functions.

Why this exists as data + arithmetic rather than "ask the model to reason
about it better": an LLM asked to explain suitability with no reference
material will produce fluent-sounding but ungrounded claims (it may say a
fabric is "breathable and season-appropriate" whether or not that's true for
the fabric actually being discussed). Feeding it real reference facts (fabric
weight, occasion dress codes, body-type fit guidance) turns "sounds
plausible" into "grounded in an actual rule," and the two numeric scores
below are computed with plain arithmetic against that same reference data so
they're consistent and explainable, not a fresh LLM guess every time.

This is intentionally small and readable rather than exhaustive - the point
is the pattern (structured knowledge -> grounded prompt context + rule-based
scores), which is easy to extend with more entries later.
"""

from typing import Any, Dict, List, Optional, Tuple

import product_catalog

BODY_TYPE_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "ectomorph_men": {
        "label": "Lean/slender build",
        "recommend": "Structured shoulders, softer padding, and a slim-to-regular fit add visual width without swamping the frame. Layering (waistcoat, textured jacket) helps.",
        "avoid": "Oversized or heavily loose cuts, which read as ill-fitting rather than relaxed.",
    },
    "mesomorph_men": {
        "label": "Athletic/broad build",
        "recommend": "A regular or slim fit with minimal shoulder padding lets the natural shape do the work; darted waists keep the silhouette clean.",
        "avoid": "Double-breasted jackets and heavy shoulder padding, which can look bulky rather than sharp.",
    },
    "endomorph_men": {
        "label": "Fuller build",
        "recommend": "A regular or slightly relaxed fit with a single-breasted, notch-lapel jacket and a longer jacket length is the most flattering and comfortable combination; vertical patterns (pinstripe) elongate the line.",
        "avoid": "Slim/skinny cuts and short jacket lengths, which tend to emphasize rather than flatter.",
    },
}

OCCASION_DRESS_CODES: Dict[str, Dict[str, Any]] = {
    "office": {"formality": 3, "notes": "Business formal to business casual - solid or subtle-pattern suits/blazers in grey, navy, or neutral tones read as professional without being severe."},
    "interview": {"formality": 3, "notes": "Lean conservative: solid colors, minimal pattern, a fit that photographs and reads as put-together rather than trend-forward."},
    "business": {"formality": 3, "notes": "Same register as office - reliable, not attention-seeking."},
    "wedding": {"formality": 4, "notes": "Depends on role (guest vs. groom) and time of day - daytime weddings tolerate lighter colors, evening/reception leans toward richer tones or black."},
    "reception": {"formality": 4, "notes": "Evening formality - darker, richer colors and a more finished silhouette (satin details, tuxedo-adjacent pieces) suit this best."},
    "party": {"formality": 3, "notes": "Room to be a little bolder with color or pattern than office wear, without going full black-tie."},
    "casual": {"formality": 1, "notes": "Comfort and ease of movement first - lighter fabrics, relaxed fits, less structure."},
    "travel": {"formality": 1, "notes": "Wrinkle-resistant, breathable fabrics matter more than formality here."},
    "diwali": {"formality": 3, "notes": "Festive but not black-tie - richer colors are welcome, but this isn't the place for a tuxedo."},
    "black_tie": {"formality": 5, "notes": "Tuxedo-only register: black/midnight, satin lapels, minimal color."},
}

FABRIC_PROFILES: Dict[str, Dict[str, Any]] = {
    "wool": {"warmth": "medium-high", "best_seasons": "autumn/winter, air-conditioned settings", "notes": "The default suiting fabric - structured drape, holds a crease well."},
    "cashmere": {"warmth": "high", "best_seasons": "winter", "notes": "Soft hand-feel and warmth at a premium price point; best for cooler climates or evening wear."},
    "linen": {"warmth": "low", "best_seasons": "summer", "notes": "Breathable and cool, but wrinkles easily - better for casual/travel than for a crisp interview look."},
    "cotton": {"warmth": "low-medium", "best_seasons": "spring/summer", "notes": "Easy-care and breathable; more casual than wool unless woven densely."},
    "silk": {"warmth": "low", "best_seasons": "all, mostly for accessories", "notes": "Used here mainly for ties/pocket squares - adds sheen and a formal finish rather than structure."},
}


def _slot_occasion_key(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return raw.strip().lower().replace(" ", "_")


def build_fashion_context(slots: Dict[str, Any], body_type: Optional[str] = None) -> str:
    """Render whatever reference knowledge is actually relevant to the
    customer's current slots, so the system prompt is grounded in real rules
    instead of asking the model to invent styling logic on the spot."""
    lines: List[str] = []

    occasion_key = _slot_occasion_key(slots.get("occasion"))
    occasion_info = OCCASION_DRESS_CODES.get(occasion_key) if occasion_key else None
    if occasion_info:
        lines.append(
            f"- Occasion dress code ({slots.get('occasion')}): formality level {occasion_info['formality']}/5. {occasion_info['notes']}"
        )

    fabric_key = (slots.get("fabric") or "").strip().lower()
    fabric_info = FABRIC_PROFILES.get(fabric_key)
    if fabric_info:
        lines.append(
            f"- Fabric reference ({slots.get('fabric')}): warmth {fabric_info['warmth']}, best in {fabric_info['best_seasons']}. {fabric_info['notes']}"
        )

    if body_type and body_type in BODY_TYPE_GUIDANCE:
        guidance = BODY_TYPE_GUIDANCE[body_type]
        lines.append(
            f"- Body-type fit guidance ({guidance['label']}): recommend {guidance['recommend']} Avoid: {guidance['avoid']}"
        )

    if not lines:
        return ""

    return "Fashion Knowledge (use this to ground *why* a recommendation suits them - don't just assert suitability without this basis):\n" + "\n".join(lines)


def style_score(product_id: str, occasion: Optional[str] = None, body_type: Optional[str] = None) -> Tuple[int, str]:
    """A deterministic 0-100 score for how well a specific product suits the
    stated occasion and body type - plain arithmetic against the reference
    tables above, not a fresh LLM judgment call each time (so the same
    inputs always produce the same score and the same reasoning)."""
    product = product_catalog.get_product(product_id)
    if not product:
        return 0, "Unknown product."

    score = 60  # baseline: a reasonable product with no negative signal
    reasons: List[str] = []

    occasion_key = _slot_occasion_key(occasion)
    if occasion_key:
        if occasion_key in (product.get("best_occasions") or []):
            score += 25
            reasons.append(f"well-suited to {occasion}")
        else:
            occasion_info = OCCASION_DRESS_CODES.get(occasion_key)
            if occasion_info and abs(occasion_info["formality"] - product["formality"]) >= 2:
                score -= 20
                reasons.append(f"formality level is a mismatch for {occasion}")
            else:
                reasons.append(f"formality level is compatible with {occasion}, though not a top pick")

    if body_type and body_type in BODY_TYPE_GUIDANCE:
        # Endomorph guidance favors single-breasted/regular fit and vertical
        # pattern - this piece's category/name gives us a rough, honest
        # signal without pretending to know the exact cut of every SKU.
        if body_type == "endomorph_men" and "pinstripe" in product["name"].lower():
            score += 10
            reasons.append("vertical pinstripe pattern is flattering for this build")
        if body_type == "mesomorph_men" and "double" in product["name"].lower():
            score -= 10
            reasons.append("double-breasted styling can look bulky for an athletic build")

    score = max(0, min(100, score))
    rationale = "; ".join(reasons) if reasons else "General-purpose fit with no strong signal either way."
    return score, rationale


_FORMALITY_TOLERANCE = 1  # pieces worn together should be within this many formality levels of each other


def compatibility_score(product_ids: List[str]) -> Tuple[int, str]:
    """A deterministic 0-100 score for how well a *set* of products work
    together as one outfit - checks formality-level alignment and basic
    color clash rules, not an LLM guessing whether things "go together.\""""
    products = [product_catalog.get_product(pid) for pid in product_ids]
    products = [p for p in products if p]
    if len(products) < 2:
        return 100, "Only one item - nothing to check compatibility against."

    score = 100
    reasons: List[str] = []

    formalities = [p["formality"] for p in products]
    spread = max(formalities) - min(formalities)
    if spread > _FORMALITY_TOLERANCE:
        penalty = 15 * (spread - _FORMALITY_TOLERANCE)
        score -= penalty
        reasons.append(f"formality levels span {spread} points, which reads as mismatched (e.g. a black-tie piece with a casual one)")
    else:
        reasons.append("formality levels are aligned across pieces")

    color_families = {p["color_family"] for p in products if p["color_family"] not in {"neutral", "multi"}}
    if len(color_families) > 2:
        score -= 15
        reasons.append(f"{len(color_families)} distinct color families in one outfit is a lot to coordinate")
    else:
        reasons.append("color palette is coherent")

    score = max(0, min(100, score))
    return score, "; ".join(reasons)
