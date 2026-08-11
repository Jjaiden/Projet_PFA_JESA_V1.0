# pages/6_History.py
"""Persistent assessment history for JESA DMAT."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import render_footer, render_header
from utils.assessment_service import (
    build_dashboard_data,
    build_roadmap_view_data,
    deserialize_backend_results,
)
from utils.history_store import list_assessment_history, load_assessment_history


render_header(
    title="HISTORY",
    subtitle="Open previous digital maturity assessments.",
    align="center",
    compact=False,
)

records = list_assessment_history()

if not records:
    st.info("No historical assessment has been saved yet.")
else:
    table = pd.DataFrame(records)
    st.dataframe(
        table[
            [
                "created_at",
                "assessment_name",
                "site_name",
                "dmi",
                "maturity_level",
                "status",
                "assessment_id",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    labels = {
        f"{item['created_at']} | {item.get('site_name') or item.get('assessment_name')} | {item['assessment_id']}": item[
            "assessment_id"
        ]
        for item in records
    }
    selected_label = st.selectbox("Assessment", list(labels.keys()))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("OPEN SELECTED ASSESSMENT", use_container_width=True):
            payload = load_assessment_history(labels[selected_label])
            if payload is None:
                st.error("The selected assessment could not be found in history.")
            else:
                backend_results = deserialize_backend_results(payload)
                st.session_state["assessment_id"] = backend_results["assessment_id"]
                st.session_state["backend_results"] = backend_results
                st.session_state["serialized_results"] = payload
                st.session_state["assessment_results"] = backend_results["aggregation"]
                st.session_state["dashboard_data"] = build_dashboard_data(backend_results)
                st.session_state["roadmap_results"] = (
                    build_roadmap_view_data(backend_results)
                    if backend_results.get("roadmap")
                    else None
                )
                st.success("Assessment restored successfully.")
                st.switch_page("pages/3_Dashboard.py")
    with col2:
        if st.button("START NEW ASSESSMENT", use_container_width=True):
            for key in (
                "assessment_id",
                "new_assessment_data",
                "backend_results",
                "assessment_results",
                "dashboard_data",
                "roadmap_results",
                "serialized_results",
                "decision_analysis_inputs",
            ):
                st.session_state[key] = None
            st.switch_page("pages/2_New_Assessment.py")

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
