from datetime import date

import pytest

from planner import replan as replan_module
from planner.budget import allocate_budget
from planner.replan import build_advice_prompt, compare_budgets, create_plan, replan

FAKE_TASKS = [{"id": "a", "title": "Book venue", "category": "Venue",
               "due_date": "2027-01-01", "priority": "High", "depends_on": []}]


@pytest.fixture(autouse=True)
def fake_ai(monkeypatch):
    monkeypatch.setattr(replan_module, "generate_timeline", lambda *a, **k: FAKE_TASKS)
    monkeypatch.setattr(replan_module, "ask_gemini", lambda prompt: "- Trade-off advice")


def base_plan():
    return create_plan("Wedding", 800000, 200, date(2027, 2, 20), ["Catering"], "good food")


def test_create_plan_stores_inputs():
    plan = base_plan()
    assert plan["guests"] == 200
    assert sum(plan["allocation"].values()) == 800000
    assert plan["tasks"] == FAKE_TASKS


def test_compare_budgets_shows_change():
    old = {"Venue": 100, "Catering": 200}
    new = {"Venue": 50, "Catering": 100}
    rows = {r["Category"]: r["Change (₹)"] for r in compare_budgets(old, new)}
    assert rows == {"Venue": -50, "Catering": -100}


def test_replan_halves_budget():
    new = replan(base_plan(), 400000, 200, date(2027, 2, 6), "family paying less")
    assert sum(new["allocation"].values()) == 400000
    assert sum(new["previous_allocation"].values()) == 800000
    assert new["advice"] == "- Trade-off advice"


def test_replan_keeps_focus_categories():
    new = replan(base_plan(), 400000, 200, date(2027, 2, 6))
    default = allocate_budget(400000, "Wedding")
    assert new["allocation"]["Catering"] > default["Catering"]


def test_advice_failure_does_not_break_replan(monkeypatch):
    def boom(prompt):
        raise RuntimeError("AI down")

    monkeypatch.setattr(replan_module, "ask_gemini", boom)
    new = replan(base_plan(), 400000, 150, date(2027, 2, 6))
    assert new["advice"] == ""
    assert sum(new["allocation"].values()) == 400000


def test_advice_prompt_truncates_long_note():
    old = base_plan()
    new = replan(old, 400000, 200, date(2027, 2, 6))
    prompt = build_advice_prompt(old, new, "x" * 5000)
    assert "x" * 501 not in prompt


def test_replan_rejects_zero_budget():
    with pytest.raises(ValueError):
        replan(base_plan(), 0, 200, date(2027, 2, 6))