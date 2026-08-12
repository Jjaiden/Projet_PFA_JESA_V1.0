"""
report.py — Structured report generation for JDMAF.

Responsibilities
----------------
- Build the complete assessment report.
- Aggregate assessment and decision results.
- Generate an executive summary.
- Serialize results to JSON.
- Coordinate PDF and Excel exports.

This module is an orchestration layer.
It does NOT perform assessment calculations
or presentation formatting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from config import settings

from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase

from exports.excel import ExcelExporter
from exports.pdf import PDFExporter

from utils.file_manager import build_output_path, ensure_directory


logger = settings.get_logger(__name__)


# ============================================================================
# REPORT DATA STRUCTURES
# ============================================================================


@dataclass
class ReportMetadata:
    """
    Metadata describing the generated report.
    """

    report_id: str
    assessment_id: str
    site_name: str
    generated_at: str
    report_version: str = "1.0"
    generator: str = "JDMAF Backend"


@dataclass
class ExecutiveSummary:
    """
    Executive-level summary of the assessment.
    """

    dmi_score: Optional[float]
    dmi_level: Optional[int]
    dmi_level_name: str

    top_strengths: List[tuple[str, float]]
    top_weaknesses: List[tuple[str, float]]

    critical_gaps: int
    priority_dimensions: int


@dataclass
class ReportData:
    """
    Complete structured report data.
    """

    metadata: ReportMetadata
    summary: ExecutiveSummary

    aggregation_results: Dict[str, Any]

    gap_results: Optional[List[GapResult]] = None
    tpi_results: Optional[List[TPIResult]] = None
    priority_results: Optional[List[PriorityResult]] = None
    roadmap: Optional[List[RoadmapPhase]] = None

    raw_data: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================================
# REPORT GENERATOR
# ============================================================================


class ReportGenerator:
    """
    Unified report orchestrator.

    Coordinates:

        ReportGenerator
            ├── PDFExporter
            ├── ExcelExporter
            └── JSON serialization

    This class does not perform calculations.
    It only prepares and routes already-computed results.
    """

    def __init__(
        self,
        config: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Initialize the report generator.

        Args:
            config:
                Optional configuration dictionary.
        """

        self.config = dict(config or {})

        self.pdf_exporter = PDFExporter(
            self.config
        )

        self.excel_exporter = ExcelExporter(
            self.config
        )

    # =========================================================================
    # MAIN API
    # =========================================================================

    def generate_full_report(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_dir: Optional[Path] = None,
        assessment_id: Optional[str] = None,
        include_pdf: bool = True,
        include_excel: bool = True,
        include_json: bool = True,
    ) -> Dict[str, Path]:
        """
        Generate the complete assessment report.

        Returns:
            Dictionary containing generated file paths.

        Example:

            {
                "pdf": Path(...),
                "excel": Path(...),
                "json": Path(...)
            }
        """

        metadata = aggregation_results.get(
            "metadata",
            {}
        )

        assessment_id = (
            assessment_id
            or metadata.get(
                "assessment_id",
                "UNKNOWN",
            )
        )

        site_name = metadata.get(
            "site_name",
            "N/A",
        )

        # ---------------------------------------------------------------------
        # Build structured report
        # ---------------------------------------------------------------------

        report_data = self._build_report_data(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            assessment_id=assessment_id,
            site_name=site_name,
        )

        outputs: Dict[str, Path] = {}

        # ---------------------------------------------------------------------
        # PDF
        # ---------------------------------------------------------------------

        if include_pdf:

            outputs["pdf"] = self._generate_pdf(
                report_data=report_data,
                output_dir=output_dir,
            )

        # ---------------------------------------------------------------------
        # Excel
        # ---------------------------------------------------------------------

        if include_excel:

            outputs["excel"] = self._generate_excel(
                report_data=report_data,
                output_dir=output_dir,
            )

        # ---------------------------------------------------------------------
        # JSON
        # ---------------------------------------------------------------------

        if include_json:

            outputs["json"] = self._generate_json(
                report_data=report_data,
                output_dir=output_dir,
            )

        logger.info(
            "Complete report generated: %s",
            ", ".join(
                f"{key}={value}"
                for key, value in outputs.items()
            ),
        )

        return outputs

    # =========================================================================
    # REPORT CONSTRUCTION
    # =========================================================================

    def _build_report_data(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        assessment_id: str = "UNKNOWN",
        site_name: str = "N/A",
    ) -> ReportData:
        """
        Build the complete structured report.
        """

        report_metadata = ReportMetadata(
            report_id=(
                f"RPT-{assessment_id}-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            assessment_id=assessment_id,
            site_name=site_name,
            generated_at=datetime.now().isoformat(),
        )

        summary = self._build_executive_summary(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
        )

        dmi = aggregation_results.get("dmi")

        return ReportData(
            metadata=report_metadata,
            summary=summary,
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            raw_data={
                "dmi": (
                    dmi.to_dict()
                    if dmi is not None
                    else None
                ),
                "indicators": self._serialize_score_results(
                    aggregation_results.get(
                        "indicators",
                        {},
                    )
                ),
                "subdimensions": self._serialize_score_results(
                    aggregation_results.get(
                        "subdimensions",
                        {},
                    )
                ),
                "dimensions": self._serialize_score_results(
                    aggregation_results.get(
                        "dimensions",
                        {},
                    )
                ),
                "pillars": self._serialize_score_results(
                    aggregation_results.get(
                        "pillars",
                        {},
                    )
                ),
            },
        )

    # =========================================================================
    # EXECUTIVE SUMMARY
    # =========================================================================

    def _build_executive_summary(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
    ) -> ExecutiveSummary:
        """
        Build the executive summary.

        No calculations related to maturity are performed here.
        This only selects and summarizes already-computed results.
        """

        dmi = aggregation_results.get("dmi")

        # ---------------------------------------------------------------------
        # Dimensions
        # ---------------------------------------------------------------------

        dimensions = aggregation_results.get(
            "dimensions",
            {}
        )

        dim_scores: List[tuple[str, float]] = []

        for dim_id, result in dimensions.items():

            if (
                isinstance(result, ScoreResult)
                and result.score is not None
            ):
                dim_scores.append(
                    (
                        dim_id,
                        float(result.score),
                    )
                )

        # Highest scores first
        dim_scores.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        top_strengths = dim_scores[:3]

        # Lowest scores first
        top_weaknesses = sorted(
            dim_scores,
            key=lambda item: item[1],
        )[:3]

        # ---------------------------------------------------------------------
        # Critical / high gaps
        # ---------------------------------------------------------------------

        critical_gaps = 0

        if gap_results:

            critical_gaps = sum(
                1
                for gap in gap_results
                if self._normalize_priority(
                    gap.priority
                )
                in {"Critical", "High"}
            )

        # ---------------------------------------------------------------------
        # Priority dimensions
        # ---------------------------------------------------------------------

        priority_dimensions = len(dim_scores)

        return ExecutiveSummary(
            dmi_score=(
                float(dmi.score)
                if dmi is not None
                and dmi.score is not None
                else None
            ),
            dmi_level=(
                dmi.level
                if dmi is not None
                else None
            ),
            dmi_level_name=(
                dmi.level_name
                if dmi is not None
                else ""
            ),
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            critical_gaps=critical_gaps,
            priority_dimensions=priority_dimensions,
        )

    # =========================================================================
    # PDF EXPORT
    # =========================================================================

    def _generate_pdf(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the PDF using PDFExporter.
        """

        filename = (
            f"assessment_report_"
            f"{report_data.metadata.assessment_id}.pdf"
        )

        if output_dir is not None:

            ensure_directory(output_dir)

            output_path = (
                Path(output_dir) / filename
            )

        else:

            output_path = build_output_path(
                filename
            )

        return self.pdf_exporter.export_assessment_results(
            aggregation_results=(
                report_data.aggregation_results
            ),
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=(
                report_data.metadata.assessment_id
            ),
        )

    # =========================================================================
    # EXCEL EXPORT
    # =========================================================================

    def _generate_excel(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the Excel workbook using ExcelExporter.
        """

        filename = (
            f"assessment_results_"
            f"{report_data.metadata.assessment_id}.xlsx"
        )

        if output_dir is not None:

            ensure_directory(output_dir)

            output_path = (
                Path(output_dir) / filename
            )

        else:

            output_path = build_output_path(
                filename
            )

        return self.excel_exporter.export_assessment_results(
            aggregation_results=(
                report_data.aggregation_results
            ),
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=(
                report_data.metadata.assessment_id
            ),
        )

    # =========================================================================
    # JSON EXPORT
    # =========================================================================

    def _generate_json(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the JSON report.
        """

        filename = (
            f"assessment_report_"
            f"{report_data.metadata.assessment_id}.json"
        )

        if output_dir is not None:

            ensure_directory(output_dir)

            output_path = (
                Path(output_dir) / filename
            )

        else:

            output_path = build_output_path(
                filename
            )

        data = self._serialize_report_data(
            report_data
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(
            "JSON report generated: %s",
            output_path,
        )

        return output_path

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def _serialize_report_data(
        self,
        report_data: ReportData,
    ) -> Dict[str, Any]:
        """
        Convert ReportData into JSON-compatible dictionaries.
        """

        return {
            "metadata": {
                "report_id": (
                    report_data.metadata.report_id
                ),
                "assessment_id": (
                    report_data.metadata.assessment_id
                ),
                "site_name": (
                    report_data.metadata.site_name
                ),
                "generated_at": (
                    report_data.metadata.generated_at
                ),
                "report_version": (
                    report_data.metadata.report_version
                ),
                "generator": (
                    report_data.metadata.generator
                ),
            },

            "summary": {
                "dmi_score": (
                    report_data.summary.dmi_score
                ),
                "dmi_level": (
                    report_data.summary.dmi_level
                ),
                "dmi_level_name": (
                    report_data.summary.dmi_level_name
                ),
                "top_strengths": [
                    list(item)
                    for item in (
                        report_data.summary.top_strengths
                    )
                ],
                "top_weaknesses": [
                    list(item)
                    for item in (
                        report_data.summary.top_weaknesses
                    )
                ],
                "critical_gaps": (
                    report_data.summary.critical_gaps
                ),
                "priority_dimensions": (
                    report_data.summary.priority_dimensions
                ),
            },

            "aggregation": self._serialize_aggregation(
                report_data.aggregation_results
            ),

            "decision": {
                "gaps": [
                    gap.to_dict()
                    for gap in (
                        report_data.gap_results or []
                    )
                ],

                "tpi": [
                    tpi.to_dict()
                    for tpi in (
                        report_data.tpi_results or []
                    )
                ],

                "priorities": [
                    priority.to_dict()
                    for priority in (
                        report_data.priority_results or []
                    )
                ],

                "roadmap": [
                    phase.to_dict()
                    for phase in (
                        report_data.roadmap or []
                    )
                ],
            },
        }

    @staticmethod
    def _serialize_aggregation(
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Serialize aggregation results.
        """

        dmi = results.get("dmi")

        return {
            "indicators": (
                ReportGenerator._serialize_score_results(
                    results.get(
                        "indicators",
                        {},
                    )
                )
            ),

            "subdimensions": (
                ReportGenerator._serialize_score_results(
                    results.get(
                        "subdimensions",
                        {},
                    )
                )
            ),

            "dimensions": (
                ReportGenerator._serialize_score_results(
                    results.get(
                        "dimensions",
                        {},
                    )
                )
            ),

            "pillars": (
                ReportGenerator._serialize_score_results(
                    results.get(
                        "pillars",
                        {},
                    )
                )
            ),

            "dmi": (
                dmi.to_dict()
                if dmi is not None
                else None
            ),

            "metadata": results.get(
                "metadata",
                {},
            ),
        }

    @staticmethod
    def _serialize_score_results(
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Serialize ScoreResult objects.
        """

        serialized: Dict[str, Any] = {}

        for key, result in results.items():

            if isinstance(
                result,
                ScoreResult,
            ):

                serialized[key] = (
                    result.to_dict()
                )

            elif isinstance(
                result,
                dict,
            ):

                serialized[key] = result

            else:

                # Keep JSON-compatible primitive values
                # if they are already serialized.
                try:

                    json.dumps(result)

                    serialized[key] = result

                except TypeError:

                    serialized[key] = str(result)

        return serialized

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _normalize_priority(
        priority: Any,
    ) -> str:
        """
        Normalize priority labels.
        """

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

        normalized = (
            str(priority)
            .strip()
            .lower()
        )

        return mapping.get(
            normalized,
            str(priority),
        )


# ============================================================================
# PUBLIC UTILITY FUNCTIONS
# ============================================================================


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
    Quick utility to generate a complete report.

    Args:
        aggregation_results:
            Results from aggregation.

        gap_results:
            Gap analysis results.

        tpi_results:
            TPI results.

        priority_results:
            Priority analysis results.

        roadmap:
            Transformation roadmap.

        output_dir:
            Output directory.

        assessment_id:
            Assessment identifier.

        formats:
            Formats to generate:
                "pdf"
                "excel"
                "json"

    Returns:
        Dictionary of generated paths.
    """

    if formats is None:

        formats = [
            "pdf",
            "excel",
            "json",
        ]

    normalized_formats = {
        str(fmt).strip().lower()
        for fmt in formats
    }

    generator = ReportGenerator()

    return generator.generate_full_report(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_dir=output_dir,
        assessment_id=assessment_id,
        include_pdf=(
            "pdf" in normalized_formats
        ),
        include_excel=(
            "excel" in normalized_formats
        ),
        include_json=(
            "json" in normalized_formats
        ),
    )


def generate_executive_summary(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
) -> Dict[str, Any]:
    """
    Generate a structured executive summary.
    """

    generator = ReportGenerator()

    summary = generator._build_executive_summary(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
    )

    return {
        "dmi_score": summary.dmi_score,
        "dmi_level": summary.dmi_level,
        "dmi_level_name": summary.dmi_level_name,
        "top_strengths": summary.top_strengths,
        "top_weaknesses": summary.top_weaknesses,
        "critical_gaps": summary.critical_gaps,
        "priority_dimensions": summary.priority_dimensions,
    }