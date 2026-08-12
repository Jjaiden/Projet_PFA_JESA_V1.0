"""
report.py — Orchestrates the generation of the full assessment report.

It uses the dedicated exporters for PDF (score summary / full report) and Excel.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from config import settings
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase
from engines.decision.tpi import TPIResult

from exports.excel import ExcelExporter
from exports.pdf import export_score_summary, export_full_report

from utils.file_manager import build_output_path, ensure_directory

logger = settings.get_logger(__name__)

# ------------------------------------------------------------------------------
# Data structures (unchanged)
# ------------------------------------------------------------------------------
@dataclass
class ReportMetadata:
    report_id: str
    assessment_id: str
    site_name: str
    generated_at: str
    report_version: str = "1.0"
    generator: str = "JDMAF Backend"

@dataclass
class ExecutiveSummary:
    dmi_score: Optional[float]
    dmi_level: Optional[int]
    dmi_level_name: str
    top_strengths: List[tuple[str, float]]
    top_weaknesses: List[tuple[str, float]]
    critical_gaps: int
    priority_dimensions: int

@dataclass
class ReportData:
    metadata: ReportMetadata
    summary: ExecutiveSummary
    aggregation_results: Dict[str, Any]
    gap_results: Optional[List[GapResult]] = None
    tpi_results: Optional[List[TPIResult]] = None
    priority_results: Optional[List[PriorityResult]] = None
    roadmap: Optional[List[RoadmapPhase]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

# ------------------------------------------------------------------------------
# ReportGenerator
# ------------------------------------------------------------------------------
class ReportGenerator:
    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})
        self.excel_exporter = ExcelExporter(self.config)

    def generate_full_report(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_dir: Optional[Path] = None,
        assessment_id: Optional[str] = None,
        include_pdf_score: bool = True,
        include_pdf_full: bool = False,
        include_excel: bool = True,
        include_json: bool = True,
    ) -> Dict[str, Path]:
        """
        Generate selected report deliverables.

        Args:
            include_pdf_score: generate the 2‑page score summary
            include_pdf_full: generate the comprehensive full report
            include_excel: generate the Excel workbook
            include_json: generate the JSON data dump
        """
        if not isinstance(aggregation_results, dict):
            raise TypeError("aggregation_results must be a dictionary.")

        metadata = aggregation_results.get("metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}

        resolved_assessment_id = assessment_id or metadata.get("assessment_id", "UNKNOWN")
        site_name = metadata.get("site_name", "N/A")

        report_data = self._build_report_data(
            aggregation_results,
            gap_results,
            tpi_results,
            priority_results,
            roadmap,
            str(resolved_assessment_id),
            str(site_name),
        )

        outputs: Dict[str, Path] = {}

        if include_pdf_score:
            outputs["pdf_score"] = self._generate_pdf_score(report_data, output_dir)

        if include_pdf_full:
            outputs["pdf_full"] = self._generate_pdf_full(report_data, output_dir)

        if include_excel:
            outputs["excel"] = self._generate_excel(report_data, output_dir)

        if include_json:
            outputs["json"] = self._generate_json(report_data, output_dir)

        logger.info("Report generated: %s", ", ".join(f"{k}={v}" for k, v in outputs.items()))
        return outputs

    def _build_report_data(self, aggregation_results, gap_results, tpi_results, priority_results, roadmap, assessment_id, site_name):
        generated_at = datetime.now().isoformat()
        report_metadata = ReportMetadata(
            report_id=f"RPT-{assessment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            assessment_id=assessment_id,
            site_name=site_name,
            generated_at=generated_at,
        )

        summary = self._build_executive_summary(aggregation_results, gap_results, priority_results)

        dmi = aggregation_results.get("dmi")
        raw_data = {
            "dmi": self._serialize_object(dmi),
            "indicators": self._serialize_score_results(aggregation_results.get("indicators", {})),
            "subdimensions": self._serialize_score_results(aggregation_results.get("subdimensions", {})),
            "dimensions": self._serialize_score_results(aggregation_results.get("dimensions", {})),
            "pillars": self._serialize_score_results(aggregation_results.get("pillars", {})),
        }

        return ReportData(
            metadata=report_metadata,
            summary=summary,
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            raw_data=raw_data,
        )

    def _build_executive_summary(self, aggregation_results, gap_results, priority_results):
        dmi = aggregation_results.get("dmi")
        dimensions = aggregation_results.get("dimensions", {})
        dim_scores = []
        if isinstance(dimensions, Mapping):
            for dim_id, result in dimensions.items():
                if isinstance(result, ScoreResult) and result.score is not None:
                    dim_scores.append((str(dim_id), float(result.score)))
        dim_scores.sort(key=lambda x: x[1], reverse=True)
        top_strengths = dim_scores[:3]
        top_weaknesses = sorted(dim_scores, key=lambda x: x[1])[:3]

        critical_gaps = 0
        if gap_results:
            critical_gaps = sum(
                1 for gap in gap_results
                if self._normalize_priority(getattr(gap, "priority", None)) in {"Critical", "High"}
            )

        priority_dimensions = len(priority_results) if priority_results else 0

        dmi_score = None
        dmi_level = None
        dmi_level_name = ""
        if dmi is not None:
            if getattr(dmi, "score", None) is not None:
                dmi_score = float(dmi.score)
            if getattr(dmi, "level", None) is not None:
                dmi_level = int(dmi.level)
            dmi_level_name = str(getattr(dmi, "level_name", "") or "")

        return ExecutiveSummary(
            dmi_score=dmi_score,
            dmi_level=dmi_level,
            dmi_level_name=dmi_level_name,
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            critical_gaps=critical_gaps,
            priority_dimensions=priority_dimensions,
        )

    def _generate_pdf_score(self, report_data, output_dir):
        filename = f"JESA_DMAT_Score_Summary_{report_data.metadata.assessment_id}.pdf"
        output_path = self._resolve_output_path(filename, output_dir)
        return export_score_summary(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    def _generate_pdf_full(self, report_data, output_dir):
        filename = f"JESA_DMAT_Full_Report_{report_data.metadata.assessment_id}.pdf"
        output_path = self._resolve_output_path(filename, output_dir)
        return export_full_report(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    def _generate_excel(self, report_data, output_dir):
        filename = f"JESA_DMAT_Workbook_{report_data.metadata.assessment_id}.xlsx"
        output_path = self._resolve_output_path(filename, output_dir)
        return self.excel_exporter.export_assessment_results(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    def _generate_json(self, report_data, output_dir):
        filename = f"JESA_DMAT_Report_{report_data.metadata.assessment_id}.json"
        output_path = self._resolve_output_path(filename, output_dir)
        data = self._serialize_report_data(report_data)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info("JSON report generated: %s", output_path)
        return output_path

    def _resolve_output_path(self, filename, output_dir):
        if output_dir is not None:
            output_dir = Path(output_dir)
            ensure_directory(output_dir)
            return output_dir / filename
        return build_output_path(filename)

    # --- Serialization helpers (unchanged) ---
    def _serialize_report_data(self, report_data):
        return {
            "metadata": {
                "report_id": report_data.metadata.report_id,
                "assessment_id": report_data.metadata.assessment_id,
                "site_name": report_data.metadata.site_name,
                "generated_at": report_data.metadata.generated_at,
                "report_version": report_data.metadata.report_version,
                "generator": report_data.metadata.generator,
            },
            "summary": {
                "dmi_score": report_data.summary.dmi_score,
                "dmi_level": report_data.summary.dmi_level,
                "dmi_level_name": report_data.summary.dmi_level_name,
                "top_strengths": [list(item) for item in report_data.summary.top_strengths],
                "top_weaknesses": [list(item) for item in report_data.summary.top_weaknesses],
                "critical_gaps": report_data.summary.critical_gaps,
                "priority_dimensions": report_data.summary.priority_dimensions,
            },
            "aggregation": self._serialize_aggregation(report_data.aggregation_results),
            "decision": {
                "gaps": [self._serialize_object(gap) for gap in (report_data.gap_results or [])],
                "tpi": [self._serialize_object(tpi) for tpi in (report_data.tpi_results or [])],
                "priorities": [self._serialize_object(priority) for priority in (report_data.priority_results or [])],
                "roadmap": [self._serialize_object(phase) for phase in (report_data.roadmap or [])],
            },
            "raw_data": report_data.raw_data,
        }

    def _serialize_aggregation(self, results):
        dmi = results.get("dmi")
        return {
            "indicators": self._serialize_score_results(results.get("indicators", {})),
            "subdimensions": self._serialize_score_results(results.get("subdimensions", {})),
            "dimensions": self._serialize_score_results(results.get("dimensions", {})),
            "pillars": self._serialize_score_results(results.get("pillars", {})),
            "dmi": self._serialize_object(dmi) if dmi is not None else None,
            "metadata": self._make_json_safe(results.get("metadata", {})),
        }

    def _serialize_score_results(self, results):
        if not isinstance(results, Mapping):
            return {}
        serialized = {}
        for key, result in results.items():
            if isinstance(result, ScoreResult):
                serialized[str(key)] = result.to_dict()
            else:
                serialized[str(key)] = self._make_json_safe(result)
        return serialized

    def _serialize_object(self, obj):
        if obj is None:
            return None
        if hasattr(obj, "to_dict"):
            try:
                return self._make_json_safe(obj.to_dict())
            except Exception:
                pass
        if hasattr(obj, "__dataclass_fields__"):
            try:
                return self._make_json_safe(asdict(obj))
            except Exception:
                pass
        return self._make_json_safe(obj)

    def _make_json_safe(self, value):
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, Mapping):
            return {str(k): self._make_json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._make_json_safe(item) for item in value]
        if hasattr(value, "to_dict"):
            try:
                return self._make_json_safe(value.to_dict())
            except Exception:
                pass
        if hasattr(value, "__dataclass_fields__"):
            try:
                return self._make_json_safe(asdict(value))
            except Exception:
                pass
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    @staticmethod
    def _normalize_priority(priority):
        if priority is None:
            return ""
        mapping = {
            "critical": "Critical",
            "critique": "Critical",
            "high": "High",
            "haute": "High",
            "medium": "Medium",
            "moyenne": "Medium",
            "low": "Low",
            "faible": "Low",
            "very low": "Very Low",
            "très faible": "Very Low",
            "tres faible": "Very Low",
        }
        norm = str(priority).strip().lower()
        return mapping.get(norm, str(priority))

# ------------------------------------------------------------------------------
# Public utilities
# ------------------------------------------------------------------------------
def generate_report(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
    tpi_results: Optional[List[TPIResult]] = None,
    priority_results: Optional[List[PriorityResult]] = None,
    roadmap: Optional[List[RoadmapPhase]] = None,
    output_dir: Optional[Path] = None,
    assessment_id: Optional[str] = None,
    formats: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """
    Generate the report with requested formats.

    Supported format values:
        "pdf_score"    → 2‑page score summary
        "pdf_full"     → comprehensive full report
        "excel"        → Excel workbook
        "json"         → JSON data dump
        "pdf"          → alias for "pdf_score" (backward compatibility)
        "report"       → alias for "pdf_full" (backward compatibility)
    """
    if formats is None:
        formats = ["pdf_score", "excel", "json"]

    normalized = set()
    for fmt in formats:
        fmt = str(fmt).strip().lower()
        if fmt == "pdf":
            normalized.add("pdf_score")
        elif fmt == "report":
            normalized.add("pdf_full")
        else:
            normalized.add(fmt)

    generator = ReportGenerator()
    return generator.generate_full_report(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_dir=output_dir,
        assessment_id=assessment_id,
        include_pdf_score="pdf_score" in normalized,
        include_pdf_full="pdf_full" in normalized,
        include_excel="excel" in normalized,
        include_json="json" in normalized,
    )


def generate_executive_summary(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
    priority_results: Optional[List[PriorityResult]] = None,
) -> Dict[str, Any]:
    """Return a structured executive summary dictionary without creating files."""
    # Reuse the same logic as ReportGenerator._build_executive_summary
    generator = ReportGenerator()
    summary = generator._build_executive_summary(aggregation_results, gap_results, priority_results)
    return {
        "dmi_score": summary.dmi_score,
        "dmi_level": summary.dmi_level,
        "dmi_level_name": summary.dmi_level_name,
        "top_strengths": summary.top_strengths,
        "top_weaknesses": summary.top_weaknesses,
        "critical_gaps": summary.critical_gaps,
        "priority_dimensions": summary.priority_dimensions,
    }