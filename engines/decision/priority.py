"""
priority.py — JDMAF decision prioritization orchestration.

Responsibilities:
- consolidate GapResult and TPIResult;
- associate recommendations with priority dimensions;
- build a prioritization matrix;
- provide priority dimensions;
- generate a decision-making summary.

This module does not recalculate TPI:
TPI calculation remains in engines/decision/tpi.py.

Architecture:
Gap
↓
TPI
↓
Priority
↓
Recommendations
↓
Roadmap
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pandas as pd

from engines.decision.gap import GapResult
from engines.decision.tpi import TPIEngine, TPIResult
from engines.decision.recommendation import (
    RecommendationEngine,
    RecommendationResult,
)


# ============================================================================
# RESULT
# ============================================================================


@dataclass
class PriorityResult:
    """
    Consolidated prioritization result for a dimension.
    """

    dimension_id: str
    dimension_name: str

    current_score: float
    target_score: float
    gap: float

    tpi_score: Optional[float]
    priority_category: str

    recommendations: list[RecommendationResult] = field(
        default_factory=list
    )

    details: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result to a dictionary.
        """

        return {
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "current_score": round(
                self.current_score,
                2,
            ),
            "target_score": round(
                self.target_score,
                2,
            ),
            "gap": round(
                self.gap,
                2,
            ),
            "tpi_score": (
                round(self.tpi_score, 3)
                if self.tpi_score is not None
                else None
            ),
            "priority_category": self.priority_category,
            "recommendations": [
                recommendation.to_dict()
                for recommendation
                in self.recommendations
            ],
            "details": self.details,
        }


# ============================================================================
# ENGINE
# ============================================================================


class PriorityEngine:
    """
    Decision prioritization orchestration engine.

    It consolidates:
    - maturity gaps;
    - TPI results;
    - recommendations.

    It does not modify any of these results.
    """

    PRIORITY_ORDER = {
        "Critical": 0,
        "High": 1,
        "Medium": 2,
        "Low": 3,
        "Very Low": 4,

        # Backward-compatible internal values
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    def __init__(
        self,
        tpi_engine: Optional[TPIEngine] = None,
        recommendation_engine: Optional[
            RecommendationEngine
        ] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> None:

        self.config = dict(config or {})

        self.tpi_engine = (
            tpi_engine
            or TPIEngine(self.config)
        )

        self.recommendation_engine = (
            recommendation_engine
        )

    # ========================================================================
    # MAIN API
    # ========================================================================

    def build_priority_analysis(
        self,
        gap_results: list[GapResult],
        tpi_results: Optional[list[TPIResult]] = None,
        recommendations: Optional[
            Mapping[str, list[RecommendationResult]]
        ] = None,
    ) -> list[PriorityResult]:

        if not isinstance(gap_results, list):
            raise TypeError(
                "gap_results must be a list."
            )

        tpi_by_dimension = {
            result.dimension_id: result
            for result in (tpi_results or [])
        }

        recommendation_by_dimension = dict(
            recommendations or {}
        )

        results: list[PriorityResult] = []

        for gap in gap_results:

            if gap.entity_type != "dimension":
                continue

            tpi = tpi_by_dimension.get(
                gap.entity_id
            )

            if tpi is None:
                continue

            results.append(
                PriorityResult(
                    dimension_id=gap.entity_id,
                    dimension_name=gap.entity_name,

                    current_score=gap.current_score,
                    target_score=gap.target_score,
                    gap=gap.gap,

                    tpi_score=float(
                        tpi.tpi_score
                    ),

                    # IMPORTANT:
                    # Priority comes directly from the TPI.
                    priority_category=(
                        tpi.priority_category
                    ),

                    recommendations=(
                        recommendation_by_dimension.get(
                            gap.entity_id,
                            [],
                        )
                    ),

                    details={
                        "gap_priority": gap.priority,
                        "gap_percent": gap.gap_percent,

                        "current_level": (
                            gap.details or {}
                        ).get(
                            "current_level"
                        ),

                        "target_level": (
                            gap.details or {}
                        ).get(
                            "target_level"
                        ),
                    },
                )
            )

        # UNIQUE ranking based on descending TPI score
        return sorted(
            results,
            key=lambda result: (
                -float(
                    result.tpi_score
                )
                if result.tpi_score is not None
                else float("inf"),
                result.dimension_id,
            ),
        )

    # ========================================================================
    # COMPLETE CALCULATION
    # ========================================================================

    def run(
        self,
        gap_results: list[GapResult],
        decision_inputs: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
        tpi_weights: Optional[
            Mapping[str, float]
        ] = None,
    ) -> dict[str, Any]:
        """
        Run a complete decision analysis.

        TPI calculation is performed only when decision_inputs
        are provided.

        Returns:
            {
                "tpi_results": [...],
                "priority_results": [...],
                "summary": {...}
            }
        """

        tpi_results: list[TPIResult] = []

        if decision_inputs is not None:
            tpi_results = (
                self.tpi_engine.calculate_tpi(
                    gap_results=gap_results,
                    decision_inputs=decision_inputs,
                    weights=tpi_weights,
                )
            )

        recommendations = {}

        if (
            self.recommendation_engine
            is not None
        ):
            recommendations = (
                self.recommendation_engine
                .get_all_recommendations(
                    gap_results,
                    tpi_results,
                )
            )

        priority_results = (
            self.build_priority_analysis(
                gap_results,
                tpi_results,
                recommendations,
            )
        )

        return {
            "tpi_results": tpi_results,
            "priority_results": priority_results,
            "summary": self.get_summary(
                priority_results
            ),
        }

    # ========================================================================
    # MATRIX
    # ========================================================================

    def build_priority_matrix(
        self,
        results: list[PriorityResult],
    ) -> pd.DataFrame:
        """
        Build a tabular prioritization matrix
        for Streamlit or data export.
        """

        rows = []

        for result in results:

            rows.append(
                {
                    "Dimension": result.dimension_id,
                    "Name": result.dimension_name,
                    "Current Score": result.current_score,
                    "Target": result.target_score,
                    "Gap": result.gap,
                    "TPI": result.tpi_score,
                    "Priority": result.priority_category,
                    "Recommendations": len(
                        result.recommendations
                    ),
                }
            )

        return pd.DataFrame(rows)

    # ========================================================================
    # PRIORITIES
    # ========================================================================

    def get_top_priorities(
        self,
        results: list[PriorityResult],
        limit: int = 5,
    ) -> list[PriorityResult]:
        """
        Return the top priority dimensions.
        """

        if limit <= 0:
            return []

        return results[:limit]

    def get_critical_priorities(
        self,
        results: list[PriorityResult],
    ) -> list[PriorityResult]:
        """
        Return critical and high-priority dimensions.
        """

        return [
            result
            for result in results
            if result.priority_category
            in {
                "Critical",
                "High",
                "critical",
                "high",
            }
        ]

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def get_summary(
        self,
        results: list[PriorityResult],
    ) -> dict[str, Any]:
        """
        Generate a prioritization summary.
        """

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

        tpi_values = [
            result.tpi_score
            for result in results
            if result.tpi_score is not None
        ]

        return {
            "total_dimensions": len(
                results
            ),
            "critical_count": sum(
                1
                for result in results
                if result.priority_category
                in {
                    "Critical",
                    "critical",
                }
            ),
            "high_count": sum(
                1
                for result in results
                if result.priority_category
                in {
                    "High",
                    "high",
                }
            ),
            "average_tpi": (
                round(
                    sum(tpi_values)
                    / len(tpi_values),
                    3,
                )
                if tpi_values
                else None
            ),
            "priority_distribution": distribution,
            "top_dimensions": [
                {
                    "dimension_id": result.dimension_id,
                    "dimension_name": result.dimension_name,
                    "priority": result.priority_category,
                    "tpi": result.tpi_score,
                    "gap": result.gap,
                }
                for result in results[:5]
            ],
        }

    # ========================================================================
    # HELPERS
    # ========================================================================

    @classmethod
    def _sort_key(
        cls,
        result: PriorityResult,
    ) -> tuple:

        priority_rank = cls.PRIORITY_ORDER.get(
            result.priority_category,
            99,
        )

        tpi = (
            result.tpi_score
            if result.tpi_score is not None
            else -1
        )

        return (
            -tpi,
        )

    @staticmethod
    def _gap_priority_label(
        priority: str,
    ) -> str:

        mapping = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "none": "Very Low",
        }

        return mapping.get(
            priority,
            priority,
        )


DecisionPriorityEngine = PriorityEngine