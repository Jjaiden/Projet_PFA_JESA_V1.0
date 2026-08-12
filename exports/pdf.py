"""
pdf.py
======

Professional Industrial Digital Maturity Assessment PDF exporter.

IMPORTANT
---------
This module ONLY formats and presents already-computed assessment results.

It does NOT calculate:
    - scores
    - DMI
    - gaps
    - TPI
    - priorities
    - roadmap phases

The PDF is intentionally SCORE-FOCUSED.

The detailed report is handled separately by report.py.

Expected input:
    aggregation_results
    gap_results
    tpi_results
    priority_results
    roadmap

Public API:
    PDFExporter.export_assessment_results()
    export_to_pdf()
    export_full_analysis()
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
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
# BRAND
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
# PROJECT ROOT / LOGOS
# ============================================================================

def _project_root() -> Path:
    """
    Return the repository root.

    pdf.py is located in:
        <project_root>/exports/pdf.py

    Therefore:
        parent      = exports
        parent.parent = project root
    """
    return Path(__file__).resolve().parent.parent


def _find_logo(filename: str) -> Optional[Path]:
    """
    Locate a real project logo.

    The repository currently stores the logos in:

        assets/logos/logo_ensam.png
        assets/logos/logo_jesa.png

    The lookup is based on __file__, NOT on Path.cwd(), so it works
    correctly when Streamlit is launched from another directory.
    """

    root = _project_root()

    candidates = [
        root / "assets" / "logos" / filename,
        root / "assets" / "logo" / filename,
        root / "assets" / filename,
    ]

    for path in candidates:
        if path.is_file():
            return path

    return None


ENSAM_LOGO = _find_logo("logo_ensam.png")
JESA_LOGO = _find_logo("logo_jesa.png")


# ============================================================================
# SAFE HELPERS
# ============================================================================

def _get(
    obj: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Read a value from either:
        - a dictionary / Mapping
        - an object attribute
    """

    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _safe_str(
    value: Any,
    default: str = "",
) -> str:
    if value is None:
        return default

    return str(value)


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
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


def _normalize_priority(
    priority: Any,
) -> str:

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


def _as_list(value: Any) -> List[Any]:
    """
    Safely convert common collection structures to a list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, Mapping):
        return list(value.values())

    return [value]


def _escape_xml(value: Any) -> str:
    """
    Escape values inserted into ReportLab Paragraph markup.
    """

    text = _safe_str(value)

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================================
# PDF EXPORTER
# ============================================================================

class PDFExporter:
    """
    Professional score-focused PDF exporter.

    This exporter presents already-computed results.

    It never recalculates assessment values.
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

        aggregation_results = (
            aggregation_results
            if isinstance(aggregation_results, Mapping)
            else {}
        )

        gap_results = _as_list(gap_results)
        tpi_results = _as_list(tpi_results)
        priority_results = _as_list(priority_results)
        roadmap = _as_list(roadmap)

        # ------------------------------------------------------------------
        # OUTPUT
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
        # METADATA
        # ------------------------------------------------------------------

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        if not isinstance(metadata, Mapping):
            metadata = {}

        # ------------------------------------------------------------------
        # DOCUMENT
        # ------------------------------------------------------------------

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title="Industrial Digital Maturity Assessment",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment - Scoring",
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="main_frame",
        )

        page_template = PageTemplate(
            id="AssessmentPDF",
            frames=frame,
            onPage=self._draw_page_header_footer,
        )

        doc.addPageTemplates([page_template])

        story: List[Any] = []

        # ------------------------------------------------------------------
        # COVER
        # ------------------------------------------------------------------

        story.extend(
            self._build_cover_page(
                metadata,
                assessment_id,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # EXECUTIVE SCORING SUMMARY
        # ------------------------------------------------------------------

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

        # ------------------------------------------------------------------
        # DMI
        # ------------------------------------------------------------------

        story.extend(
            self._build_dmi_overview(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # PILLARS
        # ------------------------------------------------------------------

        story.extend(
            self._build_pillar_assessment(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # DIMENSIONS
        # ------------------------------------------------------------------

        story.extend(
            self._build_dimension_assessment(
                aggregation_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # GAPS
        # ------------------------------------------------------------------

        story.extend(
            self._build_gap_analysis(
                gap_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # TPI
        # ------------------------------------------------------------------

        story.extend(
            self._build_tpi_prioritization(
                tpi_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # PRIORITY MATRIX
        # ------------------------------------------------------------------

        story.extend(
            self._build_priority_matrix(
                priority_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # ROADMAP - SCORE SUMMARY ONLY
        # ------------------------------------------------------------------

        story.extend(
            self._build_transformation_roadmap(
                roadmap,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # SCORING CONCLUSION
        # ------------------------------------------------------------------

        story.extend(
            self._build_scoring_conclusion(
                aggregation_results,
                priority_results,
            )
        )

        story.append(PageBreak())

        # ------------------------------------------------------------------
        # METADATA
        # ------------------------------------------------------------------

        story.extend(
            self._build_metadata(
                aggregation_results,
                assessment_id,
            )
        )

        # ------------------------------------------------------------------
        # BUILD
        # ------------------------------------------------------------------

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

            "cover_label": ParagraphStyle(
                "CoverLabel",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=JESA_DARK,
            ),
        }

    # ========================================================================
    # HEADER / FOOTER
    # ========================================================================

    def _draw_page_header_footer(
        self,
        canvas,
        doc,
    ) -> None:

        canvas.saveState()

        width, height = A4

        # Header: pages after cover
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
            (
                "JESA DMAT • Generated "
                f"{self.generated_at.strftime('%Y-%m-%d %H:%M')}"
            ),
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

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        # ------------------------------------------------------------------
        # REAL LOGOS
        # ------------------------------------------------------------------

        logo_cells = [
            self._logo_or_empty(
                ENSAM_LOGO,
                width=43 * mm,
                height=25 * mm,
            ),
            self._logo_or_empty(
                JESA_LOGO,
                width=43 * mm,
                height=25 * mm,
            ),
        ]

        logo_table = Table(
            [logo_cells],
            colWidths=[
                75 * mm,
                75 * mm,
            ],
            hAlign="CENTER",
        )

        logo_table.setStyle(
            TableStyle(
                [
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
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
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        story.append(logo_table)

        story.append(
            Spacer(
                1,
                24 * mm,
            )
        )

        # ------------------------------------------------------------------
        # TITLE
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "INDUSTRIAL DIGITAL<br/>MATURITY ASSESSMENT",
                self.styles["title"],
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        story.append(
            Paragraph(
                "Digital Maturity Assessment Tool",
                self.styles["subtitle"],
            )
        )

        story.append(
            Spacer(
                1,
                14 * mm,
            )
        )

        # ------------------------------------------------------------------
        # INFO
        # ------------------------------------------------------------------

        site_name = _get(
            metadata,
            "site_name",
            "Industrial Plant",
        )

        identifier = (
            assessment_id
            or _get(
                metadata,
                "assessment_id",
                "N/A",
            )
        )

        assessment_date = _get(
            metadata,
            "assessment_date",
            self.generated_at.strftime("%d %B %Y"),
        )

        info_data = [

            [
                Paragraph(
                    "Assessment ID",
                    self.styles["cover_label"],
                ),
                Paragraph(
                    _escape_xml(identifier),
                    self.styles["body"],
                ),
            ],

            [
                Paragraph(
                    "Site",
                    self.styles["cover_label"],
                ),
                Paragraph(
                    _escape_xml(site_name),
                    self.styles["body"],
                ),
            ],

            [
                Paragraph(
                    "Assessment Date",
                    self.styles["cover_label"],
                ),
                Paragraph(
                    _escape_xml(assessment_date),
                    self.styles["body"],
                ),
            ],

            [
                Paragraph(
                    "Generated",
                    self.styles["cover_label"],
                ),
                Paragraph(
                    self.generated_at.strftime(
                        "%d %B %Y"
                    ),
                    self.styles["body"],
                ),
            ],
        ]

        info_table = Table(
            info_data,
            colWidths=[
                45 * mm,
                95 * mm,
            ],
            hAlign="CENTER",
        )

        info_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        JESA_LIGHT,
                    ),
                    (
                        "GRID",
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
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(info_table)

        story.append(
            Spacer(
                1,
                30 * mm,
            )
        )

        story.append(
            HRFlowable(
                width="80%",
                thickness=1,
                color=JESA_GREEN,
                hAlign="CENTER",
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        story.append(
            Paragraph(
                "Scoring & Digital Maturity Assessment Results",
                self.styles["subtitle"],
            )
        )

        return story

    # ========================================================================
    # LOGO HELPER
    # ========================================================================

    @staticmethod
    def _logo_or_empty(
        path: Optional[Path],
        width: float,
        height: float,
    ):

        if path is None:
            # IMPORTANT:
            # Do NOT write "ENSAM" / "JESA" as fake logos.
            # If the real file cannot be found, leave the cell empty.
            return Spacer(
                width,
                height,
            )

        try:

            image = Image(
                str(path),
                width=width,
                height=height,
                kind="proportional",
            )

            image.hAlign = "CENTER"

            return image

        except Exception:
            return Spacer(
                width,
                height,
            )

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
                "1. Executive Scoring Summary",
                self.styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "This section presents the principal scoring results "
                "generated by the Digital Maturity Assessment Tool. "
                "All values shown below are already-computed assessment "
                "results.",
                self.styles["body"],
            )
        )

        dmi = aggregation_results.get(
            "dmi"
        )

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

        if not isinstance(metadata, Mapping):
            metadata = {}

        total_indicators = metadata.get(
            "total_indicators",
            len(
                aggregation_results.get(
                    "indicators",
                    {},
                )
                or {}
            ),
        )

        total_dimensions = metadata.get(
            "total_dimensions",
            len(
                aggregation_results.get(
                    "dimensions",
                    {},
                )
                or {}
            ),
        )

        total_pillars = metadata.get(
            "total_pillars",
            len(
                aggregation_results.get(
                    "pillars",
                    {},
                )
                or {}
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

        roadmap_count = 0

        for phase in roadmap:

            items = _get(
                phase,
                "items",
                [],
            )

            roadmap_count += len(
                _as_list(items)
            )

        # ------------------------------------------------------------------
        # KPI CARDS
        # ------------------------------------------------------------------

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
                    _escape_xml(
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
                8 * mm,
            )
        )

        # ------------------------------------------------------------------
        # SUMMARY TABLE
        # ------------------------------------------------------------------

        rows = [

            [
                Paragraph(
                    "Metric",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Value",
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
                    "Transformation actions",
                    self.styles["table"],
                ),
                Paragraph(
                    str(roadmap_count),
                    self.styles["table"],
                ),
            ],
        ]

        table = Table(
            rows,
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
                "2. Digital Maturity Index",
                self.styles["h1"],
            )
        )

        dmi = aggregation_results.get(
            "dmi"
        )

        if dmi is None:

            metadata = aggregation_results.get(
                "metadata",
                {},
            )

            if not isinstance(metadata, Mapping):
                metadata = {}

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

        story.append(
            Paragraph(
                "Overall digital maturity score",
                self.styles["h2"],
            )
        )

        data = [

            [
                Paragraph(
                    "Indicator",
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
                    "Digital Maturity Index (DMI)",
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
                    _escape_xml(level),
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
                        "BACKGROUND",
                        (0, 1),
                        (-1, 1),
                        GREY_100,
                    ),
                    (
                        "GRID",
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
    # PILLARS
    # ========================================================================

    def _build_pillar_assessment(
        self,
        aggregation_results: Dict[str, Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "3. Pillar Scoring",
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
            else _as_list(pillars)
        )

        for result in iterable:

            rows.append(
                [

                    Paragraph(
                        _escape_xml(
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
                        _escape_xml(
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
                        _escape_xml(
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
                "4. Dimension Scoring",
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
            else _as_list(dimensions)
        )

        for result in iterable:

            rows.append(
                [

                    Paragraph(
                        _escape_xml(
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
                        _escape_xml(
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
                        _escape_xml(
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
                        _escape_xml(
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

        story.append(
            Paragraph(
                "Comparison between current maturity scores and "
                "target scores.",
                self.styles["body"],
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
                        _escape_xml(
                            _get(
                                gap,
                                "entity_name",
                                "—",
                            )
                        ),
                        self.styles["table"],
                    ),

                    Paragraph(
                        _escape_xml(
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
                        _escape_xml(
                            priority or "—"
                        ),
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

        commands = [
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

        for row_index, gap in enumerate(
            gap_results,
            start=1,
        ):

            priority = _normalize_priority(
                _get(
                    gap,
                    "priority",
                    "",
                )
            )

            if priority:

                commands.append(
                    (
                        "BACKGROUND",
                        (5, row_index),
                        (5, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    commands.append(
                        (
                            "TEXTCOLOR",
                            (5, row_index),
                            (5, row_index),
                            WHITE,
                        )
                    )

        table.setStyle(
            TableStyle(commands)
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
                "6. Transformation Priority Index",
                self.styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "Transformation opportunities ranked according "
                "to the already-computed Transformation Priority "
                "Index (TPI).",
                self.styles["body"],
            )
        )

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
                        _escape_xml(
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
                        _escape_xml(
                            priority or "—"
                        ),
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

        commands = [
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

                commands.append(
                    (
                        "BACKGROUND",
                        (3, row_index),
                        (3, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    commands.append(
                        (
                            "TEXTCOLOR",
                            (3, row_index),
                            (3, row_index),
                            WHITE,
                        )
                    )

        table.setStyle(
            TableStyle(commands)
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

        story.append(
            Paragraph(
                "Priorities are presented exactly as produced by "
                "the decision engine. No priority is recalculated "
                "by the PDF exporter.",
                self.styles["body"],
            )
        )

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
                        _escape_xml(
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
                        _escape_xml(
                            priority or "—"
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

        commands = [
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

                commands.append(
                    (
                        "BACKGROUND",
                        (6, row_index),
                        (6, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    commands.append(
                        (
                            "TEXTCOLOR",
                            (6, row_index),
                            (6, row_index),
                            WHITE,
                        )
                    )

        table.setStyle(
            TableStyle(commands)
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
                "8. Transformation Roadmap — Scoring View",
                self.styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "This section provides a concise scoring-oriented "
                "view of the transformation roadmap. Detailed "
                "implementation descriptions belong to the full Report.",
                self.styles["body"],
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
                    _escape_xml(
                        phase_name
                    )
                    + (
                        f" — {_escape_xml(horizon)}"
                        if horizon
                        else ""
                    ),
                    self.styles["h2"],
                )
            )

            items = _as_list(
                _get(
                    phase,
                    "items",
                    [],
                )
            )

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
                ]
            ]

            for item in items:

                priority = _normalize_priority(
                    _get(
                        item,
                        "priority",
                        _get(
                            item,
                            "priority_category",
                            "",
                        ),
                    )
                )

                rows.append(
                    [

                        Paragraph(
                            _escape_xml(
                                _get(
                                    item,
                                    "title",
                                    _get(
                                        item,
                                        "action",
                                        "—",
                                    ),
                                )
                            ),
                            self.styles["table"],
                        ),

                        Paragraph(
                            _escape_xml(
                                _get(
                                    item,
                                    "dimension_id",
                                    _get(
                                        item,
                                        "dimension_name",
                                        "—",
                                    ),
                                )
                            ),
                            self.styles["table"],
                        ),

                        Paragraph(
                            _escape_xml(
                                priority or "—"
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
                    ]
                )

            table = Table(
                rows,
                colWidths=[
                    82 * mm,
                    30 * mm,
                    30 * mm,
                    28 * mm,
                ],
                repeatRows=1,
            )

            commands = [
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

            for row_index, item in enumerate(
                items,
                start=1,
            ):

                priority = _normalize_priority(
                    _get(
                        item,
                        "priority",
                        _get(
                            item,
                            "priority_category",
                            "",
                        ),
                    )
                )

                if priority:

                    commands.append(
                        (
                            "BACKGROUND",
                            (2, row_index),
                            (2, row_index),
                            _priority_color(priority),
                        )
                    )

                    if priority != "Medium":

                        commands.append(
                            (
                                "TEXTCOLOR",
                                (2, row_index),
                                (2, row_index),
                                WHITE,
                            )
                        )

            table.setStyle(
                TableStyle(commands)
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
    # SCORING CONCLUSION
    # ========================================================================

    def _build_scoring_conclusion(
        self,
        aggregation_results: Dict[str, Any],
        priority_results: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "9. Scoring Conclusion",
                self.styles["h1"],
            )
        )

        dmi = aggregation_results.get(
            "dmi"
        )

        score = _get(
            dmi,
            "score",
            aggregation_results.get(
                "dmi_score"
            ),
        )

        level = _get(
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

        critical = sum(
            1
            for item in priority_results
            if _normalize_priority(
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
            == "Critical"
        )

        high = sum(
            1
            for item in priority_results
            if _normalize_priority(
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
            == "High"
        )

        story.append(
            Paragraph(
                (
                    "The assessed site achieved a Digital "
                    "Maturity Index of "
                    f"<b>{_escape_xml(_format_number(score, self.decimal_precision))}</b> "
                    f"with a maturity level of "
                    f"<b>{_escape_xml(level)}</b>."
                ),
                self.styles["body"],
            )
        )

        story.append(
            Paragraph(
                (
                    f"The decision analysis identifies "
                    f"<b>{critical}</b> critical-priority "
                    f"opportunities and <b>{high}</b> "
                    "high-priority opportunities."
                ),
                self.styles["body"],
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        story.append(
            Paragraph(
                "Important:",
                self.styles["h2"],
            )
        )

        story.append(
            Paragraph(
                "This PDF presents the scoring and prioritization "
                "results of the assessment. Detailed recommendations, "
                "implementation explanations, action descriptions and "
                "supporting analysis are intentionally reserved for "
                "the detailed Report document.",
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

        if not isinstance(metadata, Mapping):
            metadata = {}

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
                        _escape_xml(field),
                        self.styles["table"],
                    ),

                    Paragraph(
                        _escape_xml(value),
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

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
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

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        story.append(
            Paragraph(
                "End of Scoring Assessment",
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
    Export the complete score-focused assessment to PDF.
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