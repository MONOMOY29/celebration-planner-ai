"""Vendor checklists and quote comparison (plain Python, no AI)."""

QUESTIONS = {
    "Venue": [
        "Is my date free, and what is the booking deposit?",
        "What is the maximum guest capacity, seated and standing?",
        "Are decoration, power backup and parking included?",
        "What is the cancellation and refund policy?",
        "Is there a time limit, and what are the overtime charges?",
    ],
    "Catering": [
        "What is the price per plate, and how many guests does the quote cover?",
        "Is the tasting free, and can the menu be changed?",
        "Are crockery, waiters and cleaning included?",
        "What extra charges apply for additional guests?",
        "Can you handle dietary needs (Jain, vegan, allergies)?",
    ],
    "Decoration": [
        "What exactly is included (stage, entry, lighting, flowers)?",
        "Are setup and takedown included in the price?",
        "Can I see photos of your previous work?",
        "What happens if the venue changes or the date moves?",
    ],
    "Photography": [
        "How many hours and how many photographers are included?",
        "When will I receive the edited photos and the album?",
        "Do I get all the raw photos and the usage rights?",
        "What are the travel and overtime charges?",
    ],
}

DEFAULT_QUESTIONS = [
    "What exactly is included in the quote?",
    "What extra charges might apply?",
    "What is the advance payment and the cancellation policy?",
    "Can you share references or photos of past work?",
]


def checklist_for(category: str) -> list[str]:
    """Questions to ask a vendor of this category."""
    return QUESTIONS.get(category, DEFAULT_QUESTIONS)


def compare_quotes(quotes: list[dict], category_budget: float, guests: int) -> list[dict]:
    """Compare vendor quotes against the planned budget, cheapest first.

    Each quote is {"vendor": str, "price": number, "extras": number}.
    Rows with no vendor name are ignored.
    """
    if guests <= 0:
        raise ValueError("Guest count must be greater than zero.")
    if category_budget <= 0:
        raise ValueError("Budget must be greater than zero.")

    rows = []
    for quote in quotes:
        name = str(quote.get("vendor", "")).strip()
        if not name:
            continue
        price = quote.get("price", 0)
        extras = quote.get("extras", 0)
        if price <= 0 or extras < 0:
            raise ValueError(f"Please check the amounts entered for {name}.")
        total = price + extras
        rows.append(
            {
                "Vendor": name,
                "Total (₹)": total,
                "Per guest (₹)": round(total / guests),
                "Difference vs budget (₹)": total - category_budget,
                "Status": "Within budget" if total <= category_budget else "Over budget",
            }
        )

    if not rows:
        raise ValueError("Enter at least one vendor name and quote.")
    return sorted(rows, key=lambda row: row["Total (₹)"])