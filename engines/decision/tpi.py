"""
TPI Engine
==========

Transformation Priority Index (TPI) engine for the JESA Digital
Maturity Assessment Tool.

Responsibilities
----------------
- Receive native decision values from the Decision Analysis UI.
- Validate the values and their real-world units.
- Normalize heterogeneous parameters internally to [0, 1].
- Calculate the weighted Transformation Priority Index.
- Classify each opportunity according to TPI thresholds.
- Produce priority-matrix data.
- Provide roadmap phase grouping.
- Provide TPI summary information.

Important
---------
The user NEVER enters normalized values.

Examples of native values:

    Business Impact        = 70 %
    Strategic Importance   = 85 %
    Expected ROI           = 30 %
    Implementation Cost   = 2_500_000 MAD
    Implementation Effort = 180 person-days

These values are normalized internally only for mathematical aggregation.

The final TPI is internally represented in [0, 1].

Example:

    0.64 -> 64.0 %
"""


from __future__ import annotations


import math

from dataclasses import dataclass

from typing import Any, Mapping, Optional


import pandas as pd


from config import constants

from engines.assessment.scoring import ScoreResult

from engines.decision.gap import GapResult


# =============================================================================
# DECISION CRITERIA
# =============================================================================
#
# These are the REAL values entered by the user.
#
# They are NOT normalized values.
#
# The engine normalizes them internally before calculating TPI.
# =============================================================================


DECISION_CRITERIA = [
    {
        "id": "business_impact",
        "label": "Business Impact",
        "display_label": "Business Impact (%)",
        "unit": "%",
        "min_value": 0.0,
        "max_value": 100.0,
        "step": 1.0,
        "format": "%.0f %%",
        "direction": "favorable",
        "help": (
            "Estimated operational and business impact of the "
            "transformation opportunity, expressed as a percentage."
        ),
    },
    {
        "id": "strategic_importance",
        "label": "Strategic Importance",
        "display_label": "Strategic Importance (%)",
        "unit": "%",
        "min_value": 0.0,
        "max_value": 100.0,
        "step": 1.0,
        "format": "%.0f %%",
        "direction": "favorable",
        "help": (
            "Estimated alignment of the opportunity with the site's "
            "digital transformation strategy."
        ),
    },
    {
        "id": "expected_roi",
        "label": "Expected ROI",
        "display_label": "Expected ROI (%)",
        "unit": "%",
        "min_value": 0.0,
        "max_value": 100.0,
        "step": 1.0,
        "format": "%.0f %%",
        "direction": "favorable",
        "help": (
            "Expected return on investment after implementation."
        ),
    },
    {
        "id": "implementation_cost",
        "label": "Implementation Cost",
        "display_label": "Implementation Cost (MAD)",
        "unit": "MAD",
        "min_value": 0.0,
        "max_value": 100_000_000.0,
        "step": 1_000.0,
        "format": "%.0f MAD",
        "direction": "inverted",
        "help": (
            "Estimated investment required to implement the "
            "transformation opportunity."
        ),
    },
    {
        "id": "implementation_difficulty",
        "label": "Implementation Difficulty",
        "display_label": "Implementation Difficulty (person-days)",
        "unit": "person-days",
        "min_value": 0.0,
        "max_value": 2_000.0,
        "step": 1.0,
        "format": "%.0f d",
        "direction": "inverted",
        "help": (
            "Estimated implementation effort expressed in "
            "person-days."
        ),
    },
]


DECISION_CRITERIA_BY_ID = {
    criterion["id"]: criterion
    for criterion in DECISION_CRITERIA
}


# =============================================================================
# TPI RESULT
# =============================================================================


@dataclass
class TPIResult:
    """
    Result of a TPI calculation for one dimension.
    """

    dimension_id: str
    dimension_name: str

    # Internal TPI score: [0, 1]
    tpi_score: float

    # Priority label
    priority_category: str

    # Gap in the original maturity scale
    gap: float

    # Original/native decision values
    business_impact: float
    strategic_importance: float
    expected_roi: float
    implementation_cost: float
    implementation_difficulty: float

    # Optional calculation details
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to a serializable dictionary.
        """

        return {
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,

            "tpi_score": round(
                float(self.tpi_score),
                3,
            ),

            "tpi_percent": round(
                float(self.tpi_score) * 100.0,
                1,
            ),

            "priority_category": self.priority_category,

            "gap": round(
                float(self.gap),
                2,
            ),

            "business_impact": self.business_impact,
            "strategic_importance": self.strategic_importance,
            "expected_roi": self.expected_roi,
            "implementation_cost": self.implementation_cost,
            "implementation_difficulty": (
                self.implementation_difficulty
            ),

            "details": self.details,
        }


# =============================================================================
# TPI ENGINE
# =============================================================================


class TPIEngine:
    """
    Transformation Priority Index engine.

    Native user inputs
    ------------------
    Business Impact:
        0 - 100 %

    Strategic Importance:
        0 - 100 %

    Expected ROI:
        0 - 100 %

    Implementation Cost:
        0 - 100,000,000 MAD

    Implementation Difficulty:
        0 - 2,000 person-days

    Internal processing
    -------------------
    Every parameter is normalized to [0, 1].

    Favorable parameter:
        higher value = higher priority

    Inverted parameter:
        higher value = lower priority
    """

    # -------------------------------------------------------------------------
    # Parameters that come from the Decision Analysis grid.
    # -------------------------------------------------------------------------

    PARAMETER_NAMES = (
        "business_impact",
        "strategic_importance",
        "expected_roi",
        "implementation_cost",
        "implementation_difficulty",
    )

    # -------------------------------------------------------------------------
    # All TPI weights, including the maturity gap.
    # -------------------------------------------------------------------------

    WEIGHT_NAMES = (
        "gap",
        *PARAMETER_NAMES,
    )

    # -------------------------------------------------------------------------
    # Default priority thresholds.
    #
    # IMPORTANT:
    #
    # 0.80 -> Critical
    # 0.60 -> High
    # 0.40 -> Medium
    # 0.20 -> Low
    # <0.20 -> Very Low
    # -------------------------------------------------------------------------

    DEFAULT_PRIORITY_THRESHOLDS = [
        (0.80, "Critical"),
        (0.60, "High"),
        (0.40, "Medium"),
        (0.20, "Low"),
    ]

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def __init__(
        self,
        config: Optional[Mapping[str, Any]] = None,
    ) -> None:

        self.config = dict(config or {})

        # ------------------------------------------------------------------
        # Decision criteria schema
        # ------------------------------------------------------------------

        configured_schema = self.config.get(
            "decision_criteria"
        )

        if configured_schema is None:

            self.decision_criteria = {
                criterion["id"]: dict(criterion)
                for criterion in DECISION_CRITERIA
            }

        else:

            self.decision_criteria = (
                self._validate_decision_schema(
                    configured_schema
                )
            )

        # ------------------------------------------------------------------
        # TPI weights
        # ------------------------------------------------------------------

        configured_weights = self.config.get(
            "tpi_weights"
        )

        if configured_weights is None:

            configured_weights = {
                name: constants.DEFAULT_TPI_WEIGHT
                for name in self.WEIGHT_NAMES
            }

        self.default_weights = self._validate_weights(
            configured_weights
        )

        # ------------------------------------------------------------------
        # Priority thresholds
        # ------------------------------------------------------------------

        self.priority_thresholds = (
            self._load_priority_thresholds(
                self.config.get(
                    "priority_thresholds"
                )
            )
        )

        # ------------------------------------------------------------------
        # Whether dimensions with zero gap should be included.
        # ------------------------------------------------------------------

        self.include_zero_gap = bool(
            self.config.get(
                "include_zero_gap",
                False,
            )
        )

    # =========================================================================
    # MAIN TPI CALCULATION
    # =========================================================================

    def calculate_tpi(
        self,
        gap_results: list[GapResult],
        decision_inputs: Mapping[str, Mapping[str, Any]],
        weights: Optional[Mapping[str, float]] = None,
    ) -> list[TPIResult]:
        """
        Calculate TPI for all applicable dimensions.

        Parameters
        ----------
        gap_results:
            Gap analysis results.

        decision_inputs:
            Dictionary indexed by dimension ID.

            Example:

                {
                    "D1": {
                        "business_impact": 70,
                        "strategic_importance": 80,
                        "expected_roi": 40,
                        "implementation_cost": 2500000,
                        "implementation_difficulty": 180,
                    }
                }

        weights:
            Optional TPI weights.

        Returns
        -------
        list[TPIResult]
            Sorted from highest TPI to lowest TPI.
        """

        if not isinstance(
            decision_inputs,
            Mapping,
        ):
            raise TypeError(
                "decision_inputs doit être un dictionnaire "
                "indexé par dimension."
            )

        active_weights = self._validate_weights(
            self.default_weights
            if weights is None
            else weights
        )

        results: list[TPIResult] = []

        # ------------------------------------------------------------------
        # Process every gap.
        # ------------------------------------------------------------------

        for gap_result in gap_results:

            # --------------------------------------------------------------
            # TPI is calculated only for dimensions.
            # --------------------------------------------------------------

            if str(
                gap_result.entity_type
            ).lower() != "dimension":
                continue

            # --------------------------------------------------------------
            # Validate gap.
            # --------------------------------------------------------------

            gap = float(
                gap_result.gap
            )

            if not math.isfinite(gap):
                raise ValueError(
                    f"Gap invalide pour "
                    f"{gap_result.entity_id}."
                )

            if gap < 0:
                raise ValueError(
                    f"Écart négatif invalide pour "
                    f"{gap_result.entity_id}."
                )

            if (
                gap == 0
                and not self.include_zero_gap
            ):
                continue

            # --------------------------------------------------------------
            # Retrieve user-entered decision criteria.
            # --------------------------------------------------------------

            dimension_id = gap_result.entity_id

            inputs = decision_inputs.get(
                dimension_id
            )

            if inputs is None:
                raise ValueError(
                    "Paramètres TPI manquants pour la dimension "
                    f"{dimension_id}."
                )

            values = self._validate_decision_inputs(
                inputs,
                dimension_id,
            )

            # --------------------------------------------------------------
            # Normalize maturity gap.
            #
            # ScoreResult normally uses SCORE_MAX = 5.
            # --------------------------------------------------------------

            gap_normalized = self._normalize(
                value=gap,
                minimum=0.0,
                maximum=float(
                    constants.SCORE_MAX
                ),
            )

            normalized: dict[str, float] = {
                "gap": gap_normalized,
            }

            # --------------------------------------------------------------
            # Normalize native decision parameters.
            # --------------------------------------------------------------

            for parameter_name in self.PARAMETER_NAMES:

                criterion = self.decision_criteria[
                    parameter_name
                ]

                raw_value = values[
                    parameter_name
                ]

                normalized_value = self._normalize(
                    value=raw_value,
                    minimum=float(
                        criterion["min_value"]
                    ),
                    maximum=float(
                        criterion["max_value"]
                    ),
                )

                direction = str(
                    criterion["direction"]
                ).lower()

                # ----------------------------------------------------------
                # Favorable:
                #
                # 100% impact is better than 20% impact.
                # ----------------------------------------------------------

                if direction == "favorable":

                    normalized[
                        parameter_name
                    ] = normalized_value

                # ----------------------------------------------------------
                # Inverted:
                #
                # 10 MAD cost is better than 1,000,000 MAD cost.
                #
                # Same logic for implementation difficulty.
                # ----------------------------------------------------------

                elif direction == "inverted":

                    normalized[
                        parameter_name
                    ] = 1.0 - normalized_value

                else:

                    raise ValueError(
                        f"Direction invalide pour "
                        f"{parameter_name}: "
                        f"{criterion['direction']}"
                    )

            # --------------------------------------------------------------
            # Weighted aggregation.
            #
            # Result is guaranteed to remain in [0, 1] if:
            # - normalized values are [0, 1]
            # - weights are non-negative
            # - weights sum to 1
            # --------------------------------------------------------------

            score = sum(
                active_weights[name]
                * normalized[name]
                for name in self.WEIGHT_NAMES
            )

            score = max(
                0.0,
                min(
                    1.0,
                    float(score),
                ),
            )

            score = round(
                score,
                3,
            )

            # --------------------------------------------------------------
            # Priority classification.
            #
            # IMPORTANT:
            #
            # We classify using the INTERNAL score.
            #
            # 0.64 = 64%
            #
            # NOT 64 as if it were a [0,1] score.
            # --------------------------------------------------------------

            priority_category = (
                self._get_priority_category(
                    score
                )
            )

            # --------------------------------------------------------------
            # Build result.
            # --------------------------------------------------------------

            result = TPIResult(
                dimension_id=dimension_id,

                dimension_name=gap_result.entity_name,

                tpi_score=score,

                priority_category=priority_category,

                gap=gap,

                # Keep ORIGINAL user values.
                business_impact=values[
                    "business_impact"
                ],

                strategic_importance=values[
                    "strategic_importance"
                ],

                expected_roi=values[
                    "expected_roi"
                ],

                implementation_cost=values[
                    "implementation_cost"
                ],

                implementation_difficulty=values[
                    "implementation_difficulty"
                ],

                details={
                    # ------------------------------------------------------
                    # Original values entered by the user.
                    # ------------------------------------------------------

                    "raw_parameters": {
                        name: values[name]
                        for name in self.PARAMETER_NAMES
                    },

                    # ------------------------------------------------------
                    # Internal normalized values.
                    # ------------------------------------------------------

                    "normalized_parameters": {
                        name: round(
                            normalized[name],
                            4,
                        )
                        for name in self.WEIGHT_NAMES
                    },

                    # ------------------------------------------------------
                    # Weights used.
                    # ------------------------------------------------------

                    "weights_used": (
                        active_weights.copy()
                    ),

                    # ------------------------------------------------------
                    # Original gap.
                    # ------------------------------------------------------

                    "gap_raw": gap,

                    # ------------------------------------------------------
                    # Normalized gap.
                    # ------------------------------------------------------

                    "gap_normalized": round(
                        gap_normalized,
                        4,
                    ),

                    # ------------------------------------------------------
                    # Display value.
                    # ------------------------------------------------------

                    "tpi_percent": round(
                        score * 100.0,
                        1,
                    ),
                },
            )

            results.append(
                result
            )

        # ------------------------------------------------------------------
        # Sort from highest TPI to lowest TPI.
        # ------------------------------------------------------------------

        return sorted(
            results,
            key=lambda result: (
                -result.tpi_score,
                result.dimension_id,
            ),
        )

    # =========================================================================
    # PRIORITY MATRIX
    # =========================================================================

    def calculate_priority_matrix(
        self,
        dimension_results: Mapping[
            str,
            ScoreResult | Mapping[str, Any],
        ],
        tpi_results: list[TPIResult],
    ) -> pd.DataFrame:
        """
        Build the priority matrix.

        TPI is kept internally as [0,1].
        """

        rows: list[dict[str, Any]] = []

        # Always use the TPI ranking.
        sorted_results = sorted(
            tpi_results,
            key=lambda result: (
                -result.tpi_score,
                result.dimension_id,
            ),
        )

        for rank, tpi in enumerate(
            sorted_results,
            start=1,
        ):

            result = dimension_results.get(
                tpi.dimension_id
            )

            # --------------------------------------------------------------
            # ScoreResult object.
            # --------------------------------------------------------------

            if isinstance(
                result,
                ScoreResult,
            ):

                current_score = result.score
                current_level = result.level

            # --------------------------------------------------------------
            # Dictionary.
            # --------------------------------------------------------------

            elif isinstance(
                result,
                Mapping,
            ):

                current_score = result.get(
                    "score"
                )

                current_level = result.get(
                    "level"
                )

            else:

                current_score = None
                current_level = None

            rows.append(
                {
                    "Rank": rank,

                    "Dimension": tpi.dimension_id,

                    "Nom": tpi.dimension_name,

                    "Score actuel": current_score,

                    "Niveau actuel": current_level,

                    "Écart": tpi.gap,

                    "TPI": tpi.tpi_score,

                    "TPI (%)": round(
                        tpi.tpi_score * 100.0,
                        1,
                    ),

                    "Priorité": (
                        tpi.priority_category
                    ),

                    "BI (%)": tpi.business_impact,

                    "SI (%)": (
                        tpi.strategic_importance
                    ),

                    "ROI (%)": tpi.expected_roi,

                    "Coût (MAD)": (
                        tpi.implementation_cost
                    ),

                    "Complexité (person-days)": (
                        tpi.implementation_difficulty
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    # =========================================================================
    # ROADMAP
    # =========================================================================

    def get_roadmap_phases(
        self,
        tpi_results: list[TPIResult],
        phase_mapping: Optional[
            Mapping[str, str]
        ] = None,
    ) -> dict[str, list[TPIResult]]:
        """
        Group TPI opportunities into roadmap phases.

        Priority determines the default roadmap phase.
        """

        default_mapping = {
            "Critical": "Phase 1 (< 6 mois)",
            "High": "Phase 1-2 (6-12 mois)",
            "Medium": "Phase 2 (12-24 mois)",
            "Low": "Phase 3-4 (> 24 mois)",
            "Very Low": "Non prioritaire",
        }

        # --------------------------------------------------------------
        # If the caller provides custom mapping, use it.
        # --------------------------------------------------------------

        mapping = (
            dict(phase_mapping)
            if phase_mapping is not None
            else default_mapping
        )

        phases: dict[
            str,
            list[TPIResult],
        ] = {}

        # --------------------------------------------------------------
        # Keep highest TPI first.
        # --------------------------------------------------------------

        sorted_results = sorted(
            tpi_results,
            key=lambda result: (
                -result.tpi_score,
                result.dimension_id,
            ),
        )

        for result in sorted_results:

            priority = self._normalize_priority_label(
                result.priority_category
            )

            phase = mapping.get(
                priority,
                "Phase 4 (> 24 mois)",
            )

            phases.setdefault(
                phase,
                [],
            ).append(
                result
            )

        return phases

    # =========================================================================
    # SUMMARY
    # =========================================================================

    @staticmethod
    def get_tpi_summary(
        tpi_results: list[TPIResult],
    ) -> dict[str, Any]:
        """
        Return summary statistics for TPI results.
        """

        if not tpi_results:

            return {
                "total_dimensions": 0,
                "average_tpi": 0.0,
                "average_tpi_percent": 0.0,
                "max_tpi": 0.0,
                "max_tpi_percent": 0.0,
                "min_tpi": 0.0,
                "min_tpi_percent": 0.0,
                "priority_distribution": {},
                "top_priority_dimensions": [],
            }

        scores = [
            float(result.tpi_score)
            for result in tpi_results
        ]

        average_tpi = (
            sum(scores)
            / len(scores)
        )

        max_tpi = max(
            scores
        )

        min_tpi = min(
            scores
        )

        distribution: dict[
            str,
            int,
        ] = {}

        for result in tpi_results:

            priority = (
                TPIEngine._normalize_priority_label(
                    result.priority_category
                )
            )

            distribution[
                priority
            ] = (
                distribution.get(
                    priority,
                    0,
                )
                + 1
            )

        sorted_results = sorted(
            tpi_results,
            key=lambda result: (
                -result.tpi_score,
                result.dimension_id,
            ),
        )

        return {
            "total_dimensions": len(
                tpi_results
            ),

            "average_tpi": round(
                average_tpi,
                3,
            ),

            "average_tpi_percent": round(
                average_tpi * 100.0,
                1,
            ),

            "max_tpi": round(
                max_tpi,
                3,
            ),

            "max_tpi_percent": round(
                max_tpi * 100.0,
                1,
            ),

            "min_tpi": round(
                min_tpi,
                3,
            ),

            "min_tpi_percent": round(
                min_tpi * 100.0,
                1,
            ),

            "priority_distribution": distribution,

            "top_priority_dimensions": [
                {
                    "dimension": result.dimension_id,
                    "name": result.dimension_name,
                    "tpi": result.tpi_score,
                    "tpi_percent": round(
                        result.tpi_score * 100.0,
                        1,
                    ),
                    "priority": (
                        result.priority_category
                    ),
                }
                for result in sorted_results[:3]
            ],
        }

    # =========================================================================
    # VALIDATE DECISION INPUTS
    # =========================================================================

    def _validate_decision_inputs(
        self,
        values: Mapping[str, Any],
        dimension_id: str,
    ) -> dict[str, float]:
        """
        Validate native user-entered decision values.
        """

        if not isinstance(
            values,
            Mapping,
        ):
            raise TypeError(
                f"Les paramètres TPI de "
                f"{dimension_id} doivent être "
                "un dictionnaire."
            )

        missing = (
            set(self.PARAMETER_NAMES)
            - set(values)
        )

        if missing:

            raise ValueError(
                f"Paramètres TPI manquants pour "
                f"{dimension_id} : "
                f"{sorted(missing)}"
            )

        validated: dict[
            str,
            float,
        ] = {}

        for name in self.PARAMETER_NAMES:

            criterion = self.decision_criteria[
                name
            ]

            value = values[
                name
            ]

            # --------------------------------------------------------------
            # Boolean is not a valid numeric input.
            # --------------------------------------------------------------

            if isinstance(
                value,
                bool,
            ):
                raise ValueError(
                    f"{dimension_id}/{name} "
                    "doit être numérique."
                )

            # --------------------------------------------------------------
            # Convert to float.
            # --------------------------------------------------------------

            try:

                numeric_value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    f"{dimension_id}/{name} "
                    "doit être numérique."
                ) from exc

            # --------------------------------------------------------------
            # Finite value.
            # --------------------------------------------------------------

            if not math.isfinite(
                numeric_value
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    "doit être une valeur finie."
                )

            # --------------------------------------------------------------
            # Minimum.
            # --------------------------------------------------------------

            minimum = criterion.get(
                "min_value"
            )

            if (
                minimum is not None
                and numeric_value < float(minimum)
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    f"doit être >= {minimum} "
                    f"{criterion['unit']}."
                )

            # --------------------------------------------------------------
            # Maximum.
            # --------------------------------------------------------------

            maximum = criterion.get(
                "max_value"
            )

            if (
                maximum is not None
                and numeric_value > float(maximum)
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    f"doit être <= {maximum} "
                    f"{criterion['unit']}."
                )

            validated[
                name
            ] = numeric_value

        return validated

    # =========================================================================
    # NORMALIZATION
    # =========================================================================

    @staticmethod
    def _normalize(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        """
        Normalize a value to [0,1].
        """

        if maximum <= minimum:

            raise ValueError(
                "La borne maximale doit être "
                "strictement supérieure à la borne minimale."
            )

        normalized = (
            value - minimum
        ) / (
            maximum - minimum
        )

        return max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )

    # =========================================================================
    # VALIDATE DECISION SCHEMA
    # =========================================================================

    def _validate_decision_schema(
        self,
        schema: Any,
    ) -> dict[str, dict[str, Any]]:
        """
        Validate a custom decision criteria schema.
        """

        # --------------------------------------------------------------
        # Accept list format.
        # --------------------------------------------------------------

        if isinstance(
            schema,
            list,
        ):

            try:

                schema = {
                    item["id"]: item
                    for item in schema
                }

            except (
                TypeError,
                KeyError,
            ) as exc:

                raise ValueError(
                    "Chaque critère TPI doit contenir un champ 'id'."
                ) from exc

        # --------------------------------------------------------------
        # Must now be a mapping.
        # --------------------------------------------------------------

        if not isinstance(
            schema,
            Mapping,
        ):

            raise TypeError(
                "decision_criteria doit être "
                "une liste ou un dictionnaire."
            )

        expected = set(
            self.PARAMETER_NAMES
        )

        received = set(
            schema.keys()
        )

        missing = (
            expected
            - received
        )

        extra = (
            received
            - expected
        )

        if missing or extra:

            raise ValueError(
                "Schéma des paramètres TPI invalide "
                f"(manquants={sorted(missing)}, "
                f"en trop={sorted(extra)})."
            )

        validated: dict[
            str,
            dict[str, Any],
        ] = {}

        for name in self.PARAMETER_NAMES:

            criterion = dict(
                schema[name]
            )

            minimum = criterion.get(
                "min_value"
            )

            maximum = criterion.get(
                "max_value"
            )

            direction = criterion.get(
                "direction"
            )

            if (
                minimum is None
                or maximum is None
            ):

                raise ValueError(
                    f"Bornes manquantes pour {name}."
                )

            if float(maximum) <= float(minimum):

                raise ValueError(
                    f"Bornes invalides pour {name}."
                )

            if direction not in {
                "favorable",
                "inverted",
            }:

                raise ValueError(
                    f"Direction invalide pour {name}: "
                    f"{direction!r}"
                )

            validated[
                name
            ] = criterion

        return validated

    # =========================================================================
    # WEIGHTS
    # =========================================================================

    def _validate_weights(
        self,
        values: Mapping[str, Any],
    ) -> dict[str, float]:
        """
        Validate TPI weights.

        All weights must:
        - be numeric
        - be >= 0
        - sum to 1
        """

        if not isinstance(
            values,
            Mapping,
        ):

            raise TypeError(
                "Les poids TPI doivent être "
                "un dictionnaire."
            )

        missing = (
            set(self.WEIGHT_NAMES)
            - set(values)
        )

        extra = (
            set(values)
            - set(self.WEIGHT_NAMES)
        )

        if missing or extra:

            raise ValueError(
                "Clés de poids invalides "
                f"(manquantes={sorted(missing)}, "
                f"en trop={sorted(extra)})."
            )

        weights: dict[
            str,
            float,
        ] = {}

        for name in self.WEIGHT_NAMES:

            try:

                value = float(
                    values[name]
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    f"Poids TPI invalide pour "
                    f"{name}: {values[name]!r}"
                ) from exc

            if (
                not math.isfinite(value)
                or value < 0
            ):

                raise ValueError(
                    f"Poids TPI invalide pour "
                    f"{name}: {value!r}"
                )

            weights[
                name
            ] = value

        total = sum(
            weights.values()
        )

        tolerance = float(
            getattr(
                constants,
                "WEIGHT_SUM_TOLERANCE",
                1e-6,
            )
        )

        if abs(
            total - 1.0
        ) > tolerance:

            raise ValueError(
                "La somme des poids TPI doit "
                "être égale à 1.0. "
                f"Somme actuelle: {total:.6f}"
            )

        return weights

    # =========================================================================
    # PRIORITY THRESHOLDS
    # =========================================================================

    def _load_priority_thresholds(
        self,
        custom: Any,
    ) -> list[tuple[float, str]]:
        """
        Load and normalize priority thresholds.

        Accepted formats:

            (0.80, "Critical")

        or:

            (0.80, 1.00, "Critical", "Phase 1")

        Thresholds expressed as percentages are also accepted:

            (80, 100, "Critical", "Phase 1")

        Internally everything becomes [0,1].
        """

        # ------------------------------------------------------------------
        # If nothing is configured, use the standard thresholds.
        # ------------------------------------------------------------------

        if custom is None:

            # Try project constants first.
            configured = getattr(
                constants,
                "TPI_PRIORITY_THRESHOLDS",
                None,
            )

            if configured is None:

                return list(
                    self.DEFAULT_PRIORITY_THRESHOLDS
                )

            custom = configured

        thresholds: list[
            tuple[float, str]
        ] = []

        # ------------------------------------------------------------------
        # Mapping format:
        #
        # {
        #     "Critical": 0.80,
        #     "High": 0.60,
        #     ...
        # }
        # ------------------------------------------------------------------

        if isinstance(
            custom,
            Mapping,
        ):

            for raw_label, raw_value in custom.items():

                label = (
                    self._normalize_priority_label(
                        raw_label
                    )
                )

                value = float(
                    raw_value
                )

                value = self._normalize_threshold_value(
                    value
                )

                thresholds.append(
                    (
                        value,
                        label,
                    )
                )

        # ------------------------------------------------------------------
        # List / tuple format.
        # ------------------------------------------------------------------

        else:

            if not isinstance(
                custom,
                (list, tuple),
            ):

                raise TypeError(
                    "priority_thresholds doit être "
                    "un dictionnaire, une liste ou un tuple."
                )

            for item in custom:

                if not isinstance(
                    item,
                    (list, tuple),
                ):

                    raise ValueError(
                        "Chaque seuil TPI doit être "
                        "une liste ou un tuple."
                    )

                # ----------------------------------------------------------
                # Format:
                #
                # (minimum, label)
                # ----------------------------------------------------------

                if len(item) == 2:

                    minimum, label = item

                # ----------------------------------------------------------
                # Format:
                #
                # (minimum, maximum, label, phase)
                # ----------------------------------------------------------

                elif len(item) == 4:

                    minimum, _maximum, label, _phase = item

                else:

                    raise ValueError(
                        "Format invalide dans "
                        "TPI_PRIORITY_THRESHOLDS : "
                        f"{item!r}. "
                        "Utilisez (minimum, label) "
                        "ou (minimum, maximum, label, phase)."
                    )

                minimum = self._normalize_threshold_value(
                    float(minimum)
                )

                label = (
                    self._normalize_priority_label(
                        label
                    )
                )

                thresholds.append(
                    (
                        minimum,
                        label,
                    )
                )

        # ------------------------------------------------------------------
        # If configuration is empty, use defaults.
        # ------------------------------------------------------------------

        if not thresholds:

            return list(
                self.DEFAULT_PRIORITY_THRESHOLDS
            )

        # ------------------------------------------------------------------
        # Sort descending.
        #
        # THIS IS CRITICAL.
        #
        # 0.80 must be tested before 0.60,
        # otherwise a score of 0.85 could be classified incorrectly.
        # ------------------------------------------------------------------

        thresholds.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        # ------------------------------------------------------------------
        # Validate threshold range.
        # ------------------------------------------------------------------

        for minimum, _label in thresholds:

            if not (
                0.0
                <= minimum
                <= 1.0
            ):

                raise ValueError(
                    "Les seuils TPI doivent être "
                    "compris entre 0 et 1 "
                    "après normalisation."
                )

        return thresholds

    # =========================================================================
    # THRESHOLD NORMALIZATION
    # =========================================================================

    @staticmethod
    def _normalize_threshold_value(
        value: float,
    ) -> float:
        """
        Convert threshold to internal [0,1].

        Examples:

            0.80 -> 0.80
            80   -> 0.80
        """

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):

            raise ValueError(
                f"Seuil TPI invalide: {value}"
            )

        # Percentage form.
        if value > 1.0:

            if value <= 100.0:

                value = value / 100.0

            else:

                raise ValueError(
                    f"Seuil TPI hors plage: {value}"
                )

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    # =========================================================================
    # PRIORITY CATEGORY
    # =========================================================================

    def _get_priority_category(
        self,
        score: float,
    ) -> str:
        """
        Classify a TPI score.

        Internal score:
            [0,1]

        Default classification:

            >= 0.80 -> Critical
            >= 0.60 -> High
            >= 0.40 -> Medium
            >= 0.20 -> Low
            <  0.20 -> Very Low

        Defensive support is included for accidental percentage input:

            64.0 -> 0.64
        """

        try:

            score = float(
                score
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                f"TPI score invalide: {score!r}"
            ) from exc

        if not math.isfinite(
            score
        ):

            raise ValueError(
                f"TPI score non fini: {score!r}"
            )

        # ------------------------------------------------------------------
        # Defensive conversion:
        #
        # If somebody accidentally sends 64.0 instead of 0.64,
        # convert it.
        # ------------------------------------------------------------------

        if score > 1.0:

            if score <= 100.0:

                score = score / 100.0

            else:

                raise ValueError(
                    f"TPI score hors plage [0,100]: {score}"
                )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        # ------------------------------------------------------------------
        # IMPORTANT:
        #
        # thresholds are sorted from HIGH to LOW.
        # ------------------------------------------------------------------

        for minimum, label in (
            self.priority_thresholds
        ):

            if score >= minimum:

                return label

        return "Very Low"

    # =========================================================================
    # PRIORITY LABEL NORMALIZATION
    # =========================================================================

    @staticmethod
    def _normalize_priority_label(
        priority: Any,
    ) -> str:
        """
        Normalize French/English priority labels.

        This prevents mismatches between:
            Critical / Critique
            High / Haute
            Medium / Moyenne
            Low / Faible
            Very Low / Très faible
        """

        if priority is None:
            return "Very Low"

        normalized = (
            str(priority)
            .strip()
            .lower()
        )

        mapping = {
            # --------------------------------------------------------------
            # Critical
            # --------------------------------------------------------------

            "critical": "Critical",
            "critique": "Critical",

            # --------------------------------------------------------------
            # High
            # --------------------------------------------------------------

            "high": "High",
            "haute": "High",

            # --------------------------------------------------------------
            # Medium
            # --------------------------------------------------------------

            "medium": "Medium",
            "moyenne": "Medium",
            "moyen": "Medium",

            # --------------------------------------------------------------
            # Low
            # --------------------------------------------------------------

            "low": "Low",
            "faible": "Low",

            # --------------------------------------------------------------
            # Very Low
            # --------------------------------------------------------------

            "very low": "Very Low",
            "très faible": "Very Low",
            "tres faible": "Very Low",
            "tres_faible": "Very Low",
        }

        return mapping.get(
            normalized,
            str(priority).strip(),
        )


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================
#
# Existing imports such as:
#
#     from engines.decision.tpi import TPICalculator
#
# will continue to work.
# =============================================================================


TPICalculator = TPIEngine