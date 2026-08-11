# pages/3_Dashboard.py
"""
Digital Maturity Dashboard for JESA DMAT – Industrial Plant Assessment Overview.
"""

from __future__ import annotations

import streamlit as st

from components import render_footer, render_header
from charts import BarChart, GaugeChart


def _get_largest_gap(dimensions: list[dict]) -> dict | None:
    """Return the dimension with the largest negative gap."""
    if not dimensions:
        return None
    sorted_dims = sorted(dimensions, key=lambda d: d["gap"])
    return sorted_dims[0] if sorted_dims[0]["gap"] < 0 else None


def _count_attention_areas(dimensions: list[dict], threshold: int = -10) -> int:
    """Count dimensions with gap below threshold (i.e., significant negative gap)."""
    return sum(1 for d in dimensions if d["gap"] < threshold)


# ------------------------------------------------------------------------------
# PAGE LAYOUT
# ------------------------------------------------------------------------------

# Check if assessment data exists
if not st.session_state.get("dashboard_data"):
    st.warning("No assessment is currently loaded. Please start a new assessment from the Home page.")
    st.stop()

data = st.session_state["dashboard_data"]

# Page header
render_header(
    title="DIGITAL MATURITY DIAGNOSTIC",
    subtitle="Industrial Plant · Assessment Overview",
    align="center",
    compact=False,
)

# ------------------------------------------------------------------------------
# SECTION A – Executive Snapshot
# ------------------------------------------------------------------------------
st.markdown("## Executive Snapshot")

# Prepare KPI values
largest_gap_dim = _get_largest_gap(data["dimensions"])
largest_gap_label = largest_gap_dim["name"] if largest_gap_dim else "—"
largest_gap_value = f"{largest_gap_dim['gap']} pts" if largest_gap_dim else "—"
attention_count = _count_attention_areas(data["dimensions"])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="DMI",
        value=f"{data['dmi']:.1f}%",
        delta=None,
    )
with col2:
    st.metric(
        label="MATURITY",
        value=data["maturity_level"].upper(),
        delta=None,
    )
with col3:
    st.metric(
        label="OVERALL GAP",
        value=f"{data['dmi_gap']:.1f} pts",
        delta_color="inverse" if data["dmi_gap"] < 0 else "normal",
    )
with col4:
    st.metric(
        label="ATTENTION",
        value=f"{attention_count} areas",
        delta=None,
    )

st.divider()

# ------------------------------------------------------------------------------
# SECTION B – Overall Position
# ------------------------------------------------------------------------------
st.markdown("## Overall Position")

col_gauge, col_info = st.columns([2, 1])

with col_gauge:
    gauge = GaugeChart(
        value=data["dmi"],
        title="DMI",
        unit="%",
        show_threshold=True,
        threshold=70,
        steps=(
            (0, 40, "#EF4444"),
            (40, 70, "#F59E0B"),
            (70, 100, "#10B981"),
        ),
    )
    st.plotly_chart(gauge.create(), width="stretch")

with col_info:
    st.metric("Maturity Level", data["maturity_level"])
    st.metric("Target", f"{data['target_dmi']:.1f}%")
    st.metric(
        "Gap",
        f"{data['dmi_gap']:.1f} pts",
        delta_color="inverse" if data["dmi_gap"] < 0 else "normal",
    )

st.divider()

# ------------------------------------------------------------------------------
# SECTION C – Maturity Profile
# ------------------------------------------------------------------------------
st.markdown("## Maturity Profile")
st.caption("What does our maturity profile look like?")

# Prepare pillar data for horizontal bar chart
pillar_names = [p["name"] for p in data["pillars"]]
pillar_scores = [p["score"] for p in data["pillars"]]

# Sort pillars descending by score for better readability
sorted_pillars = sorted(zip(pillar_names, pillar_scores), key=lambda x: x[1], reverse=True)
pillar_names_sorted = [p[0] for p in sorted_pillars]
pillar_scores_sorted = [p[1] for p in sorted_pillars]

chart = BarChart(
    categories=pillar_names_sorted,
    values=pillar_scores_sorted,
    title="Pillar Performance",
    orientation="horizontal",
    show_values=True,
    height=400,
)
st.plotly_chart(chart.create(), width="stretch")

st.divider()

# ------------------------------------------------------------------------------
# SECTION D – Dimension Gap Analysis
# ------------------------------------------------------------------------------
st.markdown("## Dimension Gap Analysis")
st.caption("Where is the transformation pressure?")

# Prepare data for grouped bar chart (current vs target)
dim_names = [d["name"] for d in data["dimensions"]]
current_scores = [d["current"] for d in data["dimensions"]]
target_scores = [d["target"] for d in data["dimensions"]]

dim_chart = BarChart(
    categories=dim_names,
    values=[current_scores, target_scores],
    series_names=["Current", "Target"],
    orientation="horizontal",
    mode="grouped",
    show_values=True,
    height=400,
    title="Current vs Target",
)
st.plotly_chart(dim_chart.create(), width="stretch")

st.divider()

# ------------------------------------------------------------------------------
# SECTION E – Diagnostic Interpretation
# ------------------------------------------------------------------------------
st.markdown("## What This Means")

for insight in data["insights"]:
    icon_map = {"danger": "🔴", "warning": "🟠", "success": "🟢"}
    color_map = {"danger": "var(--dmat-danger)", "warning": "var(--dmat-warning)", "success": "var(--dmat-success)"}
    icon = icon_map.get(insight["type"], "⚪")
    color = color_map.get(insight["type"], "var(--dmat-text)")
    st.markdown(
        f"""
        <div style="display: flex; gap: 0.75rem; margin-bottom: 0.75rem;">
            <div style="color: {color}; font-weight: 600;">{icon}</div>
            <div>
                <div style="font-weight: 500;">{insight['title']}</div>
                <div style="color: var(--dmat-muted); font-size: 0.9rem;">{insight['text']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ------------------------------------------------------------------------------
# SECTION F – Decision Gate
# ------------------------------------------------------------------------------
st.markdown("## Diagnosis Complete")

st.write(
    "Your maturity profile has been established. The next step is to identify and prioritize the transformation actions."
)

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button(
        "ANALYZE & PRIORITIZE →",
        key="to_decision",
        use_container_width=True,
    ):
        st.switch_page("pages/4_Decision_analysis.py")

# ------------------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------------------
render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {"label": "JESA", "url": "https://www.jesa.ma"},
        {"label": "ENSAM Casablanca", "url": "https://ensam-casablanca.ma"},
    ],
    align="center",
    compact=False,
    show_divider=True,
)
