"""
pdf.py
------

Professional Industrial Digital Maturity Assessment PDF exporter.

This module ONLY formats and presents already-computed assessment results.
It does NOT perform assessment calculations.

Expected input:
    aggregation_results
    gap_results
    tpi_results
    priority_results
    roadmap

The public API intentionally mirrors ExcelExporter.export_assessment_results().
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from config import settings
from utils.file_manager import ensure_directory, build_output_path


# ============================================================================
# BRAND SYSTEM
# ============================================================================

JESA_GREEN = colors.HexColor("#007A4D")
JESA_DARK = colors.HexColor("#173F35")
JESA_LIGHT = colors.HexColor("#E8F3EF")

ENSAM_BLUE = colors.HexColor("#0057A8")

WHITE = colors.white
BLACK = colors.black

GREY_100 = colors.HexColor("#F7F9F8")
GREY_200 = colors.HexColor("#E9EEEC")
GREY_400 = colors.HexColor("#B8C4BF")
GREY_600 = colors.HexColor("#5B6863")
GREY_800 = colors.HexColor("#25322E")

CRITICAL_RED = colors.HexColor("#C62828")
HIGH_ORANGE = colors.HexColor("#EF6C00")
MEDIUM_YELLOW = colors.HexColor("#F9A825")
LOW_BLUE = colors.HexColor("#1976D2")
VERY_LOW_GREY = colors.HexColor("#78909C")

SUCCESS_GREEN = colors.HexColor("#2E7D32")

PRIORITY_COLORS = {
    "Critical": CRITICAL_RED,
    "High": HIGH_ORANGE,
    "Medium": MEDIUM_YELLOW,
    "Low": LOW_BLUE,
    "Very Low": VERY_LOW_GREY,
}

PRIORITY_RANK = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4,
    "Very Low": 5,
}

PHASE_ORDER = {
    "Phase 1": 1,
    "Phase 2": 2,
    "Phase 3": 3,
    "Phase 4": 4,
}


# ============================================================================
# SAFE HELPERS
# ============================================================================

def _get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Read a value from either:
        - a dictionary
        - an object attribute
    """
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default

    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _format_number(
    value: Any,
    decimals: int = 1,
) -> str:
    if value is None:
        return "—"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_percent(value: Any) -> str:
    if value is None:
        return "—"

    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _normalize_priority(priority: Any) -> str:
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

    normalized = str(priority).strip().lower()

    return mapping.get(
        normalized,
        str(priority),
    )


def _priority_color(priority: Any):
    return PRIORITY_COLORS.get(
        _normalize_priority(priority),
        GREY_600,
    )


# ============================================================================
# PDF EXPORTER
# ============================================================================


class PDFExporter:
    """
    Generate a professional Industrial Digital Maturity Assessment Report.
    """

    def __init__(
        self,
        config: Optional[Mapping[str, Any]] = None,
    ) -> None:

        self.config = dict(config or {})

        self.decimal_precision = self.config.get(
            "decimal_precision",
            getattr(
                settings,
                "SCORE_DECIMAL_PRECISION",
                1,
            ),
        )

        self.generated_at = datetime.now()

        # IMPORTANT:
        # _build_styles() exists in this class.
        self.styles = self._build_styles()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def export_assessment_results(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[Any]] = None,
        tpi_results: Optional[List[Any]] = None,
        priority_results: Optional[List[Any]] = None,
        roadmap: Optional[List[Any]] = None,
        output_path: Optional[Path] = None,
        assessment_id: Optional[str] = None,
    ) -> Path:
        """
        Generate the complete PDF report.

        This method is intentionally compatible with ExcelExporter.
        """

        gap_results = gap_results or []
        tpi_results = tpi_results or []
        priority_results = priority_results or []
        roadmap = roadmap or []

        # ------------------------------------------------------------------
        # Output path
        # ------------------------------------------------------------------

        if output_path is None:

            suffix = (
                f"_{assessment_id}"
                if assessment_id
                else ""
            )

            filename = (
                "industrial_digital_maturity_assessment"
                f"{suffix}.pdf"
            )

            output_path = build_output_path(filename)

        output_path = Path(output_path)

        ensure_directory(output_path.parent)

        # ------------------------------------------------------------------
        # Metadata
        # ------------------------------------------------------------------

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        # ------------------------------------------------------------------
        # Document
        # ------------------------------------------------------------------

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title="Industrial Digital Maturity Assessment Report",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment",
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="main_frame",
        )

        page_template = PageTemplate(
            id="AssessmentReport",
            frames=frame,
            onPage=self._draw_page_header_footer,
        )

        doc.addPageTemplates([page_template])

        story: List[Any] = []

        # ==================================================================
        # COVER
        # ==================================================================

        story.extend(
            self._build_cover_page(
                metadata,
                assessment_id,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # EXECUTIVE SUMMARY
        # ==================================================================

        story.extend(
            self._build_executive_summary(
                aggregation_results,
                gap_results,
                tpi_results,
                priority_results,
                roadmap,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # DMI OVERVIEW
        # ==================================================================

        story.extend(
            self._build_dmi_overview(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # PILLARS
        # ==================================================================

        story.extend(
            self._build_pillar_assessment(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # DIMENSIONS
        # ==================================================================

        story.extend(
            self._build_dimension_assessment(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # GAP ANALYSIS
        # ==================================================================

        story.extend(
            self._build_gap_analysis(
                gap_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # TPI
        # ==================================================================

        story.extend(
            self._build_tpi_prioritization(
                tpi_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # PRIORITY MATRIX
        # ==================================================================

        story.extend(
            self._build_priority_matrix(
                priority_results,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # ROADMAP
        # ==================================================================

        story.extend(
            self._build_transformation_roadmap(
                roadmap,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # RECOMMENDATIONS
        # ==================================================================

        story.extend(
            self._build_recommendations(
                priority_results,
                roadmap,
            )
        )

        story.append(PageBreak())

        # ==================================================================
        # METADATA
        # ==================================================================

        story.extend(
            self._build_metadata(
                aggregation_results,
                assessment_id,
            )
        )

        # ==================================================================
        # BUILD
        # ==================================================================

        doc.build(story)

        return output_path

    # ========================================================================
    # STYLES
    # ========================================================================

    def _build_styles(self):
        styles = getSampleStyleSheet()

        return {
            "title": ParagraphStyle(
                "ReportTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=27,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
                spaceAfter=10,
            ),

            "subtitle": ParagraphStyle(
                "ReportSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=GREY_600,
                alignment=TA_CENTER,
                spaceAfter=12,
            ),

            "h1": ParagraphStyle(
                "SectionTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=17,
                leading=21,
                textColor=JESA_DARK,
                spaceAfter=8,
            ),

            "h2": ParagraphStyle(
                "SubSectionTitle",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=15,
                textColor=JESA_DARK,
                spaceBefore=8,
                spaceAfter=6,
            ),

            "body": ParagraphStyle(
                "Body",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=GREY_800,
                spaceAfter=5,
            ),

            "small": ParagraphStyle(
                "Small",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=GREY_600,
            ),

            "small_white": ParagraphStyle(
                "SmallWhite",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=WHITE,
            ),

            "kpi": ParagraphStyle(
                "KPI",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=25,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
            ),

            "kpi_label": ParagraphStyle(
                "KPILabel",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=10,
                textColor=GREY_600,
                alignment=TA_CENTER,
            ),

            "center": ParagraphStyle(
                "Center",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=10,
                alignment=TA_CENTER,
            ),

            "table": ParagraphStyle(
                "Table",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=6.8,
                leading=8.5,
                textColor=GREY_800,
            ),

            "table_header": ParagraphStyle(
                "TableHeader",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=6.8,
                leading=8.5,
                textColor=WHITE,
                alignment=TA_CENTER,
            ),
        }

    # ========================================================================
    # PAGE HEADER / FOOTER
    # ========================================================================

    def _draw_page_header_footer(
        self,
        canvas,
        doc,
    ) -> None:

        canvas.saveState()

        width, height = A4

        # Do not show header/footer on first page.
        if doc.page > 1:

            canvas.setStrokeColor(GREY_200)
            canvas.setLineWidth(0.5)

            canvas.line(
                16 * mm,
                height - 13 * mm,
                width - 16 * mm,
                height - 13 * mm,
            )

            canvas.setFont(
                "Helvetica-Bold",
                7,
            )

            canvas.setFillColor(
                JESA_DARK
            )

            canvas.drawString(
                16 * mm,
                height - 10 * mm,
                "JESA DMAT",
            )

            canvas.setFont(
                "Helvetica",
                7,
            )

            canvas.setFillColor(
                GREY_600
            )

            canvas.drawRightString(
                width - 16 * mm,
                height - 10 * mm,
                "Industrial Digital Maturity Assessment",
            )

        # Footer
        canvas.setStrokeColor(GREY_200)

        canvas.line(
            16 * mm,
            10 * mm,
            width - 16 * mm,
            10 * mm,
        )

        canvas.setFont(
            "Helvetica",
            6.5,
        )

        canvas.setFillColor(
            GREY_600
        )

        canvas.drawString(
            16 * mm,
            6 * mm,
            f"Generated {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
        )

        canvas.drawRightString(
            width - 16 * mm,
            6 * mm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    # ========================================================================
    # COVER
    # ========================================================================

    def _build_cover_page(
        self,
        metadata: Mapping[str, Any],
        assessment_id: Optional[str],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(Spacer(1, 25 * mm))

        # Logo block
        logo_table = self._build_logo_table()

        if logo_table:
            story.append(logo_table)
            story.append(Spacer(1, 18 * mm))

        story.append(
            Paragraph(
                "INDUSTRIAL DIGITAL<br/>MATURITY ASSESSMENT",
                self.styles["title"],
            )
        )

        story.append(
            Paragraph(
                "Professional Assessment Report",
                self.styles["subtitle"],
            )
        )

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        site_name = _safe_str(
            metadata.get("site_name", ""),
            "Industrial Site",
        )

        assessment_date = _safe_str(
            metadata.get("assessment_date", ""),
            self.generated_at.strftime("%Y-%m-%d"),
        )

        evaluator = _safe_str(
            metadata.get("evaluator", ""),
            "—",
        )

        assessment_id_value = (
            assessment_id
            or metadata.get("assessment_id", "")
            or "—"
        )

        data = [
            [
                Paragraph(
                    "<b>Site</b>",
                    self.styles["body"],
                ),
                Paragraph(
                    site_name,
                    self.styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Assessment ID</b>",
                    self.styles["body"],
                ),
                Paragraph(
                    assessment_id_value,
                    self.styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Assessment Date</b>",
                    self.styles["body"],
                ),
                Paragraph(
                    assessment_date,
                    self.styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Evaluator</b>",
                    self.styles["body"],
                ),
                Paragraph(
                    evaluator,
                    self.styles["body"],
                ),
            ],
        ]

        table = Table(
            data,
            colWidths=[
                45 * mm,
                100 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        JESA_LIGHT,
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (1, -1),
                        GREY_100,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        GREY_200,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        GREY_200,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                35 * mm,
            )
        )

        story.append(
            Paragraph(
                "JESA Digital Maturity Assessment Tool",
                self.styles["subtitle"],
            )
        )

        story.append(
            Paragraph(
                "Confidential Assessment Report",
                self.styles["small"],
            )
        )

        return story

    # ========================================================================
    # LOGOS
    # ========================================================================

    def _build_logo_table(self):
        logo_dir = self._get_logo_directory()

        jesa_path = self._find_logo(
            logo_dir,
            [
                "jesa_logo.png",
                "JESA_logo.png",
                "jesa.png",
                "JESA.png",
            ],
        )

        ensam_path = self._find_logo(
            logo_dir,
            [
                "ensam_logo.png",
                "ENSAM_logo.png",
                "ensam.png",
                "ENSAM.png",
            ],
        )

        cells = []

        if jesa_path:

            try:
                image = Image(
                    str(jesa_path),
                    width=48 * mm,
                    height=18 * mm,
                )

                image.hAlign = "CENTER"

                cells.append(image)

            except Exception:
                cells.append(
                    Paragraph(
                        "JESA",
                        self.styles["h2"],
                    )
                )

        else:
            cells.append(
                Paragraph(
                    "JESA",
                    self.styles["h2"],
                )
            )

        if ensam_path:

            try:
                image = Image(
                    str(ensam_path),
                    width=42 * mm,
                    height=18 * mm,
                )

                image.hAlign = "CENTER"

                cells.append(image)

            except Exception:
                cells.append(
                    Paragraph(
                        "ENSAM",
                        self.styles["h2"],
                    )
                )

        else:
            cells.append(
                Paragraph(
                    "ENSAM",
                    self.styles["h2"],
                )
            )

        table = Table(
            [cells],
            colWidths=[
                75 * mm,
                75 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

        return table

    def _get_logo_directory(self) -> Path:

        try:

            frontend = getattr(
                settings,
                "frontend",
                None,
            )

            if frontend is not None:

                logo_dir = getattr(
                    frontend,
                    "LOGO_DIR",
                    None,
                )

                if logo_dir:
                    return Path(logo_dir)

        except Exception:
            pass

        try:

            backend = getattr(
                settings,
                "backend",
                None,
            )

            if backend is not None:

                base_dir = getattr(
                    backend,
                    "BASE_DIR",
                    None,
                )

                if base_dir:

                    return (
                        Path(base_dir)
                        / "assets"
                        / "logo"
                    )

        except Exception:
            pass

        return (
            Path.cwd()
            / "assets"
            / "logo"
        )

    @staticmethod
    def _find_logo(
        directory: Path,
        candidates: List[str],
    ) -> Optional[Path]:

        if not directory.exists():
            return None

        for filename in candidates:

            path = directory / filename

            if path.exists():
                return path

        candidate_names = {
            name.lower()
            for name in candidates
        }

        try:

            for path in directory.iterdir():

                if (
                    path.is_file()
                    and path.name.lower()
                    in candidate_names
                ):
                    return path

        except OSError:
            return None

        return None

    # ========================================================================
    # EXECUTIVE SUMMARY
    # ========================================================================

    def _build_executive_summary(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: List[Any],
        tpi_results: List[Any],
        priority_results: List[Any],
        roadmap: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "1. Executive Summary",
                self.styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "This section provides an executive-level overview "
                "of the assessed site's digital maturity and the "
                "main transformation priorities identified by the "
                "assessment.",
                self.styles["body"],
            )
        )

        dmi = aggregation_results.get("dmi")

        dmi_score = _get(
            dmi,
            "score",
            aggregation_results.get(
                "dmi_score"
            ),
        )

        dmi_level = _get(
            dmi,
            "level_name",
            aggregation_results.get(
                "dmi_level_name",
                aggregation_results.get(
                    "dmi_level",
                    "—",
                ),
            ),
        )

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        total_indicators = metadata.get(
            "total_indicators",
            len(
                aggregation_results.get(
                    "indicators",
                    {},
                )
            ),
        )

        total_dimensions = metadata.get(
            "total_dimensions",
            len(
                aggregation_results.get(
                    "dimensions",
                    {},
                )
            ),
        )

        total_pillars = metadata.get(
            "total_pillars",
            len(
                aggregation_results.get(
                    "pillars",
                    {},
                )
            ),
        )

        critical_count = sum(
            1
            for result in priority_results
            if _normalize_priority(
                _get(
                    result,
                    "priority_category",
                    _get(
                        result,
                        "priority",
                        "",
                    ),
                )
            )
            == "Critical"
        )

        high_count = sum(
            1
            for result in priority_results
            if _normalize_priority(
                _get(
                    result,
                    "priority_category",
                    _get(
                        result,
                        "priority",
                        "",
                    ),
                )
            )
            == "High"
        )

        roadmap_count = sum(
            len(
                _get(
                    phase,
                    "items",
                    [],
                )
                or []
            )
            for phase in roadmap
        )

        kpis = [
            [
                Paragraph(
                    _format_number(
                        dmi_score,
                        self.decimal_precision,
                    ),
                    self.styles["kpi"],
                ),
                Paragraph(
                    _safe_str(
                        dmi_level,
                        "—",
                    ),
                    self.styles["kpi"],
                ),
                Paragraph(
                    str(total_indicators),
                    self.styles["kpi"],
                ),
                Paragraph(
                    str(total_dimensions),
                    self.styles["kpi"],
                ),
            ],
            [
                Paragraph(
                    "Digital Maturity Index",
                    self.styles["kpi_label"],
                ),
                Paragraph(
                    "Maturity Level",
                    self.styles["kpi_label"],
                ),
                Paragraph(
                    "Indicators",
                    self.styles["kpi_label"],
                ),
                Paragraph(
                    "Dimensions",
                    self.styles["kpi_label"],
                ),
            ],
        ]

        table = Table(
            kpis,
            colWidths=[
                43 * mm,
                43 * mm,
                43 * mm,
                43 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        GREY_100,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        GREY_200,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        GREY_200,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, 0),
                        10,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        10,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        summary_rows = [
            [
                Paragraph(
                    "<b>Metric</b>",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "<b>Value</b>",
                    self.styles["table_header"],
                ),
            ],
            [
                Paragraph(
                    "Pillars assessed",
                    self.styles["table"],
                ),
                Paragraph(
                    str(total_pillars),
                    self.styles["table"],
                ),
            ],
            [
                Paragraph(
                    "Critical priorities",
                    self.styles["table"],
                ),
                Paragraph(
                    str(critical_count),
                    self.styles["table"],
                ),
            ],
            [
                Paragraph(
                    "High priorities",
                    self.styles["table"],
                ),
                Paragraph(
                    str(high_count),
                    self.styles["table"],
                ),
            ],
            [
                Paragraph(
                    "Roadmap actions",
                    self.styles["table"],
                ),
                Paragraph(
                    str(roadmap_count),
                    self.styles["table"],
                ),
            ],
        ]

        table = Table(
            summary_rows,
            colWidths=[
                90 * mm,
                80 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        JESA_GREEN,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        GREY_200,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [WHITE, GREY_100],
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

        return story

    # ========================================================================
    # DMI
    # ========================================================================

    def _build_dmi_overview(
        self,
        aggregation_results: Dict[str, Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "2. Digital Maturity Overview",
                self.styles["h1"],
            )
        )

        dmi = aggregation_results.get("dmi")

        if dmi is None:

            metadata = aggregation_results.get(
                "metadata",
                {},
            )

            score = metadata.get(
                "dmi_score",
                aggregation_results.get(
                    "dmi_score"
                ),
            )

            level = metadata.get(
                "dmi_level_name",
                metadata.get(
                    "dmi_level",
                    "—",
                ),
            )

        else:

            score = _get(
                dmi,
                "score",
                None,
            )

            level = _get(
                dmi,
                "level_name",
                _get(
                    dmi,
                    "level",
                    "—",
                ),
            )

        data = [
            [
                Paragraph(
                    "Digital Maturity Index",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Score",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Maturity Level",
                    self.styles["table_header"],
                ),
            ],
            [
                Paragraph(
                    "DMI",
                    self.styles["table"],
                ),
                Paragraph(
                    _format_number(
                        score,
                        self.decimal_precision,
                    ),
                    self.styles["table"],
                ),
                Paragraph(
                    _safe_str(level),
                    self.styles["table"],
                ),
            ],
        ]

        table = Table(
            data,
            colWidths=[
                70 * mm,
                40 * mm,
                60 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        JESA_GREEN,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        GREY_200,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, 1),
                        GREY_100,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

        story.append(table)

        return story

    # ========================================================================
    # PILLARS
    # ========================================================================

    def _build_pillar_assessment(
        self,
        aggregation_results: Dict[str, Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "3. Pillar Assessment",
                self.styles["h1"],
            )
        )

        rows = [
            [
                Paragraph(
                    "Pillar",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Score",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Level",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Applicability",
                    self.styles["table_header"],
                ),
            ]
        ]

        pillars = aggregation_results.get(
            "pillars",
            {},
        )

        iterable = (
            pillars.values()
            if isinstance(pillars, Mapping)
            else pillars
        )

        for result in iterable:

            rows.append(
                [
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "entity_name",
                                _get(
                                    result,
                                    "name",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "score",
                            ),
                            self.decimal_precision,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "level_name",
                                _get(
                                    result,
                                    "level",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "applicability",
                                "—",
                            )
                        ),
                        self.styles["table"],
                    ),
                ]
            )

        if len(rows) == 1:

            rows.append(
                [
                    Paragraph(
                        "No pillar results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            rows,
            colWidths=[
                80 * mm,
                30 * mm,
                40 * mm,
                30 * mm,
                ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        JESA_GREEN,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        GREY_200,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [WHITE, GREY_100],
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

        story.append(table)

        return story

    # ========================================================================
    # DIMENSIONS
    # ========================================================================

    def _build_dimension_assessment(
        self,
        aggregation_results: Dict[str, Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "4. Dimension Assessment",
                self.styles["h1"],
            )
        )

        rows = [
            [
                Paragraph(
                    "ID",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Dimension",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Score",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Level",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Pillar",
                    self.styles["table_header"],
                ),
            ]
        ]

        dimensions = aggregation_results.get(
            "dimensions",
            {},
        )

        iterable = (
            dimensions.values()
            if isinstance(dimensions, Mapping)
            else dimensions
        )

        for result in iterable:

            rows.append(
                [
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "entity_id",
                                _get(
                                    result,
                                    "id",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "entity_name",
                                _get(
                                    result,
                                    "name",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "score",
                            ),
                            self.decimal_precision,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "level_name",
                                _get(
                                    result,
                                    "level",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "parent_id",
                                "—",
                            )
                        ),
                        self.styles["table"],
                    ),
                ]
            )

        if len(rows) == 1:

            rows.append(
                [
                    "",
                    Paragraph(
                        "No dimension results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            rows,
            colWidths=[
                20 * mm,
                75 * mm,
                25 * mm,
                40 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        JESA_GREEN,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        GREY_200,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [WHITE, GREY_100],
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "LEFT",
                    ),
                ]
            )
        )

        story.append(table)

        return story

    # ========================================================================
    # GAP ANALYSIS
    # ========================================================================

    def _build_gap_analysis(
        self,
        gap_results: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "5. Gap Analysis",
                self.styles["h1"],
            )
        )

        rows = [
            [
                Paragraph(
                    "Entity",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Type",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Current",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Target",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Gap",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Priority",
                    self.styles["table_header"],
                ),
            ]
        ]

        for gap in gap_results:

            priority = _normalize_priority(
                _get(
                    gap,
                    "priority",
                    "",
                )
            )

            rows.append(
                [
                    Paragraph(
                        _safe_str(
                            _get(
                                gap,
                                "entity_name",
                                "—",
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                gap,
                                "entity_type",
                                "—",
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                gap,
                                "current_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                gap,
                                "target_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                gap,
                                "gap",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        priority or "—",
                        self.styles["table"],
                    ),
                ]
            )

        if len(rows) == 1:

            rows.append(
                [
                    Paragraph(
                        "No gap analysis results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            rows,
            colWidths=[
                60 * mm,
                30 * mm,
                25 * mm,
                25 * mm,
                25 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        style_commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                JESA_GREEN,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                GREY_200,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GREY_100],
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER",
            ),
        ]

        # Priority cell backgrounds
        for row_index in range(1, len(rows)):

            priority = _normalize_priority(
                _get(
                    gap_results[row_index - 1]
                    if row_index - 1 < len(gap_results)
                    else None,
                    "priority",
                    "",
                )
            )

            if priority:

                style_commands.append(
                    (
                        "BACKGROUND",
                        (5, row_index),
                        (5, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    style_commands.append(
                        (
                            "TEXTCOLOR",
                            (5, row_index),
                            (5, row_index),
                            WHITE,
                        )
                    )

                style_commands.append(
                    (
                        "FONTNAME",
                        (5, row_index),
                        (5, row_index),
                        "Helvetica-Bold",
                    )
                )

        table.setStyle(
            TableStyle(style_commands)
        )

        story.append(table)

        return story

    # ========================================================================
    # TPI
    # ========================================================================

    def _build_tpi_prioritization(
        self,
        tpi_results: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "6. TPI Prioritization",
                self.styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "Transformation opportunities ranked according "
                "to their Transformation Priority Index (TPI).",
                self.styles["body"],
            )
        )

        # IMPORTANT:
        # Sorting is ONLY based on TPI score here.
        # Priority labels are displayed from the already-computed
        # decision engine result and are NOT recomputed in PDF.
        sorted_results = sorted(
            tpi_results,
            key=lambda item: _safe_float(
                _get(
                    item,
                    "tpi_score",
                    0,
                )
            ),
            reverse=True,
        )

        rows = [
            [
                Paragraph(
                    "#",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Dimension",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "TPI",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Priority",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Gap",
                    self.styles["table_header"],
                ),
            ]
        ]

        for rank, item in enumerate(
            sorted_results,
            start=1,
        ):

            priority = _normalize_priority(
                _get(
                    item,
                    "priority_category",
                    _get(
                        item,
                        "priority",
                        "",
                    ),
                )
            )

            rows.append(
                [
                    Paragraph(
                        str(rank),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                item,
                                "dimension_name",
                                _get(
                                    item,
                                    "dimension_id",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                item,
                                "tpi_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        priority or "—",
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                item,
                                "gap",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                ]
            )

        if len(rows) == 1:

            rows.append(
                [
                    "",
                    Paragraph(
                        "No TPI results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            rows,
            colWidths=[
                12 * mm,
                90 * mm,
                25 * mm,
                30 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        style_commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                JESA_GREEN,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                GREY_200,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GREY_100],
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER",
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER",
            ),
        ]

        for row_index, item in enumerate(
            sorted_results,
            start=1,
        ):

            priority = _normalize_priority(
                _get(
                    item,
                    "priority_category",
                    _get(
                        item,
                        "priority",
                        "",
                    ),
                )
            )

            if priority:

                style_commands.append(
                    (
                        "BACKGROUND",
                        (3, row_index),
                        (3, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    style_commands.append(
                        (
                            "TEXTCOLOR",
                            (3, row_index),
                            (3, row_index),
                            WHITE,
                        )
                    )

                style_commands.append(
                    (
                        "FONTNAME",
                        (3, row_index),
                        (3, row_index),
                        "Helvetica-Bold",
                    )
                )

        table.setStyle(
            TableStyle(style_commands)
        )

        story.append(table)

        return story

    # ========================================================================
    # PRIORITY MATRIX
    # ========================================================================

    def _build_priority_matrix(
        self,
        priority_results: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "7. Priority Matrix",
                self.styles["h1"],
            )
        )

        # Priority order first, TPI second.
        sorted_results = sorted(
            priority_results,
            key=lambda item: (
                PRIORITY_RANK.get(
                    _normalize_priority(
                        _get(
                            item,
                            "priority_category",
                            _get(
                                item,
                                "priority",
                                "",
                            ),
                        )
                    ),
                    99,
                ),
                -_safe_float(
                    _get(
                        item,
                        "tpi_score",
                        0,
                    )
                ),
                -_safe_float(
                    _get(
                        item,
                        "gap",
                        0,
                    )
                ),
            ),
        )

        rows = [
            [
                Paragraph(
                    "Rank",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Dimension",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Current",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Target",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Gap",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "TPI",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Priority",
                    self.styles["table_header"],
                ),
            ]
        ]

        for rank, result in enumerate(
            sorted_results,
            start=1,
        ):

            priority = _normalize_priority(
                _get(
                    result,
                    "priority_category",
                    _get(
                        result,
                        "priority",
                        "",
                    ),
                )
            )

            rows.append(
                [
                    Paragraph(
                        str(rank),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(
                            _get(
                                result,
                                "dimension_name",
                                _get(
                                    result,
                                    "dimension_id",
                                    "—",
                                ),
                            )
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "current_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "target_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "gap",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _format_number(
                            _get(
                                result,
                                "tpi_score",
                            ),
                            1,
                        ),
                        self.styles["table"],
                    ),
                    Paragraph(
                        priority or "—",
                        self.styles["table"],
                    ),
                ]
            )

        if len(rows) == 1:

            rows.append(
                [
                    "",
                    Paragraph(
                        "No priority results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )

        table = Table(
            rows,
            colWidths=[
                14 * mm,
                65 * mm,
                22 * mm,
                22 * mm,
                22 * mm,
                22 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        style_commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                JESA_GREEN,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                GREY_200,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GREY_100],
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER",
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER",
            ),
        ]

        for row_index, result in enumerate(
            sorted_results,
            start=1,
        ):

            priority = _normalize_priority(
                _get(
                    result,
                    "priority_category",
                    _get(
                        result,
                        "priority",
                        "",
                    ),
                )
            )

            if priority:

                style_commands.append(
                    (
                        "BACKGROUND",
                        (6, row_index),
                        (6, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    style_commands.append(
                        (
                            "TEXTCOLOR",
                            (6, row_index),
                            (6, row_index),
                            WHITE,
                        )
                    )

                style_commands.append(
                    (
                        "FONTNAME",
                        (6, row_index),
                        (6, row_index),
                        "Helvetica-Bold",
                    )
                )

        table.setStyle(
            TableStyle(style_commands)
        )

        story.append(table)

        return story

    # ========================================================================
    # ROADMAP
    # ========================================================================

    def _build_transformation_roadmap(
        self,
        roadmap: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "8. Transformation Roadmap",
                self.styles["h1"],
            )
        )

        if not roadmap:

            story.append(
                Paragraph(
                    "No transformation roadmap is available.",
                    self.styles["body"],
                )
            )

            return story

        sorted_phases = sorted(
            roadmap,
            key=lambda phase: PHASE_ORDER.get(
                _safe_str(
                    _get(
                        phase,
                        "phase_name",
                        "",
                    )
                ),
                99,
            ),
        )

        for phase in sorted_phases:

            phase_name = _safe_str(
                _get(
                    phase,
                    "phase_name",
                    "Phase",
                )
            )

            horizon = _safe_str(
                _get(
                    phase,
                    "horizon",
                    "",
                )
            )

            story.append(
                Paragraph(
                    f"{phase_name}"
                    + (
                        f" — {horizon}"
                        if horizon
                        else ""
                    ),
                    self.styles["h2"],
                )
            )

            items = _get(
                phase,
                "items",
                [],
            ) or []

            rows = [
                [
                    Paragraph(
                        "Action",
                        self.styles["table_header"],
                    ),
                    Paragraph(
                        "Dimension",
                        self.styles["table_header"],
                    ),
                    Paragraph(
                        "Priority",
                        self.styles["table_header"],
                    ),
                    Paragraph(
                        "TPI",
                        self.styles["table_header"],
                    ),
                    Paragraph(
                        "Impact",
                        self.styles["table_header"],
                    ),
                ]
            ]

            for item in items:

                priority = _normalize_priority(
                    _get(
                        item,
                        "priority",
                        "",
                    )
                )

                rows.append(
                    [
                        Paragraph(
                            _safe_str(
                                _get(
                                    item,
                                    "title",
                                    "—",
                                )
                            ),
                            self.styles["table"],
                        ),
                        Paragraph(
                            _safe_str(
                                _get(
                                    item,
                                    "dimension_id",
                                    "—",
                                )
                            ),
                            self.styles["table"],
                        ),
                        Paragraph(
                            priority or "—",
                            self.styles["table"],
                        ),
                        Paragraph(
                            _format_number(
                                _get(
                                    item,
                                    "tpi_score",
                                ),
                                1,
                            ),
                            self.styles["table"],
                        ),
                        Paragraph(
                            _safe_str(
                                _get(
                                    item,
                                    "expected_impact",
                                    "—",
                                )
                            ),
                            self.styles["table"],
                        ),
                    ]
                )

            if len(rows) == 1:

                rows.append(
                    [
                        Paragraph(
                            "No actions in this phase.",
                            self.styles["table"],
                        ),
                        "",
                        "",
                        "",
                        "",
                    ]
                )

            table = Table(
                rows,
                colWidths=[
                    72 * mm,
                    27 * mm,
                    27 * mm,
                    22 * mm,
                    32 * mm,
                ],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            JESA_GREEN,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            GREY_200,
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [WHITE, GREY_100],
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (3, -1),
                            "CENTER",
                        ),
                    ]
                )
            )

            story.append(table)

            story.append(
                Spacer(
                    1,
                    5 * mm,
                )
            )

        return story

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    def _build_recommendations(
        self,
        priority_results: List[Any],
        roadmap: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "9. Recommendations",
                self.styles["h1"],
            )
        )

        recommendation_count = 0

        for priority in priority_results:

            recommendations = _get(
                priority,
                "recommendations",
                [],
            ) or []

            if not recommendations:
                continue

            dimension_name = _safe_str(
                _get(
                    priority,
                    "dimension_name",
                    _get(
                        priority,
                        "dimension_id",
                        "Dimension",
                    ),
                )
            )

            priority_category = _normalize_priority(
                _get(
                    priority,
                    "priority_category",
                    _get(
                        priority,
                        "priority",
                        "",
                    ),
                )
            )

            story.append(
                Paragraph(
                    dimension_name,
                    self.styles["h2"],
                )
            )

            for recommendation in recommendations:

                recommendation_count += 1

                title = _safe_str(
                    _get(
                        recommendation,
                        "title",
                        "Recommendation",
                    )
                )

                effort = _safe_str(
                    _get(
                        recommendation,
                        "effort",
                        "—",
                    )
                )

                impact = _safe_str(
                    _get(
                        recommendation,
                        "expected_impact",
                        "—",
                    )
                )

                detailed_actions = _get(
                    recommendation,
                    "detailed_actions",
                    [],
                ) or []

                content = (
                    f"<b>{recommendation_count}. "
                    f"{title}</b><br/>"
                    f"<b>Priority:</b> "
                    f"{priority_category or '—'}"
                    f"<br/>"
                    f"<b>Effort:</b> {effort}"
                    f"<br/>"
                    f"<b>Expected Impact:</b> {impact}"
                )

                if detailed_actions:

                    content += (
                        "<br/><b>Actions:</b><br/>"
                    )

                    content += "<br/>".join(
                        f"• {_safe_str(action)}"
                        for action in detailed_actions
                    )

                story.append(
                    Paragraph(
                        content,
                        self.styles["body"],
                    )
                )

                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.4,
                        color=GREY_200,
                        spaceBefore=2,
                        spaceAfter=5,
                    )
                )

        # Fallback to roadmap recommendations.
        if recommendation_count == 0:

            for phase in roadmap:

                items = _get(
                    phase,
                    "items",
                    [],
                ) or []

                for item in items:

                    title = _safe_str(
                        _get(
                            item,
                            "title",
                            "",
                        )
                    )

                    if not title:
                        continue

                    recommendation_count += 1

                    priority = _normalize_priority(
                        _get(
                            item,
                            "priority",
                            "",
                        )
                    )

                    story.append(
                        Paragraph(
                            f"<b>{recommendation_count}. "
                            f"{title}</b><br/>"
                            f"<b>Phase:</b> "
                            f"{_safe_str(_get(phase, 'phase_name', '—'))}"
                            f"<br/>"
                            f"<b>Priority:</b> "
                            f"{priority or '—'}"
                            f"<br/>"
                            f"<b>Expected Impact:</b> "
                            f"{_safe_str(_get(item, 'expected_impact', '—'))}",
                            self.styles["body"],
                        )
                    )

        if recommendation_count == 0:

            story.append(
                Paragraph(
                    "No recommendations are available.",
                    self.styles["body"],
                )
            )

        return story

    # ========================================================================
    # METADATA
    # ========================================================================

    def _build_metadata(
        self,
        aggregation_results: Dict[str, Any],
        assessment_id: Optional[str],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "10. Assessment Metadata",
                self.styles["h1"],
            )
        )

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        rows = [
            [
                Paragraph(
                    "Field",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Value",
                    self.styles["table_header"],
                ),
            ]
        ]

        fields = [
            (
                "Assessment ID",
                assessment_id
                or metadata.get(
                    "assessment_id",
                    "—",
                ),
            ),
            (
                "Site ID",
                metadata.get(
                    "site_id",
                    "—",
                ),
            ),
            (
                "Site Name",
                metadata.get(
                    "site_name",
                    "—",
                ),
            ),
            (
                "Assessment Date",
                metadata.get(
                    "assessment_date",
                    "—",
                ),
            ),
            (
                "Evaluator",
                metadata.get(
                    "evaluator",
                    "—",
                ),
            ),
            (
                "Report Version",
                metadata.get(
                    "report_version",
                    "1.0",
                ),
            ),
            (
                "Generated At",
                self.generated_at.strftime(
                    "%Y-%m-%d %H:%M"
                ),
            ),
            (
                "Total Indicators",
                metadata.get(
                    "total_indicators",
                    0,
                ),
            ),
            (
                "Total Subdimensions",
                metadata.get(
                    "total_subdimensions",
                    0,
                ),
            ),
            (
                "Total Dimensions",
                metadata.get(
                    "total_dimensions",
                    0,
                ),
            ),
            (
                "Total Pillars",
                metadata.get(
                    "total_pillars",
                    0,
                ),
            ),
            (
                "DMI Score",
                metadata.get(
                    "dmi_score",
                    "—",
                ),
            ),
            (
                "DMI Level",
                metadata.get(
                    "dmi_level",
                    "—",
                ),
            ),
            (
                "DMI Level Name",
                metadata.get(
                    "dmi_level_name",
                    "—",
                ),
            ),
        ]

        for field, value in fields:

            rows.append(
                [
                    Paragraph(
                        _safe_str(field),
                        self.styles["table"],
                    ),
                    Paragraph(
                        _safe_str(value),
                        self.styles["table"],
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                60 * mm,
                100 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        JESA_GREEN,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        GREY_200,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [WHITE, GREY_100],
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        story.append(
            Paragraph(
                "End of Report",
                self.styles["subtitle"],
            )
        )

        return story


# ============================================================================
# PUBLIC UTILITY FUNCTIONS
# ============================================================================


def export_to_pdf(
    results: Dict[str, Any],
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    """
    Export aggregation results to PDF.
    """

    exporter = PDFExporter()

    return exporter.export_assessment_results(
        aggregation_results=results,
        assessment_id=assessment_id,
        output_path=output_path,
    )


def export_full_analysis(
    aggregation_results: Dict[str, Any],
    gap_results: List[Any],
    tpi_results: List[Any],
    priority_results: List[Any],
    roadmap: List[Any],
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    """
    Export the complete assessment and decision analysis to PDF.
    """

    exporter = PDFExporter()

    return exporter.export_assessment_results(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_path=output_path,
        assessment_id=assessment_id,
    ) 