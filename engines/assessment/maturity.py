"""
maturity.py — JDMAF Maturity Level Management.

Responsibility:
Interpret scores already calculated by the scoring engine
and determine the corresponding maturity level.

Hierarchy:
Indicator       -> score 0..5
Subdimension    -> score 0..5
Dimension       -> score 0..5
Pillar          -> score 0..5
DMI             -> internal score 0..5 / display 0..100 %

Important:
This module does NOT calculate aggregations.
Calculations are performed in scoring.py.
Orchestration is performed in aggregation.py.

This module contains no frontend logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

from config import constants, settings
from data.models import (
    Assessment,
    DimensionMaturityLevel,
    IndicatorScoringGridEntry,
    MaturityLevelDescription,
    Referentiel,
)

logger = settings.get_logger(__name__)


# ============================================================================
# MATURITY RESULT
# ============================================================================


@dataclass(frozen=True)
class MaturityResult:
    """
    Standardized result of a maturity interpretation.

    Attributes:
        score:
            Numerical score on the 0..5 scale.

        level:
            Integer maturity level from 0..5.

        level_name:
            Name of the maturity level.

        description:
            Description of the maturity level.

        evaluation_principle:
            Evaluation principle associated with the level.

        minimum_evidence_principle:
            Principle concerning the minimum expected evidence.

        source:
            Origin of the definition:
                - "generic"
                - "dimension"
                - "indicator"
                - "dmi"
    """

    score: Optional[float]
    level: Optional[int]
    level_name: str = ""
    description: str = ""
    evaluation_principle: str = ""
    minimum_evidence_principle: str = ""
    source: str = "generic"


# ============================================================================
# MATURITY ENGINE
# ============================================================================


class MaturityEngine:
    """
    Engine responsible for interpreting maturity levels.

    It uses data from the Referentiel:

        - GENERIC_MATURITY_SCALE
        - DIMENSION_MATURITY_MATRICES
        - INDICATOR_SCORING_GRIDS

    It does not perform any aggregation.
    """

    MIN_LEVEL = constants.SCORE_MIN
    MAX_LEVEL = constants.SCORE_MAX

    def __init__(
        self,
        referentiel: Referentiel,
        config: Optional[dict[str, Any]] = None,
    ) -> None:

        if not isinstance(referentiel, Referentiel):
            raise TypeError(
                "referentiel must be an instance of Referentiel."
            )

        self.referentiel = referentiel
        self.config = config or {}

        logger.info("MaturityEngine initialized.")

    # ========================================================================
    # SCORE -> LEVEL
    # ========================================================================

    def level_from_score(
        self,
        score: Optional[float],
    ) -> Optional[int]:
        """
        Converts a score from 0..5 into an integer level from 0..5.

        Rule:
            level = integer part of the score

        Examples:
            0.0 -> 0
            1.0 -> 1
            2.7 -> 2
            3.9 -> 3
            5.0 -> 5

        This rule is consistent with scoring.py, which uses
        math.floor() to determine the level.
        """

        if score is None:
            return None

        try:
            numeric_score = float(score)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid maturity score: {score!r}"
            ) from exc

        self._validate_score(numeric_score)

        return int(math.floor(numeric_score))

    # ========================================================================
    # GENERIC MATURITY
    # ========================================================================

    def get_generic_maturity(
        self,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Returns the generic maturity corresponding to a score from 0..5.
        """

        level = self.level_from_score(score)

        if level is None:
            return MaturityResult(
                score=None,
                level=None,
                source="generic",
            )

        description = self.referentiel.maturity_scale.get(level)

        if description is None:
            logger.warning(
                "Level %s is missing from the maturity reference.",
                level,
            )

            return MaturityResult(
                score=float(score),
                level=level,
                level_name=self._fallback_level_name(level),
                source="generic",
            )

        return self._build_generic_result(
            score=float(score),
            description=description,
        )

    # ========================================================================
    # DIMENSION MATURITY
    # ========================================================================

    def get_dimension_maturity(
        self,
        dimension_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Returns the maturity specific to a dimension.

        Priority:
            1. Dimension-specific maturity matrix
            2. Generic maturity scale from the reference
        """

        if not dimension_id:
            raise ValueError(
                "dimension_id cannot be empty."
            )

        level = self.level_from_score(score)

        if level is None:
            return MaturityResult(
                score=None,
                level=None,
                source="dimension",
            )

        dimension_matrix = (
            self.referentiel.dimension_maturity_matrices.get(
                dimension_id,
                {},
            )
        )

        dimension_level = dimension_matrix.get(level)

        if dimension_level is not None:
            return self._build_dimension_result(
                score=float(score),
                maturity=dimension_level,
            )

        logger.warning(
            "Specific maturity description is missing for %s "
            "at level %s. Using generic maturity.",
            dimension_id,
            level,
        )

        generic_result = self.get_generic_maturity(score)

        return MaturityResult(
            score=generic_result.score,
            level=generic_result.level,
            level_name=generic_result.level_name,
            description=generic_result.description,
            evaluation_principle=generic_result.evaluation_principle,
            minimum_evidence_principle=(
                generic_result.minimum_evidence_principle
            ),
            source="generic",
        )

    # ========================================================================
    # INDICATOR MATURITY
    # ========================================================================

    def get_indicator_maturity(
        self,
        indicator_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Returns the maturity definition of an indicator.

        The INDICATOR_SCORING_GRIDS takes priority.
        """

        if not indicator_id:
            raise ValueError(
                "indicator_id cannot be empty."
            )

        level = self.level_from_score(score)

        if level is None:
            return MaturityResult(
                score=None,
                level=None,
                source="indicator",
            )

        grid = self.referentiel.indicator_scoring_grids.get(
            indicator_id,
            {},
        )

        entry = grid.get(level)

        if entry is not None:
            return self._build_indicator_result(
                score=float(score),
                entry=entry,
            )

        logger.warning(
            "Scoring grid is missing for %s at level %s. "
            "Using generic maturity.",
            indicator_id,
            level,
        )

        generic_result = self.get_generic_maturity(score)

        return MaturityResult(
            score=generic_result.score,
            level=generic_result.level,
            level_name=generic_result.level_name,
            description=generic_result.description,
            evaluation_principle=generic_result.evaluation_principle,
            minimum_evidence_principle=(
                generic_result.minimum_evidence_principle
            ),
            source="generic",
        )

    # ========================================================================
    # DMI MATURITY
    # ========================================================================

    def get_dmi_maturity(
        self,
        dmi_score: Optional[float],
    ) -> MaturityResult:
        """
        Interprets the DMI.

        aggregation.py / scoring.py store the displayed DMI on a 0..100 scale.

        Conversion:
            DMI % / 20 = internal score 0..5

        Example:
            0 %   -> 0.0 -> level 0
            20 %  -> 1.0 -> level 1
            50 %  -> 2.5 -> level 2
            80 %  -> 4.0 -> level 4
            100 % -> 5.0 -> level 5
        """

        if dmi_score is None:
            return MaturityResult(
                score=None,
                level=None,
                source="dmi",
            )

        dmi_percent = self._validate_dmi(dmi_score)

        maturity_score = (
            dmi_percent / constants.DMI_SCALE_FACTOR
        )

        generic_result = self.get_generic_maturity(
            maturity_score
        )

        return MaturityResult(
            score=maturity_score,
            level=generic_result.level,
            level_name=generic_result.level_name,
            description=generic_result.description,
            evaluation_principle=(
                generic_result.evaluation_principle
            ),
            minimum_evidence_principle=(
                generic_result.minimum_evidence_principle
            ),
            source="dmi",
        )

    # ========================================================================
    # ASSESSMENT INTERPRETATION
    # ========================================================================

    def assess_indicator(
        self,
        assessment: Assessment,
        indicator_id: str,
    ) -> MaturityResult:
        """
        Interprets the maturity level of an indicator
        within an assessment.
        """

        if not isinstance(assessment, Assessment):
            raise TypeError(
                "assessment must be an instance of Assessment."
            )

        indicator_score = assessment.indicator_scores.get(
            indicator_id
        )

        if indicator_score is None:
            raise KeyError(
                f"Indicator missing from assessment: {indicator_id}"
            )

        if not indicator_score.is_applicable:
            return MaturityResult(
                score=None,
                level=None,
                level_name=constants.APPLICABILITY_NOT_APPLICABLE,
                source="indicator",
            )

        return self.get_indicator_maturity(
            indicator_id=indicator_id,
            score=indicator_score.selected_score,
        )

    # ========================================================================
    # DIMENSION INTERPRETATION
    # ========================================================================

    def assess_dimension(
        self,
        dimension_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Interprets the maturity level of a dimension.
        """

        if dimension_id not in self.referentiel.dimensions:
            raise KeyError(
                f"Unknown dimension in reference: {dimension_id}"
            )

        return self.get_dimension_maturity(
            dimension_id=dimension_id,
            score=score,
        )

    # ========================================================================
    # MULTI-LEVEL SUMMARY
    # ========================================================================

    def build_maturity_summary(
        self,
        indicator_scores: Optional[dict[str, float]] = None,
        dimension_scores: Optional[dict[str, float]] = None,
        pillar_scores: Optional[dict[str, float]] = None,
        dmi_score: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Builds a summary of maturity levels.

        No scores are calculated here.
        Scores are assumed to have already been calculated
        by scoring.py / aggregation.py.
        """

        summary: dict[str, Any] = {
            "indicators": {},
            "dimensions": {},
            "pillars": {},
            "dmi": None,
        }

        # ------------------------------------------------------------------
        # INDICATORS
        # ------------------------------------------------------------------

        if indicator_scores is not None:

            for indicator_id, score in indicator_scores.items():

                result = self.get_indicator_maturity(
                    indicator_id=indicator_id,
                    score=score,
                )

                summary["indicators"][indicator_id] = (
                    self._result_to_dict(result)
                )

        # ------------------------------------------------------------------
        # DIMENSIONS
        # ------------------------------------------------------------------

        if dimension_scores is not None:

            for dimension_id, score in dimension_scores.items():

                result = self.get_dimension_maturity(
                    dimension_id=dimension_id,
                    score=score,
                )

                summary["dimensions"][dimension_id] = (
                    self._result_to_dict(result)
                )

        # ------------------------------------------------------------------
        # PILLARS
        # ------------------------------------------------------------------

        if pillar_scores is not None:

            for pillar_id, score in pillar_scores.items():

                result = self.get_generic_maturity(score)

                summary["pillars"][pillar_id] = (
                    self._result_to_dict(result)
                )

        # ------------------------------------------------------------------
        # DMI
        # ------------------------------------------------------------------

        if dmi_score is not None:

            result = self.get_dmi_maturity(
                dmi_score
            )

            summary["dmi"] = self._result_to_dict(
                result
            )

            summary["dmi"]["dmi_percent"] = (
                self._validate_dmi(dmi_score)
            )

        return summary

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate_score(
        self,
        score: float,
    ) -> None:
        """
        Validates that a score complies with the 0..5 scale.
        """

        if not math.isfinite(score):
            raise ValueError(
                f"Invalid score: {score}. "
                "The score must be a finite numeric value."
            )

        if not (
            self.MIN_LEVEL
            <= score
            <= self.MAX_LEVEL
        ):
            raise ValueError(
                f"Score out of range: {score}. "
                f"The score must be between "
                f"{self.MIN_LEVEL} and {self.MAX_LEVEL}."
            )

    @staticmethod
    def _validate_dmi(
        dmi_score: float,
    ) -> float:
        """
        Validates that the DMI is between 0 and 100%.
        """

        try:
            dmi_percent = float(dmi_score)

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"Invalid DMI: {dmi_score!r}"
            ) from exc

        if not math.isfinite(dmi_percent):

            raise ValueError(
                f"Invalid DMI: {dmi_score!r}. "
                "The DMI must be a finite numeric value."
            )

        if not 0 <= dmi_percent <= 100:

            raise ValueError(
                f"Invalid DMI: {dmi_score!r}. "
                "Expected range: 0..100."
            )

        return dmi_percent

    # ========================================================================
    # MODEL CONVERSION
    # ========================================================================

    @staticmethod
    def _build_generic_result(
        score: float,
        description: MaturityLevelDescription,
    ) -> MaturityResult:

        return MaturityResult(
            score=score,
            level=description.level,
            level_name=description.name,
            description=description.generic_description,
            evaluation_principle=(
                description.generic_evaluation_principle
            ),
            minimum_evidence_principle=(
                description.minimum_evidence_principle
            ),
            source="generic",
        )

    @staticmethod
    def _build_dimension_result(
        score: float,
        maturity: DimensionMaturityLevel,
    ) -> MaturityResult:

        return MaturityResult(
            score=score,
            level=maturity.level,
            level_name=maturity.level_name,
            description=maturity.description,
            evaluation_principle=(
                maturity.key_capabilities_expected
            ),
            minimum_evidence_principle=(
                maturity.minimum_conditions
            ),
            source="dimension",
        )

    @staticmethod
    def _build_indicator_result(
        score: float,
        entry: IndicatorScoringGridEntry,
    ) -> MaturityResult:

        return MaturityResult(
            score=score,
            level=entry.score,
            level_name=entry.score_label,
            description=entry.observable_situation,
            evaluation_principle=entry.mandatory_criteria,
            minimum_evidence_principle=entry.possible_evidence,
            source="indicator",
        )

    # ========================================================================
    # FALLBACK
    # ========================================================================

    @staticmethod
    def _fallback_level_name(
        level: int,
    ) -> str:
        """
        Returns a fallback name if the reference does not contain the level.
        """

        return constants.MATURITY_LEVELS.get(
            level,
            f"Level {level}",
        )

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    @staticmethod
    def _result_to_dict(
        result: MaturityResult,
    ) -> dict[str, Any]:
        """
        Converts a MaturityResult into a dictionary.
        """

        return {
            "score": result.score,
            "level": result.level,
            "level_name": result.level_name,
            "description": result.description,
            "evaluation_principle": (
                result.evaluation_principle
            ),
            "minimum_evidence_principle": (
                result.minimum_evidence_principle
            ),
            "source": result.source,
        }


# ============================================================================
# PUBLIC UTILITY FUNCTIONS
# ============================================================================


def get_maturity_level(
    score: Optional[float],
) -> Optional[int]:
    """
    Returns the level from 0..5 corresponding to a score from 0..5.
    """

    if score is None:
        return None

    try:
        numeric_score = float(score)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            f"Invalid score: {score!r}"
        ) from exc

    if not math.isfinite(numeric_score):

        raise ValueError(
            f"Invalid score: {score!r}. "
            "The score must be a finite numeric value."
        )

    if not (
        constants.SCORE_MIN
        <= numeric_score
        <= constants.SCORE_MAX
    ):

        raise ValueError(
            f"Score out of range: {numeric_score}. "
            f"Expected range: "
            f"{constants.SCORE_MIN}..{constants.SCORE_MAX}."
        )

    return int(math.floor(numeric_score))


def get_maturity_name(
    referentiel: Referentiel,
    level: Optional[int],
) -> str:
    """
    Returns the name of a maturity level from the reference.
    """

    if level is None:
        return ""

    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError(
            f"Invalid maturity level: {level!r}"
        )

    if not (
        constants.SCORE_MIN
        <= level
        <= constants.SCORE_MAX
    ):
        raise ValueError(
            f"Invalid maturity level: {level}"
        )

    entry = referentiel.maturity_scale.get(level)

    if entry is not None:
        return entry.name

    return MaturityEngine._fallback_level_name(level)