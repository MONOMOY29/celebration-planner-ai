import pytest 


from planner.budget import allocate_budget, largest_category, per_guest_catering, rescale_budget

def test_allocation_adds_up_exactly():
    plan = allocate_budget(800000, "Wedding")
    assert sum(plan.values()) == 800000


def test_priority_increases_that_category():
    normal = allocate_budget(800000, "Wedding")
    food_first = allocate_budget(800000, "Wedding", {"Catering": 1.5})
    assert food_first["Catering"] > normal["Catering"]
    assert sum(food_first.values()) == 800000


def test_unknown_event_type_rejected():
    with pytest.raises(ValueError):
        allocate_budget(100000, "Space Launch")


def test_zero_budget_rejected():
    with pytest.raises(ValueError):
        allocate_budget(0, "Birthday")


def test_unknown_priority_category_rejected():
    with pytest.raises(ValueError):
        allocate_budget(100000, "Birthday", {"Fireworks": 2})


def test_rescale_keeps_total_and_shrinks_categories():
    plan = allocate_budget(800000, "Wedding")
    smaller = rescale_budget(plan, 400000)
    assert sum(smaller.values()) == 400000
    assert smaller["Venue"] < plan["Venue"]


def test_per_guest_catering():
    plan = {"Catering": 280000}
    assert per_guest_catering(plan, 200) == 1400
    with pytest.raises(ValueError):
        per_guest_catering(plan, 0)


def test_largest_category():
    name, share = largest_category({"Venue": 200, "Catering": 600, "Decor": 200})
    assert name == "Catering"
    assert share == 60