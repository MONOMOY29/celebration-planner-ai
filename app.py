"""Celebration & Event Planner: Streamlit front end."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from planner.budget import DEFAULT_SPLITS, largest_category, per_guest_catering
from planner.replan import compare_budgets, create_plan, replan
from planner.vendors import checklist_for, compare_quotes

st.set_page_config(page_title="Celebration Planner AI", page_icon="🎉", layout="wide")


def safe_call(func, *args):
    """Run func and show a friendly error instead of crashing."""
    try:
        return func(*args)
    except ValueError as err:
        st.error(str(err))
    except Exception:
        st.error("Could not reach the AI service. Please try again in a minute.")
    return None


st.title("Celebration & Event Planner")
st.caption(
    "Tell us about your event and get a budget split and a dated to-do timeline. "
    "All amounts are planning estimates, not vendor quotes."
)

with st.sidebar:
    st.header("Your event")
    event_type = st.selectbox("Type of event", list(DEFAULT_SPLITS))
    budget = st.number_input(
        "Total budget (₹)", min_value=10000, value=800000, step=10000
    )
    guests = st.number_input("Expected guests", min_value=1, value=200, step=10)
    event_date = st.date_input(
        "Event date",
        value=date.today() + timedelta(days=120),
        min_value=date.today() + timedelta(days=1),
    )
    focus = st.multiselect(
        "Spend more on",
        list(DEFAULT_SPLITS[event_type]),
        help="These categories get a larger share of your budget.",
    )
    must_haves = st.text_area(
        "Must-haves",
        max_chars=500,
        help="For example: great food, simple decoration, elderly-friendly venue.",
    )
    create = st.button("Create my plan", type="primary")

if create:
    with st.spinner("Building your plan..."):
        new_plan = safe_call(
            create_plan, event_type, int(budget), int(guests),
            event_date, focus, must_haves,
        )
    if new_plan:
        st.session_state["plan"] = new_plan

plan = st.session_state.get("plan")

if not plan:
    st.info("Fill in your event details on the left, then click **Create my plan**.")
else:
    with st.expander("Something changed? Update your plan"):
        col_a, col_b, col_c = st.columns(3)
        new_budget = col_a.number_input(
            "New total budget (₹)", min_value=10000, value=plan["budget"], step=10000
        )
        new_guests = col_b.number_input(
            "New guest count", min_value=1, value=plan["guests"], step=10
        )
        new_date = col_c.date_input(
            "New event date",
            value=plan["event_date"],
            min_value=date.today() + timedelta(days=1),
        )
        note = st.text_input(
            "What happened? (optional)",
            max_chars=300,
            placeholder="e.g. a family member is contributing less this year",
        )
        if st.button("Update my plan"):
            with st.spinner("Re-planning..."):
                updated = safe_call(
                    replan, plan, int(new_budget), int(new_guests), new_date, note
                )
            if updated:
                st.session_state["plan"] = updated
                st.rerun()

    tab_budget, tab_timeline, tab_vendors = st.tabs(["Budget", "Timeline", "Vendors"])

    with tab_budget:
        col1, col2 = st.columns(2)
        col1.metric("Total budget", f"₹{plan['budget']:,}")
        col2.metric(
            "Catering per guest",
            f"₹{per_guest_catering(plan['allocation'], plan['guests']):,}",
        )
        budget_df = pd.DataFrame(
            {
                "Category": list(plan["allocation"]),
                "Amount (₹)": list(plan["allocation"].values()),
            }
        )
        st.table(
            budget_df.assign(**{"Amount (₹)": budget_df["Amount (₹)"].map("{:,}".format)})
            .set_index("Category")
        )

        top_name, top_share = largest_category(plan["allocation"])
        st.markdown(
            f"**Summary:** the largest share goes to **{top_name}** "
            f"(₹{plan['allocation'][top_name]:,}, {top_share:.0f}% of the budget). "
            "The full breakdown is in the table above."
        )
        st.bar_chart(budget_df.set_index("Category"))
        st.caption("Estimates based on typical planning ratios. Confirm with real vendor quotes.")

        if plan.get("previous_allocation"):
            st.subheader("What changed")
            st.table(
                pd.DataFrame(
                    compare_budgets(plan["previous_allocation"], plan["allocation"])
                ).set_index("Category")
            )
            if plan.get("advice"):
                st.markdown(plan["advice"])
            else:
                st.info(
                    "AI advice is unavailable right now (the AI service may be busy). "
                    "Your updated plan above is still correct."
                )

    with tab_timeline:
        timeline_df = pd.DataFrame(plan["tasks"])[
            ["due_date", "priority", "title", "category"]
        ]
        timeline_df.columns = ["Due date", "Priority", "Task", "Category"]
        st.table(timeline_df.set_index("Due date"))

    with tab_vendors:
        st.subheader("Vendor checklist and quote comparison")
        category = st.selectbox(
            "Vendor type", list(plan["allocation"]), key="vendor_category"
        )
        st.markdown(
            f"Your planned budget for **{category}**: "
            f"₹{plan['allocation'][category]:,}"
        )
        st.markdown("**Questions to ask every vendor:**")
        for question in checklist_for(category):
            st.checkbox(question, key=f"q_{category}_{question}")

        st.markdown("**Compare quotes** (up to 3; leave unused vendors blank)")
        quotes = []
        for i, col in enumerate(st.columns(3), start=1):
            vendor = col.text_input(f"Vendor {i} name", key=f"v_name_{i}", max_chars=60)
            price = col.number_input(
                f"Vendor {i} quote (₹)", min_value=0, step=1000, key=f"v_price_{i}"
            )
            extras = col.number_input(
                f"Vendor {i} extra charges (₹)", min_value=0, step=500, key=f"v_extra_{i}"
            )
            quotes.append({"vendor": vendor, "price": price, "extras": extras})

        if st.button("Compare quotes"):
            try:
                rows = compare_quotes(quotes, plan["allocation"][category], plan["guests"])
                st.table(pd.DataFrame(rows).set_index("Vendor"))
                st.caption(
                    "Based only on the quotes you entered. "
                    "Confirm availability with each vendor."
                )
            except ValueError as err:
                st.error(str(err))