"""
aggregation.py — JDMAF Aggregation Engine.

Responsibility:
Orchestrate the complete scoring calculation:

    indicators
          ↓
    subdimensions
          ↓
    dimensions
          ↓
    pillars
          ↓
    DMI

This module belongs exclusively to the backend.
It contains no frontend interface logic.

Architecture used:
data.loader.load_referentiel() -> Referentiel
data.loader.load_assessment()  -> Assessment

The engine works directly with the objects defined in
data/models.py. It does not use pandas DataFrames and
does not depend on a ReferenceLoader.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from config import settings, constants
from data.models import Assessment, Referentiel
from engines.assessment.scoring import ScoringEngine, ScoreResult
from engines.assessment.validator import ensure_valid, validate_assessment


logger = settings.get_logger(__name__)


class AggregationEngine:
    """
    Engine responsible for aggregating the assessment model.

    The engine receives a Referentiel already loaded by data.loader
    and uses the ScoringEngine to perform the calculations.

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
    """

    def __init__(
        self,
        referentiel: Referentiel,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the aggregation engine.

        Args:
            referentiel:
                Referentiel object returned by load_referentiel().

            config:
                Optional scoring engine configuration.
        """

        if not isinstance(referentiel, Referentiel):
            raise TypeError(
                "referentiel must be an instance of Referentiel."
            )

        self.referentiel = referentiel
        self.config = config or {}

        self.validate_before_aggregation = self.config.get(
            "validate_before_aggregation",
            True,
        )

        self.scoring_engine = ScoringEngine(self.config)

        logger.info(
            "AggregationEngine initialized: "
            "%d pillars, %d dimensions, %d subdimensions, %d indicators.",
            len(self.referentiel.pillars),
            len(self.referentiel.dimensions),
            len(self.referentiel.subdimensions),
            len(self.referentiel.indicators),
        )

    # ========================================================================
    # MAIN API
    # ========================================================================

    def aggregate_scores(
        self,
        assessment: Assessment,
    ) -> Dict[str, Any]:
        """
        Calculate the complete assessment.

        Args:
            assessment:
                Assessment object returned by load_assessment().

        Returns:
            Dictionary containing:

                indicators
                subdimensions
                dimensions
                pillars
                dmi
                metadata
        """

        if not isinstance(assessment, Assessment):
            raise TypeError(
                "assessment must be an instance of Assessment."
            )

        if self.validate_before_aggregation:
            validation_report = validate_assessment(
                assessment,
                self.referentiel,
            )

            ensure_valid(validation_report)

        logger.info(
            "Starting aggregation for assessment %s.",
            assessment.metadata.assessment_id,
        )

        # ------------------------------------------------------------------
        # 1. Indicators
        # ------------------------------------------------------------------

        indicator_results = self._calculate_indicator_scores(
            assessment
        )

        # ------------------------------------------------------------------
        # 2. Subdimensions
        # ------------------------------------------------------------------

        subdimension_results = self._calculate_subdimension_scores(
            indicator_results
        )

        # ------------------------------------------------------------------
        # 3. Dimensions
        # ------------------------------------------------------------------

        dimension_results = self._calculate_dimension_scores(
            subdimension_results
        )

        # ------------------------------------------------------------------
        # 4. Pillars
        # ------------------------------------------------------------------

        pillar_results = self._calculate_pillar_scores(
            dimension_results
        )

        # ------------------------------------------------------------------
        # 5. DMI
        # ------------------------------------------------------------------

        dmi_result = self._calculate_dmi(
            pillar_results
        )

        results = {
            "indicators": indicator_results,
            "subdimensions": subdimension_results,
            "dimensions": dimension_results,
            "pillars": pillar_results,
            "dmi": dmi_result,
            "metadata": {
                "assessment_id": assessment.metadata.assessment_id,
                "site_id": assessment.metadata.site_id,
                "site_name": assessment.metadata.site_name,
                "total_indicators": len(indicator_results),
                "total_subdimensions": len(subdimension_results),
                "total_dimensions": len(dimension_results),
                "total_pillars": len(pillar_results),
                "dmi_score": (
                    dmi_result.score
                    if dmi_result is not None
                    else None
                ),
                "dmi_level": (
                    dmi_result.level
                    if dmi_result is not None
                    else None
                ),
                "dmi_level_name": (
                    dmi_result.level_name
                    if dmi_result is not None
                    else None
                ),
            },
        }

        logger.info(
            "Aggregation completed: DMI=%s.",
            (
                dmi_result.score
                if dmi_result is not None
                else None
            ),
        )

        return results

    # ========================================================================
    # INDICATORS
    # ========================================================================

    def _calculate_indicator_scores(
        self,
        assessment: Assessment,
    ) -> Dict[str, ScoreResult]:
        """
        Calculate individual indicator scores.

        A Not Applicable indicator is excluded from higher-level
        aggregations according to the logic defined in ScoringEngine.

        A missing score for an Applicable indicator blocks the
        calculation if settings.ALLOW_MISSING_SCORE_ON_APPLICABLE
        is False.
        """

        results: Dict[str, ScoreResult] = {}

        for indicator_id, indicator_score in (
            assessment.indicator_scores.items()
        ):
            indicator_id = str(indicator_id).strip()

            # --------------------------------------------------------------
            # Check indicator existence
            # --------------------------------------------------------------

            indicator = self.referentiel.indicators.get(
                indicator_id
            )

            if indicator is None:
                raise ValueError(
                    f"Unknown indicator in assessment: "
                    f"{indicator_id}"
                )

            # --------------------------------------------------------------
            # Applicability
            # --------------------------------------------------------------

            applicability = (
                indicator_score.applicability
                or constants.APPLICABILITY_APPLICABLE
            )

            applicability = str(
                applicability
            ).strip()

            if (
                applicability
                == constants.APPLICABILITY_NOT_APPLICABLE
            ):
                results[indicator_id] = (
                    self.scoring_engine.calculate_indicator_score(
                        indicator_id=indicator_id,
                        selected_score=0,
                        scoring_grid={},
                        indicator_name=indicator.name,
                        parent_id=indicator.subdimension_id,
                        applicability=applicability,
                    )
                )

                continue

            if (
                applicability
                != constants.APPLICABILITY_APPLICABLE
            ):
                raise ValueError(
                    f"{indicator_id}: Invalid applicability: "
                    f"{applicability!r}"
                )

            # --------------------------------------------------------------
            # Missing score
            # --------------------------------------------------------------

            selected_score = indicator_score.selected_score

            if selected_score is None:

                if settings.ALLOW_MISSING_SCORE_ON_APPLICABLE:
                    logger.warning(
                        "%s: score is missing but allowed by settings.",
                        indicator_id,
                    )

                    continue

                raise ValueError(
                    f"{indicator_id}: indicator is applicable "
                    "but Selected_Score is empty."
                )

            # --------------------------------------------------------------
            # Score normalization
            # --------------------------------------------------------------

            selected_score = self._normalize_score(
                indicator_id,
                selected_score,
            )

            # --------------------------------------------------------------
            # Scoring grid
            # --------------------------------------------------------------

            scoring_grid = self._get_scoring_grid(
                indicator_id,
                selected_score,
            )

            # --------------------------------------------------------------
            # Calculate indicator score
            # --------------------------------------------------------------

            results[indicator_id] = (
                self.scoring_engine.calculate_indicator_score(
                    indicator_id=indicator_id,
                    selected_score=selected_score,
                    scoring_grid=scoring_grid,
                    indicator_name=indicator.name,
                    parent_id=indicator.subdimension_id,
                    applicability=applicability,
                )
            )

        return results

    # ========================================================================
    # SUBDIMENSIONS
    # ========================================================================

    def _calculate_subdimension_scores(
        self,
        indicator_results: Dict[str, ScoreResult],
    ) -> Dict[str, ScoreResult]:
        """
        Aggregate indicators into subdimensions.

        Subdimensions are retrieved directly from the Referentiel
        so that no subdimension is lost, even when it contains
        only Not Applicable indicators.
        """

        results: Dict[str, ScoreResult] = {}

        for subdimension_id, subdimension in (
            self.referentiel.subdimensions.items()
        ):

            indicator_scores = []

            for indicator_id in subdimension.indicator_ids:

                result = indicator_results.get(
                    indicator_id
                )

                if result is not None:
                    indicator_scores.append(
                        result
                    )

            result = (
                self.scoring_engine.calculate_subdimension_score(
                    subdimension_id=subdimension_id,
                    indicator_scores=indicator_scores,
                    subdimension_name=subdimension.name,
                )
            )

            results[subdimension_id] = result

        return results

    # ========================================================================
    # DIMENSIONS
    # ========================================================================

    def _calculate_dimension_scores(
        self,
        subdimension_results: Dict[str, ScoreResult],
    ) -> Dict[str, ScoreResult]:
        """
        Aggregate subdimensions into dimensions.
        """

        results: Dict[str, ScoreResult] = {}

        for dimension_id, dimension in (
            self.referentiel.dimensions.items()
        ):

            subdimension_scores = []

            for subdimension_id in (
                dimension.subdimension_ids
            ):

                result = subdimension_results.get(
                    subdimension_id
                )

                if result is not None:
                    subdimension_scores.append(
                        result
                    )

            weights = self._get_weights_for_level(
                level="Subdimension",
                parent_id=dimension_id,
            )

            result = (
                self.scoring_engine.calculate_dimension_score(
                    dimension_id=dimension_id,
                    subdimension_scores=subdimension_scores,
                    dimension_name=dimension.name,
                    weights=weights,
                )
            )

            results[dimension_id] = result

        return results

    # ========================================================================
    # PILLARS
    # ========================================================================

    def _calculate_pillar_scores(
        self,
        dimension_results: Dict[str, ScoreResult],
    ) -> Dict[str, ScoreResult]:
        """
        Aggregate dimensions into pillars.
        """

        results: Dict[str, ScoreResult] = {}

        for pillar_id, pillar in (
            self.referentiel.pillars.items()
        ):

            dimension_scores = []

            for dimension_id in pillar.dimension_ids:

                result = dimension_results.get(
                    dimension_id
                )

                if result is not None:
                    dimension_scores.append(
                        result
                    )

            weights = self._get_weights_for_level(
                level="Dimension",
                parent_id=pillar_id,
            )

            result = (
                self.scoring_engine.calculate_pillar_score(
                    pillar_id=pillar_id,
                    dimension_scores=dimension_scores,
                    pillar_name=pillar.name,
                    weights=weights,
                )
            )

            results[pillar_id] = result

        return results

    # ========================================================================
    # DMI
    # ========================================================================

    def _calculate_dmi(
        self,
        pillar_results: Dict[str, ScoreResult],
    ) -> Optional[ScoreResult]:
        """
        Calculate the DMI from the pillars.
        """

        if not pillar_results:
            return None

        pillar_scores = list(
            pillar_results.values()
        )

        weights = self._get_weights_for_level(
            level="Pillar",
            parent_id="DMI",
        )

        return self.scoring_engine.calculate_dmi(
            pillar_scores=pillar_scores,
            weights=weights,
        )

    # ========================================================================
    # INDICATOR UTILITIES
    # ========================================================================

    def _normalize_score(
        self,
        indicator_id: str,
        selected_score: Any,
    ) -> int:
        """
        Convert a score into a valid integer.

        Excel may provide a value such as 3.0 while the
        expected business value is 3.
        """

        try:
            numeric_score = float(
                selected_score
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{indicator_id}: invalid score "
                f"{selected_score!r}."
            ) from exc

        if not numeric_score.is_integer():
            raise ValueError(
                f"{indicator_id}: score "
                f"{numeric_score} is not an integer."
            )

        score = int(
            numeric_score
        )

        if score < 0 or score > 5:
            raise ValueError(
                f"{indicator_id}: score out of range "
                f"(0-5): {score}."
            )

        return score

    # ========================================================================
    # SCORING GRID
    # ========================================================================

    def _get_scoring_grid(
        self,
        indicator_id: str,
        selected_score: int,
    ) -> Dict[str, Any]:
        """
        Return the scoring grid entry corresponding to an
        indicator and its selected score.

        The Referentiel directly contains:

            indicator_scoring_grids[
                indicator_id
            ][score]
        """

        indicator_grids = (
            self.referentiel.indicator_scoring_grids.get(
                indicator_id
            )
        )

        if indicator_grids is None:
            raise ValueError(
                f"No scoring grid found "
                f"for indicator {indicator_id}."
            )

        grid_entry = indicator_grids.get(
            selected_score
        )

        if grid_entry is None:
            raise ValueError(
                f"Scoring grid entry missing for "
                f"{indicator_id}, score {selected_score}."
            )

        # The ScoringEngine can receive a dictionary.
        return {
            "Indicator_ID": grid_entry.indicator_id,
            "Score": grid_entry.score,
            "Score_Label": grid_entry.score_label,
            "Observable_Situation": (
                grid_entry.observable_situation
            ),
            "Mandatory_Criteria": (
                grid_entry.mandatory_criteria
            ),
            "Possible_Evidence": (
                grid_entry.possible_evidence
            ),
            "Disqualifying_Conditions": (
                grid_entry.disqualifying_conditions
            ),
            "Evaluator_Guidance": (
                grid_entry.evaluator_guidance
            ),
            "Next_Score_Requirement": (
                grid_entry.next_score_requirement
            ),
        }

    # ========================================================================
    # WEIGHTS
    # ========================================================================

    def _get_weights_for_level(
        self,
        level: str,
        parent_id: str,
    ) -> Optional[Dict[str, float]]:
        """
        Retrieve weights from Referentiel.weights.

        Structure:

            referentiel.weights[
                hierarchy_level
            ][component_id] -> WeightEntry

        The lookup also uses parent_id to retain only the
        components belonging to the requested parent.
        """

        level_weights = self.referentiel.weights.get(
            level
        )

        if not level_weights:
            logger.warning(
                "No weights found for hierarchy level %s.",
                level,
            )

            return None

        weights: Dict[str, float] = {}

        for component_id, entry in level_weights.items():

            # Check parent.
            if entry.parent_id != parent_id:
                continue

            weight = entry.resolved_weight

            if weight < 0:
                raise ValueError(
                    f"Negative weight for {component_id}: "
                    f"{weight}"
                )

            weights[component_id] = float(
                weight
            )

        if not weights:
            logger.warning(
                "No weights found for "
                "%s/%s. Default weights from "
                "ScoringEngine will be used.",
                level,
                parent_id,
            )

            return None

        total = sum(
            weights.values()
        )

        if abs(
            total - 1.0
        ) > constants.WEIGHT_SUM_TOLERANCE:

            message = (
                f"Invalid weight sum for "
                f"{level}/{parent_id}: "
                f"{total:.6f}"
            )

            if settings.STRICT_WEIGHT_VALIDATION:
                raise ValueError(
                    message
                )

            logger.warning(
                "%s. Automatic normalization applied.",
                message,
            )

            weights = {
                component_id: weight / total
                for component_id, weight
                in weights.items()
            }

        return weights

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def get_summary(
        self,
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce a backend summary that can easily be consumed
        by future frontend pages.

        This method contains no frontend logic.
        """

        dmi = results.get(
            "dmi"
        )

        summary = {
            "dmi": {
                "score": (
                    dmi.score
                    if dmi is not None
                    else None
                ),
                "level": (
                    dmi.level
                    if dmi is not None
                    else None
                ),
                "level_name": (
                    dmi.level_name
                    if dmi is not None
                    else None
                ),
            },
            "pillars": {},
            "dimensions": {},
            "top_strengths": [],
            "top_weaknesses": [],
        }

        # ------------------------------------------------------------------
        # Pillars
        # ------------------------------------------------------------------

        for pillar_id, result in results.get(
            "pillars",
            {},
        ).items():

            summary["pillars"][pillar_id] = {
                "score": result.score,
                "level": result.level,
                "level_name": result.level_name,
            }

        # ------------------------------------------------------------------
        # Dimensions
        # ------------------------------------------------------------------

        for dimension_id, result in results.get(
            "dimensions",
            {},
        ).items():

            summary["dimensions"][dimension_id] = {
                "score": result.score,
                "level": result.level,
                "level_name": result.level_name,
            }

        # ------------------------------------------------------------------
        # Strengths / weaknesses
        # ------------------------------------------------------------------

        dimension_scores = [
            (
                dimension_id,
                result.score,
            )
            for dimension_id, result in results.get(
                "dimensions",
                {},
            ).items()
            if result.score is not None
            and result.applicability
            != constants.APPLICABILITY_NOT_APPLICABLE
        ]

        sorted_dimensions = sorted(
            dimension_scores,
            key=lambda item: item[1],
            reverse=True,
        )

        summary["top_strengths"] = (
            sorted_dimensions[:3]
        )

        summary["top_weaknesses"] = (
            sorted_dimensions[-3:]
        )

        return summary