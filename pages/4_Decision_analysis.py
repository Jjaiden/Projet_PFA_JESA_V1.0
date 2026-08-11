# pages/4_Decision_analysis.py
"""
Decision Analysis page for JESA DMAT - From identified gaps to prioritized actions.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import render_footer, render_header
from utils.assessment_service import build_decision_rows, run_decision_analysis
from utils.history_store import save_assessment_history


CRITERIA = [
    {"id": "business_impact", "label": "Business Impact", "unit": "1-5", "min": 1, "max": 5},
    {"id": "strategic_importance", "label": "Strategic Importance", "unit": "1-5", "min": 1, "max": 5},
    {"id": "expected_roi", "label": "Expected ROI", "unit": "1-5", "min": 1, "max": 5},
    {"id": "implementation_cost", "label": "Implementation Cost", "unit": "1-5", "min": 1, "max": 5},
    {"id": "implementation_difficulty", "label": "Implementation Difficulty", "unit": "1-5", "min": 1, "max": 5},
]


def _validate_row(row: dict) -> list[str]:
    errors = []
    for criterion in CRITERIA:
        value = row.get(criterion["id"])
        if value is None or pd.isna(value):
            errors.append(f"Missing value for {criterion['label']}")
            continue
        if int(value) != value or value < criterion["min"] or value > criterion["max"]:
            errors.append(f"{criterion['label']} must be an integer between 1 and 5")
    return errors


render_header(
    title="DECISION ANALYSIS",
    subtitle="From identified gaps to prioritized transformation actions",
    align="center",
    compact=False,
)

backend_results = st.session_state.get("backend_results")
if not backend_results:
    st.warning(
        "No assessment is currently loaded.\n\n"
        "Start a new assessment or open one from History first."
    )
    st.stop()

rows = build_decision_rows(backend_results)

if not rows:
    st.warning(
        "No transformation opportunities currently require decision prioritization.\n\n"
        "Return to the Dashboard to review the maturity assessment."
    )
    st.stop()

st.info(
    f"{len(rows)} transformation opportunity{'s' if len(rows) > 1 else ''} identified.\n\n"
    "Enter the required site-specific values for each dimension to calculate priorities."
)

with st.expander("How it works", expanded=False):
    st.markdown(
        """
        Enter values from 1 to 5 for each decision criterion.
        These inputs are sent to the backend TPI engine for validation,
        normalization and priority calculation.
        """
    )

df = pd.DataFrame(rows)
for criterion in CRITERIA:
    df[criterion["id"]] = 3

column_config = {
    "dimension_id": st.column_config.TextColumn("ID", disabled=True),
    "dimension": st.column_config.TextColumn("Dimension", disabled=True),
    "current_score": st.column_config.NumberColumn("Current", disabled=True, format="%.2f"),
    "target_score": st.column_config.NumberColumn("Target", disabled=True, format="%.2f"),
    "gap": st.column_config.NumberColumn("Gap", disabled=True, format="%.2f"),
}

for criterion in CRITERIA:
    column_config[criterion["id"]] = st.column_config.NumberColumn(
        f"{criterion['label']} ({criterion['unit']})",
        min_value=criterion["min"],
        max_value=criterion["max"],
        step=1,
        required=True,
        help="Enter an integer from 1 to 5.",
    )

st.markdown("### Decision Inputs")
edited_df = st.data_editor(
    df,
    column_config=column_config,
    width="stretch",
    hide_index=True,
    key="decision_matrix",
    num_rows="fixed",
)

all_valid = True
missing_count = 0
for _, row in edited_df.iterrows():
    row_errors = _validate_row(row.to_dict())
    if row_errors:
        all_valid = False
        missing_count += sum(1 for error in row_errors if "Missing" in error)

if not all_valid:
    if missing_count > 0:
        st.warning(f"{missing_count} required input{'s' if missing_count > 1 else ''} are missing.")
    st.error("Please correct the missing or out-of-range values in the table above.")
else:
    st.success("All required inputs completed")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button(
        "CONTINUE TO PRIORITIZATION ->",
        key="submit_decision",
        use_container_width=True,
        disabled=not all_valid,
    ):
        decision_inputs = {}
        for _, row in edited_df.iterrows():
            decision_inputs[row["dimension_id"]] = {
                criterion["id"]: int(row[criterion["id"]])
                for criterion in CRITERIA
            }

        try:
            result = run_decision_analysis(backend_results, decision_inputs)
            st.session_state["decision_analysis_inputs"] = decision_inputs
            st.session_state["backend_results"] = result["backend_results"]
            st.session_state["roadmap_results"] = result["roadmap_results"]
            st.session_state["serialized_results"] = result["serialized_results"]
            save_assessment_history(result["serialized_results"])
            st.success("Decision analysis completed successfully.")
            st.switch_page("pages/5_Roadmap.py")
        except Exception as exc:
            st.error(f"Decision analysis failed: {exc}")

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
