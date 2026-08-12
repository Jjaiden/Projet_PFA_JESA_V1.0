# pages/6_Export.py
"""Export the selected JESA DMAT assessment."""

from __future__ import annotations

import streamlit as st


from components import render_footer, render_header
from utils.assessment_service import export_selected_assessment


render_header(
    title="EXPORT",
    subtitle="Generate report files for the selected assessment.",
    align="center",
    compact=False,
)

backend_results = st.session_state.get("backend_results")

if not backend_results:
    st.warning("No assessment is currently loaded. Start a new assessment or open one from History first.")
    st.stop()

metadata = backend_results.get("metadata", {})
summary = backend_results.get("summary", {})

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Assessment", metadata.get("assessment_name") or backend_results.get("assessment_id"))
with col2:
    dmi = summary.get("dmi_score")
    st.metric("DMI", f"{dmi:.1f}%" if dmi is not None else "N/A")
with col3:
    st.metric("Maturity", summary.get("dmi_level_name") or "N/A")

formats = st.multiselect(
    "Export formats",
    options=["pdf", "excel", "json"],
    default=["pdf", "excel"],
)

if st.button("GENERATE EXPORT", use_container_width=True, disabled=not formats):
    try:
        export_paths = export_selected_assessment(backend_results, formats)
        st.session_state["latest_export_paths"] = {
            key: str(path) for key, path in export_paths.items()
        }
        st.success("Export generated successfully.")
    except Exception as exc:
        st.error(f"Export generation failed: {exc}")

export_paths = st.session_state.get("latest_export_paths", {})
if export_paths:
    st.markdown("### Download")
    for format_name, path in export_paths.items():
        mime = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json",
        }.get(format_name, "application/octet-stream")
        suffix = "xlsx" if format_name == "excel" else format_name
        with open(path, "rb") as file:
            st.download_button(
                label=f"DOWNLOAD {format_name.upper()}",
                data=file.read(),
                file_name=f"JESA_DMAT_{backend_results.get('assessment_id')}.{suffix}",
                mime=mime,
                key=f"download_{format_name}",
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
