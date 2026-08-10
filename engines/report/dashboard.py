"""
dashboard.py — Préparation des données du Dashboard JDMAF.

Responsabilités :
    - consolider les résultats backend ;
    - préparer les KPI ;
    - préparer les tableaux ;
    - fournir les données nécessaires aux graphiques.

IMPORTANT :
    Ce module ne réalise aucun calcul métier.
    Les scores, gaps et TPI sont supposés déjà calculés.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

import pandas as pd

from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult
from engines.decision.priority import PriorityResult
from engines.decision.roadmap import RoadmapPhase


# ============================================================================
# STRUCTURE
# ============================================================================


@dataclass
class DashboardData:
    """
    Conteneur principal des données du Dashboard.
    """

    kpis: dict[str, Any]

    maturity: pd.DataFrame
    gaps: pd.DataFrame
    priorities: pd.DataFrame
    roadmap: pd.DataFrame

    charts: dict[str, Any]

    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:

        return {
            "kpis": self.kpis,
            "maturity": self.maturity.to_dict(
                orient="records"
            ),
            "gaps": self.gaps.to_dict(
                orient="records"
            ),
            "priorities": self.priorities.to_dict(
                orient="records"
            ),
            "roadmap": self.roadmap.to_dict(
                orient="records"
            ),
            "charts": self.charts,
            "metadata": self.metadata,
        }


# ============================================================================
# ENGINE
# ============================================================================


class DashboardEngine:
    """
    Prépare les données nécessaires au Dashboard.
    """

    def build(
        self,
        dimension_scores: Optional[
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
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> DashboardData:
        """
        Construit toutes les données du Dashboard.
        """

        gap_results = gap_results or []
        tpi_results = tpi_results or []
        priority_results = (
            priority_results or []
        )
        roadmap = roadmap or []

        maturity_df = (
            self._build_maturity_table(
                dimension_scores
                or {}
            )
        )

        gap_df = (
            self._build_gap_table(
                gap_results
            )
        )

        priority_df = (
            self._build_priority_table(
                priority_results
            )
        )

        roadmap_df = (
            self._build_roadmap_table(
                roadmap
            )
        )

        kpis = (
            self._build_kpis(
                dimension_scores
                or {},
                gap_results,
                tpi_results,
                priority_results,
                roadmap,
            )
        )

        charts = (
            self._build_chart_data(
                dimension_scores
                or {},
                gap_results,
                tpi_results,
                priority_results,
            )
        )

        return DashboardData(
            kpis=kpis,
            maturity=maturity_df,
            gaps=gap_df,
            priorities=priority_df,
            roadmap=roadmap_df,
            charts=charts,
            metadata=dict(
                metadata or {}
            ),
        )

    # ========================================================================
    # KPI
    # ========================================================================

    @staticmethod
    def _build_kpis(
        dimension_scores: Mapping[str, Any],
        gap_results: list[GapResult],
        tpi_results: list[TPIResult],
        priority_results: list[PriorityResult],
        roadmap: list[RoadmapPhase],
    ) -> dict[str, Any]:

        scores = []

        for result in (
            dimension_scores.values()
        ):

            score = (
                result.score
                if hasattr(
                    result,
                    "score",
                )
                else (
                    result.get("score")
                    if isinstance(
                        result,
                        Mapping,
                    )
                    else None
                )
            )

            if score is not None:
                scores.append(
                    float(score)
                )

        gaps = [
            float(result.gap)
            for result in gap_results
        ]

        tpis = [
            float(result.tpi_score)
            for result in tpi_results
        ]

        critical = sum(
            1
            for result
            in priority_results
            if result.priority_category
            in {
                "Critique",
                "critical",
            }
        )

        high = sum(
            1
            for result
            in priority_results
            if result.priority_category
            in {
                "Haute",
                "high",
            }
        )

        return {
            "average_maturity": (
                round(
                    sum(scores)
                    / len(scores),
                    2,
                )
                if scores
                else None
            ),
            "max_maturity": (
                round(
                    max(scores),
                    2,
                )
                if scores
                else None
            ),
            "average_gap": (
                round(
                    sum(gaps)
                    / len(gaps),
                    2,
                )
                if gaps
                else 0.0
            ),
            "max_gap": (
                round(
                    max(gaps),
                    2,
                )
                if gaps
                else 0.0
            ),
            "average_tpi": (
                round(
                    sum(tpis)
                    / len(tpis),
                    3,
                )
                if tpis
                else None
            ),
            "critical_priorities": critical,
            "high_priorities": high,
            "roadmap_actions": sum(
                len(phase.items)
                for phase in roadmap
            ),
        }

    # ========================================================================
    # MATURITY
    # ========================================================================

    @staticmethod
    def _build_maturity_table(
        dimension_scores: Mapping[str, Any],
    ) -> pd.DataFrame:

        rows = []

        for entity_id, result in (
            dimension_scores.items()
        ):

            if hasattr(
                result,
                "score",
            ):

                score = result.score
                level = getattr(
                    result,
                    "level",
                    None,
                )
                name = getattr(
                    result,
                    "entity_name",
                    entity_id,
                )

            elif isinstance(
                result,
                Mapping,
            ):

                score = result.get(
                    "score"
                )
                level = result.get(
                    "level"
                )
                name = result.get(
                    "entity_name",
                    entity_id,
                )

            else:
                continue

            rows.append(
                {
                    "Dimension": entity_id,
                    "Nom": name,
                    "Score": score,
                    "Niveau": level,
                }
            )

        return pd.DataFrame(rows)

    # ========================================================================
    # GAP
    # ========================================================================

    @staticmethod
    def _build_gap_table(
        gap_results: list[GapResult],
    ) -> pd.DataFrame:

        return pd.DataFrame(
            [
                {
                    "ID": result.entity_id,
                    "Nom": result.entity_name,
                    "Type": result.entity_type,
                    "Score actuel": result.current_score,
                    "Cible": result.target_score,
                    "Écart": result.gap,
                    "Écart (%)": result.gap_percent,
                    "Priorité": result.priority,
                }
                for result
                in gap_results
            ]
        )

    # ========================================================================
    # PRIORITE
    # ========================================================================

    @staticmethod
    def _build_priority_table(
        priority_results: list[
            PriorityResult
        ],
    ) -> pd.DataFrame:

        return pd.DataFrame(
            [
                {
                    "Dimension": result.dimension_id,
                    "Nom": result.dimension_name,
                    "Score actuel": result.current_score,
                    "Cible": result.target_score,
                    "Gap": result.gap,
                    "TPI": result.tpi_score,
                    "Priorité": result.priority_category,
                    "Recommandations": len(
                        result.recommendations
                    ),
                }
                for result
                in priority_results
            ]
        )

    # ========================================================================
    # ROADMAP
    # ========================================================================

    @staticmethod
    def _build_roadmap_table(
        roadmap: list[RoadmapPhase],
    ) -> pd.DataFrame:

        rows = []

        for phase in roadmap:

            for item in phase.items:

                rows.append(
                    {
                        "Phase": phase.phase_name,
                        "Horizon": phase.horizon,
                        "Action": item.title,
                        "Dimension": item.dimension_id,
                        "Priorité": item.priority,
                        "TPI": item.tpi_score,
                        "Gap": item.gap,
                        "Effort": item.effort,
                    }
                )

        return pd.DataFrame(rows)

    # ========================================================================
    # CHART DATA
    # ========================================================================

    @staticmethod
    def _build_chart_data(
        dimension_scores: Mapping[str, Any],
        gap_results: list[GapResult],
        tpi_results: list[TPIResult],
        priority_results: list[
            PriorityResult
        ],
    ) -> dict[str, Any]:

        return {
            "maturity_by_dimension": [
                {
                    "dimension": entity_id,
                    "score": (
                        result.score
                        if hasattr(
                            result,
                            "score",
                        )
                        else result.get(
                            "score"
                        )
                        if isinstance(
                            result,
                            Mapping,
                        )
                        else None
                    ),
                }
                for entity_id, result
                in dimension_scores.items()
            ],
            "gap_by_dimension": [
                {
                    "dimension": result.entity_id,
                    "gap": result.gap,
                }
                for result
                in gap_results
                if result.entity_type
                == "dimension"
            ],
            "tpi_by_dimension": [
                {
                    "dimension": result.dimension_id,
                    "tpi": result.tpi_score,
                    "priority": result.priority_category,
                }
                for result
                in tpi_results
            ],
            "priority_distribution": (
                DashboardEngine
                ._priority_distribution(
                    priority_results
                )
            ),
        }

    @staticmethod
    def _priority_distribution(
        results: list[
            PriorityResult
        ],
    ) -> dict[str, int]:

        distribution: dict[
            str,
            int,
        ] = {}

        for result in results:

            category = (
                result.priority_category
            )

            distribution[category] = (
                distribution.get(
                    category,
                    0,
                )
                + 1
            )

        return distribution


DashboardBuilder = DashboardEngine