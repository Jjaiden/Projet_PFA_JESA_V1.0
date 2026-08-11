"""SQLite persistence for JESA DMAT assessment history."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from config import settings


DB_PATH = settings.DATA_DIR / "runtime" / "assessment_history.sqlite3"


def init_history_store(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                assessment_name TEXT,
                site_name TEXT,
                source_filename TEXT,
                dmi REAL,
                maturity_level TEXT,
                status TEXT,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_assessment_history(payload: Mapping[str, Any], db_path: Path = DB_PATH) -> None:
    init_history_store(db_path)
    assessment_id = str(payload.get("assessment_id") or "")
    if not assessment_id:
        raise ValueError("assessment_id is required for history persistence.")

    metadata = payload.get("metadata", {})
    aggregation = payload.get("aggregation", {})
    dmi_payload = aggregation.get("dmi") or {}
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        existing = conn.execute(
            "SELECT created_at FROM assessments WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        created_at = existing[0] if existing else now
        conn.execute(
            """
            INSERT INTO assessments (
                assessment_id, created_at, updated_at, assessment_name,
                site_name, source_filename, dmi, maturity_level, status,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assessment_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                assessment_name = excluded.assessment_name,
                site_name = excluded.site_name,
                source_filename = excluded.source_filename,
                dmi = excluded.dmi,
                maturity_level = excluded.maturity_level,
                status = excluded.status,
                payload_json = excluded.payload_json
            """,
            (
                assessment_id,
                created_at,
                now,
                metadata.get("assessment_name") or assessment_id,
                metadata.get("site_name"),
                metadata.get("source_filename"),
                dmi_payload.get("score"),
                dmi_payload.get("level_name"),
                _status(payload),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()


def list_assessment_history(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    init_history_store(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT assessment_id, created_at, updated_at, assessment_name,
                   site_name, source_filename, dmi, maturity_level, status
            FROM assessments
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def load_assessment_history(assessment_id: str, db_path: Path = DB_PATH) -> dict[str, Any] | None:
    init_history_store(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT payload_json FROM assessments WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def _status(payload: Mapping[str, Any]) -> str:
    if payload.get("roadmap"):
        return "Roadmap ready"
    if payload.get("tpi"):
        return "Decision analyzed"
    return "Assessment processed"
