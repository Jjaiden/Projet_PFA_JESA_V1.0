"""
pdf.py — Génération de rapports PDF pour le JDMAF.

Responsabilités :
    - Générer un rapport PDF structuré contenant :
        - Résumé exécutif
        - DMI (Digital Maturity Index)
        - Piliers et dimensions
        - Écarts (gaps)
        - Priorités
        - Roadmap
    - Utiliser ReportLab pour la génération PDF
    - Produire un rapport professionnel avec mise en page soignée

Ce module n'utilise pas le moteur de calcul.
Il travaille uniquement sur les résultats déjà calculés.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Mapping

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem,
    Image,
    Flowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from config import settings, constants
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase
from utils.file_manager import build_output_path, ensure_directory


logger = settings.get_logger(__name__)


# ============================================================================
# FONTS
# ============================================================================

# Enregistrer les polices pour le support Unicode
try:
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFontFamily(
        "DejaVuSans",
        normal="DejaVuSans",
        bold="DejaVuSans-Bold",
    )
except:
    # Fallback pour les environnements sans DejaVu
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))


# ============================================================================
# RAPPORT PDF
# ============================================================================


class PDFReportGenerator:
    """
    Génère un rapport PDF professionnel pour les résultats JDMAF.

    Le rapport contient :
        - Page de garde
        - Résumé exécutif
        - DMI (Digital Maturity Index)
        - Analyse par pilier
        - Analyse par dimension
        - Écarts (gaps)
        - Priorités TPI
        - Roadmap
        - Annexes
    """

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        """
        Initialise le générateur de rapport PDF.

        Args:
            config: Configuration optionnelle (ex: couleurs, polices)
        """
        self.config = dict(config or {})

        # Couleurs du thème JESA
        self.colors = {
            "primary": colors.HexColor("#1A5276"),      # Bleu foncé JESA
            "secondary": colors.HexColor("#2E86C1"),    # Bleu clair
            "accent": colors.HexColor("#F39C12"),       # Orange
            "success": colors.HexColor("#27AE60"),      # Vert
            "warning": colors.HexColor("#F1C40F"),      # Jaune
            "danger": colors.HexColor("#E74C3C"),       # Rouge
            "gray": colors.HexColor("#7F8C8D"),         # Gris
            "light_gray": colors.HexColor("#ECF0F1"),   # Gris clair
            "white": colors.white,
            "black": colors.black,
        }

        self.styles = self._create_styles()

    # ========================================================================
    # API PRINCIPALE
    # ========================================================================

    def generate_report(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_path: Optional[Path] = None,
        assessment_id: Optional[str] = None,
        include_charts: bool = False,
    ) -> Path:
        """
        Génère un rapport PDF complet.

        Args:
            aggregation_results: Résultats de aggregation.py
            gap_results: Résultats du GapAnalysisEngine
            tpi_results: Résultats du TPIEngine
            priority_results: Résultats du PriorityEngine
            roadmap: Résultats du RoadmapEngine
            output_path: Chemin de sortie (si None, généré automatiquement)
            assessment_id: Identifiant de l'évaluation
            include_charts: Inclure des graphiques (nécessite matplotlib)

        Returns:
            Path: Chemin du fichier PDF généré.
        """
        # Construire le nom du fichier
        if output_path is None:
            suffix = f"_{assessment_id}" if assessment_id else ""
            filename = f"assessment_report{suffix}.pdf"
            output_path = build_output_path(filename)

        ensure_directory(output_path.parent)

        # Préparer le contenu du rapport
        story = self._build_story(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            assessment_id=assessment_id,
            include_charts=include_charts,
        )

        # Générer le PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm,
        )

        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        logger.info("Rapport PDF généré : %s", output_path)
        return output_path

    # ========================================================================
    # CONSTRUCTION DU RAPPORT
    # ========================================================================

    def _build_story(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        assessment_id: Optional[str] = None,
        include_charts: bool = False,
    ) -> List[Flowable]:
        """
        Construit la liste des éléments du rapport (story).
        """
        story = []

        # Page de garde
        self._add_cover_page(story, aggregation_results, assessment_id)

        # Résumé exécutif
        self._add_executive_summary(story, aggregation_results)

        # DMI
        self._add_dmi_section(story, aggregation_results)

        # Piliers
        self._add_pillars_section(story, aggregation_results)

        # Dimensions
        self._add_dimensions_section(story, aggregation_results)

        # Gaps
        if gap_results:
            self._add_gaps_section(story, gap_results)

        # TPI
        if tpi_results:
            self._add_tpi_section(story, tpi_results)

        # Priorisation
        if priority_results:
            self._add_priorities_section(story, priority_results)

        # Roadmap
        if roadmap:
            self._add_roadmap_section(story, roadmap)

        # Annexes
        self._add_annexes(story, aggregation_results)

        return story

    # ========================================================================
    # SECTIONS DU RAPPORT
    # ========================================================================

    def _add_cover_page(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
        assessment_id: Optional[str] = None,
    ) -> None:
        """
        Ajoute la page de garde.
        """
        metadata = results.get("metadata", {})
        dmi = results.get("dmi")

        # Titre
        story.append(Paragraph(
            "Rapport d'Évaluation de Maturité Digitale",
            self.styles["Title"]
        ))
        story.append(Spacer(1, 1.5*cm))

        # Logo / En-tête
        story.append(Paragraph(
            "JESA Digital Maturity Assessment Framework",
            self.styles["Subtitle"]
        ))
        story.append(Spacer(1, 2*cm))

        # Informations de l'évaluation
        data = [
            ["ID de l'évaluation:", assessment_id or metadata.get("assessment_id", "N/A")],
            ["Site:", metadata.get("site_name", "N/A")],
            ["Date:", metadata.get("assessment_date", datetime.now().strftime("%Y-%m-%d"))],
            ["Évaluateur:", metadata.get("evaluator_name", "N/A")],
        ]
        table = Table(data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTSIZE", (0, 0), (0, -1), 12),
            ("FONTSIZE", (1, 0), (1, -1), 14),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)

        if dmi is not None:
            story.append(Spacer(1, 2*cm))
            story.append(Paragraph(
                f"DMI: {dmi.score:.1f}% — {dmi.level_name}",
                self.styles["DMI"]
            ))

        story.append(PageBreak())

    def _add_executive_summary(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
    ) -> None:
        """
        Ajoute le résumé exécutif.
        """
        story.append(Paragraph("Résumé Exécutif", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        metadata = results.get("metadata", {})
        dmi = results.get("dmi")

        # Paragraphe introductif
        if dmi is not None:
            story.append(Paragraph(
                f"L'évaluation du site <b>{metadata.get('site_name', 'N/A')}</b> "
                f"révèle un Indice de Maturité Digitale (DMI) de "
                f"<b>{dmi.score:.1f}%</b>, correspondant au niveau "
                f"<b>{dmi.level_name}</b>.",
                self.styles["Normal"]
            ))
            story.append(Spacer(1, 0.3*cm))

        # Points clés
        story.append(Paragraph("Points clés :", self.styles["Heading3"]))

        bullets = []
        pillars = results.get("pillars", {})
        for pillar_id, result in pillars.items():
            if isinstance(result, ScoreResult):
                bullets.append(f"{result.entity_name}: {result.score:.1f} / 5")

        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(b, self.styles["Normal"])) for b in bullets],
                bulletType="bullet",
                leftIndent=1*cm,
            ))

        story.append(Spacer(1, 0.5*cm))
        story.append(PageBreak())

    def _add_dmi_section(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
    ) -> None:
        """
        Ajoute la section DMI.
        """
        story.append(Paragraph("Indice de Maturité Digitale (DMI)", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        dmi = results.get("dmi")
        if dmi is None:
            story.append(Paragraph("DMI non disponible.", self.styles["Normal"]))
            return

        # Score DMI
        story.append(Paragraph(
            f"<b>Score DMI :</b> {dmi.score:.1f}%",
            self.styles["Heading3"]
        ))
        story.append(Spacer(1, 0.2*cm))

        story.append(Paragraph(
            f"<b>Niveau :</b> {dmi.level} — {dmi.level_name}",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 0.3*cm))

        # Description du niveau
        if dmi.level_name:
            story.append(Paragraph(
                constants.MATURITY_LEVEL_DESCRIPTIONS.get(dmi.level, ""),
                self.styles["Normal"]
            ))

        story.append(Spacer(1, 0.5*cm))

        # Détail des piliers
        story.append(Paragraph("Contribution des piliers :", self.styles["Heading3"]))

        data = [["Pilier", "Score", "Niveau"]]
        pillars = results.get("pillars", {})
        for pillar_id, result in pillars.items():
            if isinstance(result, ScoreResult):
                data.append([
                    result.entity_name,
                    f"{result.score:.1f}",
                    result.level_name,
                ])

        table = Table(data, colWidths=[8*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.colors["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors["gray"]),
        ]))
        story.append(table)

        story.append(PageBreak())

    def _add_pillars_section(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
    ) -> None:
        """
        Ajoute la section des piliers.
        """
        story.append(Paragraph("Analyse par Pilier", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        pillars = results.get("pillars", {})
        for pillar_id, result in pillars.items():
            if not isinstance(result, ScoreResult):
                continue

            story.append(Paragraph(
                f"<b>{result.entity_name}</b>",
                self.styles["Heading2"]
            ))
            story.append(Paragraph(f"Score : {result.score:.1f} / 5", self.styles["Normal"]))
            story.append(Paragraph(f"Niveau : {result.level} — {result.level_name}", self.styles["Normal"]))
            story.append(Spacer(1, 0.3*cm))

        story.append(PageBreak())

    def _add_dimensions_section(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
    ) -> None:
        """
        Ajoute la section des dimensions.
        """
        story.append(Paragraph("Analyse par Dimension", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        dimensions = results.get("dimensions", {})
        data = [["Dimension", "Score", "Niveau"]]

        for dim_id, result in dimensions.items():
            if isinstance(result, ScoreResult):
                data.append([
                    result.entity_name,
                    f"{result.score:.1f}",
                    result.level_name,
                ])

        table = Table(data, colWidths=[8*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.colors["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors["gray"]),
        ]))
        story.append(table)

        story.append(PageBreak())

    def _add_gaps_section(
        self,
        story: List[Flowable],
        gap_results: List[GapResult],
    ) -> None:
        """
        Ajoute la section des écarts.
        """
        story.append(Paragraph("Analyse des Écarts", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        # Filtrer les écarts significatifs
        significant_gaps = [g for g in gap_results if g.gap > 0.5]

        if not significant_gaps:
            story.append(Paragraph("Aucun écart significatif détecté.", self.styles["Normal"]))
            return

        data = [["Entité", "Actuel", "Cible", "Écart", "Priorité"]]
        for gap in significant_gaps[:10]:  # Limiter aux 10 premiers
            data.append([
                gap.entity_name,
                f"{gap.current_score:.1f}",
                f"{gap.target_score:.1f}",
                f"{gap.gap:.1f}",
                gap.priority.capitalize(),
            ])

        table = Table(data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.colors["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors["gray"]),
        ]))
        story.append(table)

        story.append(PageBreak())

    def _add_tpi_section(
        self,
        story: List[Flowable],
        tpi_results: List[TPIResult],
    ) -> None:
        """
        Ajoute la section TPI.
        """
        story.append(Paragraph("Priorisation TPI", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        data = [["Dimension", "TPI", "Priorité", "Gap"]]
        for tpi in tpi_results[:8]:  # Limiter aux 8 premiers
            data.append([
                tpi.dimension_name,
                f"{tpi.tpi_score:.3f}",
                tpi.priority_category,
                f"{tpi.gap:.1f}",
            ])

        table = Table(data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.colors["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors["gray"]),
        ]))
        story.append(table)

        story.append(PageBreak())

    def _add_priorities_section(
        self,
        story: List[Flowable],
        priority_results: List[PriorityResult],
    ) -> None:
        """
        Ajoute la section de priorisation.
        """
        story.append(Paragraph("Dimensions Prioritaires", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        # Filtrer les priorités critiques et hautes
        critical = [p for p in priority_results if p.priority_category in {"Critique", "critical"}]
        high = [p for p in priority_results if p.priority_category in {"Haute", "high"}]

        if critical:
            story.append(Paragraph("🔴 Critiques :", self.styles["Heading3"]))
            for p in critical[:5]:
                story.append(Paragraph(f"• {p.dimension_name} (Gap: {p.gap:.1f})", self.styles["Normal"]))

        if high:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("🟡 Hautes :", self.styles["Heading3"]))
            for p in high[:5]:
                story.append(Paragraph(f"• {p.dimension_name} (Gap: {p.gap:.1f})", self.styles["Normal"]))

        story.append(PageBreak())

    def _add_roadmap_section(
        self,
        story: List[Flowable],
        roadmap: List[RoadmapPhase],
    ) -> None:
        """
        Ajoute la section de roadmap.
        """
        story.append(Paragraph("Feuille de Route", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        for phase in roadmap:
            story.append(Paragraph(f"<b>{phase.phase_name}</b> — {phase.horizon}", self.styles["Heading2"]))
            story.append(Spacer(1, 0.2*cm))

            for item in phase.items[:5]:  # Limiter à 5 actions par phase
                story.append(Paragraph(f"• {item.title}", self.styles["Normal"]))
                if item.effort:
                    story.append(Paragraph(f"  Effort: {item.effort}", self.styles["Small"]))

            story.append(Spacer(1, 0.5*cm))

        story.append(PageBreak())

    def _add_annexes(
        self,
        story: List[Flowable],
        results: Dict[str, Any],
    ) -> None:
        """
        Ajoute les annexes.
        """
        story.append(Paragraph("Annexes", self.styles["Heading1"]))
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("Méthodologie d'évaluation", self.styles["Heading2"]))
        story.append(Spacer(1, 0.2*cm))

        story.append(Paragraph(
            "L'évaluation de maturité digitale repose sur le référentiel JESA JDMAF. "
            "Chaque indicateur est noté sur une échelle de 0 à 5, avec des grilles de "
            "scoring spécifiques définissant les critères pour chaque niveau.",
            self.styles["Normal"]
        ))

    # ========================================================================
    # STYLES
    # ========================================================================

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Crée les styles de paragraphe pour le rapport.
        """
        styles = getSampleStyleSheet()

        return {
            "Title": ParagraphStyle(
                name="Title",
                parent=styles["Title"],
                fontName="DejaVuSans-Bold",
                fontSize=24,
                textColor=self.colors["primary"],
                alignment=TA_CENTER,
                spaceAfter=0.5*cm,
            ),
            "Subtitle": ParagraphStyle(
                name="Subtitle",
                parent=styles["Title"],
                fontName="DejaVuSans",
                fontSize=18,
                textColor=self.colors["secondary"],
                alignment=TA_CENTER,
                spaceAfter=0.5*cm,
            ),
            "DMI": ParagraphStyle(
                name="DMI",
                parent=styles["Title"],
                fontName="DejaVuSans-Bold",
                fontSize=20,
                textColor=self.colors["accent"],
                alignment=TA_CENTER,
                spaceAfter=0.5*cm,
            ),
            "Heading1": ParagraphStyle(
                name="Heading1",
                parent=styles["Heading1"],
                fontName="DejaVuSans-Bold",
                fontSize=18,
                textColor=self.colors["primary"],
                spaceAfter=0.5*cm,
            ),
            "Heading2": ParagraphStyle(
                name="Heading2",
                parent=styles["Heading2"],
                fontName="DejaVuSans-Bold",
                fontSize=14,
                textColor=self.colors["secondary"],
                spaceAfter=0.3*cm,
            ),
            "Heading3": ParagraphStyle(
                name="Heading3",
                parent=styles["Heading3"],
                fontName="DejaVuSans-Bold",
                fontSize=12,
                spaceAfter=0.2*cm,
            ),
            "Normal": ParagraphStyle(
                name="Normal",
                parent=styles["Normal"],
                fontName="DejaVuSans",
                fontSize=11,
                spaceAfter=0.2*cm,
            ),
            "Small": ParagraphStyle(
                name="Small",
                parent=styles["Normal"],
                fontName="DejaVuSans",
                fontSize=9,
                textColor=self.colors["gray"],
            ),
        }

    # ========================================================================
    # HEADER / FOOTER
    # ========================================================================

    def _header_footer(self, canvas, doc) -> None:
        """
        Ajoute un en-tête et un pied de page à chaque page.
        """
        canvas.saveState()

        # En-tête
        canvas.setFont("DejaVuSans", 9)
        canvas.setFillColor(self.colors["gray"])
        canvas.drawString(2*cm, A4[1] - 1*cm, "JESA Digital Maturity Assessment Framework")

        # Pied de page
        canvas.setFont("DejaVuSans", 9)
        canvas.setFillColor(self.colors["gray"])
        canvas.drawString(2*cm, 1*cm, f"Page {doc.page}")
        canvas.drawRightString(A4[0] - 2*cm, 1*cm, datetime.now().strftime("%Y-%m-%d"))

        canvas.restoreState()


# ============================================================================
# FONCTIONS UTILITAIRES PUBLIQUES
# ============================================================================


def generate_pdf_report(
    results: Dict[str, Any],
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    """
    Fonction rapide pour générer un rapport PDF.

    Args:
        results: Résultats de aggregation.py
        output_path: Chemin de sortie (si None, généré automatiquement)
        assessment_id: Identifiant de l'évaluation

    Returns:
        Path: Chemin du fichier PDF généré.
    """
    generator = PDFReportGenerator()
    return generator.generate_report(
        aggregation_results=results,
        assessment_id=assessment_id,
        output_path=output_path,
    )