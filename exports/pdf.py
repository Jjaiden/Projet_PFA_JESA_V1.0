"""
pdf.py — Professional Industrial Digital Maturity Assessment Report.

Responsibilities
----------------
- Generate a professional PDF assessment report.
- Present executive-level maturity results.
- Present DMI, pillar and dimension assessments.
- Present gap analysis.
- Present TPI prioritization.
- Present the priority matrix.
- Present the transformation roadmap.
- Present recommendations.
- Present assessment metadata.

This module does NOT perform calculations.
It only formats and presents precomputed assessment results.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from config import settings
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase
from utils.file_manager import ensure_directory, build_output_path


logger = settings.get_logger(__name__)


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
            settings.SCORE_DECIMAL_PRECISION,
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
            fontSize=24,
            leading=28,
            textColor=JESA_DARK,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),

        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=GREY_600,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),

        "section": ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=JESA_DARK,
            spaceBefore=8,
            spaceAfter=12,
        ),

        "subsection": ParagraphStyle(
            "SubsectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=JESA_GREEN,
            spaceBefore=8,
            spaceAfter=8,
        ),

        "body": ParagraphStyle(
            "BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=GREY_800,
            spaceAfter=6,
        ),

        "small": ParagraphStyle(
            "SmallText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=GREY_600,
        ),

        "table_header": ParagraphStyle(
            "TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),

        "table_body": ParagraphStyle(
            "TableBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=GREY_800,
        ),

        "kpi": ParagraphStyle(
            "KPI",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=JESA_GREEN,
            alignment=TA_CENTER,
        ),
    }
    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def export_assessment_results(
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

            suffix = (
                f"_{assessment_id}"
                if assessment_id
                else ""
            )

            filename = (
                f"industrial_digital_maturity_assessment"
                f"{suffix}.pdf"
            )

            output_path = build_output_path(filename)

        output_path = Path(output_path)

        ensure_directory(output_path.parent)

        metadata = aggregation_results.get(
            "metadata",
            {},
        )

        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
            title="Digital Maturity Assessment Report",
            author="JESA DMAT",
            subject="Industrial Digital Maturity Assessment",
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="normal",
        )

        doc.addPageTemplates(
            [
                PageTemplate(
                    id="AssessmentReport",
                    frames=frame,
                    onPage=self._draw_page_header_footer,
                )
            ]
        )

        story = []

        # --------------------------------------------------------------
        # COVER
        # --------------------------------------------------------------

        story.extend(
            self._build_cover_page(
                metadata,
                assessment_id,
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # EXECUTIVE SUMMARY
        # --------------------------------------------------------------

        story.extend(
            self._build_executive_summary(
                aggregation_results,
                gap_results or [],
                tpi_results or [],
                priority_results or [],
                roadmap or [],
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # DIGITAL MATURITY OVERVIEW
        # --------------------------------------------------------------

        story.extend(
            self._build_dmi_overview(
                aggregation_results
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # PILLARS
        # --------------------------------------------------------------

        story.extend(
            self._build_pillar_assessment(
                aggregation_results
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # DIMENSIONS
        # --------------------------------------------------------------

        story.extend(
            self._build_dimension_assessment(
                aggregation_results
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # GAP ANALYSIS
        # --------------------------------------------------------------

        story.extend(
            self._build_gap_analysis(
                gap_results or []
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # TPI
        # --------------------------------------------------------------

        story.extend(
            self._build_tpi_prioritization(
                tpi_results or []
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # PRIORITY MATRIX
        # --------------------------------------------------------------

        story.extend(
            self._build_priority_matrix(
                priority_results or []
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # ROADMAP
        # --------------------------------------------------------------

        story.extend(
            self._build_transformation_roadmap(
                roadmap or []
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # RECOMMENDATIONS
        # --------------------------------------------------------------

        story.extend(
            self._build_recommendations(
                priority_results or [],
                roadmap or [],
            )
        )

        story.append(PageBreak())

        # --------------------------------------------------------------
        # APPENDIX
        # --------------------------------------------------------------

        story.extend(
            self._build_metadata(
                aggregation_results,
                assessment_id,
            )
        )

        doc.build(story)

        logger.info(
            "Industrial PDF report generated: %s",
            output_path,
        )

        return output_path
    PDFReportGenerator = PDFExporter 