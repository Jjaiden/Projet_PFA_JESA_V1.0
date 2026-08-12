"""
Moteur de calcul du Transformation Priority Index (TPI).

The TPI engine accepts native decision values with potentially different
units/ranges and normalizes them to [0, 1] before aggregation.

Decision parameters
-------------------
- Gap
- Business Impact
- Strategic Importance
- Expected ROI
- Implementation Cost
- Implementation Difficulty
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import pandas as pd

from config import constants
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult


# ==============================================================================
# DECISION CRITERIA SCHEMA
# ==============================================================================

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
            "Estimated operational/business impact of the transformation "
            "opportunity, expressed as a percentage."
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
            "digital transformation strategy, expressed as a percentage."
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
            "Estimated investment required to implement the transformation."
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
            "Estimated implementation effort in person-days, used as a "
            "measurable proxy for implementation difficulty."
        ),
    },
]


DECISION_CRITERIA_BY_ID = {
    criterion["id"]: criterion
    for criterion in DECISION_CRITERIA
}


# ==============================================================================
# TPI RESULT
# ==============================================================================


@dataclass
class TPIResult:
    """Résultat de priorisation d'une dimension."""

    dimension_id: str
    dimension_name: str

    tpi_score: float
    priority_category: str
    gap: float

    business_impact: float
    strategic_importance: float
    expected_roi: float
    implementation_cost: float
    implementation_difficulty: float

    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:

        return {
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,

            "tpi_score": round(
                float(self.tpi_score),
                3,
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
            "implementation_difficulty": self.implementation_difficulty,

            "details": self.details,
        }


# ==============================================================================
# TPI ENGINE
# ==============================================================================


class TPIEngine:
    """
    Calcule le Transformation Priority Index.

    Important
    ---------
    The engine receives native values from the frontend.

    Example:
        Business Impact       = 70 %
        Strategic Importance  = 85 %
        Expected ROI          = 30 %
        Implementation Cost  = 2_500_000 MAD
        Implementation Effort = 180 person-days

    These values are NOT required to share the same scale.

    Each parameter is normalized independently to [0, 1].
    """

    PARAMETER_NAMES = (
        "business_impact",
        "strategic_importance",
        "expected_roi",
        "implementation_cost",
        "implementation_difficulty",
    )

    WEIGHT_NAMES = (
        "gap",
        *PARAMETER_NAMES,
    )

    def __init__(
        self,
        config: Optional[Mapping[str, Any]] = None,
    ):

        self.config = dict(config or {})

        # ------------------------------------------------------------------
        # Decision schema
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

            self.decision_criteria = self._validate_decision_schema(
                configured_schema
            )

        # ------------------------------------------------------------------
        # TPI weights
        # ------------------------------------------------------------------

        self.default_weights = self._validate_weights(
            self.config.get(
                "tpi_weights",
                {
                    name: constants.DEFAULT_TPI_WEIGHT
                    for name in self.WEIGHT_NAMES
                },
            )
        )

        # ------------------------------------------------------------------
        # Priority thresholds
        # ------------------------------------------------------------------

        self.priority_thresholds = self._load_priority_thresholds(
            self.config.get(
                "priority_thresholds"
            )
        )

        self.include_zero_gap = bool(
            self.config.get(
                "include_zero_gap",
                False,
            )
        )

    # ==========================================================================
    # MAIN CALCULATION
    # ==========================================================================

    def calculate_tpi(
        self,
        gap_results: list[GapResult],
        decision_inputs: Mapping[str, Mapping[str, Any]],
        weights: Optional[Mapping[str, float]] = None,
    ) -> list[TPIResult]:

        if not isinstance(
            decision_inputs,
            Mapping,
        ):
            raise TypeError(
                "decision_inputs doit être un dictionnaire par dimension."
            )

        active_weights = self._validate_weights(
            self.default_weights
            if weights is None
            else weights
        )

        results: list[TPIResult] = []

        for gap_result in gap_results:

            # --------------------------------------------------------------
            # Only dimensions are prioritized
            # --------------------------------------------------------------

            if gap_result.entity_type != "dimension":
                continue

            # --------------------------------------------------------------
            # Gap validation
            # --------------------------------------------------------------

            if gap_result.gap < 0:

                raise ValueError(
                    f"Écart négatif invalide pour "
                    f"{gap_result.entity_id}."
                )

            if (
                gap_result.gap == 0
                and not self.include_zero_gap
            ):
                continue

            # --------------------------------------------------------------
            # Retrieve site-specific decision inputs
            # --------------------------------------------------------------

            inputs = decision_inputs.get(
                gap_result.entity_id
            )

            if inputs is None:

                raise ValueError(
                    "Paramètres TPI manquants pour la dimension "
                    f"{gap_result.entity_id}."
                )

            values = self._validate_decision_inputs(
                inputs,
                gap_result.entity_id,
            )

            # --------------------------------------------------------------
            # GAP normalization
            # --------------------------------------------------------------

            gap_normalized = self._normalize(
                value=float(gap_result.gap),
                minimum=0.0,
                maximum=float(constants.SCORE_MAX),
            )

            # --------------------------------------------------------------
            # Native parameter normalization
            # --------------------------------------------------------------

            normalized: dict[str, float] = {
                "gap": gap_normalized,
            }

            for parameter_name in self.PARAMETER_NAMES:

                criterion = self.decision_criteria[
                    parameter_name
                ]

                raw_value = values[
                    parameter_name
                ]

                normalized_value = self._normalize(
                    value=raw_value,
                    minimum=criterion["min_value"],
                    maximum=criterion["max_value"],
                )

                # ----------------------------------------------------------
                # Favorable parameters:
                # higher = better
                # ----------------------------------------------------------

                if criterion["direction"] == "favorable":

                    normalized[
                        parameter_name
                    ] = normalized_value

                # ----------------------------------------------------------
                # Inverted parameters:
                # higher = worse
                # ----------------------------------------------------------

                elif criterion["direction"] == "inverted":

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
            # TPI weighted aggregation
            # --------------------------------------------------------------

            score = round(
                sum(
                    active_weights[name]
                    * normalized[name]
                    for name in self.WEIGHT_NAMES
                ),
                3,
            )

            # --------------------------------------------------------------
            # Result
            # --------------------------------------------------------------

            results.append(
                TPIResult(
                    dimension_id=gap_result.entity_id,
                    dimension_name=gap_result.entity_name,

                    tpi_score=score,

                    priority_category=self._get_priority_category(
                        score
                    ),

                    gap=float(
                        gap_result.gap
                    ),

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
                        "raw_parameters": {
                            name: values[name]
                            for name in self.PARAMETER_NAMES
                        },

                        "normalized_parameters": {
                            name: round(
                                normalized[name],
                                4,
                            )
                            for name in self.WEIGHT_NAMES
                        },

                        "weights_used": active_weights.copy(),

                        "gap_raw": float(
                            gap_result.gap
                        ),
                    },
                )
            )

        # ----------------------------------------------------------------------
        # Highest priority first
        # ----------------------------------------------------------------------

        return sorted(
            results,
            key=lambda result: result.tpi_score,
            reverse=True,
        )

    # ==========================================================================
    # PRIORITY MATRIX
    # ==========================================================================

    def calculate_priority_matrix(
        self,
        dimension_results: Mapping[
            str,
            ScoreResult | Mapping[str, Any],
        ],
        tpi_results: list[TPIResult],
    ) -> pd.DataFrame:

        rows: list[dict[str, Any]] = []

        for tpi in tpi_results:

            result = dimension_results.get(
                tpi.dimension_id
            )

            if isinstance(
                result,
                ScoreResult,
            ):

                current_score = result.score
                current_level = result.level

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
                    "Dimension": tpi.dimension_id,
                    "Nom": tpi.dimension_name,

                    "Score actuel": current_score,
                    "Niveau actuel": current_level,

                    "Écart": tpi.gap,
                    "TPI": tpi.tpi_score,
                    "Priorité": tpi.priority_category,

                    "BI": tpi.business_impact,
                    "SI": tpi.strategic_importance,
                    "ROI": tpi.expected_roi,
                    "Coût": tpi.implementation_cost,
                    "Complexité": tpi.implementation_difficulty,
                }
            )

        return pd.DataFrame(rows)

    # ==========================================================================
    # ROADMAP
    # ==========================================================================

    def get_roadmap_phases(
        self,
        tpi_results: list[TPIResult],
        phase_mapping: Optional[
            Mapping[str, str]
        ] = None,
    ) -> dict[str, list[TPIResult]]:

        mapping = {
             "Critique": "Phase 1 (< 6 mois)",
             "Haute": "Phase 1-2 (6-12 mois)",
             "Moyenne": "Phase 2 (12-24 mois)",
             "Faible": "Phase 3-4 (> 24 mois)",
             "Très faible": "Non prioritaire",
         }
        phases: dict[
            str,
            list[TPIResult],
        ] = {}

        for result in tpi_results:

            phase = mapping.get(
                result.priority_category,
                "Phase 4 (> 24 mois)",
            )

            phases.setdefault(
                phase,
                [],
            ).append(result)

        return phases

    # ==========================================================================
    # SUMMARY
    # ==========================================================================

    @staticmethod
    def get_tpi_summary(
        tpi_results: list[TPIResult],
    ) -> dict[str, Any]:

        if not tpi_results:

            return {
                "total_dimensions": 0,
                "priority_distribution": {},
                "top_priority_dimensions": [],
            }

        scores = [
            result.tpi_score
            for result in tpi_results
        ]

        distribution: dict[
            str,
            int,
        ] = {}

        for result in tpi_results:

            distribution[
                result.priority_category
            ] = (
                distribution.get(
                    result.priority_category,
                    0,
                )
                + 1
            )

        return {
            "total_dimensions": len(
                tpi_results
            ),

            "average_tpi": round(
                sum(scores)
                / len(scores),
                3,
            ),

            "max_tpi": round(
                max(scores),
                3,
            ),

            "min_tpi": round(
                min(scores),
                3,
            ),

            "priority_distribution": distribution,

            "top_priority_dimensions": [
                {
                    "dimension": result.dimension_id,
                    "name": result.dimension_name,
                    "tpi": result.tpi_score,
                    "priority": result.priority_category,
                }
                for result in tpi_results[:3]
            ],
        }
    # ==========================================================================
    # VALIDATE DECISION INPUTS
    # ==========================================================================

    def _validate_decision_inputs(
        self,
        values: Mapping[str, Any],
        dimension_id: str,
    ) -> dict[str, float]:

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

            value = values[name]

            if isinstance(
                value,
                bool,
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    "doit être numérique."
                )

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

            if not math.isfinite(
                numeric_value
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    "doit être une valeur finie."
                )

            minimum = criterion.get(
                "min_value"
            )

            maximum = criterion.get(
                "max_value"
            )

            if (
                minimum is not None
                and numeric_value < minimum
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    f"doit être >= {minimum} "
                    f"{criterion['unit']}."
                )

            if (
                maximum is not None
                and numeric_value > maximum
            ):

                raise ValueError(
                    f"{dimension_id}/{name} "
                    f"doit être <= {maximum} "
                    f"{criterion['unit']}."
                )

            validated[name] = numeric_value

        return validated

    # ==========================================================================
    # NORMALIZATION
    # ==========================================================================

    @staticmethod
    def _normalize(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

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

    # ==========================================================================
    # VALIDATE SCHEMA
    # ==========================================================================

    def _validate_decision_schema(
        self,
        schema: Any,
    ) -> dict[str, dict[str, Any]]:

        if isinstance(
            schema,
            list,
        ):

            schema = {
                item["id"]: item
                for item in schema
            }

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

        missing = expected - received
        extra = received - expected

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

            if maximum <= minimum:

                raise ValueError(
                    f"Bornes invalides pour {name}."
                )

            if direction not in {
                "favorable",
                "inverted",
            }:

                raise ValueError(
                    f"Direction invalide pour {name}."
                )

            validated[name] = criterion

        return validated

    # ==========================================================================
    # WEIGHTS
    # ==========================================================================

    def _validate_weights(
        self,
        values: Mapping[str, Any],
    ) -> dict[str, float]:

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

            weights[name] = value

        if abs(
            sum(weights.values())
            - 1.0
        ) > constants.WEIGHT_SUM_TOLERANCE:

            raise ValueError(
                "La somme des poids TPI doit "
                "être égale à 1.0."
            )

        return weights

    # ==========================================================================
    # PRIORITY THRESHOLDS
    # ==========================================================================

    def _load_priority_thresholds(
        self,
        custom: Any,
    ) -> list[
        tuple[float, str]
    ]:

        if custom is None:

          thresholds = []

          for item in constants.TPI_PRIORITY_THRESHOLDS:

              # Format complet :
              # (minimum, maximum, label, phase)
            if len(item) == 4:

               minimum, maximum, label, phase = item

               thresholds.append(
                  (
                    float(minimum),
                    str(label),
                  )
             )

             # Format simplifié :
             # (minimum, label)
            elif len(item) == 2:

                 minimum, label = item

                 thresholds.append(
                 (
                    float(minimum),
                    str(label),
                 )
             )

            else:

                 raise ValueError(
                  "Format invalide dans "
                  "TPI_PRIORITY_THRESHOLDS : "
                  f"{item!r}. "
                  "Chaque seuil doit contenir "
                  "soit 2 valeurs "
                  "(minimum, label), "
                  "soit 4 valeurs "
                  "(minimum, maximum, label, phase)."
             )

       # Highest threshold first
        return sorted(
          thresholds,
          key=lambda item: item[0],
          reverse=True,
         )

        if not isinstance(
            custom,
            Mapping,
        ):

            raise TypeError(
                "priority_thresholds doit être "
                "un dictionnaire."
            )

        labels = {
            "critique": "Critique",
            "haute": "Haute",
            "moyenne": "Moyenne",
            "faible": "Faible",
            "tres_faible": "Très faible",
            "très faible": "Très faible",
        }

        thresholds = []

        for raw_label, raw_value in custom.items():

            label = labels.get(
                str(raw_label).lower()
            )

            if label is None:

                raise ValueError(
                    f"Catégorie TPI inconnue : "
                    f"{raw_label!r}"
                )

            value = float(
                raw_value
            )

            if not 0 <= value <= 1:

                raise ValueError(
                    "Les seuils TPI doivent être "
                    "compris entre 0 et 1."
                )

            thresholds.append(
                (
                    value,
                    label,
                )
            )

        return sorted(
            thresholds,
            reverse=True,
        )

    # ==========================================================================
    # PRIORITY CATEGORY
    # ==========================================================================

def _get_priority_category(
    self,
    score: float,
) -> str:

    for minimum, label in self.priority_thresholds:

        if score >= minimum:
            return label

    return "Très faible"
# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

TPICalculator = TPIEngine