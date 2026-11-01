import pytest

from planner.vendors import DEFAULT_QUESTIONS, checklist_for, compare_quotes


def test_known_category_has_specific_questions():
    assert len(checklist_for("Catering")) >= 4
    assert checklist_for("Catering") != DEFAULT_QUESTIONS


def test_unknown_category_uses_default_questions():
    assert checklist_for("Fireworks") == DEFAULT_QUESTIONS


def test_quotes_sorted_cheapest_first():
    quotes = [
        {"vendor": "B", "price": 300000, "extras": 0},
        {"vendor": "A", "price": 200000, "extras": 0},
    ]
    rows = compare_quotes(quotes, 280000, 200)
    assert [r["Vendor"] for r in rows] == ["A", "B"]


def test_over_budget_flagged_and_extras_counted():
    quotes = [{"vendor": "A", "price": 250000, "extras": 50000}]
    row = compare_quotes(quotes, 280000, 200)[0]
    assert row["Total (₹)"] == 300000
    assert row["Status"] == "Over budget"
    assert row["Difference vs budget (₹)"] == 20000


def test_per_guest_cost():
    row = compare_quotes([{"vendor": "A", "price": 280000, "extras": 0}], 300000, 200)[0]
    assert row["Per guest (₹)"] == 1400
    assert row["Status"] == "Within budget"


def test_blank_vendor_rows_ignored():
    quotes = [{"vendor": "", "price": 0, "extras": 0},
              {"vendor": "A", "price": 100, "extras": 0}]
    assert len(compare_quotes(quotes, 500, 10)) == 1


def test_no_quotes_rejected():
    with pytest.raises(ValueError):
        compare_quotes([{"vendor": "", "price": 0, "extras": 0}], 500, 10)


def test_bad_amount_rejected():
    with pytest.raises(ValueError):
        compare_quotes([{"vendor": "A", "price": 0, "extras": 0}], 500, 10)