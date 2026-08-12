"""
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

The PDF is intentionally SCORE-FOCUSED and limited to a maximum
of two pages.

Detailed analysis belongs to the Excel report / detailed report.

Expected input:
- aggregation_results
- gap_results
- tpi_results
- priority_results
- roadmap

Public API:
- PDFExporter.export_assessment_results()
- export_to_pdf()
- export_full_analysis()
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


def _escape_xml(
    value: Any,
    default: Any = None,
) -> str:
    """
    Escape values inserted into ReportLab Paragraph markup.
    """

    text = _safe_str(
        value,
        _safe_str(default),
    )

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

    The exporter only presents already-computed values.

    Maximum PDF length:
        2 pages.
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

        # Roadmap is intentionally NOT displayed in the PDF,
        # but we keep it in the public API for compatibility.
        roadmap = _as_list(roadmap)

        # --------------------------------------------------------------------
        # OUTPUT
        # --------------------------------------------------------------------

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

        # --------------------------------------------------------------------
        # DOCUMENT
        # --------------------------------------------------------------------

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=17 * mm,
            bottomMargin=14 * mm,
            title="Industrial Digital Maturity Assessment",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment - Scores",
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

        # ====================================================================
        # PAGE 1
        # ====================================================================

        story.extend(
            self._build_page_one(
                aggregation_results,
                assessment_id,
            )
        )

        story.append(PageBreak())

        # ====================================================================
        # PAGE 2
        # ====================================================================

        story.extend(
            self._build_page_two(
                aggregation_results,
                gap_results,
                tpi_results,
                priority_results,
            )
        )

        # ====================================================================
        # BUILD
        # ====================================================================

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
                fontSize=17,
                leading=20,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
                spaceAfter=4,
            ),

            "subtitle": ParagraphStyle(
                "ReportSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                textColor=GREY_600,
                alignment=TA_CENTER,
                spaceAfter=5,
            ),

            "h1": ParagraphStyle(
                "SectionTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=15,
                textColor=JESA_DARK,
                spaceBefore=0,
                spaceAfter=5,
            ),

            "h2": ParagraphStyle(
                "SubSectionTitle",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=JESA_DARK,
                spaceBefore=4,
                spaceAfter=3,
            ),

            "body": ParagraphStyle(
                "Body",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=GREY_800,
                spaceAfter=3,
            ),

            "small": ParagraphStyle(
                "Small",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=6,
                leading=7,
                textColor=GREY_600,
            ),

            "kpi": ParagraphStyle(
                "KPI",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=17,
                leading=19,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
            ),

            "kpi_label": ParagraphStyle(
                "KPILabel",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=6.5,
                leading=8,
                textColor=GREY_600,
                alignment=TA_CENTER,
            ),

            "table": ParagraphStyle(
                "Table",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=5.8,
                leading=7,
                textColor=GREY_800,
            ),

            "table_header": ParagraphStyle(
                "TableHeader",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=5.8,
                leading=7,
                textColor=WHITE,
                alignment=TA_CENTER,
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

        # Header
        canvas.setStrokeColor(GREY_200)
        canvas.setLineWidth(0.5)

        canvas.line(
            12 * mm,
            height - 10 * mm,
            width - 12 * mm,
            height - 10 * mm,
        )

        canvas.setFont(
            "Helvetica-Bold",
            6.5,
        )

        canvas.setFillColor(
            JESA_DARK
        )

        canvas.drawString(
            12 * mm,
            height - 7.5 * mm,
            "JESA DMAT",
        )

        canvas.setFont(
            "Helvetica",
            6.5,
        )

        canvas.setFillColor(
            GREY_600
        )

        canvas.drawRightString(
            width - 12 * mm,
            height - 7.5 * mm,
            "Industrial Digital Maturity Assessment — Scoring",
        )

        # Footer
        canvas.setStrokeColor(GREY_200)

        canvas.line(
            12 * mm,
            8 * mm,
            width - 12 * mm,
            8 * mm,
        )

        canvas.setFont(
            "Helvetica",
            5.8,
        )

        canvas.setFillColor(
            GREY_600
        )

        canvas.drawString(
            12 * mm,
            4.5 * mm,
            (
                "JESA DMAT • Score-focused assessment"
            ),
        )

        canvas.drawRightString(
            width - 12 * mm,
            4.5 * mm,
            f"Page {doc.page} / 2",
        )

        canvas.restoreState()

    # ========================================================================
    # PAGE 1
    # ========================================================================

    def _build_page_one(
        self,
        aggregation_results: Dict[str, Any],
        assessment_id: Optional[str],
    ) -> List[Any]:

        story: List[Any] = []

        # --------------------------------------------------------------------
        # TITLE
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "INDUSTRIAL DIGITAL MATURITY ASSESSMENT",
                self.styles["title"],
            )
        )

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        if not isinstance(metadata, Mapping):
            metadata = {}

        site_name = metadata.get(
            "site_name",
            "Industrial Plant",
        )

        story.append(
            Paragraph(
                (
                    f"{_escape_xml(site_name)}"
                    f" • Assessment ID: "
                    f"{_escape_xml(assessment_id or metadata.get('assessment_id', 'N/A'))}"
                ),
                self.styles["subtitle"],
            )
        )

        # --------------------------------------------------------------------
        # DMI
        # --------------------------------------------------------------------

        dmi = aggregation_results.get("dmi")

        dmi_score = _get(
            dmi,
            "score",
            aggregation_results.get("dmi_score"),
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

        kpi_data = [
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
            ],
            [
                Paragraph(
                    "DIGITAL MATURITY INDEX",
                    self.styles["kpi_label"],
                ),
                Paragraph(
                    "MATURITY LEVEL",
                    self.styles["kpi_label"],
                ),
            ],
        ]

        kpi_table = Table(
            kpi_data,
            colWidths=[
                85 * mm,
                85 * mm,
            ],
        )

        kpi_table.setStyle(
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
                        0.8,
                        JESA_GREEN,
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
                        "TOPPADDING",
                        (0, 0),
                        (-1, 0),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 1),
                        (-1, 1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 1),
                        (-1, 1),
                        4,
                    ),
                ]
            )
        )

        story.append(kpi_table)

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        # --------------------------------------------------------------------
        # PILLAR SCORES
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "1. Pillar Scores",
                self.styles["h1"],
            )
        )

        pillars = aggregation_results.get(
            "pillars",
            {},
        )

        pillar_iterable = (
            pillars.values()
            if isinstance(pillars, Mapping)
            else _as_list(pillars)
        )

        pillar_rows = [
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
                    "Maturity Level",
                    self.styles["table_header"],
                ),
            ]
        ]

        for result in pillar_iterable:

            pillar_rows.append(
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
                ]
            )

        if len(pillar_rows) == 1:

            pillar_rows.append(
                [
                    Paragraph(
                        "No pillar results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                ]
            )

        pillar_table = Table(
            pillar_rows,
            colWidths=[
                90 * mm,
                35 * mm,
                45 * mm,
            ],
            repeatRows=1,
        )

        pillar_table.setStyle(
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
                        0.35,
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
                        3,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                ]
            )
        )

        story.append(pillar_table)

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        # --------------------------------------------------------------------
        # DIMENSION SCORES
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "2. Dimension Scores",
                self.styles["h1"],
            )
        )

        dimensions = aggregation_results.get(
            "dimensions",
            {},
        )

        dimension_iterable = (
            dimensions.values()
            if isinstance(dimensions, Mapping)
            else _as_list(dimensions)
        )

        dimension_rows = [
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
            ]
        ]

        for result in dimension_iterable:

            dimension_rows.append(
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
                ]
            )

        if len(dimension_rows) == 1:

            dimension_rows.append(
                [
                    "",
                    Paragraph(
                        "No dimension results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                ]
            )

        dimension_table = Table(
            dimension_rows,
            colWidths=[
                20 * mm,
                85 * mm,
                30 * mm,
                35 * mm,
            ],
            repeatRows=1,
        )

        dimension_table.setStyle(
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
                        0.35,
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
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2.5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2.5,
                    ),
                ]
            )
        )

        story.append(dimension_table)

        return story

    # ========================================================================
    # PAGE 2
    # ========================================================================

    def _build_page_two(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: List[Any],
        tpi_results: List[Any],
        priority_results: List[Any],
    ) -> List[Any]:

        story: List[Any] = []

        story.append(
            Paragraph(
                "3. Score-Based Transformation Analysis",
                self.styles["h1"],
            )
        )

        # --------------------------------------------------------------------
        # GAP ANALYSIS
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "Gap Scores",
                self.styles["h2"],
            )
        )

        gap_rows = [
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
            ]
        ]

        for gap in gap_results:

            gap_rows.append(
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
                ]
            )

        if len(gap_rows) == 1:

            gap_rows.append(
                [
                    Paragraph(
                        "No gap results available.",
                        self.styles["table"],
                    ),
                    "",
                    "",
                    "",
                    "",
                ]
            )

        gap_table = Table(
            gap_rows,
            colWidths=[
                65 * mm,
                30 * mm,
                25 * mm,
                25 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        gap_table.setStyle(
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
                        0.35,
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
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2.5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2.5,
                    ),
                ]
            )
        )

        story.append(gap_table)

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        # --------------------------------------------------------------------
        # TPI
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "Transformation Priority Index (TPI)",
                self.styles["h2"],
            )
        )

        sorted_tpi = sorted(
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

        tpi_rows = [
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
                    "Gap",
                    self.styles["table_header"],
                ),
                Paragraph(
                    "Priority",
                    self.styles["table_header"],
                ),
            ]
        ]

        for rank, item in enumerate(
            sorted_tpi,
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

            tpi_rows.append(
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
                        _format_number(
                            _get(
                                item,
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

        if len(tpi_rows) == 1:

            tpi_rows.append(
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

        tpi_table = Table(
            tpi_rows,
            colWidths=[
                12 * mm,
                80 * mm,
                25 * mm,
                25 * mm,
                28 * mm,
            ],
            repeatRows=1,
        )

        tpi_commands = [
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
                0.35,
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
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2.5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2.5,
            ),
        ]

        for row_index, item in enumerate(
            sorted_tpi,
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

                tpi_commands.append(
                    (
                        "BACKGROUND",
                        (4, row_index),
                        (4, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    tpi_commands.append(
                        (
                            "TEXTCOLOR",
                            (4, row_index),
                            (4, row_index),
                            WHITE,
                        )
                    )

        tpi_table.setStyle(
            TableStyle(tpi_commands)
        )

        story.append(tpi_table)

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        # --------------------------------------------------------------------
        # PRIORITY RESULTS
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "Priority Scores",
                self.styles["h2"],
            )
        )

        priority_rows = [
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

        def priority_sort_key(item):

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

            rank = {
                "Critical": 1,
                "High": 2,
                "Medium": 3,
                "Low": 4,
                "Very Low": 5,
            }.get(
                priority,
                99,
            )

            return (
                rank,
                -_safe_float(
                    _get(
                        item,
                        "tpi_score",
                        0,
                    )
                ),
            )

        sorted_priorities = sorted(
            priority_results,
            key=priority_sort_key,
        )

        for rank, result in enumerate(
            sorted_priorities,
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

            priority_rows.append(
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

        if len(priority_rows) == 1:

            priority_rows.append(
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

        priority_table = Table(
            priority_rows,
            colWidths=[
                12 * mm,
                58 * mm,
                21 * mm,
                21 * mm,
                21 * mm,
                21 * mm,
                26 * mm,
            ],
            repeatRows=1,
        )

        priority_commands = [
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
                0.35,
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
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
        ]

        for row_index, result in enumerate(
            sorted_priorities,
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

                priority_commands.append(
                    (
                        "BACKGROUND",
                        (6, row_index),
                        (6, row_index),
                        _priority_color(priority),
                    )
                )

                if priority != "Medium":

                    priority_commands.append(
                        (
                            "TEXTCOLOR",
                            (6, row_index),
                            (6, row_index),
                            WHITE,
                        )
                    )

        priority_table.setStyle(
            TableStyle(priority_commands)
        )

        story.append(priority_table)

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            Paragraph(
                (
                    "This document presents only the numerical "
                    "assessment results. Detailed recommendations, "
                    "roadmap actions and implementation guidance "
                    "are excluded from this score-focused PDF."
                ),
                self.styles["small"],
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

    The function keeps the same API for compatibility with the
    existing export service, while the PDF itself only contains
    score-focused information.
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