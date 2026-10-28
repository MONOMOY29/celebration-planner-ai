import json
from datetime import date

import pytest

from planner import timeline
from planner.timeline import parse_timeline

TODAY = date(2026, 10, 28)
EVENT = date(2027, 2, 20)


def make(tasks):
    return json.dumps({"tasks": tasks})


def test_sorted_by_due_date():
    raw = make([
        {"id": "a", "title": "Later", "due_date": "2027-01-10", "priority": "Low"},
        {"id": "b", "title": "Sooner", "due_date": "2026-11-15", "priority": "High"},
    ])
    result = parse_timeline(raw, TODAY, EVENT)
    assert [t["id"] for t in result] == ["b", "a"]


def test_dates_clamped_inside_window():
    raw = make([
        {"id": "a", "title": "Too early", "due_date": "2020-01-01"},
        {"id": "b", "title": "Too late", "due_date": "2030-01-01"},
    ])
    result = {t["id"]: t["due_date"] for t in parse_timeline(raw, TODAY, EVENT)}
    assert result["a"] == "2026-10-28"
    assert result["b"] == "2027-02-20"


def test_task_not_due_before_its_dependency():
    raw = make([
        {"id": "venue", "title": "Book venue", "due_date": "2026-12-01"},
        {"id": "invites", "title": "Send invites", "due_date": "2026-11-01",
         "depends_on": ["venue"]},
    ])
    result = {t["id"]: t["due_date"] for t in parse_timeline(raw, TODAY, EVENT)}
    assert result["invites"] >= result["venue"]


def test_unknown_dependency_removed():
    raw = make([{"id": "a", "title": "Task", "due_date": "2026-12-01",
                 "depends_on": ["ghost", "a"]}])
    assert parse_timeline(raw, TODAY, EVENT)[0]["depends_on"] == []


def test_invalid_priority_defaults_to_medium():
    raw = make([{"id": "a", "title": "Task", "due_date": "2026-12-01",
                 "priority": "URGENT!!"}])
    assert parse_timeline(raw, TODAY, EVENT)[0]["priority"] == "Medium"


def test_garbage_response_rejected():
    with pytest.raises(ValueError):
        parse_timeline("not json at all", TODAY, EVENT)
    with pytest.raises(ValueError):
        parse_timeline(json.dumps({"tasks": []}), TODAY, EVENT)


def test_past_event_date_rejected():
    with pytest.raises(ValueError):
        timeline.generate_timeline("Wedding", date(2020, 1, 1), 100, 50000)


def test_generate_timeline_uses_ai_reply(monkeypatch):
    fake = make([{"id": "a", "title": "Book venue", "due_date": "2027-01-01"}])
    monkeypatch.setattr(timeline, "ask_gemini_json", lambda prompt: fake)
    result = timeline.generate_timeline("Wedding", date(2027, 6, 1), 200, 800000)
    assert result[0]["title"] == "Book venue"