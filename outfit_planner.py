from __future__ import annotations

"""
A real (if simple) constraint-satisfaction outfit planner - deterministic
arithmetic over the product catalog, not an LLM guessing at a complete
outfit. This directly answers the "doesn't automatically plan the best
outfit within a customer's budget when one isn't specified" gap: it runs
whenever we know enough (occasion + gender) to plan something, whether or
not a budget was stated - constrained to the budget when one exists, and
optimizing for occasion fit alone when it doesn't.
"""

from typing import Any, Dict, List, Optional

import fashion_knowledge
import product_catalog


def _best_candidate(
    candidate_ids: List[str],
    occasion: Optional[str],
    body_type: Optional[str],
    max_price: Optional[int],
) -> Optional[Dict[str, Any]]:
    scored = []
    for pid in candidate_ids:
        product = product_catalog.get_product(pid)
        if not product:
            continue
        if max_price is not None and product["price"] > max_price:
            continue
        score, rationale = fashion_knowledge.style_score(pid, occasion=occasion, body_type=body_type)
        scored.append((score, pid, product, rationale))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    score, pid, product, rationale = scored[0]
    return {
        "product_id": pid,
        "name": product["name"],
        "price": product["price"],
        "style_score": score,
        "style_rationale": rationale,
    }


def plan_outfit(
    occasion: Optional[str],
    budget: Optional[int] = None,
    gender: str = "men",
    body_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble one complete outfit (a main garment plus, budget permitting,
    one accessory). When `budget` is None, this still returns the
    best-for-occasion pick rather than doing nothing - the "not specifying a
    budget" case is exactly the one the original app never handled."""

    garment_budget_cap = int(budget * 0.85) if budget else None
    garment = _best_candidate(
        product_catalog.main_garments(gender), occasion, body_type, garment_budget_cap
    )

    over_budget = False
    if garment is None and budget is not None:
        # Nothing fits comfortably under budget with headroom for an
        # accessory - relax to the full budget and flag it honestly rather
        # than silently returning nothing.
        garment = _best_candidate(product_catalog.main_garments(gender), occasion, body_type, budget)
        if garment is None:
            # Still nothing - the budget is below even the cheapest option.
            cheapest_id = min(
                product_catalog.main_garments(gender),
                key=lambda pid: product_catalog.get_product(pid)["price"],
                default=None,
            )
            if cheapest_id:
                product = product_catalog.get_product(cheapest_id)
                score, rationale = fashion_knowledge.style_score(cheapest_id, occasion=occasion, body_type=body_type)
                garment = {
                    "product_id": cheapest_id,
                    "name": product["name"],
                    "price": product["price"],
                    "style_score": score,
                    "style_rationale": rationale,
                }
                over_budget = True

    items = []
    total_price = 0
    if garment:
        items.append({**garment, "role": "main_garment"})
        total_price += garment["price"]
        if budget is not None and total_price > budget:
            over_budget = True

    remaining_budget = (budget - total_price) if budget is not None else None
    accessory = _best_candidate(
        product_catalog.accessories(gender), occasion, body_type, remaining_budget
    )
    if accessory:
        items.append({**accessory, "role": "accessory"})
        total_price += accessory["price"]

    compat_score, compat_rationale = fashion_knowledge.compatibility_score([item["product_id"] for item in items])

    return {
        "occasion": occasion,
        "budget": budget,
        "gender": gender,
        "items": items,
        "total_price": total_price,
        "within_budget": (total_price <= budget) if budget is not None else None,
        "over_budget": over_budget,
        "compatibility_score": compat_score,
        "compatibility_rationale": compat_rationale,
    }
