"""
report.py — Global assessment report orchestration for JDMAF.

Responsibilities
----------------
- Build the complete assessment report.
- Aggregate already-computed assessment and decision results.
- Generate an executive summary.
- Serialize the complete report to JSON.
- Coordinate PDF and Excel exports.

This module does NOT:
- Calculate assessment scores.
- Perform maturity calculations.
- Perform gap analysis.
- Calculate TPI.
- Calculate priorities.
- Build the transformation roadmap.
- Perform presentation formatting.

It acts as the orchestration layer between the
assessment/decision engines and the export layer.
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
from exports.pdf import PDFExporter

from utils.file_manager import build_output_path, ensure_directory


logger = settings.get_logger(__name__)


# ============================================================================
# REPORT DATA STRUCTURES
# ============================================================================


@dataclass
class ReportMetadata:
    """
    Metadata describing the generated global report.
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
    Executive-level summary of the complete assessment.
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
    Complete structured global report data.

    This object contains:
    - report metadata,
    - executive summary,
    - assessment aggregation,
    - decision-analysis results,
    - raw serialized data.
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
    Unified global report orchestrator.

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

    # ========================================================================
    # MAIN API
    # ========================================================================

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
        Generate the complete global assessment report.

        The calculations must already have been performed by the
        assessment and decision engines.

        Args:
            aggregation_results:
                Already-computed assessment aggregation results.

            gap_results:
                Already-computed gap analysis results.

            tpi_results:
                Already-computed TPI results.

            priority_results:
                Already-computed prioritization results.

            roadmap:
                Already-computed transformation roadmap.

            output_dir:
                Optional directory where generated files are stored.

            assessment_id:
                Optional assessment identifier.

            include_pdf:
                Whether to generate the PDF report.

            include_excel:
                Whether to generate the Excel report.

            include_json:
                Whether to generate the JSON report.

        Returns:
            Dictionary containing generated file paths.

        Example:
            {
                "pdf": Path(...),
                "excel": Path(...),
                "json": Path(...)
            }
        """

        if not isinstance(
            aggregation_results,
            dict,
        ):
            raise TypeError(
                "aggregation_results must be a dictionary."
            )

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            metadata = {}

        resolved_assessment_id = (
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

        # ------------------------------------------------------------------
        # Build structured global report
        # ------------------------------------------------------------------

        report_data = self._build_report_data(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            assessment_id=str(
                resolved_assessment_id
            ),
            site_name=str(site_name),
        )

        outputs: Dict[str, Path] = {}

        # ------------------------------------------------------------------
        # PDF
        # ------------------------------------------------------------------

        if include_pdf:
            outputs["pdf"] = self._generate_pdf(
                report_data=report_data,
                output_dir=output_dir,
            )

        # ------------------------------------------------------------------
        # Excel
        # ------------------------------------------------------------------

        if include_excel:
            outputs["excel"] = self._generate_excel(
                report_data=report_data,
                output_dir=output_dir,
            )

        # ------------------------------------------------------------------
        # JSON
        # ------------------------------------------------------------------

        if include_json:
            outputs["json"] = self._generate_json(
                report_data=report_data,
                output_dir=output_dir,
            )

        logger.info(
            "Complete global report generated: %s",
            ", ".join(
                f"{key}={value}"
                for key, value in outputs.items()
            ),
        )

        return outputs

    # ========================================================================
    # REPORT CONSTRUCTION
    # ========================================================================

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
        Build the complete structured global report.

        No assessment or decision calculations are performed here.
        """

        generated_at = datetime.now().isoformat()

        report_metadata = ReportMetadata(
            report_id=(
                f"RPT-{assessment_id}-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            assessment_id=assessment_id,
            site_name=site_name,
            generated_at=generated_at,
        )

        summary = self._build_executive_summary(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            priority_results=priority_results,
        )

        dmi = aggregation_results.get(
            "dmi"
        )

        raw_data = {
            "dmi": self._serialize_object(
                dmi
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

    # ========================================================================
    # EXECUTIVE SUMMARY
    # ========================================================================

    def _build_executive_summary(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
    ) -> ExecutiveSummary:
        """
        Build the executive summary.

        This method only selects and summarizes already-computed results.

        No maturity or scoring calculations are performed here.
        """

        dmi = aggregation_results.get(
            "dmi"
        )

        # ------------------------------------------------------------------
        # Dimensions
        # ------------------------------------------------------------------

        dimensions = aggregation_results.get(
            "dimensions",
            {},
        )

        if not isinstance(
            dimensions,
            Mapping,
        ):
            dimensions = {}

        dim_scores: List[tuple[str, float]] = []

        for dim_id, result in dimensions.items():

            if (
                isinstance(
                    result,
                    ScoreResult,
                )
                and result.score is not None
            ):
                dim_scores.append(
                    (
                        str(dim_id),
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

        # ------------------------------------------------------------------
        # Critical / high gaps
        # ------------------------------------------------------------------

        critical_gaps = 0

        if gap_results:

            critical_gaps = sum(
                1
                for gap in gap_results
                if self._normalize_priority(
                    getattr(
                        gap,
                        "priority",
                        None,
                    )
                )
                in {
                    "Critical",
                    "High",
                }
            )

        # ------------------------------------------------------------------
        # Priority dimensions
        # ------------------------------------------------------------------

        if priority_results:

            priority_dimensions = len(
                priority_results
            )

        else:

            priority_dimensions = 0

        # ------------------------------------------------------------------
        # DMI information
        # ------------------------------------------------------------------

        dmi_score: Optional[float] = None
        dmi_level: Optional[int] = None
        dmi_level_name = ""

        if dmi is not None:

            score = getattr(
                dmi,
                "score",
                None,
            )

            level = getattr(
                dmi,
                "level",
                None,
            )

            level_name = getattr(
                dmi,
                "level_name",
                "",
            )

            if score is not None:
                dmi_score = float(score)

            if level is not None:
                dmi_level = int(level)

            if level_name is not None:
                dmi_level_name = str(
                    level_name
                )

        return ExecutiveSummary(
            dmi_score=dmi_score,
            dmi_level=dmi_level,
            dmi_level_name=dmi_level_name,
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            critical_gaps=critical_gaps,
            priority_dimensions=priority_dimensions,
        )

    # ========================================================================
    # PDF EXPORT
    # ========================================================================

    def _generate_pdf(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the global assessment report as PDF.

        PDFExporter is responsible only for PDF presentation.
        """

        filename = (
            f"assessment_report_"
            f"{report_data.metadata.assessment_id}.pdf"
        )

        output_path = self._resolve_output_path(
            filename=filename,
            output_dir=output_dir,
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

    # ========================================================================
    # EXCEL EXPORT
    # ========================================================================

    def _generate_excel(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the global assessment report as Excel.
        """

        filename = (
            f"assessment_results_"
            f"{report_data.metadata.assessment_id}.xlsx"
        )

        output_path = self._resolve_output_path(
            filename=filename,
            output_dir=output_dir,
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

    # ========================================================================
    # JSON EXPORT
    # ========================================================================

    def _generate_json(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate the complete structured report as JSON.
        """

        filename = (
            f"assessment_report_"
            f"{report_data.metadata.assessment_id}.json"
        )

        output_path = self._resolve_output_path(
            filename=filename,
            output_dir=output_dir,
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
                default=str,
            )

        logger.info(
            "JSON report generated: %s",
            output_path,
        )

        return output_path

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

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
                    self._serialize_object(gap)
                    for gap in (
                        report_data.gap_results or []
                    )
                ],

                "tpi": [
                    self._serialize_object(tpi)
                    for tpi in (
                        report_data.tpi_results or []
                    )
                ],

                "priorities": [
                    self._serialize_object(priority)
                    for priority in (
                        report_data.priority_results or []
                    )
                ],

                "roadmap": [
                    self._serialize_object(phase)
                    for phase in (
                        report_data.roadmap or []
                    )
                ],
            },

            "raw_data": report_data.raw_data,
        }

    # ========================================================================
    # AGGREGATION SERIALIZATION
    # ========================================================================

    @staticmethod
    def _serialize_aggregation(
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Serialize aggregation results.
        """

        dmi = results.get(
            "dmi"
        )

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
                ReportGenerator._serialize_object(
                    dmi
                )
                if dmi is not None
                else None
            ),

            "metadata": ReportGenerator._make_json_safe(
                results.get(
                    "metadata",
                    {},
                )
            ),
        }

    # ========================================================================
    # SCORE RESULT SERIALIZATION
    # ========================================================================

    @staticmethod
    def _serialize_score_results(
        results: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Serialize ScoreResult objects.

        Already serialized dictionaries and JSON-compatible primitive
        values are preserved.
        """

        if not isinstance(
            results,
            Mapping,
        ):
            return {}

        serialized: Dict[str, Any] = {}

        for key, result in results.items():

            if isinstance(
                result,
                ScoreResult,
            ):

                serialized[str(key)] = (
                    result.to_dict()
                )

            elif isinstance(
                result,
                Mapping,
            ):

                serialized[str(key)] = (
                    ReportGenerator._make_json_safe(
                        result
                    )
                )

            else:

                serialized[str(key)] = (
                    ReportGenerator._make_json_safe(
                        result
                    )
                )

        return serialized

    # ========================================================================
    # GENERIC SERIALIZATION HELPERS
    # ========================================================================

    @staticmethod
    def _serialize_object(
        obj: Any,
    ) -> Any:
        """
        Convert a project object into JSON-compatible data.

        Priority:
        1. to_dict()
        2. dataclasses.asdict()
        3. mappings
        4. lists/tuples
        5. primitive values
        6. string fallback
        """

        if obj is None:
            return None

        # Project classes exposing to_dict()
        if hasattr(
            obj,
            "to_dict",
        ):

            try:
                return ReportGenerator._make_json_safe(
                    obj.to_dict()
                )
            except Exception:
                pass

        # Dataclass objects
        if hasattr(
            obj,
            "__dataclass_fields__",
        ):

            try:
                return ReportGenerator._make_json_safe(
                    asdict(obj)
                )
            except Exception:
                pass

        return ReportGenerator._make_json_safe(
            obj
        )

    @staticmethod
    def _make_json_safe(
        value: Any,
    ) -> Any:
        """
        Recursively convert values into JSON-compatible structures.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        if isinstance(
            value,
            Path,
        ):
            return str(value)

        if isinstance(
            value,
            Mapping,
        ):
            return {
                str(key): ReportGenerator._make_json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                ReportGenerator._make_json_safe(
                    item
                )
                for item in value
            ]

        if hasattr(
            value,
            "to_dict",
        ):

            try:
                return ReportGenerator._make_json_safe(
                    value.to_dict()
                )
            except Exception:
                pass

        if hasattr(
            value,
            "__dataclass_fields__",
        ):

            try:
                return ReportGenerator._make_json_safe(
                    asdict(value)
                )
            except Exception:
                pass

        try:
            json.dumps(value)
            return value

        except TypeError:
            return str(value)

    # ========================================================================
    # OUTPUT PATH
    # ========================================================================

    @staticmethod
    def _resolve_output_path(
        filename: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Resolve the final output path.
        """

        if output_dir is not None:

            output_dir = Path(
                output_dir
            )

            ensure_directory(
                output_dir
            )

            return output_dir / filename

        return build_output_path(
            filename
        )

    # ========================================================================
    # PRIORITY NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_priority(
        priority: Any,
    ) -> str:
        """
        Normalize priority labels.

        Supports English and French labels.
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
    Quick utility to generate a complete global report.

    Args:
        aggregation_results:
            Results from assessment aggregation.

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
        Dictionary of generated file paths.
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

    supported_formats = {
        "pdf",
        "excel",
        "json",
    }

    unsupported_formats = (
        normalized_formats
        - supported_formats
    )

    if unsupported_formats:

        logger.warning(
            "Unsupported report formats ignored: %s",
            ", ".join(
                sorted(
                    unsupported_formats
                )
            ),
        )

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
    priority_results: Optional[List[PriorityResult]] = None,
) -> Dict[str, Any]:
    """
    Generate a structured executive summary.

    This utility does not generate a file.
    It only returns the summary as a dictionary.
    """

    # Avoid unnecessary exporter initialization.
    dimensions = aggregation_results.get(
        "dimensions",
        {},
    )

    dmi = aggregation_results.get(
        "dmi"
    )

    # ----------------------------------------------------------------------
    # Dimension scores
    # ----------------------------------------------------------------------

    dim_scores: List[tuple[str, float]] = []

    if isinstance(
        dimensions,
        Mapping,
    ):

        for dim_id, result in dimensions.items():

            if (
                isinstance(
                    result,
                    ScoreResult,
                )
                and result.score is not None
            ):
                dim_scores.append(
                    (
                        str(dim_id),
                        float(result.score),
                    )
                )

    dim_scores.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    top_strengths = dim_scores[:3]

    top_weaknesses = sorted(
        dim_scores,
        key=lambda item: item[1],
    )[:3]

    # ----------------------------------------------------------------------
    # Critical gaps
    # ----------------------------------------------------------------------

    critical_gaps = 0

    if gap_results:

        critical_gaps = sum(
            1
            for gap in gap_results
            if ReportGenerator._normalize_priority(
                getattr(
                    gap,
                    "priority",
                    None,
                )
            )
            in {
                "Critical",
                "High",
            }
        )

    # ----------------------------------------------------------------------
    # Priority dimensions
    # ----------------------------------------------------------------------

    priority_dimensions = (
        len(priority_results)
        if priority_results
        else 0
    )

    # ----------------------------------------------------------------------
    # DMI
    # ----------------------------------------------------------------------

    dmi_score = None
    dmi_level = None
    dmi_level_name = ""

    if dmi is not None:

        if getattr(
            dmi,
            "score",
            None,
        ) is not None:

            dmi_score = float(
                dmi.score
            )

        if getattr(
            dmi,
            "level",
            None,
        ) is not None:

            dmi_level = int(
                dmi.level
            )

        dmi_level_name = str(
            getattr(
                dmi,
                "level_name",
                "",
            )
            or ""
        )

    return {
        "dmi_score": dmi_score,
        "dmi_level": dmi_level,
        "dmi_level_name": dmi_level_name,
        "top_strengths": top_strengths,
        "top_weaknesses": top_weaknesses,
        "critical_gaps": critical_gaps,
        "priority_dimensions": priority_dimensions,
    }