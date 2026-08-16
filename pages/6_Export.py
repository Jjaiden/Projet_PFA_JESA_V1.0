# pages/6_Export.py
"""
Export page for JESA DMAT.

Generates:
- PDF Score Summary
- PDF Full Report
- Excel Workbook
- JSON Report
- Complete report bundle
"""

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

import streamlit as st

from components import render_footer, render_header
from config import settings
from utils.assessment_service import export_selected_assessment


# =============================================================================
# EXCEL LOGO COMPATIBILITY
# =============================================================================


def _ensure_excel_logo_names() -> None:
    """Expose the committed logo files under the names used by the Excel exporter."""
    logo_dir = Path(settings.frontend.LOGO_DIR)
    aliases = {
        "logo_jesa.png": "jesa_logo.png",
        "logo_ensam.png": "ensam_logo.png",
    }

    for source_name, alias_name in aliases.items():
        source = logo_dir / source_name
        alias = logo_dir / alias_name
        if source.is_file() and not alias.exists():
            try:
                shutil.copyfile(source, alias)
            except OSError:
                # The Excel exporter will simply omit the logo if the runtime
                # filesystem cannot create the compatibility alias.
                pass


# =============================================================================
# EXPORT BUTTON STYLE
# =============================================================================

st.markdown(
    """
    <style>
    /* Main export buttons */
    div.stButton > button,
    div[data-testid="stDownloadButton"] > button {
        background-color: #007A4D !important;
        color: white !important;
        border: 1px solid #007A4D !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    div.stButton > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #00643F !important;
        color: white !important;
        border-color: #00643F !important;
    }

    div.stButton > button:focus,
    div[data-testid="stDownloadButton"] > button:focus {
        color: white !important;
        border-color: #007A4D !important;
        box-shadow: 0 0 0 2px rgba(0, 122, 77, 0.20) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# HEADER
# =============================================================================

render_header(
    title="EXPORT",
    subtitle="Generate and download the complete assessment report.",
    align="center",
    compact=False,
)


# =============================================================================
# LOAD CURRENT ASSESSMENT
# =============================================================================

backend_results = st.session_state.get("backend_results")

if not backend_results:
    st.warning(
        "No assessment is currently loaded. "
        "Start a new assessment or open one from History first."
    )
    st.stop()


assessment_id = str(
    backend_results.get("assessment_id")
    or "assessment"
)

metadata = (
    backend_results.get("metadata")
    or {}
)

summary = (
    backend_results.get("summary")
    or {}
)


# =============================================================================
# ASSESSMENT SUMMARY
# =============================================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Assessment",
        metadata.get(
            "assessment_name"
        )
        or assessment_id,
    )

with col2:
    dmi = summary.get("dmi_score")

    if dmi is not None:
        st.metric(
            "DMI",
            f"{float(dmi):.1f}%",
        )
    else:
        st.metric(
            "DMI",
            "N/A",
        )

with col3:
    st.metric(
        "Maturity",
        summary.get(
            "dmi_level_name"
        )
        or "N/A",
    )


# =============================================================================
# EXPORT FORMAT SELECTION
# =============================================================================

st.markdown("### Select files to export")

# Three specific export options
col_format1, col_format2, col_format3 = st.columns(3)

with col_format1:
    export_pdf_score = st.checkbox(
        "📊 Score Summary",
        value=True,
        help="2-page PDF score summary",
    )

with col_format2:
    export_pdf_full = st.checkbox(
        "📄 Full Report",
        value=True,
        help="Complete PDF report",
    )

with col_format3:
    export_excel = st.checkbox(
        "📈 Excel Workbook",
        value=True,
        help="Full Excel workbook",
    )

# Build formats list from checkboxes
formats = []
if export_pdf_score:
    formats.append("pdf_score")
if export_pdf_full:
    formats.append("pdf_full")
if export_excel:
    formats.append("excel")


# =============================================================================
# GENERATE EXPORTS
# =============================================================================

if st.button(
    "GENERATE EXPORT",
    use_container_width=True,
    disabled=not formats,
):

    try:

        # -------------------------------------------------------------
        # Generate selected files
        # -------------------------------------------------------------

        if "excel" in formats:
            _ensure_excel_logo_names()

        export_paths = export_selected_assessment(
            backend_results,
            formats,
        )

        # The export service keeps successful files in its result mapping.
        # Compare that mapping with the requested formats so partial failures
        # are visible instead of being reported as generic success.
        succeeded_formats = [fmt for fmt in formats if fmt in export_paths]
        failed_formats = [fmt for fmt in formats if fmt not in export_paths]

        # -------------------------------------------------------------
        # Store generated files in session state
        # -------------------------------------------------------------

        st.session_state[
            "latest_export_paths"
        ] = {
            key: str(path)
            for key, path in export_paths.items()
            if path is not None
        }

        # -------------------------------------------------------------
        # Reset previous report bundle
        # -------------------------------------------------------------

        st.session_state.pop(
            "latest_report_path",
            None,
        )

        # -------------------------------------------------------------
        # Create complete ZIP report from successful exports only
        # -------------------------------------------------------------

        valid_paths = []

        for path in export_paths.values():

            if path is None:
                continue

            path = Path(path)

            if path.exists() and path.is_file():
                valid_paths.append(path)

        if valid_paths:

            output_dir = (
                valid_paths[0].parent
            )

            report_path = (
                output_dir
                / f"JESA_DMAT_Report_{assessment_id}.zip"
            )

            with zipfile.ZipFile(
                report_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:

                for path in valid_paths:

                    archive.write(
                        path,
                        arcname=path.name,
                    )

            st.session_state[
                "latest_report_path"
            ] = str(report_path)

        labels = {
            "pdf_score": "PDF Score Summary",
            "pdf_full": "PDF Full Report",
            "excel": "Excel Workbook",
        }

        if succeeded_formats and not failed_formats:
            st.success("All requested exports were generated successfully.")
        elif succeeded_formats:
            succeeded_text = ", ".join(labels.get(fmt, fmt) for fmt in succeeded_formats)
            failed_text = ", ".join(labels.get(fmt, fmt) for fmt in failed_formats)
            st.warning(
                f"Partial export result — succeeded: {succeeded_text}; "
                f"failed: {failed_text}."
            )
        else:
            failed_text = ", ".join(labels.get(fmt, fmt) for fmt in failed_formats)
            st.error(f"All requested exports failed: {failed_text}.")

    except Exception as exc:

        st.error(
            f"Export generation failed: {exc}"
        )


# =============================================================================
# DOWNLOAD GENERATED FILES
# =============================================================================

export_paths = (
    st.session_state.get(
        "latest_export_paths",
        {},
    )
)


if export_paths:

    st.markdown(
        "### Download individual files"
    )

    mime_types = {
        "pdf_score": "application/pdf",
        "pdf_full": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
    }

    for format_name, path_string in export_paths.items():

        path = Path(path_string)

        if not path.exists():

            st.warning(
                f"{format_name.upper()} file is no longer available."
            )

            continue

        # Use the actual file extension from the path
        file_extension = path.suffix.lstrip(".")
        
        # Map format name to display label
        label_map = {
            "pdf_score": "Score Summary",
            "pdf_full": "Full Report",
            "excel": "Excel Workbook",
        }
        display_name = label_map.get(format_name, format_name.replace('_', ' ').title())

        with open(
            path,
            "rb",
        ) as file:

            st.download_button(
                label=(f"DOWNLOAD {display_name}"),
                data=file.read(),
                file_name=(f"JESA_DMAT_{assessment_id}.{file_extension}"),
                mime=mime_types.get(
                    format_name,
                    "application/octet-stream",
                ),
                key=f"download_{format_name}",
                use_container_width=True,
            )


# =============================================================================
# COMPLETE REPORT DOWNLOAD
# =============================================================================

report_path_string = (
    st.session_state.get(
        "latest_report_path"
    )
)


if report_path_string:

    report_path = Path(
        report_path_string
    )

    if report_path.exists():

        st.markdown(
            "### Complete report"
        )

        st.caption(
            "Download the complete JESA DMAT assessment package "
            "containing all generated report files."
        )

        with open(
            report_path,
            "rb",
        ) as file:

            st.download_button(
                label="DOWNLOAD REPORT",
                data=file.read(),
                file_name=report_path.name,
                mime="application/zip",
                key="download_complete_report",
                use_container_width=True,
            )

    else:

        st.warning(
            "Report file was generated previously "
            "but is no longer available."
        )


# =============================================================================
# FOOTER
# =============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline=(
        "Internship Project · "
        "Digital Transformation & Industry 5.0"
    ),
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