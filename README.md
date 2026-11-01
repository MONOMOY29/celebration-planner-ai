# 🎉 Celebration & Event Planner (Challenge 5)

A GenAI-powered planning assistant that helps Indian families organize weddings,
birthdays and community events within a budget, and **re-plans instantly when
something changes**.

**Live app:**   https://celebration-planner-ai-6vuhredcku5jxbzkjzcpc8.streamlit.app/

## Chosen vertical

Family celebrations on a tight budget (wedding, birthday, community event). The assistant is built for a family that knows roughly what they want but needs help splitting the money, sequencing the work, and adapting when plans change.

## Approach and logic

The project separates what code does well from what AI does well:

| Part | Done by | Why |
|---|---|---|
| Budget split, per-guest catering, rescaling | Plain Python (`planner/budget.py`) | Money math must be exact and testable |
| Dated task timeline with dependencies | Gemini, then validated by Python (`planner/timeline.py`) | AI understands the event context; code makes sure the output is safe |
| Re-planning and trade-off advice | Python recalculates, Gemini explains (`planner/replan.py`) | AI never invents numbers |

## How it works

1. The user enters event type, budget, guests, date, categories to spend more on,and must-haves.
2. **Budget:** the total is split across categories using typical planning ratios.
   Categories the user prioritises get a larger share, and the total always
   adds up exactly.
3. **Timeline:** Gemini returns tasks as JSON. The code then checks every task:
   dates are kept between today and the event date, unknown dependencies are
   removed, and no task is due before the task it depends on.
4. **Something changed?** The user updates budget, guest count or date. The plan is rebuilt, a before/after table shows what changed, and Gemini gives short trade-off advice using numbers already calculated by Python.
5. **Vendors:** a category-specific checklist of questions to ask vendors, plus a
quote comparison that adds extra charges, shows the cost per guest, and flags each quote as within or over the planned budget. It uses only the quotes the user enters, so no prices are invented.

## GenAI usage

- **Google Gemini** (`gemini-flash-lite-latest`, via the `google-genai` SDK) is used for 
(1) generating the dependency-aware task timeline as structured JSON and
(2) explaining trade-offs when a plan changes.
- AI output is validated before use, user text is length-limited, and if the
  advice call fails the updated plan still shows.

## Assumptions

- Budget percentages are rough planning guidelines, **not vendor quotes**. The app says so on screen and never claims a vendor is available or a price is confirmed.
- Amounts are in Indian rupees (₹).
- The event date must be in the future.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file containing `GEMINI_API_KEY=your_key_here`, then:

```bash
streamlit run app.py
```

## Tests

```bash
pip install pytest
python -m pytest
```

Tests cover budget math, timeline validation and re-planning. The AI is mocked,so tests run offline.

## Security

The API key is read from the environment (`.env` locally, Streamlit secrets when deployed) and is never committed to the repository.

## Accessibility

- Every input has a visible text label and help text; no information depends on colour alone.
- The budget chart has a text summary and a full data table, so it is readable without sight.
- Tab and section names are plain text (no emoji-only labels).
- All controls are standard Streamlit widgets, so they work with keyboard and screen readers.
