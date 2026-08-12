"""
Professional PDF exports for JESA DMAT.

Two distinct exports are provided:
- Score Summary (2 pages): DMI, pillar scores, dimension scores, gaps, TPI, priorities.
- Full Report (comprehensive, multi‑page): reproduces all sheets from the Excel workbook.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
from reportlab.lib.utils import ImageReader

from config import settings
from utils.file_manager import ensure_directory, build_output_path

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Brand / Palette
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _safe_str(value: Any, default: str = "") -> str:
    return str(value) if value is not None else default

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def _format_number(value: Any, decimals: int = 1) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.{decimals}f}"
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
    norm = str(priority).strip().lower()
    return mapping.get(norm, str(priority))

def _priority_color(priority: Any) -> colors.Color:
    return PRIORITY_COLORS.get(_normalize_priority(priority), GREY_600)

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

def _escape_xml(value: Any, default: Any = None) -> str:
    text = _safe_str(value, _safe_str(default))
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _find_logo(directory: Path, candidates: List[str]) -> Optional[Path]:
    if not directory.exists():
        return None
    for fname in candidates:
        path = directory / fname
        if path.exists():
            return path
    # case‑insensitive fallback
    names = {name.lower() for name in candidates}
    for path in directory.iterdir():
        if path.is_file() and path.name.lower() in names:
            return path
    return None

# ------------------------------------------------------------------------------
# Base PDF Exporter
# ------------------------------------------------------------------------------
class _BasePDFExporter:
    """Common functionality for both PDF types."""

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})
        self.decimal_precision = self.config.get(
            "decimal_precision",
            getattr(settings, "SCORE_DECIMAL_PRECISION", 1),
        )
        self.generated_at = datetime.now()
        self.styles = self._build_styles()
        self._logo_paths = self._locate_logos()

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
            "table_header": ParagraphStyle(
                "TableHeader",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=5.8,
                leading=7,
                textColor=WHITE,
                alignment=TA_CENTER,
            ),
            "table_cell": ParagraphStyle(
                "TableCell",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=5.8,
                leading=7,
                textColor=GREY_800,
            ),
            "table_cell_bold": ParagraphStyle(
                "TableCellBold",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=5.8,
                leading=7,
                textColor=GREY_800,
            ),
        }

    def _locate_logos(self) -> Dict[str, Optional[Path]]:
        """Locate JESA and ENSAM logos."""
        # Try multiple possible directories
        base_dir = Path(settings.backend.BASE_DIR)
        candidates_dirs = [
            base_dir / "assets" / "logos",
            base_dir / "assets" / "logo",
            base_dir / "assets",
        ]
        jesa_path = None
        ensam_path = None
        for d in candidates_dirs:
            if not d.exists():
                continue
            if jesa_path is None:
                jesa_path = _find_logo(d, ["jesa_logo.png", "JESA_logo.png", "jesa.png", "JESA.png"])
            if ensam_path is None:
                ensam_path = _find_logo(d, ["ensam_logo.png", "ENSAM_logo.png", "ensam.png", "ENSAM.png"])
        return {"jesa": jesa_path, "ensam": ensam_path}

    def _draw_header_footer(self, canvas, doc, title_prefix=""):
        """Standard header/footer with logos and page numbers."""
        canvas.saveState()
        width, height = A4

        # Header line
        canvas.setStrokeColor(GREY_200)
        canvas.setLineWidth(0.5)
        canvas.line(12*mm, height - 12*mm, width - 12*mm, height - 12*mm)

        # Logos
        if self._logo_paths.get("jesa"):
            try:
                img = ImageReader(str(self._logo_paths["jesa"]))
                canvas.drawImage(img, 12*mm, height - 16*mm, width=80, height=40, preserveAspectRatio=True)
            except Exception as e:
                logger.warning(f"Could not draw JESA logo: {e}")
        if self._logo_paths.get("ensam"):
            try:
                img = ImageReader(str(self._logo_paths["ensam"]))
                canvas.drawImage(img, width - 92*mm, height - 16*mm, width=80, height=40, preserveAspectRatio=True)
            except Exception as e:
                logger.warning(f"Could not draw ENSAM logo: {e}")

        # Title text
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(JESA_DARK)
        canvas.drawString(12*mm, height - 9*mm, "JESA DMAT")

        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(GREY_600)
        canvas.drawRightString(width - 12*mm, height - 9*mm, title_prefix + " — Industrial Digital Maturity Assessment")

        # Footer
        canvas.setStrokeColor(GREY_200)
        canvas.line(12*mm, 8*mm, width - 12*mm, 8*mm)
        canvas.setFont("Helvetica", 5.8)
        canvas.setFillColor(GREY_600)
        canvas.drawString(12*mm, 4.5*mm, "JESA DMAT • Digital Maturity Assessment")
        canvas.drawRightString(width - 12*mm, 4.5*mm, f"Page {doc.page}")

        canvas.restoreState()

# ------------------------------------------------------------------------------
# PDF Score Summary (2 pages)
# ------------------------------------------------------------------------------
class PDFScoreSummaryExporter(_BasePDFExporter):
    """Generates a concise 2‑page PDF with DMI, pillars, dimensions, gaps, TPI, priorities."""

    def export(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[Any]] = None,
        tpi_results: Optional[List[Any]] = None,
        priority_results: Optional[List[Any]] = None,
        output_path: Optional[Path] = None,
        assessment_id: Optional[str] = None,
    ) -> Path:

        if output_path is None:
            suffix = f"_{assessment_id}" if assessment_id else ""
            filename = f"JESA_DMAT_Score_Summary{suffix}.pdf"
            output_path = build_output_path(filename)

        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=12*mm,
            leftMargin=12*mm,
            topMargin=20*mm,  # increased for logos
            bottomMargin=14*mm,
            title="Score Summary – JESA DMAT",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment – Scores",
        )

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main_frame")
        page_template = PageTemplate(
            id="ScoreSummary",
            frames=frame,
            onPage=lambda canvas, doc: self._draw_header_footer(canvas, doc, "Score Summary"),
        )
        doc.addPageTemplates([page_template])

        story = []
        self._build_page1(story, aggregation_results, assessment_id)
        story.append(PageBreak())
        self._build_page2(story, aggregation_results, gap_results, tpi_results, priority_results)

        doc.build(story)
        return output_path

    def _build_page1(self, story, results, assessment_id):
        metadata = results.get("metadata", {})
        site_name = metadata.get("site_name", "Industrial Plant")
        dmi = results.get("dmi")
        dmi_score = _get(dmi, "score", results.get("dmi_score"))
        dmi_level = _get(dmi, "level_name", results.get("dmi_level_name", results.get("dmi_level", "—")))

        story.append(Paragraph("DIGITAL MATURITY SCORE SUMMARY", self.styles["title"]))
        story.append(Paragraph(
            f"{_escape_xml(site_name)} • Assessment: {_escape_xml(assessment_id or metadata.get('assessment_id', 'N/A'))}",
            self.styles["subtitle"]
        ))

        # KPI table
        kpi_data = [
            [Paragraph(_format_number(dmi_score, self.decimal_precision), self.styles["kpi"]),
             Paragraph(_escape_xml(dmi_level, "—"), self.styles["kpi"])],
            [Paragraph("DIGITAL MATURITY INDEX", self.styles["kpi_label"]),
             Paragraph("MATURITY LEVEL", self.styles["kpi_label"])],
        ]
        kpi_table = Table(kpi_data, colWidths=[85*mm, 85*mm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GREY_100),
            ("BOX", (0,0), (-1,-1), 0.8, JESA_GREEN),
            ("INNERGRID", (0,0), (-1,-1), 0.4, GREY_200),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,0), 8),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 4*mm))

        # Pillars
        story.append(Paragraph("1. Pillar Scores", self.styles["h1"]))
        pillars = results.get("pillars", {})
        pillar_iter = pillars.values() if isinstance(pillars, Mapping) else _as_list(pillars)
        rows = [[Paragraph("Pillar", self.styles["table_header"]),
                 Paragraph("Score", self.styles["table_header"]),
                 Paragraph("Maturity", self.styles["table_header"])]]
        for res in pillar_iter:
            rows.append([
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table_cell"]),
            ])
        if len(rows) == 1:
            rows.append([Paragraph("No pillar results", self.styles["table_cell"]), "", ""])

        tab = Table(rows, colWidths=[90*mm, 35*mm, 45*mm], repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ]))
        story.append(tab)
        story.append(Spacer(1, 4*mm))

        # Dimensions
        story.append(Paragraph("2. Dimension Scores", self.styles["h1"]))
        dimensions = results.get("dimensions", {})
        dim_iter = dimensions.values() if isinstance(dimensions, Mapping) else _as_list(dimensions)
        rows_dim = [[Paragraph("ID", self.styles["table_header"]),
                     Paragraph("Dimension", self.styles["table_header"]),
                     Paragraph("Score", self.styles["table_header"]),
                     Paragraph("Level", self.styles["table_header"])]]
        for res in dim_iter:
            rows_dim.append([
                Paragraph(_escape_xml(_get(res, "entity_id", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table_cell"]),
            ])
        if len(rows_dim) == 1:
            rows_dim.append(["", Paragraph("No dimensions", self.styles["table_cell"]), "", ""])

        tab_dim = Table(rows_dim, colWidths=[20*mm, 85*mm, 30*mm, 35*mm], repeatRows=1)
        tab_dim.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]))
        story.append(tab_dim)

    def _build_page2(self, story, results, gap_results, tpi_results, priority_results):
        story.append(Paragraph("3. Gap & Priority Analysis", self.styles["h1"]))

        # Gaps
        story.append(Paragraph("Gap Scores", self.styles["h2"]))
        gap_rows = [[Paragraph("Entity", self.styles["table_header"]),
                     Paragraph("Type", self.styles["table_header"]),
                     Paragraph("Current", self.styles["table_header"]),
                     Paragraph("Target", self.styles["table_header"]),
                     Paragraph("Gap", self.styles["table_header"])]]
        for gap in gap_results or []:
            gap_rows.append([
                Paragraph(_escape_xml(_get(gap, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(gap, "entity_type", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "current_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "target_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "gap"), 1), self.styles["table_cell"]),
            ])
        if len(gap_rows) == 1:
            gap_rows.append([Paragraph("No gaps", self.styles["table_cell"]), "", "", "", ""])
        gap_tab = Table(gap_rows, colWidths=[65*mm, 30*mm, 25*mm, 25*mm, 25*mm], repeatRows=1)
        gap_tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]))
        story.append(gap_tab)
        story.append(Spacer(1, 3*mm))

        # TPI
        story.append(Paragraph("Transformation Priority Index (TPI)", self.styles["h2"]))
        sorted_tpi = sorted(tpi_results or [], key=lambda x: -_safe_float(_get(x, "tpi_score", 0)))
        tpi_rows = [[Paragraph("#", self.styles["table_header"]),
                     Paragraph("Dimension", self.styles["table_header"]),
                     Paragraph("TPI", self.styles["table_header"]),
                     Paragraph("Gap", self.styles["table_header"]),
                     Paragraph("Priority", self.styles["table_header"])]]
        for rank, item in enumerate(sorted_tpi, 1):
            priority = _normalize_priority(_get(item, "priority_category", _get(item, "priority", "")))
            tpi_rows.append([
                Paragraph(str(rank), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(item, "dimension_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(item, "tpi_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(item, "gap"), 1), self.styles["table_cell"]),
                Paragraph(_escape_xml(priority or "—"), self.styles["table_cell"]),
            ])
        if len(tpi_rows) == 1:
            tpi_rows.append(["", Paragraph("No TPI", self.styles["table_cell"]), "", "", ""])
        tpi_tab = Table(tpi_rows, colWidths=[12*mm, 80*mm, 25*mm, 25*mm, 28*mm], repeatRows=1)
        tpi_cmds = [
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]
        for i, item in enumerate(sorted_tpi, 1):
            pri = _normalize_priority(_get(item, "priority_category", ""))
            if pri:
                tpi_cmds.append(("BACKGROUND", (4,i), (4,i), _priority_color(pri)))
                if pri != "Medium":
                    tpi_cmds.append(("TEXTCOLOR", (4,i), (4,i), WHITE))
        tpi_tab.setStyle(TableStyle(tpi_cmds))
        story.append(tpi_tab)

        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("This document presents only the numerical scores. Detailed recommendations and roadmap are available in the Full Report.", self.styles["small"]))

# ------------------------------------------------------------------------------
# PDF Full Report (Comprehensive, reproduces Excel content)
# ------------------------------------------------------------------------------
class PDFFullReportExporter(_BasePDFExporter):
    """Generates a comprehensive PDF with all data from the Excel workbook."""

    def export(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[Any]] = None,
        tpi_results: Optional[List[Any]] = None,
        priority_results: Optional[List[Any]] = None,
        roadmap: Optional[List[Any]] = None,
        output_path: Optional[Path] = None,
        assessment_id: Optional[str] = None,
    ) -> Path:

        if output_path is None:
            suffix = f"_{assessment_id}" if assessment_id else ""
            filename = f"JESA_DMAT_Full_Report{suffix}.pdf"
            output_path = build_output_path(filename)

        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=12*mm,
            leftMargin=12*mm,
            topMargin=20*mm,
            bottomMargin=14*mm,
            title="Full Report – JESA DMAT",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment – Full Report",
        )

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main_frame")
        page_template = PageTemplate(
            id="FullReport",
            frames=frame,
            onPage=lambda canvas, doc: self._draw_header_footer(canvas, doc, "Full Report"),
        )
        doc.addPageTemplates([page_template])

        story = []
        self._build_page1(story, aggregation_results, assessment_id)
        story.append(PageBreak())
        self._build_page2(story, aggregation_results, gap_results, tpi_results, priority_results)
        story.append(PageBreak())
        self._build_indicator_details(story, aggregation_results)
        story.append(PageBreak())
        self._build_recommendations(story, priority_results)
        story.append(PageBreak())
        self._build_roadmap(story, roadmap)
        story.append(PageBreak())
        self._build_metadata(story, aggregation_results, assessment_id)

        doc.build(story)
        return output_path

    def _build_page1(self, story, results, assessment_id):
        metadata = results.get("metadata", {})
        site_name = metadata.get("site_name", "Industrial Plant")
        dmi = results.get("dmi")
        dmi_score = _get(dmi, "score", results.get("dmi_score"))
        dmi_level = _get(dmi, "level_name", results.get("dmi_level_name", results.get("dmi_level", "—")))

        story.append(Paragraph("DIGITAL MATURITY FULL REPORT", self.styles["title"]))
        story.append(Paragraph(
            f"{_escape_xml(site_name)} • Assessment: {_escape_xml(assessment_id or metadata.get('assessment_id', 'N/A'))}",
            self.styles["subtitle"]
        ))

        # KPI table
        kpi_data = [
            [Paragraph(_format_number(dmi_score, self.decimal_precision), self.styles["kpi"]),
             Paragraph(_escape_xml(dmi_level, "—"), self.styles["kpi"])],
            [Paragraph("DIGITAL MATURITY INDEX", self.styles["kpi_label"]),
             Paragraph("MATURITY LEVEL", self.styles["kpi_label"])],
        ]
        kpi_table = Table(kpi_data, colWidths=[85*mm, 85*mm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GREY_100),
            ("BOX", (0,0), (-1,-1), 0.8, JESA_GREEN),
            ("INNERGRID", (0,0), (-1,-1), 0.4, GREY_200),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,0), 8),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 4*mm))

        # Pillars
        story.append(Paragraph("1. Pillar Scores", self.styles["h1"]))
        pillars = results.get("pillars", {})
        pillar_iter = pillars.values() if isinstance(pillars, Mapping) else _as_list(pillars)
        rows = [[Paragraph("Pillar", self.styles["table_header"]),
                 Paragraph("Score", self.styles["table_header"]),
                 Paragraph("Maturity", self.styles["table_header"])]]
        for res in pillar_iter:
            rows.append([
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table_cell"]),
            ])
        if len(rows) == 1:
            rows.append([Paragraph("No pillar results", self.styles["table_cell"]), "", ""])
        tab = Table(rows, colWidths=[90*mm, 35*mm, 45*mm], repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ]))
        story.append(tab)
        story.append(Spacer(1, 4*mm))

        # Dimensions
        story.append(Paragraph("2. Dimension Scores", self.styles["h1"]))
        dimensions = results.get("dimensions", {})
        dim_iter = dimensions.values() if isinstance(dimensions, Mapping) else _as_list(dimensions)
        rows_dim = [[Paragraph("ID", self.styles["table_header"]),
                     Paragraph("Dimension", self.styles["table_header"]),
                     Paragraph("Score", self.styles["table_header"]),
                     Paragraph("Level", self.styles["table_header"])]]
        for res in dim_iter:
            rows_dim.append([
                Paragraph(_escape_xml(_get(res, "entity_id", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table_cell"]),
            ])
        if len(rows_dim) == 1:
            rows_dim.append(["", Paragraph("No dimensions", self.styles["table_cell"]), "", ""])
        tab_dim = Table(rows_dim, colWidths=[20*mm, 85*mm, 30*mm, 35*mm], repeatRows=1)
        tab_dim.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]))
        story.append(tab_dim)

    def _build_page2(self, story, results, gap_results, tpi_results, priority_results):
        story.append(Paragraph("3. Gap & Priority Analysis", self.styles["h1"]))

        # Gaps
        story.append(Paragraph("Gap Scores", self.styles["h2"]))
        gap_rows = [[Paragraph("Entity", self.styles["table_header"]),
                     Paragraph("Type", self.styles["table_header"]),
                     Paragraph("Current", self.styles["table_header"]),
                     Paragraph("Target", self.styles["table_header"]),
                     Paragraph("Gap", self.styles["table_header"])]]
        for gap in gap_results or []:
            gap_rows.append([
                Paragraph(_escape_xml(_get(gap, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(gap, "entity_type", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "current_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "target_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(gap, "gap"), 1), self.styles["table_cell"]),
            ])
        if len(gap_rows) == 1:
            gap_rows.append([Paragraph("No gaps", self.styles["table_cell"]), "", "", "", ""])
        gap_tab = Table(gap_rows, colWidths=[65*mm, 30*mm, 25*mm, 25*mm, 25*mm], repeatRows=1)
        gap_tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]))
        story.append(gap_tab)
        story.append(Spacer(1, 3*mm))

        # TPI
        story.append(Paragraph("Transformation Priority Index (TPI)", self.styles["h2"]))
        sorted_tpi = sorted(tpi_results or [], key=lambda x: -_safe_float(_get(x, "tpi_score", 0)))
        tpi_rows = [[Paragraph("#", self.styles["table_header"]),
                     Paragraph("Dimension", self.styles["table_header"]),
                     Paragraph("TPI", self.styles["table_header"]),
                     Paragraph("Gap", self.styles["table_header"]),
                     Paragraph("Priority", self.styles["table_header"])]]
        for rank, item in enumerate(sorted_tpi, 1):
            priority = _normalize_priority(_get(item, "priority_category", _get(item, "priority", "")))
            tpi_rows.append([
                Paragraph(str(rank), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(item, "dimension_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(item, "tpi_score"), 1), self.styles["table_cell"]),
                Paragraph(_format_number(_get(item, "gap"), 1), self.styles["table_cell"]),
                Paragraph(_escape_xml(priority or "—"), self.styles["table_cell"]),
            ])
        if len(tpi_rows) == 1:
            tpi_rows.append(["", Paragraph("No TPI", self.styles["table_cell"]), "", "", ""])
        tpi_tab = Table(tpi_rows, colWidths=[12*mm, 80*mm, 25*mm, 25*mm, 28*mm], repeatRows=1)
        tpi_cmds = [
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]
        for i, item in enumerate(sorted_tpi, 1):
            pri = _normalize_priority(_get(item, "priority_category", ""))
            if pri:
                tpi_cmds.append(("BACKGROUND", (4,i), (4,i), _priority_color(pri)))
                if pri != "Medium":
                    tpi_cmds.append(("TEXTCOLOR", (4,i), (4,i), WHITE))
        tpi_tab.setStyle(TableStyle(tpi_cmds))
        story.append(tpi_tab)

    def _build_indicator_details(self, story, results):
        story.append(Paragraph("4. Indicator Details", self.styles["h1"]))
        indicators = results.get("indicators", {})
        if not indicators:
            story.append(Paragraph("No indicators found.", self.styles["body"]))
            return
        rows = [[Paragraph("Indicator ID", self.styles["table_header"]),
                 Paragraph("Indicator Name", self.styles["table_header"]),
                 Paragraph("Score", self.styles["table_header"]),
                 Paragraph("Level", self.styles["table_header"]),
                 Paragraph("Parent ID", self.styles["table_header"])]]
        for _, res in indicators.items():
            rows.append([
                Paragraph(_escape_xml(_get(res, "entity_id", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table_cell"]),
                Paragraph(_format_number(_get(res, "score"), 1), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table_cell"]),
                Paragraph(_escape_xml(_get(res, "parent_id", "—")), self.styles["table_cell"]),
            ])
        tab = Table(rows, colWidths=[30*mm, 80*mm, 20*mm, 20*mm, 20*mm], repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ]))
        story.append(tab)

    def _build_recommendations(self, story, priority_results):
        story.append(Paragraph("5. Recommendations", self.styles["h1"]))
        if not priority_results:
            story.append(Paragraph("No recommendations available.", self.styles["body"]))
            return
        rows = [[Paragraph("Dimension", self.styles["table_header"]),
                 Paragraph("Priority", self.styles["table_header"]),
                 Paragraph("Recommendation", self.styles["table_header"]),
                 Paragraph("Effort", self.styles["table_header"]),
                 Paragraph("Expected Impact", self.styles["table_header"])]]
        for pr in priority_results:
            for rec in pr.recommendations:
                rows.append([
                    Paragraph(_escape_xml(pr.dimension_name or pr.dimension_id), self.styles["table_cell"]),
                    Paragraph(_escape_xml(_normalize_priority(pr.priority_category)), self.styles["table_cell"]),
                    Paragraph(_escape_xml(rec.title or rec.recommendation_id), self.styles["table_cell"]),
                    Paragraph(_escape_xml(rec.effort or ""), self.styles["table_cell"]),
                    Paragraph(_escape_xml(rec.expected_impact or ""), self.styles["table_cell"]),
                ])
        tab = Table(rows, colWidths=[40*mm, 25*mm, 80*mm, 20*mm, 25*mm], repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(tab)

    def _build_roadmap(self, story, roadmap):
        story.append(Paragraph("6. Transformation Roadmap", self.styles["h1"]))
        if not roadmap:
            story.append(Paragraph("No roadmap available.", self.styles["body"]))
            return
        rows = [[Paragraph("Phase", self.styles["table_header"]),
                 Paragraph("Action", self.styles["table_header"]),
                 Paragraph("TPI", self.styles["table_header"]),
                 Paragraph("Priority", self.styles["table_header"]),
                 Paragraph("Effort", self.styles["table_header"])]]
        for phase in roadmap:
            for item in phase.items:
                rows.append([
                    Paragraph(_escape_xml(phase.phase_name), self.styles["table_cell"]),
                    Paragraph(_escape_xml(item.title), self.styles["table_cell"]),
                    Paragraph(_format_number(item.tpi_score, 1), self.styles["table_cell"]),
                    Paragraph(_escape_xml(_normalize_priority(item.priority)), self.styles["table_cell"]),
                    Paragraph(_escape_xml(item.effort or ""), self.styles["table_cell"]),
                ])
        tab = Table(rows, colWidths=[30*mm, 80*mm, 20*mm, 20*mm, 20*mm], repeatRows=1)
        tab.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
            ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(tab)

    def _build_metadata(self, story, results, assessment_id):
        story.append(Paragraph("7. Assessment Metadata", self.styles["h1"]))
        metadata = results.get("metadata", {})
        rows = [
            ["Assessment ID", assessment_id or metadata.get("assessment_id", "")],
            ["Site Name", metadata.get("site_name", "")],
            ["Assessment Date", metadata.get("assessment_date", "")],
            ["Evaluator", metadata.get("evaluator", "")],
            ["Total Indicators", metadata.get("total_indicators", 0)],
            ["Total Dimensions", metadata.get("total_dimensions", 0)],
            ["Total Pillars", metadata.get("total_pillars", 0)],
        ]
        data = [[Paragraph(field, self.styles["table_cell_bold"]), Paragraph(str(value), self.styles["table_cell"])] for field, value in rows]
        tab = Table(data, colWidths=[80*mm, 110*mm])
        tab.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, GREY_200),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [GREY_100, WHITE]),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(tab)

# ------------------------------------------------------------------------------
# Public utilities
# ------------------------------------------------------------------------------
def export_score_summary(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[Any]] = None,
    tpi_results: Optional[List[Any]] = None,
    priority_results: Optional[List[Any]] = None,
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    exporter = PDFScoreSummaryExporter()
    return exporter.export(
        aggregation_results,
        gap_results,
        tpi_results,
        priority_results,
        output_path,
        assessment_id,
    )

def export_full_report(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[Any]] = None,
    tpi_results: Optional[List[Any]] = None,
    priority_results: Optional[List[Any]] = None,
    roadmap: Optional[List[Any]] = None,
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    exporter = PDFFullReportExporter()
    return exporter.export(
        aggregation_results,
        gap_results,
        tpi_results,
        priority_results,
        roadmap,
        output_path,
        assessment_id,
    )