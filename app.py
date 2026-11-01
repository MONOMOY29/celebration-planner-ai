"""Celebration & Event Planner: Streamlit front end."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from planner.budget import DEFAULT_SPLITS, allocate_budget, per_guest_catering
from planner.timeline import generate_timeline

st.set_page_config(page_title="Celebration Planner AI", page_icon="🎉", layout="wide")

st.title("🎉 Celebration & Event Planner")
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
    try:
        allocation = allocate_budget(
            budget, event_type, {name: 1.5 for name in focus}
        )
        with st.spinner("Building your timeline..."):
            tasks = generate_timeline(
                event_type, event_date, int(guests), int(budget), must_haves
            )
        st.session_state["plan"] = {
            "allocation": allocation,
            "tasks": tasks,
            "guests": int(guests),
            "budget": int(budget),
        }
    except ValueError as err:
        st.error(str(err))
    except Exception:
        st.error("Could not reach the AI service. Please try again in a minute.")

plan = st.session_state.get("plan")

if not plan:
    st.info("Fill in your event details on the left, then click **Create my plan**.")
else:
    tab_budget, tab_timeline = st.tabs(["💰 Budget", "📅 Timeline"])

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
        st.dataframe(budget_df, hide_index=True)
        st.bar_chart(budget_df.set_index("Category"))
        st.caption("Estimates based on typical planning ratios. Confirm with real vendor quotes.")

    with tab_timeline:
        timeline_df = pd.DataFrame(plan["tasks"])[
            ["due_date", "priority", "title", "category"]
        ]
        timeline_df.columns = ["Due date", "Priority", "Task", "Category"]
        st.dataframe(timeline_df, hide_index=True)