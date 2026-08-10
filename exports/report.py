"""
report.py — Génération de rapports structurés pour le JDMAF.

Responsabilités :
    - Produire un rapport complet (agrégation + décision)
    - Sérialiser les résultats en format JSON
    - Produire un résumé exécutif structuré
    - Coordonner les exportations Excel et PDF

Ce module sert d'interface unifiée pour tous les exports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Mapping

from config import settings
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase

from exports.excel import ExcelExporter, export_to_excel, export_full_analysis
from exports.pdf import PDFReportGenerator, generate_pdf_report


logger = settings.get_logger(__name__)


# ============================================================================
# STRUCTURE DU RAPPORT
# ============================================================================


@dataclass
class ReportMetadata:
    """
    Métadonnées du rapport.
    """
    report_id: str
    assessment_id: str
    site_name: str
    generated_at: str
    report_version: str = "1.0"
    generator: str = "JDMAF Backend"


@dataclass
class ExecutiveSummary:
    """
    Résumé exécutif du rapport.
    """
    dmi_score: Optional[float]
    dmi_level: Optional[int]
    dmi_level_name: str
    top_strengths: List[tuple[str, float]]
    top_weaknesses: List[tuple[str, float]]
    critical_gaps: int
    priority_dimensions: int


@dataclass
class ReportData:
    """
    Données complètes du rapport.
    """
    metadata: ReportMetadata
    summary: ExecutiveSummary
    aggregation_results: Dict[str, Any]
    gap_results: Optional[List[GapResult]] = None
    tpi_results: Optional[List[TPIResult]] = None
    priority_results: Optional[List[PriorityResult]] = None
    roadmap: Optional[List[RoadmapPhase]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# GÉNÉRATEUR DE RAPPORT
# ============================================================================


class ReportGenerator:
    """
    Générateur de rapports unifié.

    Il coordonne :
        - La construction du rapport
        - L'export Excel
        - L'export PDF
        - L'export JSON
        - Le résumé exécutif
    """

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        """
        Initialise le générateur de rapport.

        Args:
            config: Configuration optionnelle
        """
        self.config = dict(config or {})
        self.excel_exporter = ExcelExporter(self.config)
        self.pdf_generator = PDFReportGenerator(self.config)

    # ========================================================================
    # API PRINCIPALE
    # ========================================================================

    def generate_full_report(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        output_dir: Optional[Path] = None,
        assessment_id: Optional[str] = None,
        include_pdf: bool = True,
        include_excel: bool = True,
        include_json: bool = True,
    ) -> Dict[str, Path]:
        """
        Génère un rapport complet avec tous les formats.

        Args:
            aggregation_results: Résultats de aggregation.py
            gap_results: Résultats du GapAnalysisEngine
            tpi_results: Résultats du TPIEngine
            priority_results: Résultats du PriorityEngine
            roadmap: Résultats du RoadmapEngine
            output_dir: Dossier de sortie
            assessment_id: Identifiant de l'évaluation
            include_pdf: Inclure le PDF
            include_excel: Inclure l'Excel
            include_json: Inclure le JSON

        Returns:
            Dict[str, Path]: Chemins des fichiers générés.
        """
        # Métadonnées
        metadata = aggregation_results.get("metadata", {})
        assessment_id = assessment_id or metadata.get("assessment_id", "UNKNOWN")
        site_name = metadata.get("site_name", "N/A")

        # Construire le rapport
        report_data = self._build_report_data(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            assessment_id=assessment_id,
            site_name=site_name,
        )

        outputs = {}

        # Export PDF
        if include_pdf:
            pdf_path = self._generate_pdf(report_data, output_dir)
            outputs["pdf"] = pdf_path

        # Export Excel
        if include_excel:
            excel_path = self._generate_excel(report_data, output_dir)
            outputs["excel"] = excel_path

        # Export JSON
        if include_json:
            json_path = self._generate_json(report_data, output_dir)
            outputs["json"] = json_path

        logger.info(
            "Rapport complet généré : %s",
            ", ".join(f"{k}={v}" for k, v in outputs.items()),
        )

        return outputs

    # ========================================================================
    # CONSTRUCTION DU RAPPORT
    # ========================================================================

    def _build_report_data(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
        tpi_results: Optional[List[TPIResult]] = None,
        priority_results: Optional[List[PriorityResult]] = None,
        roadmap: Optional[List[RoadmapPhase]] = None,
        assessment_id: str = "UNKNOWN",
        site_name: str = "N/A",
    ) -> ReportData:
        """
        Construit les données structurées du rapport.
        """
        metadata = aggregation_results.get("metadata", {})

        # Métadonnées du rapport
        report_metadata = ReportMetadata(
            report_id=f"RPT-{assessment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            assessment_id=assessment_id,
            site_name=site_name,
            generated_at=datetime.now().isoformat(),
        )

        # Résumé exécutif
        dmi = aggregation_results.get("dmi")
        summary = self._build_executive_summary(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
        )

        return ReportData(
            metadata=report_metadata,
            summary=summary,
            aggregation_results=aggregation_results,
            gap_results=gap_results,
            tpi_results=tpi_results,
            priority_results=priority_results,
            roadmap=roadmap,
            raw_data={
                "dmi": dmi.to_dict() if dmi else None,
                "pillars": self._serialize_score_results(aggregation_results.get("pillars", {})),
                "dimensions": self._serialize_score_results(aggregation_results.get("dimensions", {})),
            },
        )

    def _build_executive_summary(
        self,
        aggregation_results: Dict[str, Any],
        gap_results: Optional[List[GapResult]] = None,
    ) -> ExecutiveSummary:
        """
        Construit le résumé exécutif.
        """
        dmi = aggregation_results.get("dmi")

        # Forces et faiblesses
        dimensions = aggregation_results.get("dimensions", {})
        dim_scores = []
        for dim_id, result in dimensions.items():
            if isinstance(result, ScoreResult) and result.score is not None:
                dim_scores.append((dim_id, result.score))

        dim_scores.sort(key=lambda x: x[1], reverse=True)
        top_strengths = dim_scores[:3]
        top_weaknesses = dim_scores[-3:]

        # Écarts critiques
        critical_gaps = 0
        if gap_results:
            critical_gaps = sum(1 for g in gap_results if g.priority in {"critical", "high"})

        # Dimensions prioritaires
        priority_dimensions = len(dim_scores)

        return ExecutiveSummary(
            dmi_score=dmi.score if dmi else None,
            dmi_level=dmi.level if dmi else None,
            dmi_level_name=dmi.level_name if dmi else "",
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            critical_gaps=critical_gaps,
            priority_dimensions=priority_dimensions,
        )

    # ========================================================================
    # EXPORTS SPÉCIFIQUES
    # ========================================================================

    def _generate_pdf(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Génère le rapport PDF.
        """
        filename = f"assessment_report_{report_data.metadata.assessment_id}.pdf"
        if output_dir:
            output_path = output_dir / filename
        else:
            output_path = None

        return self.pdf_generator.generate_report(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    def _generate_excel(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Génère le rapport Excel.
        """
        filename = f"assessment_results_{report_data.metadata.assessment_id}.xlsx"
        if output_dir:
            output_path = output_dir / filename
        else:
            output_path = None

        return self.excel_exporter.export_assessment_results(
            aggregation_results=report_data.aggregation_results,
            gap_results=report_data.gap_results,
            tpi_results=report_data.tpi_results,
            priority_results=report_data.priority_results,
            roadmap=report_data.roadmap,
            output_path=output_path,
            assessment_id=report_data.metadata.assessment_id,
        )

    def _generate_json(
        self,
        report_data: ReportData,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Génère le rapport JSON.
        """
        from utils.file_manager import build_output_path, ensure_directory

        filename = f"assessment_report_{report_data.metadata.assessment_id}.json"
        if output_dir:
            ensure_directory(output_dir)
            output_path = output_dir / filename
        else:
            output_path = build_output_path(filename)

        # Sérialiser les données
        data = self._serialize_report_data(report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("JSON exporté : %s", output_path)
        return output_path

    # ========================================================================
    # SÉRIALISATION
    # ========================================================================

    def _serialize_report_data(self, report_data: ReportData) -> Dict[str, Any]:
        """
        Sérialise les données du rapport en dictionnaire.
        """
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
                "top_strengths": report_data.summary.top_strengths,
                "top_weaknesses": report_data.summary.top_weaknesses,
                "critical_gaps": report_data.summary.critical_gaps,
                "priority_dimensions": report_data.summary.priority_dimensions,
            },
            "aggregation": self._serialize_aggregation(report_data.aggregation_results),
            "decision": {
                "gaps": [gap.to_dict() for gap in (report_data.gap_results or [])],
                "tpi": [tpi.to_dict() for tpi in (report_data.tpi_results or [])],
                "priorities": [prio.to_dict() for prio in (report_data.priority_results or [])],
                "roadmap": [phase.to_dict() for phase in (report_data.roadmap or [])],
            },
        }

    @staticmethod
    def _serialize_aggregation(results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sérialise les résultats d'agrégation.
        """
        return {
            "indicators": ReportGenerator._serialize_score_results(results.get("indicators", {})),
            "subdimensions": ReportGenerator._serialize_score_results(results.get("subdimensions", {})),
            "dimensions": ReportGenerator._serialize_score_results(results.get("dimensions", {})),
            "pillars": ReportGenerator._serialize_score_results(results.get("pillars", {})),
            "dmi": results.get("dmi").to_dict() if results.get("dmi") else None,
            "metadata": results.get("metadata", {}),
        }

    @staticmethod
    def _serialize_score_results(results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sérialise un dictionnaire de ScoreResult.
        """
        serialized = {}
        for key, result in results.items():
            if isinstance(result, ScoreResult):
                serialized[key] = result.to_dict()
            elif isinstance(result, dict):
                serialized[key] = result
        return serialized


# ============================================================================
# FONCTIONS UTILITAIRES PUBLIQUES
# ============================================================================


def generate_report(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
    tpi_results: Optional[List[TPIResult]] = None,
    priority_results: Optional[List[PriorityResult]] = None,
    roadmap: Optional[List[RoadmapPhase]] = None,
    output_dir: Optional[Path] = None,
    assessment_id: Optional[str] = None,
    formats: List[str] = None,
) -> Dict[str, Path]:
    """
    Fonction rapide pour générer un rapport complet.

    Args:
        aggregation_results: Résultats de aggregation.py
        gap_results: Résultats du GapAnalysisEngine
        tpi_results: Résultats du TPIEngine
        priority_results: Résultats du PriorityEngine
        roadmap: Résultats du RoadmapEngine
        output_dir: Dossier de sortie
        assessment_id: Identifiant de l'évaluation
        formats: Formats à générer ("pdf", "excel", "json")

    Returns:
        Dict[str, Path]: Chemins des fichiers générés.
    """
    if formats is None:
        formats = ["pdf", "excel", "json"]

    generator = ReportGenerator()
    return generator.generate_full_report(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
        tpi_results=tpi_results,
        priority_results=priority_results,
        roadmap=roadmap,
        output_dir=output_dir,
        assessment_id=assessment_id,
        include_pdf="pdf" in formats,
        include_excel="excel" in formats,
        include_json="json" in formats,
    )


def generate_executive_summary(
    aggregation_results: Dict[str, Any],
    gap_results: Optional[List[GapResult]] = None,
) -> Dict[str, Any]:
    """
    Génère un résumé exécutif structuré.

    Args:
        aggregation_results: Résultats de aggregation.py
        gap_results: Résultats du GapAnalysisEngine

    Returns:
        Dict[str, Any]: Résumé exécutif.
    """
    generator = ReportGenerator()
    summary = generator._build_executive_summary(
        aggregation_results=aggregation_results,
        gap_results=gap_results,
    )

    return {
        "dmi_score": summary.dmi_score,
        "dmi_level": summary.dmi_level,
        "dmi_level_name": summary.dmi_level_name,
        "top_strengths": summary.top_strengths,
        "top_weaknesses": summary.top_weaknesses,
        "critical_gaps": summary.critical_gaps,
        "priority_dimensions": summary.priority_dimensions,
    }