"""Create plans and re-plan when the user's situation changes."""
from planner.ai import ask_gemini
from planner.budget import allocate_budget, per_guest_catering
from planner.timeline import generate_timeline

FOCUS_BOOST = 1.5
MAX_TEXT = 500


def create_plan(event_type, budget, guests, event_date, focus, must_haves=""):
    """Build a full plan: budget split plus dated timeline."""
    allocation = allocate_budget(
        budget, event_type, {name: FOCUS_BOOST for name in focus}
    )
    tasks = generate_timeline(event_type, event_date, guests, budget, must_haves)
    return {
        "event_type": event_type,
        "focus": list(focus),
        "must_haves": must_haves,
        "event_date": event_date,
        "guests": guests,
        "budget": budget,
        "allocation": allocation,
        "tasks": tasks,
    }


def compare_budgets(old, new):
    """Rows showing how each category changed between two plans."""
    return [
        {
            "Category": name,
            "Before (₹)": old.get(name, 0),
            "After (₹)": amount,
            "Change (₹)": amount - old.get(name, 0),
        }
        for name, amount in new.items()
    ]


def build_advice_prompt(old_plan, new_plan, note):
    """Prompt for Gemini. All numbers are calculated here, not by the AI."""
    rows = compare_budgets(old_plan["allocation"], new_plan["allocation"])
    biggest = sorted(rows, key=lambda r: abs(r["Change (₹)"]), reverse=True)[:3]
    changes = "; ".join(f"{r['Category']}: {r['Change (₹)']:+,} INR" for r in biggest)
    old_pg = per_guest_catering(old_plan["allocation"], old_plan["guests"])
    new_pg = per_guest_catering(new_plan["allocation"], new_plan["guests"])
    note = (note or "none")[:MAX_TEXT]
    return f"""You are an event planning assistant for Indian families.
The user's {new_plan['event_type']} plan changed. These facts are already
calculated, do not recalculate them:
- Budget: {old_plan['budget']} INR -> {new_plan['budget']} INR
- Guests: {old_plan['guests']} -> {new_plan['guests']}
- Event date: {old_plan['event_date']} -> {new_plan['event_date']}
- Catering per guest: {old_pg} INR -> {new_pg} INR
- Biggest category changes: {changes}
- User's note: {note}

Give 3 to 5 short bullet points on the trade-offs and what to prioritise.
End by asking which part of the event matters most to them.
Do not invent prices or claim any vendor is available."""


def replan(plan, new_budget, new_guests, new_date, note=""):
    """Update an existing plan after something changed."""
    context = plan["must_haves"]
    if note:
        context = f"{context} | Latest change: {note}"
    new_plan = create_plan(
        plan["event_type"], new_budget, new_guests, new_date, plan["focus"], context
    )
    new_plan["must_haves"] = plan["must_haves"]
    new_plan["previous_allocation"] = plan["allocation"]
    try:
        new_plan["advice"] = ask_gemini(build_advice_prompt(plan, new_plan, note))
    except Exception:  # advice is a bonus; the new plan must still show
        new_plan["advice"] = ""
    return new_plan