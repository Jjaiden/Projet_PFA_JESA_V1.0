"""Session-scoped assessment history for JESA DMAT."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import streamlit as st


_HISTORY_KEY = "assessment_history"


def _history_store() -> dict[str, dict[str, Any]]:
    """Return the current browser session's assessment history store."""
    history = st.session_state.get(_HISTORY_KEY)
    if not isinstance(history, dict):
        history = {}
        st.session_state[_HISTORY_KEY] = history
    return history


def save_assessment_history(payload: Mapping[str, Any]) -> None:
    """Save an assessment only in the current Streamlit session."""
    assessment_id = str(payload.get("assessment_id") or "")
    if not assessment_id:
        raise ValueError("assessment_id is required for history persistence.")

    _history_store()[assessment_id] = dict(payload)


def list_assessment_history() -> list[dict[str, Any]]:
    """List assessments saved by the current Streamlit session."""
    records: list[dict[str, Any]] = []

    for payload in _history_store().values():
        metadata = payload.get("metadata", {}) or {}
        aggregation = payload.get("aggregation", {}) or {}
        dmi_payload = aggregation.get("dmi") or {}

        records.append(
            {
                "created_at": payload.get("created_at") or _created_at(payload),
                "updated_at": payload.get("updated_at") or _created_at(payload),
                "assessment_name": metadata.get("assessment_name")
                or payload.get("assessment_id"),
                "site_name": metadata.get("site_name") or metadata.get("plant"),
                "source_filename": metadata.get("source_filename"),
                "dmi": dmi_payload.get("score"),
                "maturity_level": dmi_payload.get("level_name"),
                "status": _status(payload),
                "assessment_id": payload.get("assessment_id"),
            }
        )

    records.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return records


def load_assessment_history(assessment_id: str) -> dict[str, Any] | None:
    """Load an assessment saved by the current Streamlit session."""
    payload = _history_store().get(str(assessment_id))
    return dict(payload) if payload is not None else None


def _created_at(payload: Mapping[str, Any]) -> str:
    """Provide a stable display timestamp for session-scoped history."""
    metadata = payload.get("metadata", {}) or {}
    value = metadata.get("assessment_date")
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat()


def _status(payload: Mapping[str, Any]) -> str:
    if payload.get("roadmap"):
        return "Roadmap ready"
    if payload.get("tpi"):
        return "Decision analyzed"
    return "Assessment processed"
