"""
scoring.py — JDMAF Score Calculation Engine.

Responsibilities:
- calculate indicator scores
- calculate subdimension scores
- calculate dimension scores
- calculate pillar scores
- calculate the DMI

This module contains no frontend logic.

Hierarchy:
Indicator
↓
Subdimension
↓
Dimension
↓
Pillar
↓
DMI

Rules:
R1: Indicator score must be an integer in [0, 5]
R2: Level is selected by the evaluator according to the scoring grid
R3: Recommended evidence is controlled in validator.py

Aggregation:
Subdimension = capped average of indicators
Dimension    = weighted average of subdimensions
Pillar       = weighted average of dimensions
DMI          = weighted average of pillars × 20
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from config import constants, settings

logger = settings.get_logger(__name__)

# ============================================================================
# CALCULATION RESULT
# ============================================================================

@dataclass
class ScoreResult:
    """
    Result of a score calculation for an entity in the hierarchy.
    """

    entity_id: str
    entity_name: str
    entity_type: str
    score: float
    level: int
    level_name: str

    parent_id: Optional[str] = None
    children_scores: Optional[Dict[str, float]] = None

    applicability: str = constants.APPLICABILITY_APPLICABLE

    gap_to_target: Optional[float] = None

    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result into a dictionary that can be consumed
        by other backend modules or by the frontend.
        """

        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "score": round(
                self.score,
                settings.SCORE_DECIMAL_PRECISION,
            ),
            "level": self.level,
            "level_name": self.level_name,
            "parent_id": self.parent_id,
            "children_scores": self.children_scores,
            "applicability": self.applicability,
            "gap_to_target": self.gap_to_target,
            "details": self.details,
        }


# ============================================================================
# SCORING ENGINE
# ============================================================================

class ScoringEngine:
    """
    JDMAF scoring engine.

    This class performs mathematical calculations only.
    Global orchestration is handled by aggregation.py.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            config:
                Optional configuration that may contain:

                {
                    "pillar_weights": {...},
                    "dimension_weights": {...},
                    "subdimension_weights": {...}
                }
        """

        self.config = config or {}

        self.maturity_levels = constants.MATURITY_LEVELS

        self.weights = self._load_weights()

    # ------------------------------------------------------------------------
    # WEIGHT LOADING
    # ------------------------------------------------------------------------

    def _load_weights(
        self,
    ) -> Dict[str, Dict[str, float]]:
        """
        Load weighting configurations when provided.

        Weights from the Excel reference repository are normally
        retrieved by aggregation.py.
        """

        return {
            "pillars": self.config.get(
                "pillar_weights",
                {
                    pillar_id: constants.DEFAULT_WEIGHT_PILLAR
                    for pillar_id in constants.PILLARS
                },
            ),
            "dimensions": self.config.get(
                "dimension_weights",
                {},
            ),
            "subdimensions": self.config.get(
                "subdimension_weights",
                {},
            ),
        }

    # ------------------------------------------------------------------------
    # INTERNAL UTILITIES
    # ------------------------------------------------------------------------

    def _get_level_name(
        self,
        level: int,
    ) -> str:
        """Return the name of a maturity level."""

        return self.maturity_levels.get(
            level,
            f"Level {level}",
        )

    def get_maturity_level_description(
        self,
        level: int,
    ) -> str:
        """
        Return the description of a maturity level.

        Descriptions correspond to the maturity scale defined
        in the reference repository.
        """

        descriptions = {
            0: (
                "No digital initiative identified. "
                "Processes are entirely manual or analogue."
            ),
            1: (
                "Digital tools are deployed occasionally "
                "to replace certain manual tasks. "
                "Solutions remain local and poorly standardized."
            ),
            2: (
                "Industrial and information systems (OT/IT) "
                "are interconnected and exchange data reliably."
            ),
            3: (
                "Data is centralized, historized, and accessible "
                "in real time. Performance indicators support management."
            ),
            4: (
                "Data is leveraged to analyze performance, "
                "identify the causes of deviations, and improve operations."
            ),
            5: (
                "Systems assist or automate decision-making "
                "through advanced analytics and artificial intelligence."
            ),
        }

        return descriptions.get(
            level,
            "Level not defined",
        )

    def _validate_score(
        self,
        score: Any,
    ) -> None:
        """
        Validate that an indicator score is an integer between 0 and 5.

        Booleans are explicitly rejected because Python considers
        bool to be a subclass of int.
        """

        if isinstance(score, bool):
            raise ValueError(
                "Score cannot be a boolean."
            )

        if not isinstance(score, int):
            raise ValueError(
                f"Score must be an integer. Received value: {score!r}"
            )

        if score not in constants.VALID_INDICATOR_SCORES:
            raise ValueError(
                f"Score must be between "
                f"{constants.SCORE_MIN} and {constants.SCORE_MAX}. "
                f"Received value: {score}"
            )

    def _normalize_weights(
        self,
        component_ids: List[str],
        weights: Optional[Dict[str, float]],
        default_weight: float,
    ) -> List[float]:
        """
        Return a normalized list of weights.

        Excluded elements (e.g. Not Applicable) are not included
        in component_ids. The remaining weights are therefore
        automatically renormalized.

        Example:
            initial weights = [0.5, 0.5]
            second element = N/A
            remaining weights = [1.0]
        """

        if not component_ids:
            return []

        # No weights provided -> equal weights
        if not weights:
            raw_weights = [
                default_weight
            ] * len(component_ids)

        else:
            raw_weights = []

            for component_id in component_ids:
                value = weights.get(
                    component_id,
                    default_weight,
                )

                if value is None:
                    value = default_weight

                try:
                    value = float(value)

                except (
                    TypeError,
                    ValueError,
                ) as exc:
                    raise ValueError(
                        f"Invalid weight for {component_id}: {value!r}"
                    ) from exc

                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        f"Weight for {component_id} must be "
                        "a finite non-negative number."
                    )

                raw_weights.append(value)

        total_weight = sum(raw_weights)

        if total_weight <= 0:
            raise ValueError(
                "The sum of applicable weights must be strictly positive."
            )

        return [
            weight / total_weight
            for weight in raw_weights
        ]

    def _build_non_applicable_result(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        parent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ScoreResult:
        """
        Build a standard result for an entirely non-applicable entity.
        """

        return ScoreResult(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            score=0.0,
            level=0,
            level_name=self._get_level_name(0),
            parent_id=parent_id,
            applicability=constants.APPLICABILITY_NOT_APPLICABLE,
            details=details or {},
        )

    # ------------------------------------------------------------------------
    # INDICATOR
    # ------------------------------------------------------------------------

    def calculate_indicator_score(
        self,
        indicator_id: str,
        selected_score: int,
        scoring_grid: Optional[Dict[str, Any]] = None,
        indicator_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        applicability: str = constants.APPLICABILITY_APPLICABLE,
    ) -> ScoreResult:
        """
        Calculate the score of an indicator.

        R1:
            Score must be an integer in [0, 5].

        Args:
            indicator_id:
                Indicator ID, e.g. I-D1-01.

            selected_score:
                Score assigned by the evaluator.

            scoring_grid:
                Scoring grid information corresponding
                to the selected level.

            indicator_name:
                Indicator name.

            parent_id:
                Parent subdimension.

            applicability:
                Applicable / Not Applicable.
        """

        if (
            applicability
            == constants.APPLICABILITY_NOT_APPLICABLE
        ):
            return self._build_non_applicable_result(
                entity_id=indicator_id,
                entity_name=indicator_name or indicator_id,
                entity_type="indicator",
                parent_id=parent_id,
                details={
                    "reason": "Indicator marked as Not Applicable"
                },
            )

        if (
            applicability
            != constants.APPLICABILITY_APPLICABLE
        ):
            raise ValueError(
                f"Invalid applicability for {indicator_id}: "
                f"{applicability!r}"
            )

        self._validate_score(
            selected_score
        )

        grid = scoring_grid or {}

        level_name = self._get_level_name(
            selected_score
        )

        return ScoreResult(
            entity_id=indicator_id,
            entity_name=indicator_name
            or grid.get(
                "Indicator_Name",
                indicator_id,
            ),
            entity_type="indicator",
            score=float(selected_score),
            level=selected_score,
            level_name=level_name,
            parent_id=parent_id,
            applicability=(
                constants.APPLICABILITY_APPLICABLE
            ),
            details={
                "selected_score": selected_score,
                "grid_description": grid.get(
                    "Observable_Situation",
                    "",
                ),
                "evidence_required": grid.get(
                    "Possible_Evidence",
                    "",
                ),
            },
        )

    # ------------------------------------------------------------------------
    # SUBDIMENSION
    # ------------------------------------------------------------------------

    def calculate_subdimension_score(
        self,
        subdimension_id: str,
        indicator_scores: List[ScoreResult],
        subdimension_name: Optional[str] = None,
    ) -> ScoreResult:
        """
        Calculate the score of a subdimension.

        Rule:
            Score_SD =
                min(
                    average(applicable indicators),
                    minimum(applicable indicators) + 1
                )

        This rule prevents a critical weakness from being hidden
        by a high average score.
        """

        if not indicator_scores:
            return self._build_non_applicable_result(
                entity_id=subdimension_id,
                entity_name=(
                    subdimension_name
                    or subdimension_id
                ),
                entity_type="subdimension",
                details={
                    "error": "No indicators available"
                },
            )

        applicable_scores = [
            result
            for result in indicator_scores
            if (
                result.applicability
                != constants.APPLICABILITY_NOT_APPLICABLE
            )
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=subdimension_id,
                entity_name=(
                    subdimension_name
                    or subdimension_id
                ),
                entity_type="subdimension",
                details={
                    "reason": (
                        "All indicators are Not Applicable"
                    ),
                    "total_count": len(
                        indicator_scores
                    ),
                },
            )

        scores = [
            result.score
            for result in applicable_scores
        ]

        mean_score = sum(scores) / len(scores)

        minimum_score = min(scores)

        # Capped average rule
        cap = minimum_score + 1.0

        final_score = min(
            mean_score,
            cap,
        )

        final_score = round(
            final_score,
            settings.SCORE_DECIMAL_PRECISION,
        )

        level = int(
            math.floor(final_score)
        )

        level = min(
            max(
                level,
                constants.SCORE_MIN,
            ),
            constants.SCORE_MAX,
        )

        # Determine parent from constants.py
        parent_id = constants.SUBDIMENSIONS.get(
            subdimension_id,
            (None, None),
        )[0]

        return ScoreResult(
            entity_id=subdimension_id,
            entity_name=(
                subdimension_name
                or subdimension_id
            ),
            entity_type="subdimension",
            score=final_score,
            level=level,
            level_name=self._get_level_name(
                level
            ),
            parent_id=parent_id,
            children_scores={
                result.entity_id: result.score
                for result in indicator_scores
            },
            applicability=(
                constants.APPLICABILITY_APPLICABLE
            ),
            details={
                "indicator_scores": scores,
                "mean_score": round(
                    mean_score,
                    settings.SCORE_DECIMAL_PRECISION,
                ),
                "minimum_score": minimum_score,
                "cap": cap,
                "applicable_count": len(
                    applicable_scores
                ),
                "total_count": len(
                    indicator_scores
                ),
            },
        )

    # ------------------------------------------------------------------------
    # DIMENSION
    # ------------------------------------------------------------------------

    def calculate_dimension_score(
        self,
        dimension_id: str,
        subdimension_scores: List[ScoreResult],
        dimension_name: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> ScoreResult:
        """
        Calculate the score of a dimension using a weighted average
        of applicable subdimensions.
        """

        if not subdimension_scores:
            return self._build_non_applicable_result(
                entity_id=dimension_id,
                entity_name=(
                    dimension_name
                    or dimension_id
                ),
                entity_type="dimension",
                parent_id=constants.DIMENSIONS.get(
                    dimension_id,
                    (None, None),
                )[0],
                details={
                    "error": "No subdimensions available"
                },
            )

        applicable_scores = [
            result
            for result in subdimension_scores
            if (
                result.applicability
                != constants.APPLICABILITY_NOT_APPLICABLE
            )
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=dimension_id,
                entity_name=(
                    dimension_name
                    or dimension_id
                ),
                entity_type="dimension",
                parent_id=constants.DIMENSIONS.get(
                    dimension_id,
                    (None, None),
                )[0],
                details={
                    "reason": (
                        "All subdimensions are Not Applicable"
                    )
                },
            )

        component_ids = [
            result.entity_id
            for result in applicable_scores
        ]

        normalized_weights = self._normalize_weights(
            component_ids=component_ids,
            weights=weights,
            default_weight=(
                constants
                .DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION
            ),
        )

        weighted_sum = sum(
            result.score * weight
            for result, weight in zip(
                applicable_scores,
                normalized_weights,
            )
        )

        final_score = round(
            weighted_sum,
            settings.SCORE_DECIMAL_PRECISION,
        )

        level = int(
            math.floor(final_score)
        )

        level = min(
            max(
                level,
                constants.SCORE_MIN,
            ),
            constants.SCORE_MAX,
        )

        parent_id = constants.DIMENSIONS.get(
            dimension_id,
            (None, None),
        )[0]

        return ScoreResult(
            entity_id=dimension_id,
            entity_name=(
                dimension_name
                or dimension_id
            ),
            entity_type="dimension",
            score=final_score,
            level=level,
            level_name=self._get_level_name(
                level
            ),
            parent_id=parent_id,
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=(
                constants.APPLICABILITY_APPLICABLE
            ),
            details={
                "subdimension_scores": [
                    result.score
                    for result in applicable_scores
                ],
                "weights": dict(
                    zip(
                        component_ids,
                        normalized_weights,
                    )
                ),
                "weighted_sum": round(
                    weighted_sum,
                    settings.SCORE_DECIMAL_PRECISION,
                ),
                "applicable_count": len(
                    applicable_scores
                ),
                "total_count": len(
                    subdimension_scores
                ),
            },
        )

    # ------------------------------------------------------------------------
    # PILLAR
    # ------------------------------------------------------------------------

    def calculate_pillar_score(
        self,
        pillar_id: str,
        dimension_scores: List[ScoreResult],
        pillar_name: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> ScoreResult:
        """
        Calculate the score of a pillar using a weighted average
        of applicable dimensions.
        """

        if not dimension_scores:
            return self._build_non_applicable_result(
                entity_id=pillar_id,
                entity_name=(
                    pillar_name
                    or pillar_id
                ),
                entity_type="pillar",
                details={
                    "error": "No dimensions available"
                },
            )

        applicable_scores = [
            result
            for result in dimension_scores
            if (
                result.applicability
                != constants.APPLICABILITY_NOT_APPLICABLE
            )
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=pillar_id,
                entity_name=(
                    pillar_name
                    or pillar_id
                ),
                entity_type="pillar",
                details={
                    "reason": (
                        "All dimensions are Not Applicable"
                    )
                },
            )

        component_ids = [
            result.entity_id
            for result in applicable_scores
        ]

        normalized_weights = self._normalize_weights(
            component_ids=component_ids,
            weights=weights,
            default_weight=(
                constants
                .DEFAULT_WEIGHT_DIMENSION_PER_PILLAR
            ),
        )

        weighted_sum = sum(
            result.score * weight
            for result, weight in zip(
                applicable_scores,
                normalized_weights,
            )
        )

        final_score = round(
            weighted_sum,
            settings.SCORE_DECIMAL_PRECISION,
        )

        level = int(
            math.floor(final_score)
        )

        level = min(
            max(
                level,
                constants.SCORE_MIN,
            ),
            constants.SCORE_MAX,
        )

        return ScoreResult(
            entity_id=pillar_id,
            entity_name=(
                pillar_name
                or pillar_id
            ),
            entity_type="pillar",
            score=final_score,
            level=level,
            level_name=self._get_level_name(
                level
            ),
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=(
                constants.APPLICABILITY_APPLICABLE
            ),
            details={
                "dimension_scores": [
                    result.score
                    for result in applicable_scores
                ],
                "weights": dict(
                    zip(
                        component_ids,
                        normalized_weights,
                    )
                ),
                "weighted_sum": round(
                    weighted_sum,
                    settings.SCORE_DECIMAL_PRECISION,
                ),
                "applicable_count": len(
                    applicable_scores
                ),
                "total_count": len(
                    dimension_scores
                ),
            },
        )

    # ------------------------------------------------------------------------
    # DMI
    # ------------------------------------------------------------------------

    def calculate_dmi(
        self,
        pillar_scores: List[ScoreResult],
        weights: Optional[Dict[str, float]] = None,
    ) -> ScoreResult:
        """
        Calculate the Digital Maturity Index.

        Formula:

            DMI_score = Σ(wi × Pillar_Score)

            DMI_% = DMI_score × 20

        The internal score remains on [0, 5].
        The displayed DMI is expressed on [0, 100].
        """

        if not pillar_scores:
            return self._build_non_applicable_result(
                entity_id="DMI",
                entity_name="Digital Maturity Index",
                entity_type="dmi",
                details={
                    "error": "No pillars available"
                },
            )

        applicable_scores = [
            result
            for result in pillar_scores
            if (
                result.applicability
                != constants.APPLICABILITY_NOT_APPLICABLE
            )
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id="DMI",
                entity_name="Digital Maturity Index",
                entity_type="dmi",
                details={
                    "reason": "No applicable pillars"
                },
            )

        component_ids = [
            result.entity_id
            for result in applicable_scores
        ]

        normalized_weights = self._normalize_weights(
            component_ids=component_ids,
            weights=weights,
            default_weight=constants.DEFAULT_WEIGHT_PILLAR,
        )

        weighted_sum = sum(
            result.score * weight
            for result, weight in zip(
                applicable_scores,
                normalized_weights,
            )
        )

        weighted_sum = round(
            weighted_sum,
            settings.SCORE_DECIMAL_PRECISION,
        )

        dmi_percent = round(
            weighted_sum
            * constants.DMI_SCALE_FACTOR,
            settings.DMI_DECIMAL_PRECISION,
        )

        level = int(
            math.floor(weighted_sum)
        )

        level = min(
            max(
                level,
                constants.SCORE_MIN,
            ),
            constants.SCORE_MAX,
        )

        return ScoreResult(
            entity_id="DMI",
            entity_name="Digital Maturity Index",
            entity_type="dmi",
            score=dmi_percent,
            level=level,
            level_name=self._get_level_name(
                level
            ),
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=(
                constants.APPLICABILITY_APPLICABLE
            ),
            details={
                "pillar_scores": {
                    result.entity_id: result.score
                    for result in applicable_scores
                },
                "weights": dict(
                    zip(
                        component_ids,
                        normalized_weights,
                    )
                ),
                "weighted_score_0_5": weighted_sum,
                "dmi_percent": dmi_percent,
                "applicable_count": len(
                    applicable_scores
                ),
                "total_count": len(
                    pillar_scores
                ),
            },
        )