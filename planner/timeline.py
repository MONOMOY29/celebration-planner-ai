"""AI-generated, dependency-aware event timeline.

Gemini proposes the tasks; this module validates them so bad AI output
cannot break the app.
"""
import json
from datetime import date, datetime

from planner.ai import ask_gemini_json

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
MAX_TEXT = 500


def build_prompt(event_type, event_date, today, guests, budget, must_haves):
    """Build the instruction sent to Gemini."""
    must_haves = (must_haves or "none")[:MAX_TEXT]
    return f"""You are an event planning assistant for Indian families.
Create a task timeline for a {event_type}.
Today: {today.isoformat()}. Event date: {event_date.isoformat()}.
Guests: {guests}. Total budget: INR {budget}. Must-haves: {must_haves}.

Rules:
- Return ONLY JSON: {{"tasks": [{{"id": "t1", "title": "...", "category": "...",
  "due_date": "YYYY-MM-DD", "priority": "High|Medium|Low", "depends_on": ["t0"]}}]}}
- 12 to 20 tasks. Every due_date must be between today and the event date.
- A task must come after the tasks it depends on (e.g. book venue before invitations).
- Do not invent prices or claim any vendor is available."""


def parse_timeline(raw, today, event_date):
    """Validate Gemini's JSON and return a clean, sorted task list."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("The AI returned an invalid response.") from exc

    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("The AI returned no tasks.")

    clean = {}
    for item in tasks:
        task_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        if not task_id or not title or task_id in clean:
            continue
        due = datetime.strptime(str(item.get("due_date", "")), "%Y-%m-%d").date()
        due = min(max(due, today), event_date)
        priority = item.get("priority")
        clean[task_id] = {
            "id": task_id,
            "title": title,
            "category": str(item.get("category", "General")),
            "due": due,
            "priority": priority if priority in PRIORITY_RANK else "Medium",
            "depends_on": [str(d) for d in item.get("depends_on", [])],
        }

    if not clean:
        raise ValueError("The AI returned no usable tasks.")

    for task in clean.values():
        task["depends_on"] = [
            d for d in task["depends_on"] if d in clean and d != task["id"]
        ]

    # A task can never be due before the tasks it depends on.
    for _ in range(len(clean)):
        changed = False
        for task in clean.values():
            for dep in task["depends_on"]:
                if clean[dep]["due"] > task["due"]:
                    task["due"] = clean[dep]["due"]
                    changed = True
        if not changed:
            break

    result = sorted(
        clean.values(), key=lambda t: (t["due"], PRIORITY_RANK[t["priority"]])
    )
    for task in result:
        task["due_date"] = task.pop("due").isoformat()
    return result


def generate_timeline(event_type, event_date, guests, budget, must_haves=""):
    """Ask Gemini for a timeline and return validated tasks."""
    today = date.today()
    if event_date <= today:
        raise ValueError("The event date must be in the future.")
    prompt = build_prompt(event_type, event_date, today, guests, budget, must_haves)
    return parse_timeline(ask_gemini_json(prompt), today, event_date)