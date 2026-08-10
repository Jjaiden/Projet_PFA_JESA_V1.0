# pages/4_Decision_Analysis.py
"""
Decision Analysis page for JESA DMAT – From identified gaps to prioritized actions.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from components import render_footer, render_header

# ------------------------------------------------------------------------------
# MOCK DATA PROVIDER (temporary – to be replaced by backend adapter)
# ------------------------------------------------------------------------------
def _get_mock_decision_data() -> dict:
    """
    Return mock decision‑analysis data for frontend development.

    This function is temporary. In production, the criteria and recommendations
    will come from the backend/dashboard via a dedicated service.
    The frontend must NOT generate or filter recommendations itself.
    """
    return {
        "criteria": [
            {
                "id": "gap",
                "label": "Maturity Gap",
                "unit": "points",
                "min": 0,
                "max": 100,
            },
            {
                "id": "business_impact",
                "label": "Business Impact",
                "unit": "/100",
                "min": 0,
                "max": 100,
            },
            {
                "id": "strategic_importance",
                "label": "Strategic Importance",
                "unit": "/100",
                "min": 0,
                "max": 100,
            },
            {
                "id": "expected_roi",
                "label": "Expected ROI",
                "unit": "%",
                "min": 0,
                "max": 100,
            },
            {
                "id": "implementation_cost",
                "label": "Implementation Cost",
                "unit": "k€",
                "min": 0,
                "max": 1000,
            },
            {
                "id": "implementation_difficulty",
                "label": "Implementation Difficulty",
                "unit": "/100",
                "min": 0,
                "max": 100,
            },
        ],
        "recommendations": [
            {
                "id": "REC_001",
                "dimension": "Digital Culture",
                "title": "Digital Workforce Program",
            },
            {
                "id": "REC_002",
                "dimension": "Smart Operations",
                "title": "Smart Operations Improvement",
            },
            {
                "id": "REC_003",
                "dimension": "Cybersecurity",
                "title": "OT Security Enhancement",
            },
        ],
    }


def _validate_row(row: dict, criteria: list[dict]) -> list[str]:
    """Validate a single row's inputs against criteria bounds and completeness."""
    errors = []
    for criterion in criteria:
        cid = criterion["id"]
        value = row.get(cid)
        # Check presence
        if value is None or (isinstance(value, float) and value != value):  # NaN check
            errors.append(f"Missing value for {criterion['label']}")
        else:
            # Check bounds
            min_val = criterion.get("min")
            max_val = criterion.get("max")
            if min_val is not None and value < min_val:
                errors.append(f"{criterion['label']} must be ≥ {min_val}")
            if max_val is not None and value > max_val:
                errors.append(f"{criterion['label']} must be ≤ {max_val}")
    return errors


# ------------------------------------------------------------------------------
# PAGE CONTENT
# ------------------------------------------------------------------------------

# Page header
render_header(
    title="DECISION ANALYSIS",
    subtitle="From identified gaps to prioritized transformation actions",
    align="center",
    compact=False,
)

# Retrieve mock data – in production this will come from the backend/dashboard
data = _get_mock_decision_data()
criteria = data["criteria"]
recommendations = data["recommendations"]

# ------------------------------------------------------------------------------
# Empty state
# ------------------------------------------------------------------------------
if not recommendations:
    st.warning(
        "No transformation opportunities currently require decision prioritization.\n\n"
        "Return to the Dashboard to review the maturity assessment."
    )
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
    st.stop()

# ------------------------------------------------------------------------------
# Dynamic information banner
# ------------------------------------------------------------------------------
count = len(recommendations)
st.info(
    f"{count} transformation opportunity{'s' if count > 1 else ''} identified.\n\n"
    f"Enter the required site‑specific values for each opportunity to calculate their priorities."
)

# ------------------------------------------------------------------------------
# Methodology explanation (small, non‑intrusive)
# ------------------------------------------------------------------------------
with st.expander("How it works", expanded=False):
    st.markdown(
        """
        Enter the site‑specific values required by the decision model.
        These inputs will be sent to the decision engine for validation,
        normalization and priority calculation.
        """
    )

# ------------------------------------------------------------------------------
# Build the decision matrix (data editor)
# ------------------------------------------------------------------------------
# Create a DataFrame with recommendation metadata and blank input columns
rows = []
for rec in recommendations:
    row = {
        "recommendation_id": rec["id"],
        "dimension": rec["dimension"],
        "title": rec["title"],
    }
    for criterion in criteria:
        row[criterion["id"]] = None  # user must fill
    rows.append(row)

df = pd.DataFrame(rows)

# Configure column types
column_config = {
    "recommendation_id": st.column_config.TextColumn("ID", disabled=True),
    "dimension": st.column_config.TextColumn("Dimension", disabled=True),
    "title": st.column_config.TextColumn("Transformation Opportunity", disabled=True),
}

for criterion in criteria:
    column_config[criterion["id"]] = st.column_config.NumberColumn(
        f"{criterion['label']} ({criterion['unit']})",
        min_value=criterion.get("min"),
        max_value=criterion.get("max"),
        required=True,
        help=f"Enter a value between {criterion.get('min', '–')} and {criterion.get('max', '–')}.",
    )

# Display the editor with fixed rows (no add/delete)
st.markdown("### Decision Inputs")
edited_df = st.data_editor(
    df,
    column_config=column_config,
    width="stretch",
    hide_index=True,
    key="decision_matrix",
    num_rows="fixed",  # Prevent row addition/deletion
)

# ------------------------------------------------------------------------------
# Validation & status
# ------------------------------------------------------------------------------
all_valid = True
missing_count = 0

for idx, row in edited_df.iterrows():
    row_errors = _validate_row(row.to_dict(), criteria)
    if row_errors:
        all_valid = False
        missing_count += sum(1 for e in row_errors if "Missing" in e)

# Display validation summary – we keep it simple and avoid per-row expanders
if not all_valid:
    if missing_count > 0:
        st.warning(f"⚠ {missing_count} required input{'s' if missing_count > 1 else ''} are missing.")
    st.error("Please correct the missing or out‑of‑range values in the table above.")
else:
    st.success("✓ All required inputs completed")

# ------------------------------------------------------------------------------
# Submission button (decision gate)
# ------------------------------------------------------------------------------
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button(
        "CONTINUE TO PRIORITIZATION →",
        key="submit_decision",
        use_container_width=True,
        disabled=not all_valid,
    ):
        # Build the payload
        payload = []
        for idx, row in edited_df.iterrows():
            rec_id = row["recommendation_id"]
            criteria_inputs = {}
            for criterion in criteria:
                criteria_inputs[criterion["id"]] = row[criterion["id"]]
            payload.append({"recommendation_id": rec_id, "criteria": criteria_inputs})

        # Store the decision inputs in session state for the backend
        st.session_state["decision_analysis_inputs"] = payload

        # Navigate to Roadmap page (when available)
        # st.switch_page("pages/5_Roadmap.py")
        st.info("The Roadmap page is currently under development. Your inputs have been stored.")

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