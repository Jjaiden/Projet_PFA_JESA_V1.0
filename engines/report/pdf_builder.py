"""
pdf_builder.py — JDMAF PDF report generation.

Responsibilities:
    - generate a professional PDF report;
    - present KPIs;
    - present maturity results;
    - present gaps;
    - present priorities;
    - present the roadmap;
    - present recommendations.

This module performs no business calculations.
It only consumes already-computed results.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from engines.decision.priority import PriorityResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.roadmap import RoadmapPhase


class PDFBuilder:
    """
    Constructeur de rapport PDF JDMAF.
    """

    def __init__(
        self,
        title: str = (
            "JDMAF — Digital Maturity Assessment"
        ),
        author: str = "JESA",
    ) -> None:

        self.title = title
        self.author = author

    # ========================================================================
    # API PRINCIPALE
    # ========================================================================

    def build(
        self,
        output_path: str | Path,
        dashboard_data: Optional[
            Any
        ] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
        gap_results: Optional[
            list[GapResult]
        ] = None,
        tpi_results: Optional[
            list[TPIResult]
        ] = None,
        priority_results: Optional[
            list[PriorityResult]
        ] = None,
        roadmap: Optional[
            list[RoadmapPhase]
        ] = None,
    ) -> Path:
        """
        Génère le rapport PDF.

        Args:
            output_path:
                Chemin du PDF à créer.

            dashboard_data:
                Objet DashboardData optionnel.

            metadata:
                Informations de l'assessment.

            gap_results:
                Résultats Gap.

            tpi_results:
                Résultats TPI.

            priority_results:
                Résultats de priorisation.

            roadmap:
                Feuille de route.

        Returns:
            Path du PDF créé.
        """

        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import (
                TA_CENTER,
                TA_LEFT,
            )
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import (
                ParagraphStyle,
                getSampleStyleSheet,
            )
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

        except ImportError as exc:

            raise ImportError(
                "reportlab is required to "
                "generate the PDF. "
                "Install it with: pip install reportlab"
            ) from exc

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata = dict(
            metadata or {}
        )

        gap_results = gap_results or []
        tpi_results = tpi_results or []
        priority_results = (
            priority_results or []
        )
        roadmap = roadmap or []

        # --------------------------------------------------------------------
        # DOCUMENT
        # --------------------------------------------------------------------

        document = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=self.title,
            author=self.author,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "JDMAFTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=15,
        )

        heading_style = ParagraphStyle(
            "JDMAFHeading",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=8,
        )

        subheading_style = ParagraphStyle(
            "JDMAFSubHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=5,
        )

        normal_style = ParagraphStyle(
            "JDMAFNormal",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
        )

        small_style = ParagraphStyle(
            "JDMAFSMall",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
        )

        story = []

        # --------------------------------------------------------------------
        # PAGE DE GARDE
        # --------------------------------------------------------------------

        story.append(
            Spacer(
                1,
                35 * mm,
            )
        )

        story.append(
            Paragraph(
                self.title,
                title_style,
            )
        )

        assessment_id = metadata.get(
            "assessment_id",
            metadata.get(
                "Assessment_ID",
                "Not provided",
            ),
        )

        plant_name = metadata.get(
            "plant_name",
            metadata.get(
                "Plant_Name",
                "Industrial site",
            ),
        )

        story.append(
            Paragraph(
                f"<b>Assessment:</b> "
                f"{self._escape(assessment_id)}",
                normal_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Site :</b> "
                f"{self._escape(plant_name)}",
                normal_style,
            )
        )

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        story.append(
            Paragraph(
                f"Report generated on "
                f"{datetime.now():%d/%m/%Y at %H:%M}",
                normal_style,
            )
        )

        story.append(
            PageBreak()
        )

        # --------------------------------------------------------------------
        # EXECUTIVE SUMMARY
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "1. Executive summary",
                heading_style,
            )
        )

        kpis = self._extract_kpis(
            dashboard_data,
            gap_results,
            tpi_results,
            priority_results,
            roadmap,
        )

        kpi_table = self._build_kpi_table(
            kpis
        )

        story.append(
            kpi_table
        )

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        summary_text = self._build_summary_text(
            kpis
        )

        story.append(
            Paragraph(
                summary_text,
                normal_style,
            )
        )

        # --------------------------------------------------------------------
        # MATURITE
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "2. Maturity overview",
                heading_style,
            )
        )

        maturity_df = (
            self._extract_maturity(
                dashboard_data
            )
        )

        if not maturity_df.empty:

            story.append(
                self._dataframe_to_table(
                    maturity_df,
                    small_style,
                )
            )

        else:

            story.append(
                Paragraph(
                    "No maturity data available.",
                    normal_style,
                )
            )

        # --------------------------------------------------------------------
        # GAP
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "3. Gap analysis",
                heading_style,
            )
        )

        gap_df = (
            self._build_gap_dataframe(
                gap_results
            )
        )

        if not gap_df.empty:

            story.append(
                self._dataframe_to_table(
                    gap_df,
                    small_style,
                )
            )

        else:

            story.append(
                Paragraph(
                    "No gap available.",
                    normal_style,
                )
            )

        # --------------------------------------------------------------------
        # PRIORISATION
        # --------------------------------------------------------------------

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "4. Decision analysis",
                heading_style,
            )
        )

        priority_df = (
            self._build_priority_dataframe(
                priority_results,
                tpi_results,
            )
        )

        if not priority_df.empty:

            story.append(
                self._dataframe_to_table(
                    priority_df,
                    small_style,
                )
            )

        else:

            story.append(
                Paragraph(
                    "No decision analysis available.",
                    normal_style,
                )
            )

        # --------------------------------------------------------------------
        # ROADMAP
        # --------------------------------------------------------------------

        story.append(
            Paragraph(
                "5. Roadmap",
                heading_style,
            )
        )

        if roadmap:

            for phase in roadmap:

                story.append(
                    Paragraph(
                        (
                            f"{self._escape(phase.phase_name)} "
                            f"— {self._escape(phase.horizon)}"
                        ),
                        subheading_style,
                    )
                )

                phase_rows = []

                for item in phase.items:

                    phase_rows.append(
                        [
                            item.recommendation_id,
                            item.dimension_id,
                            item.title,
                            item.priority,
                            (
                                f"{item.tpi_score:.3f}"
                                if item.tpi_score
                                is not None
                                else "-"
                            ),
                            (
                                f"{item.gap:.2f}"
                                if item.gap
                                is not None
                                else "-"
                            ),
                        ]
                    )

                if phase_rows:

                    table_data = [
                        [
                            "ID",
                            "Dimension",
                            "Action",
                            "Priority",
                            "TPI",
                            "Gap",
                        ]
                    ] + phase_rows

                    story.append(
                        self._make_table(
                            table_data,
                            small_style,
                            widths=[
                                22 * mm,
                                22 * mm,
                                75 * mm,
                                20 * mm,
                                15 * mm,
                                15 * mm,
                            ],
                        )
                    )

        else:

            story.append(
                Paragraph(
                    "No roadmap available.",
                    normal_style,
                )
            )

        # --------------------------------------------------------------------
        # RECOMMANDATIONS
        # --------------------------------------------------------------------

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "6. Recommendations",
                heading_style,
            )
        )

        if priority_results:

            for priority in priority_results:

                if not priority.recommendations:
                    continue

                story.append(
                    Paragraph(
                        (
                            f"{self._escape(priority.dimension_id)} "
                            f"— "
                            f"{self._escape(priority.dimension_name)}"
                        ),
                        subheading_style,
                    )
                )

                for recommendation in (
                    priority.recommendations
                ):

                    story.append(
                        Paragraph(
                            (
                                f"<b>"
                                f"{self._escape(recommendation.title)}"
                                f"</b>"
                            ),
                            normal_style,
                        )
                    )

                    if recommendation.description:

                        story.append(
                            Paragraph(
                                self._escape(
                                    recommendation.description
                                ),
                                small_style,
                            )
                        )

                    if recommendation.detailed_actions:

                        actions = "<br/>".join(
                            f"• {self._escape(action)}"
                            for action
                            in recommendation.detailed_actions
                        )

                        story.append(
                            Paragraph(
                                f"<b>Actions:</b><br/>{actions}",
                                small_style,
                            )
                        )

                    story.append(
                        Spacer(
                            1,
                            3 * mm,
                        )
                    )

        else:

            story.append(
                Paragraph(
                    "No recommendation available.",
                    normal_style,
                )
            )

        # --------------------------------------------------------------------
        # BUILD
        # --------------------------------------------------------------------

        document.build(
            story,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer,
        )

        return output

    # ========================================================================
    # KPI
    # ========================================================================

    @staticmethod
    def _extract_kpis(
        dashboard_data: Any,
        gap_results: list[GapResult],
        tpi_results: list[TPIResult],
        priority_results: list[PriorityResult],
        roadmap: list[RoadmapPhase],
    ) -> dict[str, Any]:

        if dashboard_data is not None:

            kpis = getattr(
                dashboard_data,
                "kpis",
                None,
            )

            if isinstance(
                kpis,
                Mapping,
            ):
                return dict(kpis)

        gaps = [
            result.gap
            for result in gap_results
        ]

        tpis = [
            result.tpi_score
            for result in tpi_results
        ]

        return {
            "average_gap": (
                sum(gaps) / len(gaps)
                if gaps
                else 0
            ),
            "max_gap": (
                max(gaps)
                if gaps
                else 0
            ),
            "average_tpi": (
                sum(tpis) / len(tpis)
                if tpis
                else None
            ),
            "critical_priorities": sum(
                1
                for result
                in priority_results
                if result.priority_category
                in {
                    "Critique",
                    "critical",
                }
            ),
            "roadmap_actions": sum(
                len(phase.items)
                for phase in roadmap
            ),
        }

    @staticmethod
    def _build_kpi_table(
        kpis: Mapping[str, Any],
    ):

        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Table,
            TableStyle,
        )

        values = [
            [
                "Average maturity",
                "Average gap",
                "Maximum gap",
                "Average TPI",
                "Critical priorities",
                "Roadmap actions",
            ],
            [
                PDFBuilder._format_value(
                    kpis.get(
                        "average_maturity"
                    )
                ),
                PDFBuilder._format_value(
                    kpis.get(
                        "average_gap"
                    )
                ),
                PDFBuilder._format_value(
                    kpis.get(
                        "max_gap"
                    )
                ),
                PDFBuilder._format_value(
                    kpis.get(
                        "average_tpi"
                    )
                ),
                PDFBuilder._format_value(
                    kpis.get(
                        "critical_priorities",
                        0,
                    )
                ),
                PDFBuilder._format_value(
                    kpis.get(
                        "roadmap_actions",
                        0,
                    )
                ),
            ],
        ]

        table = Table(
            values,
            colWidths=[
                27 * mm
                for _ in values[0]
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#1F4E78"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
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

        return table

    # ========================================================================
    # DATAFRAMES
    # ========================================================================

    @staticmethod
    def _extract_maturity(
        dashboard_data: Any,
    ) -> pd.DataFrame:

        if dashboard_data is None:
            return pd.DataFrame()

        maturity = getattr(
            dashboard_data,
            "maturity",
            None,
        )

        if isinstance(
            maturity,
            pd.DataFrame,
        ):
            return maturity.copy()

        return pd.DataFrame()

    @staticmethod
    def _build_gap_dataframe(
        gap_results: list[GapResult],
    ) -> pd.DataFrame:

        return pd.DataFrame(
            [
                {
                    "ID": result.entity_id,
                    "Name": result.entity_name,
                    "Type": result.entity_type,
                    "Current": round(
                        result.current_score,
                        2,
                    ),
                    "Target": round(
                        result.target_score,
                        2,
                    ),
                    "Gap": round(
                        result.gap,
                        2,
                    ),
                    "Priority": result.priority,
                }
                for result
                in gap_results
            ]
        )

    @staticmethod
    def _build_priority_dataframe(
        priority_results: list[
            PriorityResult
        ],
        tpi_results: list[TPIResult],
    ) -> pd.DataFrame:

        if priority_results:

            return pd.DataFrame(
                [
                    {
                        "Dimension": (
                            result.dimension_id
                        ),
                        "Name": (
                            result.dimension_name
                        ),
                        "Current": round(
                            result.current_score,
                            2,
                        ),
                        "Target": round(
                            result.target_score,
                            2,
                        ),
                        "Gap": round(
                            result.gap,
                            2,
                        ),
                        "TPI": (
                            round(
                                result.tpi_score,
                                3,
                            )
                            if result.tpi_score
                            is not None
                            else "-"
                        ),
                        "Priority": (
                            result.priority_category
                        ),
                    }
                    for result
                    in priority_results
                ]
            )

        return pd.DataFrame(
            [
                {
                    "Dimension": result.dimension_id,
                    "Name": result.dimension_name,
                    "Gap": round(
                        result.gap,
                        2,
                    ),
                    "TPI": round(
                        result.tpi_score,
                        3,
                    ),
                    "Priority": (
                        result.priority_category
                    ),
                }
                for result
                in tpi_results
            ]
        )

    # ========================================================================
    # TABLE HELPERS
    # ========================================================================

    @staticmethod
    def _dataframe_to_table(
        dataframe: pd.DataFrame,
        small_style: Any,
    ):

        data = [
            [
                str(column)
                for column
                in dataframe.columns
            ]
        ]

        for _, row in dataframe.iterrows():

            data.append(
                [
                    PDFBuilder._format_value(
                        value
                    )
                    for value
                    in row.tolist()
                ]
            )

        return PDFBuilder._make_table(
            data,
            small_style,
        )

    @staticmethod
    def _make_table(
        data: Sequence[
            Sequence[Any]
        ],
        small_style: Any,
        widths: Optional[
            Sequence[float]
        ] = None,
    ):

        from reportlab.lib import colors
        from reportlab.platypus import (
            Paragraph,
            Table,
            TableStyle,
        )

        formatted_data = []

        for row_index, row in enumerate(
            data
        ):

            formatted_row = []

            for value in row:

                style = small_style

                if row_index == 0:
                    formatted_row.append(
                        Paragraph(
                            f"<b>{PDFBuilder._escape(str(value))}</b>",
                            style,
                        )
                    )
                else:
                    formatted_row.append(
                        Paragraph(
                            PDFBuilder._escape(
                                str(value)
                            ),
                            style,
                        )
                    )

            formatted_data.append(
                formatted_row
            )

        table = Table(
            formatted_data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#1F4E78"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
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

        return table

    # ========================================================================
    # SUMMARY
    # ========================================================================

    @staticmethod
    def _build_summary_text(
        kpis: Mapping[str, Any],
    ) -> str:

        average_maturity = kpis.get(
            "average_maturity"
        )

        average_gap = kpis.get(
            "average_gap",
            0,
        )

        critical = kpis.get(
            "critical_priorities",
            0,
        )

        if average_maturity is None:
            maturity_text = (
                "The average maturity level "
                "is not available."
            )
        else:
            maturity_text = (
                f"The average maturity level "
                f"is <b>{average_maturity:.2f}/5</b>."
            )

        return (
            f"{maturity_text} "
            f"The average gap to targets "
            f"is <b>{average_gap:.2f}</b>. "
            f"The analysis identifies "
            f"<b>{critical}</b> critical priority(ies)."
        )

    # ========================================================================
    # FORMATAGE
    # ========================================================================

    @staticmethod
    def _format_value(
        value: Any,
    ) -> str:

        if value is None:
            return "-"

        try:

            if pd.isna(value):
                return "-"

        except (
            TypeError,
            ValueError,
        ):
            pass

        if isinstance(
            value,
            float,
        ):

            return f"{value:.2f}"

        return str(value)

    @staticmethod
    def _escape(
        value: Any,
    ) -> str:

        text = str(
            value
        )

        return (
            text.replace(
                "&",
                "&amp;",
            )
            .replace(
                "<",
                "&lt;",
            )
            .replace(
                ">",
                "&gt;",
            )
        )

    # ========================================================================
    # HEADER / FOOTER
    # ========================================================================

    def _header_footer(
        self,
        canvas: Any,
        document: Any,
    ) -> None:

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm

        canvas.saveState()

        width, height = A4

        canvas.setFont(
            "Helvetica",
            7,
        )

        canvas.setFillColor(
            colors.grey
        )

        canvas.drawString(
            15 * mm,
            10 * mm,
            self.author,
        )

        canvas.drawRightString(
            width - 15 * mm,
            10 * mm,
            f"Page {document.page}",
        )

        canvas.restoreState()


PDFReportBuilder = PDFBuilder