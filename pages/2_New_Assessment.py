# pages/2_New_Assessment.py
"""
New Assessment page for JESA DMAT – Digital Maturity Assessment Tool.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import streamlit as st

from components import render_footer, render_header
from utils.assessment_service import (
    AssessmentProcessingError,
    process_uploaded_assessment,
    save_uploaded_workbook,
)
from utils.history_store import save_assessment_history


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="New Assessment",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# PATHS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ASSESSMENT_TEMPLATE = (
    BASE_DIR
    / "assets"
    / "templates"
    / "assessment_template.xlsx"
)


# ==============================================================================
# HELPERS
# ==============================================================================


def _validate_email(email: str) -> bool:
    """Basic email format validation."""
    if not email:
        return True
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def _required_label(label: str) -> str:
    """Render a consistent required-field label."""
    return f"""
        <div class="dmat-field-label">
            {label}
            <span class="dmat-required">*</span>
        </div>
    """


def _optional_label(label: str) -> str:
    """Render a consistent optional-field label."""
    return f"""
        <div class="dmat-field-label">
            {label}
            <span class="dmat-optional">Optional</span>
        </div>
    """


# ==============================================================================
# PAGE STYLES (injected via st.markdown)
# ==============================================================================

# Main CSS injection
st.markdown("""
<style>
    /* ==============================================================
       FIELD LABELS
       ============================================================== */
    .dmat-field-label {
        margin-top: 0.15rem;
        margin-bottom: 0.32rem;
        color: #173f69;
        font-size: 0.95rem;
        font-weight: 500;
        line-height: 1.35;
    }
    .dmat-required {
        color: #d14343;
        font-size: 0.95rem;
        font-weight: 800;
        margin-left: 0.18rem;
    }
    .dmat-optional {
        display: inline-block;
        margin-left: 0.45rem;
        padding: 0.08rem 0.38rem;
        border-radius: 999px;
        background: rgba(23, 105, 170, 0.07);
        color: #71869a;
        font-size: 0.60rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        vertical-align: middle;
    }

    /* ==============================================================
       SECTION HEADINGS
       ============================================================== */
    .dmat-section-title {
        margin-top: 1.45rem;
        margin-bottom: 0.95rem;
        color: #102f55;
        font-size: 1.32rem;
        font-weight: 750;
        letter-spacing: 0.015em;
    }
    .dmat-section-title::after {
        content: "";
        display: block;
        width: 42px;
        height: 3px;
        margin-top: 0.35rem;
        border-radius: 999px;
        background: linear-gradient(90deg, #1769aa, #0f9d94);
    }

    /* ==============================================================
       TEMPLATE DOWNLOAD AREA
       ============================================================== */
    .dmat-template-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.25rem;
        margin: 0.15rem 0 0.85rem;
        padding: 0.90rem 1.05rem;
        border: 1px solid rgba(23,105,170,0.12);
        border-radius: 13px;
        background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(241,247,251,0.82));
        box-shadow: 0 6px 18px rgba(31,65,96,0.045);
    }
    .dmat-template-content {
        flex: 1;
    }
    .dmat-template-title {
        color: #173f69;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }
    .dmat-template-description {
        color: #71869a;
        font-size: 0.68rem;
        line-height: 1.45;
    }

    /* ==============================================================
       DOWNLOAD TEMPLATE BUTTON
       ============================================================== */
    .st-key-download_template_button button {
        min-height: 40px !important;
        padding: 0.55rem 1rem !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: var(--dmat-font) !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18) !important;
    }
    .st-key-download_template_button button:hover {
        background: #1D4ED8 !important;
    }
    .st-key-download_template_button button span,
    .st-key-download_template_button button p {
        color: #FFFFFF !important;
    }

    /* ==============================================================
       UPLOAD ASSESSMENT FILE – NO BUTTONS, CLICK DROPZONE
       ============================================================== */
    [data-testid="stFileUploader"] {
        margin-top: 0.10rem !important;
    }
    /* Hide ALL buttons inside the file uploader */
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploader"] button[data-testid="baseButton-secondary"],
    [data-testid="stFileUploader"] button[kind="secondary"],
    [data-testid="stFileUploader"] [data-testid="baseButton-secondary"] {
        display: none !important;
    }
    /* Style the dropzone as a clickable area */
    [data-testid="stFileUploaderDropzone"] {
        min-height: 120px !important;
        background: #FAFCFF !important;
        border: 2px dashed rgba(23, 63, 105, 0.20) !important;
        border-radius: 12px !important;
        padding: 2rem 1rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        transition: border-color 0.2s ease, background 0.2s ease !important;
        cursor: pointer !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #2563EB !important;
        background: #EFF6FF !important;
    }
    /* Add icon and text inside the dropzone */
    [data-testid="stFileUploaderDropzone"]::before {
        content: "📤" !important;
        display: block !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Click here or drag & drop your assessment file" !important;
        display: block !important;
        color: #64748B !important;
        font-size: 0.85rem !important;
        font-family: var(--dmat-font) !important;
        text-align: center !important;
        letter-spacing: 0.02em !important;
    }
    /* Hide any file info containers that appear after upload */
    [data-testid="stFileUploader"] > div:last-child,
    [data-testid="stFileUploader"] .st-emotion-cache-1j2m9f4,
    [data-testid="stFileUploader"] .st-emotion-cache-1wivap2,
    [data-testid="stFileUploader"] .st-emotion-cache-1xarl3l,
    [data-testid="stFileUploader"] .st-emotion-cache-1miwxuw,
    [data-testid="stFileUploader"] .st-emotion-cache-1r6slb0 {
        display: none !important;
    }

    /* ==============================================================
       FILE INFORMATION
       ============================================================== */
    .dmat-upload-help {
        margin-top: 0.35rem;
        color: #7a8c9d;
        font-size: 0.65rem;
        line-height: 1.45;
    }

    /* ==============================================================
       REVIEW SUMMARY
       ============================================================== */
    .dmat-summary-card {
        padding: 0.80rem 1rem;
        border: 1px solid rgba(23,105,170,0.10);
        border-radius: 11px;
        background: rgba(255,255,255,0.68);
    }
    .dmat-summary-label {
        color: #6d8194;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .dmat-summary-value {
        color: #173f69;
        font-size: 0.80rem;
        font-weight: 650;
    }

    /* ==============================================================
       MAIN CTA
       ============================================================== */
    .st-key-start_assessment_button button {
        min-height: 46px !important;
        border: none !important;
        border-radius: 10px !important;
        background: linear-gradient(100deg, #1557a6 0%, #176fc1 48%, #168f91 100%) !important;
        color: #ffffff !important;
        font-size: 0.92rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.025em !important;
        box-shadow: 0 7px 20px rgba(22,91,148,0.20) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .st-key-start_assessment_button button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 11px 26px rgba(22,91,148,0.26) !important;
    }

    /* ==============================================================
       INFO / SUCCESS / ERROR
       ============================================================== */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# PAGE HEADER
# ==============================================================================

render_header(
    title="New Assessment",
    subtitle="Define, upload, and launch a new digital maturity assessment.",
    align="center",
    compact=False,
)


# ==============================================================================
# 1 — ASSESSMENT IDENTITY
# ==============================================================================

st.markdown('<div class="dmat-section-title">Assessment Identity</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TWO-COLUMN IDENTITY FORM
# ------------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    # Assessment Name
    st.markdown(_required_label("Assessment Name / Reference"), unsafe_allow_html=True)
    assessment_name = st.text_input(
        "Assessment Name / Reference",
        placeholder="e.g. JESA Plant Digital Maturity Assessment",
        key="assessment_name",
        label_visibility="collapsed",
    )

    # Company
    st.markdown(_required_label("Company / Business Unit"), unsafe_allow_html=True)
    company = st.text_input(
        "Company / Business Unit",
        placeholder="e.g. JESA",
        key="company",
        label_visibility="collapsed",
    )

    # Assessor
    st.markdown(_required_label("Assessor Name"), unsafe_allow_html=True)
    assessor_name = st.text_input(
        "Assessor Name",
        placeholder="e.g. John Doe",
        key="assessor_name",
        label_visibility="collapsed",
    )

    # Contact
    st.markdown(_optional_label("Contact / Email"), unsafe_allow_html=True)
    contact_email = st.text_input(
        "Contact / Email",
        placeholder="e.g. john.doe@example.com",
        key="contact_email",
        label_visibility="collapsed",
    )

with col2:
    # Industrial Site
    st.markdown(_required_label("Industrial Site / Plant"), unsafe_allow_html=True)
    plant = st.text_input(
        "Industrial Site / Plant",
        placeholder="e.g. Jorf Lasfar Plant",
        key="plant",
        label_visibility="collapsed",
    )

    # Assessment Date
    st.markdown(_required_label("Assessment Date"), unsafe_allow_html=True)
    assessment_date = st.date_input(
        "Assessment Date",
        value=date.today(),
        key="assessment_date",
        label_visibility="collapsed",
    )

    # Assessor Role
    st.markdown(_required_label("Assessor Role"), unsafe_allow_html=True)
    assessor_role = st.text_input(
        "Assessor Role",
        placeholder="e.g. Digital Transformation Engineer",
        key="assessor_role",
        label_visibility="collapsed",
    )


# ==============================================================================
# 2 — ASSESSMENT DATA
# ==============================================================================

st.markdown('<div class="dmat-section-title">Assessment Data</div>', unsafe_allow_html=True)


# ==============================================================================
# OFFICIAL TEMPLATE DOWNLOAD
# ==============================================================================

st.markdown("""
<div class="dmat-template-card">
    <div class="dmat-template-content">
        <div class="dmat-template-title">Assessment Template</div>
        <div class="dmat-template-description">
            Download the official Excel template, complete the assessment
            questionnaire, then upload the completed file below.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# DOWNLOAD TEMPLATE
# ------------------------------------------------------------------------------

template_exists = ASSESSMENT_TEMPLATE.exists()

if template_exists:
    template_data = ASSESSMENT_TEMPLATE.read_bytes()
    st.download_button(
        "Download Assessment Template",
        data=template_data,
        file_name="JESA_DMAT_Assessment_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_template_button",
        type="primary",
        width="content",
    )
else:
    st.warning(
        "The official assessment template is not available. "
        "Please place 'assessment_template.xlsx' in 'assets/templates/'."
    )


# ==============================================================================
# UPLOAD ASSESSMENT GRID
# ==============================================================================

uploaded_file = st.file_uploader(
    "Upload Assessment Grid",
    type=["xlsx"],
    help="Upload the completed official Excel assessment template.",
    key="assessment_file",
)

st.markdown("""
<div class="dmat-upload-help">
    Excel workbook (.xlsx) · Maximum 50 MB per file ·
    Use the official assessment template for compatibility.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# UPLOAD STATUS
# ==============================================================================

if uploaded_file is not None:
    st.success(f"✓ Ready to process: `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")
else:
    st.info("No assessment file selected. Download the official template above, complete it, and upload it here.")


# ==============================================================================
# 3 — REVIEW & LAUNCH
# ==============================================================================

st.markdown('<div class="dmat-section-title">Review & Launch</div>', unsafe_allow_html=True)


# ==============================================================================
# SUMMARY DATA
# ==============================================================================

summary_data = {
    "Assessment": assessment_name.strip() if assessment_name.strip() else "—",
    "Site": plant.strip() if plant.strip() else "—",
    "Company": company.strip() if company.strip() else "—",
    "Date": assessment_date.strftime("%Y-%m-%d") if assessment_date else "—",
    "Assessor": assessor_name.strip() if assessor_name.strip() else "—",
    "Role": assessor_role.strip() if assessor_role.strip() else "—",
    "Assessment File": uploaded_file.name if uploaded_file else "—",
}


# ==============================================================================
# SUMMARY DISPLAY
# ==============================================================================

col_sum1, col_sum2 = st.columns(2)

with col_sum1:
    st.markdown(f"""
    <div class="dmat-summary-card">
        <div class="dmat-summary-label">Assessment</div>
        <div class="dmat-summary-value">{summary_data['Assessment']}</div>
        <br>
        <div class="dmat-summary-label">Site</div>
        <div class="dmat-summary-value">{summary_data['Site']}</div>
        <br>
        <div class="dmat-summary-label">Company</div>
        <div class="dmat-summary-value">{summary_data['Company']}</div>
        <br>
        <div class="dmat-summary-label">Date</div>
        <div class="dmat-summary-value">{summary_data['Date']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_sum2:
    st.markdown(f"""
    <div class="dmat-summary-card">
        <div class="dmat-summary-label">Assessor</div>
        <div class="dmat-summary-value">{summary_data['Assessor']}</div>
        <br>
        <div class="dmat-summary-label">Role</div>
        <div class="dmat-summary-value">{summary_data['Role']}</div>
        <br>
        <div class="dmat-summary-label">Assessment File</div>
        <div class="dmat-summary-value">{summary_data['Assessment File']}</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# MAIN CTA
# ==============================================================================

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    if st.button(
        "START ASSESSMENT  →",
        key="start_assessment_button",
        use_container_width=True,
        type="primary",
    ):
        # Validation
        errors = []
        if not assessment_name.strip():
            errors.append("Assessment Name / Reference is required.")
        if not plant.strip():
            errors.append("Industrial Site / Plant is required.")
        if not company.strip():
            errors.append("Company / Business Unit is required.")
        if not assessor_name.strip():
            errors.append("Assessor Name is required.")
        if not assessor_role.strip():
            errors.append("Assessor Role is required.")
        if uploaded_file is None:
            errors.append("Please upload the completed assessment grid.")
        if contact_email and not _validate_email(contact_email):
            errors.append("Please enter a valid email address (or leave it empty).")

        if errors:
            for err in errors:
                st.error(err)
        else:
            metadata = {
                "assessment_name": assessment_name.strip(),
                "plant": plant.strip(),
                "company": company.strip(),
                "assessment_date": assessment_date.isoformat() if assessment_date else "",
                "assessor_name": assessor_name.strip(),
                "assessor_role": assessor_role.strip(),
                "contact_email": contact_email.strip() if contact_email else None,
                "evaluator": assessor_name.strip(),
                "evaluator_name": assessor_name.strip(),
                "evaluator_function": assessor_role.strip(),
                "site_name": plant.strip(),
                "site_id": plant.strip(),
            }

            try:
                with st.spinner("Validating and processing the assessment workbook..."):
                    workbook_path = save_uploaded_workbook(uploaded_file)
                    result = process_uploaded_assessment(workbook_path, metadata, uploaded_file.name)

                    # Session state
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

                st.switch_page("pages/3_Dashboard.py")

            except AssessmentProcessingError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Assessment processing failed: {exc}")


# ==============================================================================
# FOOTER
# ==============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {"label": "JESA", "url": "https://www.jesagroup.com/"},
        {"label": "ENSAM Casablanca", "url": "https://ensam-casa.ma/"},
    ],
    align="center",
    compact=False,
    show_divider=True,
)