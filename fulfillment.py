from __future__ import annotations

"""Deterministic lead-time / delivery-date math - kept separate from
fashion_knowledge/outfit_planner because this is about logistics, not
styling, but it's the same idea: plain arithmetic, not another LLM guess.

The gap this closes: nothing in the app previously checked whether the
sizing method a customer picks can actually get a finished garment to them
before whatever they're shopping for (a wedding, a specific event date).
"Schedule a doorstep visit" for a wedding reception in 3 days would happily
book a technician for tomorrow with zero acknowledgement that stitching +
shipping alone takes longer than that. These numbers are estimates for the
prototype (tune to real production/shipping SLAs when known) - the point is
that the check happens at all, and happens the same way every time."""

from datetime import date, timedelta
from typing import Any, Dict, Optional

# Rough estimates, in calendar days from today, until a finished garment
# could realistically reach the customer via each sizing method.
LEAD_TIME_DAYS: Dict[str, int] = {
    "ready_to_wear": 3,        # in-stock item, size already known -> ships now
    "manual_measurements": 10,  # made-to-measure production + shipping
    "doorstep_visit": 13,       # technician visit lead time + production + shipping
    "virtual_tryon": 10,        # same production timeline as manual, no visit wait
}

# Earliest a technician can typically be booked for a doorstep visit.
VISIT_SCHEDULING_LEAD_DAYS = 2

_METHOD_BY_ACTION = {
    "request_measurements": "manual_measurements",
    "schedule_technician": "doorstep_visit",
    "request_photo": "virtual_tryon",
    "show_style_preview": "virtual_tryon",
}


def method_for_action(action_type: str) -> Optional[str]:
    return _METHOD_BY_ACTION.get(action_type)


def earliest_visit_date(from_date: Optional[date] = None) -> date:
    base = from_date or date.today()
    return base + timedelta(days=VISIT_SCHEDULING_LEAD_DAYS)


def estimate(method: str, event_date: Optional[str] = None) -> Dict[str, Any]:
    """Earliest realistic delivery date for `method`, from today. If
    `event_date` (an ISO 'YYYY-MM-DD' string) is known, also says whether
    that's actually in time, so the conversation can flag a real risk
    ("that visit alone won't leave enough time before the 12th") instead of
    silently confirming something that can't arrive in time."""
    today = date.today()
    lead_days = LEAD_TIME_DAYS.get(method, LEAD_TIME_DAYS["manual_measurements"])
    delivery = today + timedelta(days=lead_days)

    result: Dict[str, Any] = {
        "method": method,
        "lead_time_days": lead_days,
        "earliest_delivery": delivery.isoformat(),
    }

    if event_date:
        try:
            event = date.fromisoformat(event_date)
        except ValueError:
            return result
        result["event_date"] = event_date
        result["days_to_spare"] = (event - delivery).days
        result["can_make_it"] = delivery <= event

    return result
