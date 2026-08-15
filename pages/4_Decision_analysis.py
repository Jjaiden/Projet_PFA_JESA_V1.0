"""
Decision Analysis page for JESA DMAT.

Collect site-specific decision parameters for each
transformation opportunity and send them to the TPI engine.
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from components import render_footer, render_header
from engines.decision.tpi import DECISION_CRITERIA
from utils.assessment_service import (
    build_decision_rows,
    run_decision_analysis,
)
from utils.history_store import save_assessment_history


# ==============================================================================
# VALIDATION
# ==============================================================================

def _validate_value(value, criterion: dict) -> str | None:
    """Validate one decision input against its criterion definition."""

    if value is None or pd.isna(value):
        return f"{criterion['label']} is required."

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return f"{criterion['label']} must be numeric."

    if not math.isfinite(numeric_value):
        return f"{criterion['label']} must be a finite number."

    minimum = criterion.get("min_value")
    maximum = criterion.get("max_value")

    if minimum is not None and numeric_value < minimum:
        return (
            f"{criterion['label']} must be greater than or equal to "
            f"{minimum:g} {criterion['unit']}."
        )

    if maximum is not None and numeric_value > maximum:
        return (
            f"{criterion['label']} must be lower than or equal to "
            f"{maximum:g} {criterion['unit']}."
        )

    return None


def _validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Validate every editable decision cell."""

    errors: list[str] = []

    for row_index, row in df.iterrows():
        dimension_name = row.get(
            "dimension",
            f"Dimension {row_index + 1}",
        )

        for criterion in DECISION_CRITERIA:
            error = _validate_value(
                row.get(criterion["id"]),
                criterion,
            )

            if error:
                errors.append(
                    f"{dimension_name}: {error}"
                )

    return errors


# ==============================================================================
# PAGE HEADER
# ==============================================================================

render_header(
    title="DECISION ANALYSIS",
    subtitle="From identified gaps to prioritized transformation actions",
    align="center",
    compact=False,
)


# ==============================================================================
# LOAD ASSESSMENT
# ==============================================================================

backend_results = st.session_state.get("backend_results")

if not backend_results:
    st.warning(
        "No assessment is currently loaded. "
        "Start a new assessment or open one from History first."
    )
    st.stop()



# ==============================================================================
# BUILD DECISION OPPORTUNITIES
# ==============================================================================

rows = build_decision_rows(backend_results)

if not rows:
    st.warning(
        "No transformation opportunities currently require "
        "decision prioritization."
    )
    st.stop()


# ==============================================================================
# INTRODUCTION
# ==============================================================================

opportunity_count = len(rows)

st.info(
    f"**{opportunity_count} transformation "
    f"opportunit{'y' if opportunity_count == 1 else 'ies'} identified.**\n\n"
    "Complete all decision criteria for each transformation opportunity."
)


# ==============================================================================
# DECISION DATAFRAME
# ==============================================================================

df = pd.DataFrame(rows)

# ==============================================================================
# DECISION CRITERIA EXPLANATION
# ==============================================================================

if "show_criteria" not in st.session_state:
    st.session_state.show_criteria = False

if st.button("Understanding the Decision Criteria", type="secondary"):
    st.session_state.show_criteria = not st.session_state.show_criteria

if st.session_state.show_criteria:

    st.markdown(
        """
        <div style="font-size: 1rem; color: #666; margin-bottom: 15px;">
        Before completing the matrix, review what each criterion represents
        and how its value should be interpreted.
        </div>
        """,
        unsafe_allow_html=True
    )

    criteria_columns = st.columns(len(DECISION_CRITERIA))

    for column, criterion in zip(criteria_columns, DECISION_CRITERIA):
        with column:

            st.markdown(
                f"**{criterion['display_label']}**"
            )

            st.markdown(
                f"""
                <div style="font-size: 0.75rem; color: #666;">
                {criterion.get(
                    "help",
                    "Enter the value that best represents the current "
                    "site-specific situation."
                )}
                </div>
                """,
                unsafe_allow_html=True
            )

            unit = criterion.get("unit")
            minimum = criterion.get("min_value")
            maximum = criterion.get("max_value")

            if unit and minimum is not None and maximum is not None:
                st.markdown(
                    f"""
                    <div style="font-size: 0.72rem; color: #777;">
                    <strong>Expected range:</strong>
                    {minimum:,.0f}–{maximum:,.0f} {unit}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            elif unit:
                st.markdown(
                    f"""
                    <div style="font-size: 0.72rem; color: #777;">
                    <strong>Unit:</strong> {unit}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
# ------------------------------------------------------------------------------
# EMPTY DECISION INPUTS
# ------------------------------------------------------------------------------

for criterion in DECISION_CRITERIA:
    df[criterion["id"]] = pd.Series(
        [pd.NA] * len(df),
        dtype="Float64",
    )


# ==============================================================================
# COLUMN CONFIGURATION
# ==============================================================================

column_config = {

    # --------------------------------------------------------------------------
    # Fixed assessment information
    # --------------------------------------------------------------------------

    "dimension_id": st.column_config.TextColumn(
        "ID",
        disabled=True,
        width="small",
    ),

    "dimension": st.column_config.TextColumn(
        "Dimension",
        disabled=True,
        width="large",
    ),

    "current_score": st.column_config.NumberColumn(
        "Current",
        disabled=True,
        format="%.2f",
        width="small",
    ),

    "target_score": st.column_config.NumberColumn(
        "Target",
        disabled=True,
        format="%.2f",
        width="small",
    ),

    "gap": st.column_config.NumberColumn(
        "Gap",
        disabled=True,
        format="%.2f",
        width="small",
    ),
}


# ------------------------------------------------------------------------------
# Editable decision criteria
# ------------------------------------------------------------------------------

for criterion in DECISION_CRITERIA:

    column_config[criterion["id"]] = st.column_config.NumberColumn(
        label=criterion["display_label"],
        help=criterion["help"],
        min_value=criterion.get("min_value"),
        max_value=criterion.get("max_value"),
        step=criterion["step"],
        required=True,
        format=criterion["format"],
        width="medium",
    )


# ==============================================================================
# SECTION TITLE
# ==============================================================================

st.markdown("### Transformation Priority Inputs")

st.caption(
    "Complete every white input cell using the unit and range specified "
    "for each criterion."
)


# ==============================================================================
# EDITABLE TABLE
# ==============================================================================

edited_df = st.data_editor(
    df,
    column_config=column_config,

    column_order=[
        "dimension",
        "current_score",
        "target_score",
        "gap",
        *[criterion["id"] for criterion in DECISION_CRITERIA],
    ],

    hide_index=True,
    width="stretch",
    num_rows="fixed",

    key="decision_matrix_v3",

    row_height=46,

    placeholder="Required",
)


# ==============================================================================
# VALIDATION
# ==============================================================================

validation_errors = _validate_dataframe(edited_df)

all_valid = len(validation_errors) == 0


# Count missing values only
missing_count = sum(
    1
    for _, row in edited_df.iterrows()
    for criterion in DECISION_CRITERIA
    if row.get(criterion["id"]) is None
    or pd.isna(row.get(criterion["id"]))
)


# ------------------------------------------------------------------------------
# SINGLE STATUS MESSAGE
# ------------------------------------------------------------------------------

if missing_count > 0:

    st.warning(
        f"{missing_count} required "
        f"value{'s' if missing_count > 1 else ''} "
        "missing."
    )

elif all_valid:

    st.success(
        "All required inputs are complete."
    )


# ------------------------------------------------------------------------------
# NON-MISSING VALIDATION ERRORS
# ------------------------------------------------------------------------------

non_missing_errors = [
    error
    for error in validation_errors
    if "is required." not in error
]

if non_missing_errors:

    st.warning(
        "Please correct the highlighted input values "
        "before continuing."
    )


# ==============================================================================
# ACTION
# ==============================================================================

st.markdown("")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:

    if st.button(
        "CONTINUE TO PRIORITIZATION →",
        key="submit_decision_v3",
        use_container_width=True,
        disabled=not all_valid,
        type="primary",
    ):

        # ----------------------------------------------------------------------
        # Convert edited table into backend decision inputs
        # ----------------------------------------------------------------------

        decision_inputs: dict[str, dict[str, float]] = {}

        for _, row in edited_df.iterrows():

            dimension_id = str(row["dimension_id"])

            decision_inputs[dimension_id] = {}

            for criterion in DECISION_CRITERIA:

                value = row[criterion["id"]]

                decision_inputs[dimension_id][
                    criterion["id"]
                ] = float(value)

        # ----------------------------------------------------------------------
        # Run TPI / decision analysis
        # ----------------------------------------------------------------------

        try:

            result = run_decision_analysis(
                backend_results,
                decision_inputs,
            )

            # ------------------------------------------------------------------
            # Preserve user inputs
            # ------------------------------------------------------------------

            st.session_state[
                "decision_analysis_inputs"
            ] = decision_inputs

            # ------------------------------------------------------------------
            # Store backend outputs
            # ------------------------------------------------------------------

            st.session_state[
                "backend_results"
            ] = result["backend_results"]

            st.session_state[
                "roadmap_results"
            ] = result["roadmap_results"]

            st.session_state[
                "serialized_results"
            ] = result["serialized_results"]

            # ------------------------------------------------------------------
            # History
            # ------------------------------------------------------------------

            save_assessment_history(
                result["serialized_results"]
            )

            st.success(
                "Decision analysis completed successfully."
            )

            # ------------------------------------------------------------------
            # Continue to roadmap
            # ------------------------------------------------------------------

            st.switch_page(
                "pages/5_Roadmap.py"
            )

        except Exception as exc:

            st.error(
                f"Decision analysis failed: {exc}"
            )


# ==============================================================================
# FOOTER
# ==============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {
            "label": "JESA",
            "url": "https://www.jesagroup.com/",
        },
        {
            "label": "ENSAM Casablanca",
            "url": "https://ensam-casa.ma/",
        },
    ],
    align="center",
    compact=False,
    show_divider=True,
)