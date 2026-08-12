"""
Professional PDF exports for JESA DMAT.

Two distinct exports are provided:
- Score Summary (2 pages): DMI, pillar scores, dimension scores, gaps, TPI, priorities.
- Full Report (multiple pages): includes all score data + recommendations + roadmap details.

This module ONLY formats pre‑computed results.
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
from reportlab.lib.utils import ImageReader

from config import settings
from utils.file_manager import ensure_directory, build_output_path

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

# ------------------------------------------------------------------------------
# PDF Exporter – Base class
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

         # Line under logos
         canvas.setStrokeColor(GREY_200)
         canvas.setLineWidth(0.5)
         canvas.line(12*mm, height - 14*mm, width - 12*mm, height - 14*mm)

         canvas.restoreState()

    @staticmethod
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

    def _header_footer(self, canvas, doc, title_prefix=""):
        """Standard header/footer with page numbers."""
        canvas.saveState()
        width, height = A4

        # Header line
        canvas.setStrokeColor(GREY_200)
        canvas.setLineWidth(0.5)
        canvas.line(12*mm, height - 10*mm, width - 12*mm, height - 10*mm)

        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(JESA_DARK)
        canvas.drawString(12*mm, height - 7.5*mm, "JESA DMAT")

        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(GREY_600)
        canvas.drawRightString(width - 12*mm, height - 7.5*mm, title_prefix + " — Industrial Digital Maturity Assessment")

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
            topMargin=17*mm,
            bottomMargin=14*mm,
            title="Score Summary – JESA DMAT",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment – Scores",
        )

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main_frame")
        page_template = PageTemplate(
            id="ScoreSummary",
            frames=frame,
            onPage=lambda canvas, doc: self._header_footer(canvas, doc, "Score Summary"),
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
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table"]),
            ])
        if len(rows) == 1:
            rows.append([Paragraph("No pillar results", self.styles["table"]), "", ""])

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
                Paragraph(_escape_xml(_get(res, "entity_id", "—")), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table"]),
            ])
        if len(rows_dim) == 1:
            rows_dim.append(["", Paragraph("No dimensions", self.styles["table"]), "", ""])

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
                Paragraph(_escape_xml(_get(gap, "entity_name", "—")), self.styles["table"]),
                Paragraph(_escape_xml(_get(gap, "entity_type", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "current_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "target_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "gap"), 1), self.styles["table"]),
            ])
        if len(gap_rows) == 1:
            gap_rows.append([Paragraph("No gaps", self.styles["table"]), "", "", "", ""])
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
                Paragraph(str(rank), self.styles["table"]),
                Paragraph(_escape_xml(_get(item, "dimension_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(item, "tpi_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(item, "gap"), 1), self.styles["table"]),
                Paragraph(_escape_xml(priority or "—"), self.styles["table"]),
            ])
        if len(tpi_rows) == 1:
            tpi_rows.append(["", Paragraph("No TPI", self.styles["table"]), "", "", ""])
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
# PDF Full Report (includes recommendations, roadmap, etc.)
# ------------------------------------------------------------------------------
class PDFFullReportExporter(_BasePDFExporter):
    """Generates a comprehensive PDF with all assessment data + recommendations + roadmap."""

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
            topMargin=17*mm,
            bottomMargin=14*mm,
            title="Full Report – JESA DMAT",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment – Full Report",
        )

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main_frame")
        page_template = PageTemplate(
            id="FullReport",
            frames=frame,
            onPage=lambda canvas, doc: self._header_footer(canvas, doc, "Full Report"),
        )
        doc.addPageTemplates([page_template])

        story = []
        # Page 1: same as score summary's page 1
        self._build_page1(story, aggregation_results, assessment_id)
        story.append(PageBreak())
        # Page 2: gaps, TPI, priorities (like score summary)
        self._build_page2(story, aggregation_results, gap_results, tpi_results, priority_results)
        story.append(PageBreak())
        # Additional pages: recommendations, roadmap
        self._build_recommendations_and_roadmap(story, priority_results, roadmap)

        doc.build(story)
        return output_path

    def _build_page1(self, story, results, assessment_id):
        # Same as ScoreSummaryExporter._build_page1
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
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table"]),
            ])
        if len(rows) == 1:
            rows.append([Paragraph("No pillar results", self.styles["table"]), "", ""])

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
                Paragraph(_escape_xml(_get(res, "entity_id", "—")), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "entity_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(res, "score"), self.decimal_precision), self.styles["table"]),
                Paragraph(_escape_xml(_get(res, "level_name", "—")), self.styles["table"]),
            ])
        if len(rows_dim) == 1:
            rows_dim.append(["", Paragraph("No dimensions", self.styles["table"]), "", ""])

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
        # Same as ScoreSummaryExporter._build_page2
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
                Paragraph(_escape_xml(_get(gap, "entity_name", "—")), self.styles["table"]),
                Paragraph(_escape_xml(_get(gap, "entity_type", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "current_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "target_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(gap, "gap"), 1), self.styles["table"]),
            ])
        if len(gap_rows) == 1:
            gap_rows.append([Paragraph("No gaps", self.styles["table"]), "", "", "", ""])
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
                Paragraph(str(rank), self.styles["table"]),
                Paragraph(_escape_xml(_get(item, "dimension_name", "—")), self.styles["table"]),
                Paragraph(_format_number(_get(item, "tpi_score"), 1), self.styles["table"]),
                Paragraph(_format_number(_get(item, "gap"), 1), self.styles["table"]),
                Paragraph(_escape_xml(priority or "—"), self.styles["table"]),
            ])
        if len(tpi_rows) == 1:
            tpi_rows.append(["", Paragraph("No TPI", self.styles["table"]), "", "", ""])
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

    def _build_recommendations_and_roadmap(self, story, priority_results, roadmap):
        # Recommendations
        story.append(Paragraph("4. Recommendations", self.styles["h1"]))
        if priority_results:
            rows = [[Paragraph("Dimension", self.styles["table_header"]),
                     Paragraph("Priority", self.styles["table_header"]),
                     Paragraph("Recommendation", self.styles["table_header"])]]
            for pr in priority_results:
                for rec in pr.recommendations:
                    rows.append([
                        Paragraph(_escape_xml(pr.dimension_name or pr.dimension_id), self.styles["table"]),
                        Paragraph(_escape_xml(_normalize_priority(pr.priority_category)), self.styles["table"]),
                        Paragraph(_escape_xml(rec.title or rec.recommendation_id), self.styles["table"]),
                    ])
            if len(rows) == 1:
                rows.append([Paragraph("No recommendations", self.styles["table"]), "", ""])
            rec_tab = Table(rows, colWidths=[60*mm, 30*mm, 80*mm], repeatRows=1)
            rec_tab.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
                ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            story.append(rec_tab)
        else:
            story.append(Paragraph("No recommendations available.", self.styles["body"]))

        story.append(Spacer(1, 4*mm))

        # Roadmap
        story.append(Paragraph("5. Transformation Roadmap", self.styles["h1"]))
        if roadmap:
            rows = [[Paragraph("Phase", self.styles["table_header"]),
                     Paragraph("Action", self.styles["table_header"]),
                     Paragraph("TPI", self.styles["table_header"]),
                     Paragraph("Priority", self.styles["table_header"])]]
            for phase in roadmap:
                for item in phase.items:
                    rows.append([
                        Paragraph(_escape_xml(phase.phase_name), self.styles["table"]),
                        Paragraph(_escape_xml(item.title), self.styles["table"]),
                        Paragraph(_format_number(item.tpi_score, 1), self.styles["table"]),
                        Paragraph(_escape_xml(_normalize_priority(item.priority)), self.styles["table"]),
                    ])
            if len(rows) == 1:
                rows.append([Paragraph("No roadmap items", self.styles["table"]), "", "", ""])
            roadmap_tab = Table(rows, colWidths=[40*mm, 80*mm, 25*mm, 25*mm], repeatRows=1)
            roadmap_tab.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), JESA_GREEN),
                ("GRID", (0,0), (-1,-1), 0.35, GREY_200),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GREY_100]),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            story.append(roadmap_tab)
        else:
            story.append(Paragraph("No roadmap available.", self.styles["body"]))

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