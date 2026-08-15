"""
report.py
=========

JESA DMAT - Complete Report Generator

This version fixes wide-table clipping in the complete PDF report.

Key fixes
---------
- Supports both A4 portrait and A4 landscape page templates.
- Automatically switches wide sections to landscape pages.
- Automatically scales supplied column widths to the available page width.
- Uses Paragraph cells so long text wraps instead of disappearing.
- Allows long table rows to split across pages when required.
- Repeats table headers on continuation pages.
- Removes the unused secondary BaseDocTemplate that previously existed
  inside Gap Analysis.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape as landscape_page
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from config import settings
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase
from engines.decision.tpi import TPIResult
from exports.excel import ExcelExporter
from exports.pdf import export_score_summary
from utils.file_manager import build_output_path, ensure_directory
from utils.helpers import translate_entity_name


logger = logging.getLogger(__name__)


# ============================================================================
# BRAND / DESIGN SYSTEM
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
# DATA STRUCTURES
# ============================================================================

@dataclass
class ReportMetadata:
    report_id: str
    assessment_id: str
    site_name: str
    generated_at: str
    report_version: str = "1.0"
    generator: str = "JESA DMAT"


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


# ============================================================================
# GENERIC HELPERS
# ============================================================================

def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Read a field from either a mapping or an object."""
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _safe_str(value: Any, default: str = "-") -> str:
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


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
    suffix: str = "",
) -> str:
    if value is None:
        return "-"

    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return f"{value}{suffix}"


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
    return mapping.get(normalized, str(priority))


def _priority_color(priority: Any) -> colors.Color:
    return PRIORITY_COLORS.get(
        _normalize_priority(priority),
        GREY_600,
    )


def _escape_xml(value: Any) -> str:
    text = _safe_str(value, "")
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, Mapping):
        return list(value.values())

    return [value]


def _join_values(value: Any) -> str:
    if value is None:
        return "-"

    if isinstance(value, (list, tuple, set)):
        values = [_safe_str(item, "") for item in value]
        values = [item for item in values if item]
        return "; ".join(values) if values else "-"

    return _safe_str(value)


# ============================================================================
# LOGO MANAGEMENT
# ============================================================================

def _find_logo(directory: Path, candidates: Sequence[str]) -> Optional[Path]:
    """Find a logo using exact names first, then case-insensitive fallback."""
    if not directory.exists() or not directory.is_dir():
        return None

    for filename in candidates:
        path = directory / filename
        if path.is_file():
            return path

    candidate_names = {name.lower() for name in candidates}

    try:
        for path in directory.iterdir():
            if path.is_file() and path.name.lower() in candidate_names:
                return path
    except OSError:
        pass

    return None


def _locate_logos() -> Dict[str, Optional[Path]]:
    """Locate JESA and ENSAM logos in common asset locations."""
    try:
        base_dir = Path(settings.backend.BASE_DIR)
    except Exception:
        base_dir = Path(__file__).resolve().parents[1]

    directories = [
        base_dir / "assets" / "logos",
        base_dir / "assets" / "logo",
        base_dir / "assets",
    ]

    jesa_candidates = [
        "jesa_logo.png",
        "JESA_logo.png",
        "jesa.png",
        "JESA.png",
        "logo_jesa.png",
        "logo_JESA.png",
        "jesa_logo.jpg",
        "JESA_logo.jpg",
        "jesa.jpg",
        "JESA.jpg",
    ]

    ensam_candidates = [
        "ensam_logo.png",
        "ENSAM_logo.png",
        "ensam.png",
        "ENSAM.png",
        "logo_ensam.png",
        "logo_ENSAM.png",
        "ensam_logo.jpg",
        "ENSAM_logo.jpg",
        "ensam.jpg",
        "ENSAM.jpg",
    ]

    jesa_logo = None
    ensam_logo = None

    for directory in directories:
        if jesa_logo is None:
            jesa_logo = _find_logo(directory, jesa_candidates)

        if ensam_logo is None:
            ensam_logo = _find_logo(directory, ensam_candidates)

        if jesa_logo is not None and ensam_logo is not None:
            break

    logger.info("JESA logo: %s", jesa_logo)
    logger.info("ENSAM logo: %s", ensam_logo)

    return {
        "jesa": jesa_logo,
        "ensam": ensam_logo,
    }


# ============================================================================
# COMPLETE PDF EXPORTER
# ============================================================================

class CompletePDFReportExporter:
    """Generates the complete PDF equivalent of the Excel workbook."""

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})

        self.decimal_precision = self.config.get(
            "decimal_precision",
            getattr(settings, "SCORE_DECIMAL_PRECISION", 1),
        )

        self.generated_at = datetime.now()
        self.logo_paths = _locate_logos()
        self.styles = self._build_styles()

        # A4 portrait: 210 mm - 12 mm - 12 mm = 186 mm
        # A4 landscape: 297 mm - 12 mm - 12 mm = 273 mm
        self._portrait_content_width = 186 * mm
        self._landscape_content_width = 273 * mm

    # ----------------------------------------------------------------------
    # STYLES
    # ----------------------------------------------------------------------

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()

        return {
            "title": ParagraphStyle(
                "CompleteTitle",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=17,
                leading=20,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
                spaceAfter=4,
            ),
            "subtitle": ParagraphStyle(
                "CompleteSubtitle",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=GREY_600,
                alignment=TA_CENTER,
                spaceAfter=7,
            ),
            "section": ParagraphStyle(
                "Section",
                parent=base["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=15,
                textColor=JESA_DARK,
                spaceBefore=0,
                spaceAfter=6,
            ),
            "subsection": ParagraphStyle(
                "Subsection",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=JESA_DARK,
                spaceBefore=4,
                spaceAfter=4,
            ),
            "body": ParagraphStyle(
                "Body",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=GREY_800,
                spaceAfter=3,
            ),
            "small": ParagraphStyle(
                "Small",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=5.8,
                leading=7,
                textColor=GREY_600,
            ),
            "table_header": ParagraphStyle(
                "TableHeader",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=5.2,
                leading=6.1,
                textColor=WHITE,
                alignment=TA_CENTER,
            ),
            "table_cell": ParagraphStyle(
                "TableCell",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=5.2,
                leading=6.2,
                textColor=GREY_800,
                wordWrap="CJK",
            ),
            "table_cell_center": ParagraphStyle(
                "TableCellCenter",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=5.2,
                leading=6.2,
                textColor=GREY_800,
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
            "table_cell_bold": ParagraphStyle(
                "TableCellBold",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=5.2,
                leading=6.2,
                textColor=GREY_800,
                wordWrap="CJK",
            ),
            "kpi": ParagraphStyle(
                "KPI",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=21,
                textColor=JESA_DARK,
                alignment=TA_CENTER,
            ),
            "kpi_label": ParagraphStyle(
                "KPILabel",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=6,
                leading=7,
                textColor=GREY_600,
                alignment=TA_CENTER,
            ),
            "metadata_label": ParagraphStyle(
                "MetadataLabel",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=6.5,
                leading=8,
                textColor=JESA_DARK,
            ),
            "metadata_value": ParagraphStyle(
                "MetadataValue",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=6.5,
                leading=8,
                textColor=GREY_800,
            ),
        }

    # ----------------------------------------------------------------------
    # PAGE HEADER / FOOTER
    # ----------------------------------------------------------------------

    def _draw_header_footer(
        self,
        canvas,
        doc,
        section_name: str = "Complete Report",
    ) -> None:
        canvas.saveState()

        # IMPORTANT: use the actual page size of the current template.
        page_width, page_height = doc.pagesize

        # --------------------------------------------------------------
        # LOGOS
        # --------------------------------------------------------------

        logo_y = page_height - 16 * mm

        if self.logo_paths.get("jesa"):
            try:
                image = ImageReader(str(self.logo_paths["jesa"]))
                canvas.drawImage(
                    image,
                    12 * mm,
                    logo_y,
                    width=62,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception as exc:
                logger.warning("Unable to render JESA logo: %s", exc)

        if self.logo_paths.get("ensam"):
            try:
                image = ImageReader(str(self.logo_paths["ensam"]))
                canvas.drawImage(
                    image,
                    page_width - 74 * mm,
                    logo_y,
                    width=62,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception as exc:
                logger.warning("Unable to render ENSAM logo: %s", exc)

        # --------------------------------------------------------------
        # HEADER LINE / TEXT
        # --------------------------------------------------------------

        canvas.setStrokeColor(GREY_200)
        canvas.setLineWidth(0.6)
        canvas.line(
            12 * mm,
            page_height - 18 * mm,
            page_width - 12 * mm,
            page_height - 18 * mm,
        )

        canvas.setFont("Helvetica-Bold", 6.2)
        canvas.setFillColor(JESA_DARK)
        canvas.drawString(
            12 * mm,
            page_height - 21.5 * mm,
            "JESA DMAT",
        )

        canvas.setFont("Helvetica", 6.2)
        canvas.setFillColor(GREY_600)
        canvas.drawRightString(
            page_width - 12 * mm,
            page_height - 21.5 * mm,
            f"{section_name} - Industrial Digital Maturity Assessment",
        )

        # --------------------------------------------------------------
        # FOOTER
        # --------------------------------------------------------------

        canvas.setStrokeColor(GREY_200)
        canvas.line(
            12 * mm,
            9 * mm,
            page_width - 12 * mm,
            9 * mm,
        )

        canvas.setFont("Helvetica", 5.8)
        canvas.setFillColor(GREY_600)
        canvas.drawString(
            12 * mm,
            5 * mm,
            "JESA DMAT - Digital Maturity Assessment",
        )

        canvas.drawRightString(
            page_width - 12 * mm,
            5 * mm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    # ----------------------------------------------------------------------
    # GENERATE
    # ----------------------------------------------------------------------

    def export(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_path: Optional[Path] = None,
        assessment_id: Optional[str] = None,
    ) -> Path:
        if output_path is None:
            suffix = f"_{assessment_id}" if assessment_id else ""
            output_path = build_output_path(
                f"JESA_DMAT_Full_Report{suffix}.pdf"
            )

        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=25 * mm,
            bottomMargin=14 * mm,
            title="JESA DMAT Complete Assessment Report",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment",
            allowSplitting=1,
        )

        # --------------------------------------------------------------
        # PORTRAIT FRAME
        # --------------------------------------------------------------

        portrait_frame = Frame(
            12 * mm,
            14 * mm,
            186 * mm,
            297 * mm - 25 * mm - 14 * mm,
            id="portrait_frame",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        # --------------------------------------------------------------
        # LANDSCAPE FRAME
        # --------------------------------------------------------------

        landscape_frame = Frame(
            12 * mm,
            14 * mm,
            273 * mm,
            210 * mm - 25 * mm - 14 * mm,
            id="landscape_frame",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        portrait_template = PageTemplate(
            id="Portrait",
            frames=[portrait_frame],
            pagesize=A4,
            onPage=lambda canvas, doc: self._draw_header_footer(
                canvas,
                doc,
                "Complete Report",
            ),
        )

        landscape_template = PageTemplate(
            id="Landscape",
            frames=[landscape_frame],
            pagesize=landscape_page(A4),
            onPage=lambda canvas, doc: self._draw_header_footer(
                canvas,
                doc,
                "Complete Report",
            ),
        )

        doc.addPageTemplates(
            [
                portrait_template,
                landscape_template,
            ]
        )

        self._portrait_content_width = portrait_frame._width
        self._landscape_content_width = landscape_frame._width

        story: List[Any] = []

        # ==============================================================
        # 01 - EXECUTIVE SUMMARY (PORTRAIT)
        # ==============================================================

        self._build_executive_summary(
            story,
            aggregation_results,
            gap_results or [],
            tpi_results or [],
            priority_results or [],
            roadmap or [],
            assessment_id,
        )

        story.append(PageBreak())

        # ==============================================================
        # 02 - DMI OVERVIEW (PORTRAIT)
        # ==============================================================

        self._build_dmi_overview(
            story,
            aggregation_results,
        )

        story.append(PageBreak())

        # ==============================================================
        # 03 - PILLAR ASSESSMENT (PORTRAIT)
        # ==============================================================

        self._build_pillar_assessment(
            story,
            aggregation_results,
        )

        # Switch to landscape before section 04.
        story.append(NextPageTemplate("Landscape"))
        story.append(PageBreak())

        # ==============================================================
        # 04 - DIMENSION ASSESSMENT (LANDSCAPE)
        # ==============================================================

        self._build_dimension_assessment(
            story,
            aggregation_results,
        )

        story.append(PageBreak())

        # ==============================================================
        # 05 - INDICATOR DETAILS (LANDSCAPE)
        # ==============================================================

        self._build_indicator_details(
            story,
            aggregation_results,
        )

        # Return to portrait for section 06.
        story.append(NextPageTemplate("Portrait"))
        story.append(PageBreak())

        # ==============================================================
        # 06 - GAP ANALYSIS (PORTRAIT)
        # ==============================================================

        self._build_gap_analysis(
            story,
            gap_results or [],
        )

        # Switch to landscape for sections 07-10.
        story.append(NextPageTemplate("Landscape"))
        story.append(PageBreak())

        # ==============================================================
        # 07 - TPI PRIORITIZATION (LANDSCAPE)
        # ==============================================================

        self._build_tpi_prioritization(
            story,
            tpi_results or [],
        )

        story.append(PageBreak())

        # ==============================================================
        # 08 - PRIORITY MATRIX (LANDSCAPE)
        # ==============================================================

        self._build_priority_matrix(
            story,
            priority_results or [],
        )

        story.append(PageBreak())

        # ==============================================================
        # 09 - TRANSFORMATION ROADMAP (LANDSCAPE)
        # ==============================================================

        self._build_transformation_roadmap(
            story,
            roadmap or [],
        )

        story.append(PageBreak())

        # ==============================================================
        # 10 - RECOMMENDATIONS (LANDSCAPE)
        # ==============================================================

        self._build_recommendations(
            story,
            priority_results or [],
            roadmap or [],
        )

        # Return to portrait for section 11.
        story.append(NextPageTemplate("Portrait"))
        story.append(PageBreak())

        # ==============================================================
        # 11 - METADATA (PORTRAIT)
        # ==============================================================

        self._build_metadata(
            story,
            aggregation_results,
            assessment_id,
        )

        doc.build(story)

        logger.info(
            "Complete PDF report generated: %s",
            output_path,
        )

        return output_path

    # =========================================================================
    # TABLE HELPERS
    # =========================================================================

    def _paragraph(
        self,
        value: Any,
        style: str = "table_cell",
    ) -> Paragraph:
        return Paragraph(
            _escape_xml(value),
            self.styles[style],
        )

    def _make_table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        widths: Optional[Sequence[float]] = None,
        repeat_rows: int = 1,
        priority_column: Optional[int] = None,
        landscape: bool = False,
    ) -> Table:
        """
        Build a table that never exceeds the page content width.

        Wide tables use the landscape content width when ``landscape=True``.
        If the requested widths exceed that area, widths are scaled
        proportionally rather than allowing columns to run off the page.
        """

        header_row = [
            self._paragraph(header, "table_header")
            for header in headers
        ]

        table_rows = [header_row]

        for row in rows:
            converted = [
                self._paragraph(value, "table_cell")
                for value in row
            ]
            table_rows.append(converted)

        safe_widths = None

        if widths is not None:
            safe_widths = [float(width) for width in widths]

            available_width = (
                self._landscape_content_width
                if landscape
                else self._portrait_content_width
            )

            total_width = sum(safe_widths)

            if total_width > available_width:
                scale = available_width / total_width
                safe_widths = [
                    width * scale
                    for width in safe_widths
                ]

                logger.debug(
                    "Table widths scaled from %.2f pt to %.2f pt "
                    "(landscape=%s, scale=%.3f)",
                    total_width,
                    sum(safe_widths),
                    landscape,
                    scale,
                )

        table = Table(
            table_rows,
            colWidths=safe_widths,
            repeatRows=repeat_rows,
            splitByRow=1,
            splitInRow=1,
            hAlign="LEFT",
        )

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), JESA_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("GRID", (0, 0), (-1, -1), 0.35, GREY_200),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]

        # Alternating rows.
        for row_index in range(1, len(table_rows)):
            if row_index % 2 == 0:
                style_commands.append(
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (-1, row_index),
                        GREY_100,
                    )
                )

        # Priority coloring.
        if priority_column is not None:
            for row_index, row in enumerate(rows, start=1):
                if priority_column >= len(row):
                    continue

                priority = row[priority_column]

                if priority:
                    style_commands.extend(
                        [
                            (
                                "BACKGROUND",
                                (priority_column, row_index),
                                (priority_column, row_index),
                                _priority_color(priority),
                            ),
                            (
                                "TEXTCOLOR",
                                (priority_column, row_index),
                                (priority_column, row_index),
                                WHITE,
                            ),
                        ]
                    )

        table.setStyle(TableStyle(style_commands))
        return table

    def _section_title(
        self,
        number: str,
        title: str,
    ) -> Paragraph:
        return Paragraph(
            f"{_escape_xml(number)}. {_escape_xml(title)}",
            self.styles["section"],
        )

    # =========================================================================
    # 01 - EXECUTIVE SUMMARY
    # =========================================================================

    def _build_executive_summary(
        self,
        story: List[Any],
        results: Dict[str, Any],
        gap_results: List[Any],
        tpi_results: List[Any],
        priority_results: List[Any],
        roadmap: List[Any],
        assessment_id: Optional[str],
    ) -> None:
        metadata = results.get("metadata", {}) or {}
        dmi = results.get("dmi")

        dmi_score = _get(
            dmi,
            "score",
            metadata.get("dmi_score"),
        )

        dmi_level = _get(
            dmi,
            "level_name",
            metadata.get("dmi_level_name", "-"),
        )

        # Capture metadata with fallbacks - using the actual keys from New Assessment
        site_name = metadata.get(
            "plant",
            metadata.get("site_name", "Industrial Plant"),
        )

        resolved_id = (
            assessment_id
            or metadata.get("assessment_id")
            or "N/A"
        )

        story.append(
            Paragraph(
                "INDUSTRIAL DIGITAL MATURITY ASSESSMENT REPORT",
                self.styles["title"],
            )
        )

        story.append(
            Paragraph(
                "Executive Assessment Workbook - PDF equivalent of the complete Excel report",
                self.styles["subtitle"],
            )
        )

        metadata_rows = [
            [
                "Assessment ID",
                resolved_id,
                "Site",
                site_name,
            ],
            [
                "Report Version",
                metadata.get("report_version", "1.0"),
                "Generated",
                self.generated_at.strftime("%Y-%m-%d %H:%M"),
            ],
        ]

        metadata_table = Table(
            [
                [
                    self._paragraph("Field", "table_header"),
                    self._paragraph("Value", "table_header"),
                    self._paragraph("Field", "table_header"),
                    self._paragraph("Value", "table_header"),
                ]
            ]
            + [
                [
                    self._paragraph(row[0], "metadata_label"),
                    self._paragraph(row[1], "metadata_value"),
                    self._paragraph(row[2], "metadata_label"),
                    self._paragraph(row[3], "metadata_value"),
                ]
                for row in metadata_rows
            ],
            colWidths=[30 * mm, 55 * mm, 30 * mm, 55 * mm],
        )

        metadata_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), JESA_DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("GRID", (0, 0), (-1, -1), 0.35, GREY_200),
                    ("BACKGROUND", (0, 1), (-1, -1), GREY_100),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.append(metadata_table)
        story.append(Spacer(1, 5 * mm))

        kpi_table = Table(
            [
                [
                    self._paragraph(
                        _format_number(
                            dmi_score,
                            self.decimal_precision,
                        ),
                        "kpi",
                    ),
                    self._paragraph(
                        _safe_str(dmi_level),
                        "kpi",
                    ),
                    self._paragraph(
                        str(metadata.get("total_indicators", 0)),
                        "kpi",
                    ),
                ],
                [
                    self._paragraph(
                        "DIGITAL MATURITY INDEX",
                        "kpi_label",
                    ),
                    self._paragraph(
                        "MATURITY LEVEL",
                        "kpi_label",
                    ),
                    self._paragraph(
                        "TOTAL INDICATORS",
                        "kpi_label",
                    ),
                ],
            ],
            colWidths=[56 * mm, 56 * mm, 56 * mm],
        )

        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), GREY_100),
                    ("BOX", (0, 0), (-1, -1), 0.8, JESA_GREEN),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, GREY_200),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, 0), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ]
            )
        )

        story.append(kpi_table)
        story.append(Spacer(1, 5 * mm))

        critical_count = sum(
            1
            for item in priority_results
            if _normalize_priority(
                _get(item, "priority_category")
            )
            == "Critical"
        )

        high_count = sum(
            1
            for item in priority_results
            if _normalize_priority(
                _get(item, "priority_category")
            )
            == "High"
        )

        roadmap_actions = sum(
            len(_get(phase, "items", []) or [])
            for phase in roadmap
        )

        executive_rows = [
            [
                "Digital Maturity Index",
                _format_number(
                    dmi_score,
                    self.decimal_precision,
                ),
                "%",
            ],
            ["Maturity Level", _safe_str(dmi_level), ""],
            [
                "Total Indicators",
                metadata.get("total_indicators", 0),
                "Indicators",
            ],
            [
                "Total Dimensions",
                metadata.get("total_dimensions", 0),
                "Dimensions",
            ],
            [
                "Total Pillars",
                metadata.get("total_pillars", 0),
                "Pillars",
            ],
            ["Critical Priorities", critical_count, "Actions"],
            ["High Priorities", high_count, "Actions"],
            ["Roadmap Actions", roadmap_actions, "Actions"],
        ]

        story.append(
            self._section_title("01", "Executive Summary")
        )

        story.append(
            self._make_table(
                ["Executive KPI", "Value", "Unit"],
                executive_rows,
                widths=[70 * mm, 50 * mm, 45 * mm],
            )
        )

    # =========================================================================
    # 02 - DMI OVERVIEW
    # =========================================================================

    def _build_dmi_overview(
        self,
        story: List[Any],
        results: Dict[str, Any],
    ) -> None:
        story.append(self._section_title("02", "DMI Overview"))

        dmi = results.get("dmi")
        rows = []

        if dmi is not None:
            rows.append(
                [
                    "Digital Maturity Index",
                    "DMI",
                    "Digital Maturity Index",
                    _format_number(
                        _get(dmi, "score"),
                        self.decimal_precision,
                    ),
                    _get(dmi, "level"),
                    _get(dmi, "level_name"),
                ]
            )

        story.append(
            self._make_table(
                [
                    "Assessment Level",
                    "ID",
                    "Name",
                    "Score",
                    "Maturity Level",
                    "Maturity Level Name",
                ],
                rows,
                widths=[
                    30 * mm,
                    13 * mm,
                    48 * mm,
                    22 * mm,
                    25 * mm,
                    42 * mm,
                ],
            )
        )

    # =========================================================================
    # 03 - PILLAR ASSESSMENT
    # =========================================================================

    def _build_pillar_assessment(
        self,
        story: List[Any],
        results: Dict[str, Any],
    ) -> None:
        story.append(self._section_title("03", "Pillar Assessment"))

        rows = []
        pillars = results.get("pillars", {})
        values = (
            pillars.values()
            if isinstance(pillars, Mapping)
            else _as_list(pillars)
        )

        for result in values:
            if not isinstance(result, ScoreResult):
                continue

            rows.append(
                [
                    result.entity_id,
                    translate_entity_name(
                        result.entity_id,
                        result.entity_name,
                    ),
                    _format_number(
                        result.score,
                        self.decimal_precision,
                    ),
                    result.level,
                    result.level_name,
                    result.applicability,
                ]
            )

        story.append(
            self._make_table(
                [
                    "Pillar ID",
                    "Pillar Name",
                    "Score",
                    "Maturity Level",
                    "Maturity Level Name",
                    "Applicability",
                ],
                rows,
                widths=[
                    20 * mm,
                    48 * mm,
                    23 * mm,
                    25 * mm,
                    45 * mm,
                    25 * mm,
                ],
            )
        )

    # =========================================================================
    # 04 - DIMENSION ASSESSMENT
    # =========================================================================

    def _build_dimension_assessment(
        self,
        story: List[Any],
        results: Dict[str, Any],
    ) -> None:
        story.append(self._section_title("04", "Dimension Assessment"))

        rows = []
        dimensions = results.get("dimensions", {})
        values = (
            dimensions.values()
            if isinstance(dimensions, Mapping)
            else _as_list(dimensions)
        )

        for result in values:
            if not isinstance(result, ScoreResult):
                continue

            rows.append(
                [
                    result.entity_id,
                    translate_entity_name(
                        result.entity_id,
                        result.entity_name,
                    ),
                    _format_number(
                        result.score,
                        self.decimal_precision,
                    ),
                    result.level,
                    result.level_name,
                    result.applicability,
                    result.parent_id,
                ]
            )

        story.append(
            self._make_table(
                [
                    "Dimension ID",
                    "Dimension Name",
                    "Score",
                    "Maturity Level",
                    "Maturity Level Name",
                    "Applicability",
                    "Parent Pillar ID",
                ],
                rows,
                widths=[
                    18 * mm,
                    43 * mm,
                    18 * mm,
                    23 * mm,
                    42 * mm,
                    25 * mm,
                    25 * mm,
                ],
                landscape=True,
            )
        )

    # =========================================================================
    # 05 - INDICATOR DETAILS
    # =========================================================================

    def _build_indicator_details(
        self,
        story: List[Any],
        results: Dict[str, Any],
    ) -> None:
        story.append(self._section_title("05", "Indicator Details"))

        rows = []
        indicators = results.get("indicators", {})
        values = (
            indicators.values()
            if isinstance(indicators, Mapping)
            else _as_list(indicators)
        )

        for result in values:
            if not isinstance(result, ScoreResult):
                continue

            rows.append(
                [
                    result.entity_id,
                    translate_entity_name(
                        result.entity_id,
                        result.entity_name,
                    ),
                    _format_number(
                        result.score,
                        self.decimal_precision,
                    ),
                    result.level,
                    result.level_name,
                    result.applicability,
                    result.parent_id,
                ]
            )

        story.append(
            self._make_table(
                [
                    "Indicator ID",
                    "Indicator Name",
                    "Score",
                    "Maturity Level",
                    "Maturity Level Name",
                    "Applicability",
                    "Parent ID",
                ],
                rows,
                widths=[
                    22 * mm,
                    43 * mm,
                    20 * mm,
                    25 * mm,
                    40 * mm,
                    25 * mm,
                    25 * mm,
                ],
                landscape=True,
            )
        )

    # =========================================================================
    # 06 - GAP ANALYSIS
    # =========================================================================

    def _build_gap_analysis(
        self,
        story: List[Any],
        gap_results: List[Any],
    ) -> None:
        story.append(self._section_title("06", "Gap Analysis"))

        rows = []

        for gap in gap_results:
            rows.append(
                [
                    _get(gap, "entity_id"),
                    translate_entity_name(
                        _get(gap, "entity_id"),
                        _get(gap, "entity_name"),
                    ),
                    _get(gap, "entity_type"),
                    _format_number(
                        _get(gap, "current_score"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(gap, "target_score"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(gap, "gap"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(gap, "gap_percent"),
                        self.decimal_precision,
                        "%",
                    ),
                    _normalize_priority(
                        _get(gap, "priority")
                    ),
                ]
            )

        # Keep Gap Analysis portrait; it fits comfortably in the page width.
        story.append(
            self._make_table(
                [
                    "Entity ID",
                    "Entity Name",
                    "Entity Type",
                    "Current Score",
                    "Target Score",
                    "Gap",
                    "Gap (%)",
                    "Priority",
                ],
                rows,
                widths=[
                    14 * mm,
                    28 * mm,
                    16 * mm,
                    16 * mm,
                    16 * mm,
                    14 * mm,
                    16 * mm,
                    18 * mm,
                ],
                priority_column=7,
            )
        )

    # =========================================================================
    # 07 - TPI PRIORITIZATION
    # =========================================================================

    def _build_tpi_prioritization(
        self,
        story: List[Any],
        tpi_results: List[Any],
    ) -> None:
        story.append(self._section_title("07", "TPI Prioritization"))

        sorted_results = sorted(
            tpi_results,
            key=lambda x: (
                -_safe_float(_get(x, "tpi_score"), 0),
                PRIORITY_RANK.get(
                    _normalize_priority(
                        _get(x, "priority_category")
                    ),
                    99,
                ),
            ),
        )

        rows = []

        for rank, tpi in enumerate(sorted_results, start=1):
            raw_tpi = _get(tpi, "tpi_score")
            tpi_display = (
                _safe_float(raw_tpi) * 100
                if raw_tpi is not None
                else None
            )

            rows.append(
                [
                    rank,
                    _get(tpi, "dimension_id"),
                    translate_entity_name(
                        _get(tpi, "dimension_id"),
                        _get(tpi, "dimension_name"),
                    ),
                    _format_number(
                        tpi_display,
                        self.decimal_precision,
                    ),
                    _normalize_priority(
                        _get(tpi, "priority_category")
                    ),
                    _format_number(
                        _get(tpi, "gap"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(tpi, "business_impact"),
                        self.decimal_precision,
                        "%",
                    ),
                    _format_number(
                        _get(tpi, "strategic_importance"),
                        self.decimal_precision,
                        "%",
                    ),
                    _format_number(
                        _get(tpi, "expected_roi"),
                        self.decimal_precision,
                        "%",
                    ),
                    _format_number(
                        _get(tpi, "implementation_cost"),
                        0,
                        " MAD",
                    ),
                    _format_number(
                        _get(tpi, "implementation_difficulty"),
                        self.decimal_precision,
                    ),
                ]
            )

        story.append(
            self._make_table(
                [
                    "Rank",
                    "Dimension ID",
                    "Dimension Name",
                    "TPI Score",
                    "Priority",
                    "Gap",
                    "Business Impact (%)",
                    "Strategic Importance (%)",
                    "Expected ROI (%)",
                    "Implementation Cost (MAD)",
                    "Implementation Difficulty (person-days)",
                ],
                rows,
                widths=[
                    10 * mm,
                    20 * mm,
                    32 * mm,
                    18 * mm,
                    22 * mm,
                    18 * mm,
                    25 * mm,
                    27 * mm,
                    22 * mm,
                    30 * mm,
                    30 * mm,
                ],
                priority_column=4,
                landscape=True,
            )
        )

    # =========================================================================
    # 08 - PRIORITY MATRIX
    # =========================================================================

    def _build_priority_matrix(
        self,
        story: List[Any],
        priority_results: List[Any],
    ) -> None:
        story.append(self._section_title("08", "Priority Matrix"))

        sorted_results = sorted(
            priority_results,
            key=lambda x: (
                PRIORITY_RANK.get(
                    _normalize_priority(
                        _get(x, "priority_category")
                    ),
                    99,
                ),
                -_safe_float(_get(x, "tpi_score"), -1),
                -_safe_float(_get(x, "gap"), 0),
            ),
        )

        rows = []

        for rank, result in enumerate(sorted_results, start=1):
            recommendations = _get(
                result,
                "recommendations",
                [],
            )

            rows.append(
                [
                    rank,
                    _get(result, "dimension_id"),
                    translate_entity_name(
                        _get(result, "dimension_id"),
                        _get(result, "dimension_name"),
                    ),
                    _format_number(
                        _get(result, "current_score"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(result, "target_score"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(result, "gap"),
                        self.decimal_precision,
                    ),
                    _format_number(
                        _get(result, "tpi_score"),
                        self.decimal_precision,
                    ),
                    _normalize_priority(
                        _get(result, "priority_category")
                    ),
                    len(recommendations or []),
                ]
            )

        story.append(
            self._make_table(
                [
                    "Rank",
                    "Dimension ID",
                    "Dimension Name",
                    "Current Score",
                    "Target Score",
                    "Gap",
                    "TPI Score",
                    "Priority",
                    "Recommendations",
                ],
                rows,
                widths=[
                    10 * mm,
                    20 * mm,
                    40 * mm,
                    23 * mm,
                    23 * mm,
                    20 * mm,
                    20 * mm,
                    23 * mm,
                    25 * mm,
                ],
                priority_column=7,
                landscape=True,
            )
        )

    # =========================================================================
    # 09 - TRANSFORMATION ROADMAP
    # =========================================================================

    def _build_transformation_roadmap(
        self,
        story: List[Any],
        roadmap: List[Any],
    ) -> None:
        story.append(self._section_title("09", "Transformation Roadmap"))

        sorted_phases = sorted(
            roadmap,
            key=lambda phase: PHASE_ORDER.get(
                _safe_str(_get(phase, "phase_name"), ""),
                99,
            ),
        )

        rows = []

        for phase in sorted_phases:
            items = _get(phase, "items", []) or []

            sorted_items = sorted(
                items,
                key=lambda item: (
                    -_safe_float(_get(item, "tpi_score"), 0),
                    -_safe_float(_get(item, "gap"), 0),
                    _safe_str(_get(item, "title"), ""),
                ),
            )

            for item in sorted_items:
                rows.append(
                    [
                        _get(phase, "phase_name"),
                        _get(phase, "horizon"),
                        _get(item, "recommendation_id"),
                        _get(item, "title"),
                        _get(item, "dimension_id"),
                        _get(item, "pillar_id"),
                        _normalize_priority(_get(item, "priority")),
                        _format_number(
                            _get(item, "tpi_score"),
                            self.decimal_precision,
                        ),
                        _format_number(
                            _get(item, "gap"),
                            self.decimal_precision,
                        ),
                        _get(item, "effort"),
                        _get(item, "expected_impact"),
                        _join_values(_get(item, "prerequisites")),
                        _join_values(_get(item, "dependencies")),
                    ]
                )

        story.append(
            self._make_table(
                [
                    "Phase",
                    "Horizon",
                    "Recommendation ID",
                    "Action",
                    "Dimension ID",
                    "Pillar ID",
                    "Priority",
                    "TPI Score",
                    "Gap",
                    "Effort",
                    "Expected Impact",
                    "Prerequisites",
                    "Dependencies",
                ],
                rows,
                widths=[
                    16 * mm,
                    20 * mm,
                    25 * mm,
                    38 * mm,
                    20 * mm,
                    18 * mm,
                    20 * mm,
                    18 * mm,
                    18 * mm,
                    20 * mm,
                    25 * mm,
                    32 * mm,
                    32 * mm,
                ],
                priority_column=6,
                landscape=True,
            )
        )

    # =========================================================================
    # 10 - RECOMMENDATIONS
    # =========================================================================

    def _build_recommendations(
        self,
        story: List[Any],
        priority_results: List[Any],
        roadmap: List[Any],
    ) -> None:
        story.append(self._section_title("10", "Recommendations"))

        rows = []

        for priority in priority_results:
            normalized_priority = _normalize_priority(
                _get(priority, "priority_category")
            )

            recommendations = _get(
                priority,
                "recommendations",
                [],
            ) or []

            for recommendation in recommendations:
                rows.append(
                    [
                        _get(recommendation, "recommendation_id"),
                        _get(priority, "dimension_id"),
                        translate_entity_name(
                            _get(priority, "dimension_id"),
                            _get(priority, "dimension_name"),
                        ),
                        normalized_priority,
                        _format_number(
                            _get(priority, "tpi_score"),
                            self.decimal_precision,
                        ),
                        _format_number(
                            _get(priority, "gap"),
                            self.decimal_precision,
                        ),
                        _get(recommendation, "title"),
                        _get(recommendation, "pillar_id"),
                        _get(recommendation, "effort"),
                        _get(recommendation, "expected_impact"),
                        _join_values(
                            _get(recommendation, "detailed_actions")
                        ),
                        _join_values(
                            _get(recommendation, "prerequisites")
                        ),
                        _join_values(
                            _get(recommendation, "dependencies")
                        ),
                        _join_values(
                            _get(recommendation, "completion_evidence")
                        ),
                        _get(recommendation, "source_reference"),
                    ]
                )

        # Excel-equivalent fallback when priority recommendations are empty.
        if not rows and roadmap:
            for phase in roadmap:
                items = _get(phase, "items", []) or []

                for item in items:
                    recommendation_id = _safe_str(
                        _get(item, "recommendation_id"),
                        "",
                    )

                    if recommendation_id.startswith("NO-REC-"):
                        continue

                    rows.append(
                        [
                            recommendation_id,
                            _get(item, "dimension_id"),
                            "",
                            _normalize_priority(
                                _get(item, "priority")
                            ),
                            _format_number(
                                _get(item, "tpi_score"),
                                self.decimal_precision,
                            ),
                            _format_number(
                                _get(item, "gap"),
                                self.decimal_precision,
                            ),
                            _get(item, "title"),
                            _get(item, "pillar_id"),
                            _get(item, "effort"),
                            _get(item, "expected_impact"),
                            _join_values(
                                _get(item, "detailed_actions")
                            ),
                            _join_values(
                                _get(item, "prerequisites")
                            ),
                            _join_values(
                                _get(item, "dependencies")
                            ),
                            _join_values(
                                _get(item, "completion_evidence")
                            ),
                            _get(item, "source_reference"),
                        ]
                    )

        story.append(
            self._make_table(
                [
                    "Recommendation ID",
                    "Dimension ID",
                    "Dimension Name",
                    "Priority",
                    "TPI Score",
                    "Gap",
                    "Title",
                    "Pillar ID",
                    "Effort",
                    "Expected Impact",
                    "Detailed Actions",
                    "Prerequisites",
                    "Dependencies",
                    "Completion Evidence",
                    "Source Reference",
                ],
                rows,
                widths=[
                    22 * mm,
                    18 * mm,
                    32 * mm,
                    20 * mm,
                    18 * mm,
                    18 * mm,
                    35 * mm,
                    18 * mm,
                    20 * mm,
                    25 * mm,
                    40 * mm,
                    32 * mm,
                    32 * mm,
                    35 * mm,
                    30 * mm,
                ],
                priority_column=3,
                landscape=True,
            )
        )

    # =========================================================================
    # 11 - METADATA
    # =========================================================================

    def _build_metadata(
        self,
        story: List[Any],
        results: Dict[str, Any],
        assessment_id: Optional[str],
    ) -> None:
        story.append(self._section_title("11", "Assessment Metadata"))

        metadata = results.get("metadata", {}) or {}

        rows = [
            [
                "Assessment ID",
                assessment_id or metadata.get("assessment_id", ""),
            ],
            ["Site ID", metadata.get("site_id", "")],
            ["Site Name", metadata.get("site_name", "")],
            ["Assessment Date", metadata.get("assessment_date", "")],
            ["Evaluator", metadata.get("evaluator", "")],
            ["Report Version", metadata.get("report_version", "1.0")],
            [
                "Generated At",
                self.generated_at.strftime("%Y-%m-%d %H:%M"),
            ],
            [
                "Total Indicators",
                metadata.get("total_indicators", 0),
            ],
            [
                "Total Subdimensions",
                metadata.get("total_subdimensions", 0),
            ],
            [
                "Total Dimensions",
                metadata.get("total_dimensions", 0),
            ],
            [
                "Total Pillars",
                metadata.get("total_pillars", 0),
            ],
            [
                "DMI Score",
                metadata.get("dmi_score", None),
            ],
            [
                "DMI Level",
                metadata.get("dmi_level", ""),
            ],
            [
                "DMI Level Name",
                metadata.get("dmi_level_name", ""),
            ],
        ]

        story.append(
            self._make_table(
                ["Field", "Value"],
                rows,
                widths=[65 * mm, 105 * mm],
            )
        )


# ============================================================================
# REPORT GENERATOR
# ============================================================================

class ReportGenerator:
    """High-level orchestrator for PDF, Excel and JSON outputs."""

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})

        self.excel_exporter = ExcelExporter(self.config)
        self.complete_pdf_exporter = CompletePDFReportExporter(self.config)

    # ----------------------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------------------

    def generate_full_report(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_dir: Optional[Path] = None,
        assessment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        include_pdf_score: bool = True,
        include_pdf_full: bool = False,
        include_excel: bool = True,
        include_json: bool = True,
    ) -> Dict[str, Path]:
        if not isinstance(aggregation_results, dict):
            raise TypeError("aggregation_results must be a dictionary.")

        # Use provided metadata if available, otherwise fall back to aggregation_results
        if metadata is None:
            metadata = aggregation_results.get("metadata", {})

        if not isinstance(metadata, Mapping):
            metadata = {}

        resolved_assessment_id = (
            assessment_id
            or metadata.get("assessment_id", "UNKNOWN")
        )

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
            outputs["pdf_score"] = self._generate_pdf_score(
                report_data,
                output_dir,
            )

        if include_pdf_full:
            outputs["pdf_full"] = self._generate_pdf_full(
                report_data,
                output_dir,
            )

        if include_excel:
            outputs["excel"] = self._generate_excel(
                report_data,
                output_dir,
            )

        if include_json:
            outputs["json"] = self._generate_json(
                report_data,
                output_dir,
            )

        logger.info(
            "Reports generated: %s",
            ", ".join(
                f"{key}={value}"
                for key, value in outputs.items()
            ),
        )

        return outputs

    # ----------------------------------------------------------------------
    # BUILD REPORT DATA
    # ----------------------------------------------------------------------

    def _build_report_data(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]],
        tpi_results: Optional[List[TPIResult]],
        priority_results: Optional[List[PriorityResult]],
        roadmap: Optional[List[RoadmapPhase]],
        assessment_id: str,
        site_name: str,
    ) -> ReportData:
        generated_at = datetime.now().isoformat()

        metadata = ReportMetadata(
            report_id=(
                f"RPT-{assessment_id}-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            assessment_id=assessment_id,
            site_name=site_name,
            generated_at=generated_at,
        )

        summary = self._build_executive_summary(
            aggregation_results,
            gap_results,
            priority_results,
        )

        raw_data = {
            "dmi": self._serialize_object(
                aggregation_results.get("dmi")
            ),
            "indicators": self._serialize_score_results(
                aggregation_results.get("indicators", {})
            ),
            "subdimensions": self._serialize_score_results(
                aggregation_results.get("subdimensions", {})
            ),
            "dimensions": self._serialize_score_results(
                aggregation_results.get("dimensions", {})
            ),
            "pillars": self._serialize_score_results(
                aggregation_results.get("pillars", {})
            ),
        }

        return ReportData(
            metadata=metadata,
            summary=summary,
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            raw_data=raw_data,
        )

    # ----------------------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ----------------------------------------------------------------------

    def _build_executive_summary(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]],
        priority_results: Optional[List[PriorityResult]],
    ) -> ExecutiveSummary:
        dmi = aggregation_results.get("dmi")

        dimensions = aggregation_results.get("dimensions", {})
        dimension_scores = []

        if isinstance(dimensions, Mapping):
            for dim_id, result in dimensions.items():
                if (
                    isinstance(result, ScoreResult)
                    and result.score is not None
                ):
                    dimension_scores.append(
                        (str(dim_id), float(result.score))
                    )

        dimension_scores.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        top_strengths = dimension_scores[:3]
        top_weaknesses = sorted(
            dimension_scores,
            key=lambda item: item[1],
        )[:3]

        critical_gaps = 0

        if gap_results:
            critical_gaps = sum(
                1
                for gap in gap_results
                if _normalize_priority(
                    getattr(gap, "priority", None)
                )
                in {"Critical", "High"}
            )

        priority_dimensions = (
            len(priority_results)
            if priority_results
            else 0
        )

        dmi_score = None
        dmi_level = None
        dmi_level_name = ""

        if dmi is not None:
            if getattr(dmi, "score", None) is not None:
                dmi_score = float(dmi.score)

            if getattr(dmi, "level", None) is not None:
                try:
                    dmi_level = int(dmi.level)
                except (TypeError, ValueError):
                    dmi_level = None

            dmi_level_name = str(
                getattr(dmi, "level_name", "") or ""
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

    # ----------------------------------------------------------------------
    # PDF SCORE
    # ----------------------------------------------------------------------

    def _generate_pdf_score(
        self,
        report_data: ReportData,
        output_dir: Optional[Path],
    ) -> Path:
        filename = (
            f"JESA_DMAT_Score_Summary_"
            f"{report_data.metadata.assessment_id}.pdf"
        )

        output_path = self._resolve_output_path(
            filename,
            output_dir,
        )

        return export_score_summary(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    # ----------------------------------------------------------------------
    # COMPLETE PDF
    # ----------------------------------------------------------------------

    def _generate_pdf_full(
        self,
        report_data: ReportData,
        output_dir: Optional[Path],
    ) -> Path:
        filename = (
            f"JESA_DMAT_Full_Report_"
            f"{report_data.metadata.assessment_id}.pdf"
        )

        output_path = self._resolve_output_path(
            filename,
            output_dir,
        )

        return self.complete_pdf_exporter.export(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    # ----------------------------------------------------------------------
    # EXCEL
    # ----------------------------------------------------------------------

    def _generate_excel(
        self,
        report_data: ReportData,
        output_dir: Optional[Path],
    ) -> Path:
        filename = (
            f"JESA_DMAT_Workbook_"
            f"{report_data.metadata.assessment_id}.xlsx"
        )

        output_path = self._resolve_output_path(
            filename,
            output_dir,
        )

        return self.excel_exporter.export_assessment_results(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    # ----------------------------------------------------------------------
    # JSON
    # ----------------------------------------------------------------------

    def _generate_json(
        self,
        report_data: ReportData,
        output_dir: Optional[Path],
    ) -> Path:
        filename = (
            f"JESA_DMAT_Report_"
            f"{report_data.metadata.assessment_id}.json"
        )

        output_path = self._resolve_output_path(
            filename,
            output_dir,
        )

        data = self._serialize_report_data(report_data)

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

        logger.info("JSON report generated: %s", output_path)
        return output_path

    # ----------------------------------------------------------------------
    # PATH
    # ----------------------------------------------------------------------

    def _resolve_output_path(
        self,
        filename: str,
        output_dir: Optional[Path],
    ) -> Path:
        if output_dir is not None:
            directory = Path(output_dir)
            ensure_directory(directory)
            return directory / filename

        return build_output_path(filename)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def _serialize_report_data(
        self,
        report_data: ReportData,
    ) -> Dict[str, Any]:
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
                "top_strengths": [
                    list(item)
                    for item in report_data.summary.top_strengths
                ],
                "top_weaknesses": [
                    list(item)
                    for item in report_data.summary.top_weaknesses
                ],
                "critical_gaps": report_data.summary.critical_gaps,
                "priority_dimensions": report_data.summary.priority_dimensions,
            },
            "aggregation": self._serialize_aggregation(
                report_data.aggregation_results
            ),
            "decision": {
                "gaps": [
                    self._serialize_object(item)
                    for item in (report_data.gap_results or [])
                ],
                "tpi": [
                    self._serialize_object(item)
                    for item in (report_data.tpi_results or [])
                ],
                "priorities": [
                    self._serialize_object(item)
                    for item in (report_data.priority_results or [])
                ],
                "roadmap": [
                    self._serialize_object(item)
                    for item in (report_data.roadmap or [])
                ],
            },
            "raw_data": report_data.raw_data,
        }

    def _serialize_aggregation(
        self,
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        dmi = results.get("dmi")

        return {
            "indicators": self._serialize_score_results(
                results.get("indicators", {})
            ),
            "subdimensions": self._serialize_score_results(
                results.get("subdimensions", {})
            ),
            "dimensions": self._serialize_score_results(
                results.get("dimensions", {})
            ),
            "pillars": self._serialize_score_results(
                results.get("pillars", {})
            ),
            "dmi": (
                self._serialize_object(dmi)
                if dmi is not None
                else None
            ),
            "metadata": self._make_json_safe(
                results.get("metadata", {})
            ),
        }

    def _serialize_score_results(
        self,
        results: Any,
    ) -> Dict[str, Any]:
        if not isinstance(results, Mapping):
            return {}

        serialized = {}

        for key, result in results.items():
            if isinstance(result, ScoreResult):
                serialized[str(key)] = result.to_dict()
            else:
                serialized[str(key)] = self._make_json_safe(result)

        return serialized

    def _serialize_object(self, obj: Any) -> Any:
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

    def _make_json_safe(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, Mapping):
            return {
                str(key): self._make_json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                self._make_json_safe(item)
                for item in value
            ]

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


# ============================================================================
# PUBLIC FUNCTION
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
    Generate reports in requested formats.

    Supported values:
        pdf_score  - Short score summary.
        pdf_full   - Complete PDF equivalent of Excel.
        excel      - Excel workbook.
        json       - JSON dump.
        pdf        - Backward-compatible alias for pdf_score.
        report     - Backward-compatible alias for pdf_full.
    """

    if formats is None:
        formats = [
            "pdf_score",
            "excel",
            "json",
        ]

    normalized = set()

    for fmt in formats:
        value = str(fmt).strip().lower()

        if value == "pdf":
            normalized.add("pdf_score")
        elif value == "report":
            normalized.add("pdf_full")
        else:
            normalized.add(value)

    generator = ReportGenerator()

    return generator.generate_full_report(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_dir=output_dir,
        assessment_id=assessment_id,
        include_pdf_score=("pdf_score" in normalized),
        include_pdf_full=("pdf_full" in normalized),
        include_excel=("excel" in normalized),
        include_json=("json" in normalized),
    )


# ============================================================================
# EXECUTIVE SUMMARY PUBLIC UTILITY
# ============================================================================

def generate_executive_summary(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
    priority_results: Optional[List[PriorityResult]] = None,
) -> Dict[str, Any]:
    """Return the executive summary as a JSON-safe dictionary."""

    generator = ReportGenerator()

    summary = generator._build_executive_summary(
        aggregation_results,
        gap_results,
        priority_results,
    )

    return {
        "dmi_score": summary.dmi_score,
        "dmi_level": summary.dmi_level,
        "dmi_level_name": summary.dmi_level_name,
        "top_strengths": [
            list(item)
            for item in summary.top_strengths
        ],
        "top_weaknesses": [
            list(item)
            for item in summary.top_weaknesses
        ],
        "critical_gaps": summary.critical_gaps,
        "priority_dimensions": summary.priority_dimensions,
    }