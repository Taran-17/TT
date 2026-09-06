from __future__ import annotations

"""
Server-side mirror of the product data in static/app.js's CATALOG, extended
with the attributes needed for deterministic (non-LLM) styling logic: how
formal a piece is, its color family, which occasions/body types it suits.

This intentionally duplicates the id/name/price fields already in app.js
rather than trying to share a single source across Python and JS in this
prototype - keeping this file authoritative for anything the backend reasons
about (budget planning, scoring), and app.js authoritative for rendering.
If this app grows a proper product service, these should merge into one
source of truth.

Formality scale: 1 = casual, 2 = smart-casual, 3 = business, 4 = formal/
black-tie-adjacent, 5 = black-tie/tuxedo only.
"""

from typing import Any, Dict, List, Optional

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "silver-slate": {
        "name": "Silver Slate Suit Set",
        "category": "main_garment",
        "gender": "men",
        "price": 32000,
        "formality": 3,
        "color_family": "grey",
        "fabric_weight": "medium",
        "best_occasions": ["office", "interview", "business", "wedding_guest"],
    },
    "pearl-white": {
        "name": "Pearl White Suit Set",
        "category": "main_garment",
        "gender": "men",
        "price": 35000,
        "formality": 4,
        "color_family": "white",
        "fabric_weight": "medium",
        "best_occasions": ["wedding", "reception", "party"],
    },
    "umber-pinstripe": {
        "name": "Umber Pinstripe Suit Set",
        "category": "main_garment",
        "gender": "men",
        "price": 38000,
        "formality": 3,
        "color_family": "brown",
        "fabric_weight": "heavy",
        "best_occasions": ["office", "business", "interview"],
    },
    "soot-black": {
        "name": "Soot Black Tuxedo Set",
        "category": "main_garment",
        "gender": "men",
        "price": 34000,
        "formality": 5,
        "color_family": "black",
        "fabric_weight": "medium",
        "best_occasions": ["wedding", "reception", "party", "black_tie"],
    },
    "misty-aqua": {
        "name": "Misty Aqua Suit Set",
        "category": "main_garment",
        "gender": "women",
        "price": 31000,
        "formality": 2,
        "color_family": "blue",
        "fabric_weight": "light",
        "best_occasions": ["office", "casual", "travel"],
    },
    "charcoal-blazer": {
        "name": "Charcoal Dusk Blazer",
        "category": "main_garment",
        "gender": "women",
        "price": 18000,
        "formality": 3,
        "color_family": "grey",
        "fabric_weight": "medium",
        "best_occasions": ["office", "business", "party"],
    },
    "printed-tie-combo": {
        "name": "Printed Tie & Pocket Square Combo",
        "category": "accessory",
        "gender": "men",
        "price": 1800,
        "formality": 3,
        "color_family": "multi",
        "fabric_weight": "light",
        "best_occasions": ["office", "wedding", "party", "business"],
    },
    "mens-belt": {
        "name": "Classic Men's Leather Belt",
        "category": "accessory",
        "gender": "men",
        "price": 2000,
        "formality": 2,
        "color_family": "neutral",
        "fabric_weight": "n/a",
        "best_occasions": ["office", "casual", "business", "travel"],
    },
}


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    return PRODUCTS.get(product_id)


def main_garments(gender: Optional[str] = None) -> List[str]:
    return [
        pid
        for pid, p in PRODUCTS.items()
        if p["category"] == "main_garment" and (gender is None or p["gender"] == gender)
    ]


def accessories(gender: Optional[str] = None) -> List[str]:
    return [
        pid
        for pid, p in PRODUCTS.items()
        if p["category"] == "accessory" and (gender is None or p["gender"] == gender)
    ]
