"""Budget logic for the Celebration Planner.

Plain Python, no AI. The percentages are rough planning guidelines,
NOT confirmed vendor prices.
"""

DEFAULT_SPLITS = {
    "Wedding": {
        "Venue": 25, "Catering": 35, "Decoration": 12, "Photography": 10,
        "Attire & Beauty": 8, "Invitations & Misc": 5, "Contingency": 5,
    },
    "Birthday": {
        "Venue": 20, "Catering": 35, "Decoration": 15, "Entertainment": 15,
        "Photography": 5, "Return Gifts & Misc": 5, "Contingency": 5,
    },
    "Community Event": {
        "Venue": 20, "Catering": 25, "Decoration": 10, "Publicity": 10,
        "Entertainment": 15, "Volunteers & Logistics": 10, "Contingency": 10,
    },
}


def _scale(weights: dict, total: int) -> dict:
    """Split `total` rupees in proportion to `weights`; amounts add up exactly."""
    weight_sum = sum(weights.values())
    result = {name: int(total * w / weight_sum) for name, w in weights.items()}
    leftover = total - sum(result.values())
    result[max(result, key=result.get)] += leftover
    return result


def allocate_budget(total: float, event_type: str, priorities: dict | None = None) -> dict:
    """Split a total budget into categories.

    priorities: optional multipliers, e.g. {"Catering": 1.5} spends more on food.
    """
    total = round(total)
    if total <= 0:
        raise ValueError("Budget must be greater than zero.")
    if event_type not in DEFAULT_SPLITS:
        raise ValueError(f"Unknown event type: {event_type}")

    split = DEFAULT_SPLITS[event_type]
    priorities = priorities or {}
    for name, factor in priorities.items():
        if name not in split:
            raise ValueError(f"Unknown category: {name}")
        if factor <= 0:
            raise ValueError("Priority multipliers must be greater than zero.")

    weights = {name: pct * priorities.get(name, 1.0) for name, pct in split.items()}
    return _scale(weights, total)


def rescale_budget(allocation: dict, new_total: float) -> dict:
    """Shrink or grow an existing plan to a new total, keeping the same proportions."""
    new_total = round(new_total)
    if new_total <= 0:
        raise ValueError("Budget must be greater than zero.")
    return _scale(allocation, new_total)


def per_guest_catering(allocation: dict, guests: int) -> int:
    """Catering money available per guest."""
    if guests <= 0:
        raise ValueError("Guest count must be greater than zero.")
    return allocation["Catering"] // guests

def largest_category(allocation: dict) -> tuple[str, float]:
    """Return the biggest category and its percentage share of the budget."""
    name = max(allocation, key=allocation.get)
    return name, allocation[name] / sum(allocation.values()) * 100