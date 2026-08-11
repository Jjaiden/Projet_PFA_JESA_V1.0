# pages/2_New_Assessment.py
"""
New Assessment page for JESA DMAT – Digital Maturity Assessment Tool.
"""

from __future__ import annotations

import re
from datetime import date

import streamlit as st

from components import render_footer, render_header
from utils.assessment_service import (
    AssessmentProcessingError,
    process_uploaded_assessment,
    save_uploaded_workbook,
)
from utils.history_store import save_assessment_history

# ------------------------------------------------------------------------------
# PAGE SPECIFIC CSS (to be added to main.css)
# ------------------------------------------------------------------------------
# Add the following classes to assets/styles/main.css:
#
# .st-key-start_assessment_button button {
#     background: var(--dmat-primary);
#     color: #ffffff;
#     border: none;
#     border-radius: var(--dmat-radius-sm);
#     font-size: 1.125rem;
#     font-weight: 700;
#     padding: 0.75rem 2rem;
#     box-shadow: var(--dmat-shadow-md);
#     transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
#     letter-spacing: 0.02em;
# }
# .st-key-start_assessment_button button:hover {
#     background: var(--dmat-primary-hover);
#     color: #ffffff;
#     box-shadow: var(--dmat-shadow-lg);
#     transform: translateY(-2px);
# }
# .st-key-start_assessment_button button:active {
#     transform: translateY(0);
#     box-shadow: var(--dmat-shadow-sm);
# }


# ------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------

def _validate_email(email: str) -> bool:
    """Basic email format validation."""
    if not email:
        return True

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


# ------------------------------------------------------------------------------
# PAGE CONTENT
# ------------------------------------------------------------------------------

# Page header
render_header(
    title="New Assessment",
    subtitle="Define, upload, and launch a new digital maturity assessment.",
    align="center",
    compact=False,
)

# ------------------------------------------------------------------------------
# 01 — Assessment Identity
# ------------------------------------------------------------------------------

st.markdown("### 01 — Assessment Identity")

# Use a two‑column layout for identity fields
col1, col2 = st.columns(2)

with col1:
    assessment_name = st.text_input(
        "Assessment Name / Reference",
        placeholder="e.g. JESA Plant Digital Maturity Assessment",
        key="assessment_name",
    )
    company = st.text_input(
        "Company / Business Unit",
        placeholder="e.g. JESA",
        key="company",
    )
    assessor_name = st.text_input(
        "Assessor Name",
        placeholder="e.g. John Doe",
        key="assessor_name",
    )
    contact_email = st.text_input(
        "Contact / Email",
        placeholder="e.g. john.doe@example.com",
        key="contact_email",
    )

with col2:
    plant = st.text_input(
        "Industrial Site / Plant",
        placeholder="e.g. Jorf Lasfar Plant",
        key="plant",
    )
    assessment_date = st.date_input(
        "Assessment Date",
        value=date.today(),
        key="assessment_date",
    )
    assessor_role = st.text_input(
        "Assessor Role",
        placeholder="e.g. Digital Transformation Engineer",
        key="assessor_role",
    )

# ------------------------------------------------------------------------------
# 02 — Assessment Data
# ------------------------------------------------------------------------------

st.markdown("### 02 — Assessment Data")

# File uploader
uploaded_file = st.file_uploader(
    "Upload Assessment Grid",
    type=["xlsx", "xls"],
    help="Upload the Excel file containing the assessment questionnaire.",
    key="assessment_file",
)

if uploaded_file is not None:
    st.success(f"✓ Ready to process: `{uploaded_file.name}` ({uploaded_file.size} bytes)")
else:
    st.info("No assessment file selected. Use the official assessment template to ensure compatibility.")

# ------------------------------------------------------------------------------
# 03 — Review & Launch
# ------------------------------------------------------------------------------

st.markdown("### 03 — Review & Launch")

# Build a summary dictionary for display
summary_data = {
    "Assessment": assessment_name or "—",
    "Site": plant or "—",
    "Company": company or "—",
    "Date": assessment_date.strftime("%Y-%m-%d") if assessment_date else "—",
    "Assessor": assessor_name or "—",
    "Role": assessor_role or "—",
    "Assessment File": uploaded_file.name if uploaded_file else "—",
}

# Display summary in a two‑column layout
col_sum1, col_sum2 = st.columns(2)

with col_sum1:
    st.markdown(f"**Assessment**<br>{summary_data['Assessment']}", unsafe_allow_html=True)
    st.markdown(f"**Site**<br>{summary_data['Site']}", unsafe_allow_html=True)
    st.markdown(f"**Company**<br>{summary_data['Company']}", unsafe_allow_html=True)
    st.markdown(f"**Date**<br>{summary_data['Date']}", unsafe_allow_html=True)

with col_sum2:
    st.markdown(f"**Assessor**<br>{summary_data['Assessor']}", unsafe_allow_html=True)
    st.markdown(f"**Role**<br>{summary_data['Role']}", unsafe_allow_html=True)
    st.markdown(f"**Assessment File**<br>{summary_data['Assessment File']}", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MAIN CTA
# ------------------------------------------------------------------------------

# Center the button
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    if st.button(
        "+ START ASSESSMENT →",
        key="start_assessment_button",
        use_container_width=True,
    ):
        # ---- Validation ----
        errors = []

        if not assessment_name.strip():
            errors.append("Assessment Name is required.")
        if not plant.strip():
            errors.append("Industrial Site / Plant is required.")
        if not company.strip():
            errors.append("Company / Business Unit is required.")
        if not assessor_name.strip():
            errors.append("Assessor Name is required.")
        if not assessor_role.strip():
            errors.append("Assessor Role is required.")
        if uploaded_file is None:
            errors.append("Please upload the assessment grid before starting.")
        if contact_email and not _validate_email(contact_email):
            errors.append("Please enter a valid email address (or leave it empty).")

        if errors:
            for err in errors:
                st.error(err)
        else:
            metadata = {
                "assessment_name": assessment_name,
                "plant": plant,
                "company": company,
                "assessment_date": assessment_date.isoformat(),
                "assessor_name": assessor_name,
                "assessor_role": assessor_role,
                "contact_email": contact_email or None,
            }

            try:
                with st.spinner("Validating and processing the assessment workbook..."):
                    workbook_path = save_uploaded_workbook(uploaded_file)
                    result = process_uploaded_assessment(
                        workbook_path,
                        metadata,
                        uploaded_file.name,
                    )
                    st.session_state["assessment_id"] = result["assessment_id"]
                    st.session_state["new_assessment_data"] = {
                        "metadata": metadata,
                        "source_filename": uploaded_file.name,
                    }
                    st.session_state["backend_results"] = result["backend_results"]
                    st.session_state["assessment_results"] = result["backend_results"]["aggregation"]
                    st.session_state["dashboard_data"] = result["dashboard_data"]
                    st.session_state["roadmap_results"] = result["roadmap_results"]
                    st.session_state["serialized_results"] = result["serialized_results"]
                    save_assessment_history(result["serialized_results"])

                st.success("Assessment processed successfully.")
                if result["validation_warnings"]:
                    with st.expander("Validation warnings", expanded=False):
                        for warning in result["validation_warnings"][:10]:
                            st.warning(warning)
                st.switch_page("pages/3_Dashboard.py")
            except AssessmentProcessingError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Assessment processing failed: {exc}")

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
