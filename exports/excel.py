"""
excel.py — Export des résultats d'évaluation au format Excel.

Responsabilités :
    - Exporter les résultats d'agrégation (indicateurs, sous-dimensions, dimensions, piliers, DMI)
    - Exporter les résultats de gap analysis
    - Exporter les résultats TPI
    - Exporter la matrice de priorisation
    - Exporter la roadmap
    - Produire un classeur complet avec plusieurs feuilles

Ce module n'utilise pas le moteur de calcul.
Il travaille uniquement sur les résultats déjà calculés.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Mapping

import pandas as pd

from config import settings
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase
from utils.file_manager import ensure_directory, build_output_path


logger = settings.get_logger(__name__)


# ============================================================================
# EXPORTEUR EXCEL
# ============================================================================


class ExcelExporter:
    """
    Exporte les résultats d'évaluation et de décision au format Excel.

    Le classeur produit contient plusieurs feuilles :
        - Résumé (DMI, piliers, dimensions)
        - Indicateurs (détail des scores par indicateur)
        - Sous-dimensions
        - Dimensions
        - Piliers
        - Gaps (écarts entre scores actuels et cibles)
        - TPI (Transformation Priority Index)
        - Priorisation (matrice de priorisation)
        - Roadmap (feuille de route des actions)
        - Métadonnées (informations sur l'évaluation)
    """

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        """
        Initialise l'exporteur Excel.

        Args:
            config: Configuration optionnelle (ex: format des nombres)
        """
        self.config = dict(config or {})
        self.decimal_precision = self.config.get(
            "decimal_precision",
            settings.SCORE_DECIMAL_PRECISION,
        )

    # ========================================================================
    # API PRINCIPALE
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
        """
        Exporte tous les résultats dans un classeur Excel structuré.

        Args:
            aggregation_results: Résultats de aggregation.py
            gap_results: Résultats du GapAnalysisEngine
            tpi_results: Résultats du TPIEngine
            priority_results: Résultats du PriorityEngine
            roadmap: Résultats du RoadmapEngine
            output_path: Chemin de sortie (si None, généré automatiquement)
            assessment_id: Identifiant de l'évaluation (pour nommer le fichier)

        Returns:
            Path: Chemin du fichier Excel généré.
        """
        # Construire le nom du fichier
        if output_path is None:
            suffix = f"_{assessment_id}" if assessment_id else ""
            filename = f"assessment_results{suffix}.xlsx"
            output_path = build_output_path(filename)

        # S'assurer que le dossier parent existe
        ensure_directory(output_path.parent)

        # Construire les DataFrames
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            self._write_summary(writer, aggregation_results)
            self._write_indicators(writer, aggregation_results)
            self._write_subdimensions(writer, aggregation_results)
            self._write_dimensions(writer, aggregation_results)
            self._write_pillars(writer, aggregation_results)

            if gap_results is not None:
                self._write_gaps(writer, gap_results)

            if tpi_results is not None:
                self._write_tpi(writer, tpi_results)

            if priority_results is not None:
                self._write_priorities(writer, priority_results)

            if roadmap is not None:
                self._write_roadmap(writer, roadmap)

            self._write_metadata(writer, aggregation_results)

        logger.info("Export Excel terminé : %s", output_path)
        return output_path

    # ========================================================================
    # FEUILLES DU CLASSEUR
    # ========================================================================

    def _write_summary(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille de résumé (DMI + piliers + dimensions).
        """
        rows = []

        # DMI
        dmi = results.get("dmi")
        if dmi is not None:
            rows.append({
                "Niveau": "DMI",
                "ID": "DMI",
                "Nom": "Indice de Maturité Digitale",
                "Score": dmi.score if dmi.score is not None else None,
                "Niveau": dmi.level if dmi.level is not None else None,
                "Niveau_Nom": dmi.level_name or "",
            })

        # Piliers
        pillars = results.get("pillars", {})
        for pillar_id, result in pillars.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Niveau": "Pilier",
                    "ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                })

        # Dimensions (top 10)
        dimensions = results.get("dimensions", {})
        for dim_id, result in dimensions.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Niveau": "Dimension",
                    "ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Résumé", index=False)

    def _write_indicators(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille des indicateurs.
        """
        indicators = results.get("indicators", {})
        rows = []

        for indicator_id, result in indicators.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Indicator_ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                    "Applicabilité": result.applicability,
                    "Parent_ID": result.parent_id,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Indicateurs", index=False)

    def _write_subdimensions(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille des sous-dimensions.
        """
        subdimensions = results.get("subdimensions", {})
        rows = []

        for sd_id, result in subdimensions.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Subdimension_ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                    "Applicabilité": result.applicability,
                    "Parent_ID": result.parent_id,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Sous-dimensions", index=False)

    def _write_dimensions(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille des dimensions.
        """
        dimensions = results.get("dimensions", {})
        rows = []

        for dim_id, result in dimensions.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Dimension_ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                    "Applicabilité": result.applicability,
                    "Parent_ID": result.parent_id,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Dimensions", index=False)

    def _write_pillars(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille des piliers.
        """
        pillars = results.get("pillars", {})
        rows = []

        for pillar_id, result in pillars.items():
            if isinstance(result, ScoreResult):
                rows.append({
                    "Pillar_ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Score": result.score,
                    "Niveau": result.level,
                    "Niveau_Nom": result.level_name,
                    "Applicabilité": result.applicability,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Piliers", index=False)

    def _write_gaps(self, writer: pd.ExcelWriter, gap_results: List[GapResult]) -> None:
        """
        Écrit la feuille des écarts (gaps).
        """
        rows = []

        for gap in gap_results:
            rows.append({
                "Entity_ID": gap.entity_id,
                "Entity_Name": gap.entity_name,
                "Entity_Type": gap.entity_type,
                "Current_Score": gap.current_score,
                "Target_Score": gap.target_score,
                "Gap": gap.gap,
                "Gap_%": gap.gap_percent,
                "Priorité": gap.priority,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Écarts", index=False)

    def _write_tpi(self, writer: pd.ExcelWriter, tpi_results: List[TPIResult]) -> None:
        """
        Écrit la feuille TPI.
        """
        rows = []

        for tpi in tpi_results:
            rows.append({
                "Dimension_ID": tpi.dimension_id,
                "Dimension_Name": tpi.dimension_name,
                "TPI_Score": tpi.tpi_score,
                "Priorité": tpi.priority_category,
                "Gap": tpi.gap,
                "Business_Impact": tpi.business_impact,
                "Strategic_Importance": tpi.strategic_importance,
                "Expected_ROI": tpi.expected_roi,
                "Implementation_Cost": tpi.implementation_cost,
                "Implementation_Difficulty": tpi.implementation_difficulty,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="TPI", index=False)

    def _write_priorities(self, writer: pd.ExcelWriter, priority_results: List[PriorityResult]) -> None:
        """
        Écrit la feuille de priorisation.
        """
        rows = []

        for priority in priority_results:
            rows.append({
                "Dimension_ID": priority.dimension_id,
                "Dimension_Name": priority.dimension_name,
                "Current_Score": priority.current_score,
                "Target_Score": priority.target_score,
                "Gap": priority.gap,
                "TPI_Score": priority.tpi_score,
                "Priorité": priority.priority_category,
                "Nb_Recommandations": len(priority.recommendations),
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Priorisation", index=False)

    def _write_roadmap(self, writer: pd.ExcelWriter, roadmap: List[RoadmapPhase]) -> None:
        """
        Écrit la feuille de roadmap.
        """
        rows = []

        for phase in roadmap:
            for item in phase.items:
                rows.append({
                    "Phase": phase.phase_name,
                    "Horizon": phase.horizon,
                    "Recommendation_ID": item.recommendation_id,
                    "Action": item.title,
                    "Dimension_ID": item.dimension_id,
                    "Pillar_ID": item.pillar_id,
                    "Priorité": item.priority,
                    "TPI_Score": item.tpi_score,
                    "Gap": item.gap,
                    "Effort": item.effort,
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_excel(writer, sheet_name="Roadmap", index=False)

    def _write_metadata(self, writer: pd.ExcelWriter, results: Dict[str, Any]) -> None:
        """
        Écrit la feuille des métadonnées.
        """
        metadata = results.get("metadata", {})
        rows = [
            {"Champ": "Assessment_ID", "Valeur": metadata.get("assessment_id", "")},
            {"Champ": "Site_ID", "Valeur": metadata.get("site_id", "")},
            {"Champ": "Site_Name", "Valeur": metadata.get("site_name", "")},
            {"Champ": "Total_Indicateurs", "Valeur": metadata.get("total_indicators", 0)},
            {"Champ": "Total_Sous_dimensions", "Valeur": metadata.get("total_subdimensions", 0)},
            {"Champ": "Total_Dimensions", "Valeur": metadata.get("total_dimensions", 0)},
            {"Champ": "Total_Piliers", "Valeur": metadata.get("total_pillars", 0)},
            {"Champ": "DMI_Score", "Valeur": metadata.get("dmi_score", None)},
            {"Champ": "DMI_Niveau", "Valeur": metadata.get("dmi_level", None)},
            {"Champ": "DMI_Niveau_Nom", "Valeur": metadata.get("dmi_level_name", "")},
        ]

        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Métadonnées", index=False)


# ============================================================================
# FONCTIONS UTILITAIRES PUBLIQUES
# ============================================================================


def export_to_excel(
    results: Dict[str, Any],
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    """
    Fonction rapide pour exporter les résultats d'agrégation.

    Args:
        results: Résultats de aggregation.py
        output_path: Chemin de sortie (si None, généré automatiquement)
        assessment_id: Identifiant de l'évaluation

    Returns:
        Path: Chemin du fichier Excel généré.
    """
    exporter = ExcelExporter()
    return exporter.export_assessment_results(
        aggregation_results=results,
        assessment_id=assessment_id,
        output_path=output_path,
    )


def export_full_analysis(
    aggregation_results: Dict[str, Any],
    gap_results: List[GapResult],
    tpi_results: List[TPIResult],
    priority_results: List[PriorityResult],
    roadmap: List[RoadmapPhase],
    output_path: Optional[Path] = None,
    assessment_id: Optional[str] = None,
) -> Path:
    """
    Exporte une analyse complète (agrégation + décision).

    Args:
        aggregation_results: Résultats de aggregation.py
        gap_results: Résultats du GapAnalysisEngine
        tpi_results: Résultats du TPIEngine
        priority_results: Résultats du PriorityEngine
        roadmap: Résultats du RoadmapEngine
        output_path: Chemin de sortie
        assessment_id: Identifiant de l'évaluation

    Returns:
        Path: Chemin du fichier Excel généré.
    """
    exporter = ExcelExporter()
    return exporter.export_assessment_results(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_path=output_path,
        assessment_id=assessment_id,
    )