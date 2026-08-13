"""
roadmap.py — JDMAF roadmap generation.

Responsibilities:

- transform priorities into phases;
- associate recommendations with phases;
- respect dependencies whenever possible;
- produce a roadmap usable by the frontend and PDF.

This module does not calculate scores, gaps, or TPI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pandas as pd

from engines.decision.tpi import TPIResult
from engines.decision.recommendation import (
    RecommendationResult,
)


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class RoadmapItem:
    """Action or recommendation assigned to a roadmap phase."""

    recommendation_id: str
    title: str

    dimension_id: str
    pillar_id: str

    priority: str
    phase: str
    horizon: str
    effort: str

    tpi_score: Optional[float] = None
    gap: Optional[float] = None

    detailed_actions: list[str] = field(
        default_factory=list
    )

    prerequisites: list[str] = field(
        default_factory=list
    )

    dependencies: list[str] = field(
        default_factory=list
    )

    completion_evidence: list[str] = field(
        default_factory=list
    )

    expected_impact: str = ""
    source_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "dimension_id": self.dimension_id,
            "pillar_id": self.pillar_id,
            "priority": self.priority,
            "phase": self.phase,
            "horizon": self.horizon,
            "effort": self.effort,
            "tpi_score": self.tpi_score,
            "gap": self.gap,
            "detailed_actions": self.detailed_actions,
            "prerequisites": self.prerequisites,
            "dependencies": self.dependencies,
            "completion_evidence": self.completion_evidence,
            "expected_impact": self.expected_impact,
            "source_reference": self.source_reference,
        }


@dataclass
class RoadmapPhase:
    """A roadmap phase."""

    phase_id: str
    phase_name: str
    horizon: str

    items: list[RoadmapItem] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "horizon": self.horizon,
            "items": [
                item.to_dict()
                for item in self.items
            ],
        }


# ============================================================================
# ENGINE
# ============================================================================


class RoadmapEngine:
    """
    Generates a structured roadmap from TPI results
    and recommendations.
    """

    # ========================================================================
    # DEFAULT PHASE MAPPING
    # ========================================================================

    DEFAULT_PHASE_MAPPING = {
        "Critique": (
            "Phase 1",
            "< 6 months",
        ),
        "Haute": (
            "Phase 1–2",
            "6–12 months",
        ),
        "Moyenne": (
            "Phase 2",
            "12–24 months",
        ),
        "Faible": (
            "Phase 4",
            "> 24 months",
        ),
        "Très faible": (
            "Phase 4",
            "> 24 months",
        ),

        # English priority labels
        "Critical": (
            "Phase 1",
            "< 6 months",
        ),
        "High": (
            "Phase 1–2",
            "6–12 months",
        ),
        "Medium": (
            "Phase 2",
            "12–24 months",
        ),
        "Low": (
            "Phase 4",
            "> 24 months",
        ),
        "Very low": (
            "Phase 4",
            "> 24 months",
        ),

        # Internal normalized priority values
        "critical": (
            "Phase 1",
            "< 6 months",
        ),
        "high": (
            "Phase 1–2",
            "6–12 months",
        ),
        "medium": (
            "Phase 2",
            "12–24 months",
        ),
        "low": (
            "Phase 4",
            "> 24 months",
        ),
    }

    def __init__(
        self,
        config: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:

        self.config = dict(
            config or {}
        )

        custom_mapping = self.config.get(
            "phase_mapping"
        )

        self.phase_mapping = dict(
            custom_mapping
            or self.DEFAULT_PHASE_MAPPING
        )

    # ========================================================================
    # MAIN API
    # ========================================================================

    def build_roadmap(
        self,
        tpi_results: list[TPIResult],
        recommendations: Optional[
            Mapping[
                str,
                list[RecommendationResult],
            ]
        ] = None,
    ) -> list[RoadmapPhase]:
        """
        Generates the complete roadmap.
        """

        recommendations = (
            recommendations or {}
        )

        phases: dict[
            str,
            RoadmapPhase,
        ] = {}

        for tpi in tpi_results:

            phase_name, horizon = (
                self._resolve_phase(
                    tpi.priority_category
                )
            )

            phase_id = (
                phase_name
                .lower()
                .replace(" ", "_")
                .replace("–", "_")
            )

            phase = phases.setdefault(
                phase_id,
                RoadmapPhase(
                    phase_id=phase_id,
                    phase_name=phase_name,
                    horizon=horizon,
                ),
            )

            dimension_recommendations = (
                recommendations.get(
                    tpi.dimension_id,
                    [],
                )
            )

            if dimension_recommendations:

                for recommendation in (
                    dimension_recommendations
                ):

                    phase.items.append(
                        self._create_item(
                            tpi,
                            recommendation,
                            phase_name,
                            horizon,
                        )
                    )

            else:

                phase.items.append(
                    self._create_placeholder_item(
                        tpi,
                        phase_name,
                        horizon,
                    )
                )

        return self._sort_phases(
            list(phases.values())
        )

    # ========================================================================
    # TABLE
    # ========================================================================

    def to_dataframe(
        self,
        roadmap: list[RoadmapPhase],
    ) -> pd.DataFrame:
        """
        Converts the roadmap into a DataFrame
        suitable for Streamlit or export.
        """

        rows = []

        for phase in roadmap:

            for item in phase.items:

                rows.append(
                    {
                        "Phase": phase.phase_name,
                        "Horizon": phase.horizon,
                        "Recommendation_ID": (
                            item.recommendation_id
                        ),
                        "Action": item.title,
                        "Dimension": (
                            item.dimension_id
                        ),
                        "Pillar": item.pillar_id,
                        "Priority": item.priority,
                        "TPI": item.tpi_score,
                        "Gap": item.gap,
                        "Effort": item.effort,
                    }
                )

        return pd.DataFrame(rows)

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def get_summary(
        self,
        roadmap: list[RoadmapPhase],
    ) -> dict[str, Any]:
        """
        Produces a roadmap summary.
        """

        total_items = sum(
            len(phase.items)
            for phase in roadmap
        )

        return {
            "phase_count": len(
                roadmap
            ),
            "total_actions": total_items,
            "actions_by_phase": {
                phase.phase_name: len(
                    phase.items
                )
                for phase in roadmap
            },
            "phases": [
                {
                    "phase": phase.phase_name,
                    "horizon": phase.horizon,
                    "actions": len(
                        phase.items
                    ),
                }
                for phase in roadmap
            ],
        }

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _resolve_phase(
        self,
        priority: str,
    ) -> tuple[str, str]:

        if priority in self.phase_mapping:
            return self.phase_mapping[
                priority
            ]

        normalized = (
            str(priority)
            .strip()
            .lower()
        )

        for key, value in (
            self.phase_mapping.items()
        ):
            if (
                key.lower()
                == normalized
            ):
                return value

        return (
            "Phase 4",
            "> 24 months",
        )

    @staticmethod
    def _create_item(
        tpi: TPIResult,
        recommendation: RecommendationResult,
        phase_name: str,
        horizon: str,
    ) -> RoadmapItem:

        return RoadmapItem(
            recommendation_id=(
                recommendation.recommendation_id
            ),
            title=recommendation.title,
            dimension_id=tpi.dimension_id,
            pillar_id=recommendation.pillar_id,
            priority=(
                recommendation.priority
            ),
            phase=phase_name,
            horizon=horizon,
            effort=recommendation.effort,
            tpi_score=tpi.tpi_score,
            gap=tpi.gap,
            detailed_actions=(
                recommendation.detailed_actions
            ),
            prerequisites=(
                recommendation.prerequisites
            ),
            dependencies=(
                recommendation.dependencies
            ),
            completion_evidence=(
                recommendation.completion_evidence
            ),
            expected_impact=(
                recommendation.expected_impact
            ),
            source_reference=(
                recommendation.source_reference
            ),
        )

    @staticmethod
    def _create_placeholder_item(
        tpi: TPIResult,
        phase_name: str,
        horizon: str,
    ) -> RoadmapItem:

        return RoadmapItem(
            recommendation_id=(
                f"NO-REC-{tpi.dimension_id}"
            ),
            title=(
                f"Define an action "
                f"for {tpi.dimension_name}"
            ),
            dimension_id=tpi.dimension_id,
            pillar_id="",
            priority=tpi.priority_category,
            phase=phase_name,
            horizon=horizon,
            effort="To be determined",
            tpi_score=tpi.tpi_score,
            gap=tpi.gap,
        )

    @staticmethod
    def _sort_phases(
        phases: list[RoadmapPhase],
    ) -> list[RoadmapPhase]:

        order = {
            "Phase 1": 1,
            "Phase 1–2": 2,
            "Phase 2": 3,
            "Phase 3": 4,
            "Phase 4": 5,
        }

        for phase in phases:

            phase.items.sort(
                key=lambda item: (
                    -(
                        item.tpi_score
                        if item.tpi_score
                        is not None
                        else 0
                    ),
                    -(
                        item.gap
                        if item.gap
                        is not None
                        else 0
                    ),
                    item.title,
                )
            )

        return sorted(
            phases,
            key=lambda phase: order.get(
                phase.phase_name,
                99,
            ),
        )


RoadmapGenerator = RoadmapEngine