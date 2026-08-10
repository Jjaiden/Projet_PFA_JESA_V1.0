"""Moteur de calcul du Transformation Priority Index (TPI)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import pandas as pd

from config import constants
from engines.assessment.scoring import ScoreResult
from engines.decision.gap import GapResult


@dataclass
class TPIResult:
    """Résultat de priorisation d'une dimension."""

    dimension_id: str
    dimension_name: str
    tpi_score: float
    priority_category: str
    gap: float
    business_impact: int
    strategic_importance: int
    expected_roi: int
    implementation_cost: int
    implementation_difficulty: int
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "tpi_score": round(self.tpi_score, 3),
            "priority_category": self.priority_category,
            "gap": round(self.gap, 2),
            "business_impact": self.business_impact,
            "strategic_importance": self.strategic_importance,
            "expected_roi": self.expected_roi,
            "implementation_cost": self.implementation_cost,
            "implementation_difficulty": self.implementation_difficulty,
            "details": self.details,
        }


class TPIEngine:
    """Calcule le TPI à partir des écarts et des paramètres décisionnels 1 à 5."""

    PARAMETER_NAMES = (
        "business_impact",
        "strategic_importance",
        "expected_roi",
        "implementation_cost",
        "implementation_difficulty",
    )
    WEIGHT_NAMES = ("gap",) + PARAMETER_NAMES

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})
        self.default_weights = self._validate_weights(
            self.config.get(
                "tpi_weights",
                {name: constants.DEFAULT_TPI_WEIGHT for name in self.WEIGHT_NAMES},
            )
        )
        self.priority_thresholds = self._load_priority_thresholds(
            self.config.get("priority_thresholds")
        )
        self.include_zero_gap = bool(self.config.get("include_zero_gap", False))

    def calculate_tpi(
        self,
        gap_results: list[GapResult],
        decision_inputs: Mapping[str, Mapping[str, Any]],
        weights: Optional[Mapping[str, float]] = None,
    ) -> list[TPIResult]:
        """Calcule et trie les TPI des dimensions ayant un écart positif."""

        if not isinstance(decision_inputs, Mapping):
            raise TypeError("decision_inputs doit être un dictionnaire par dimension.")
        active_weights = self._validate_weights(
            self.default_weights if weights is None else weights
        )
        results: list[TPIResult] = []

        for gap_result in gap_results:
            if gap_result.entity_type != "dimension":
                continue
            if gap_result.gap < 0:
                raise ValueError(f"Écart négatif invalide pour {gap_result.entity_id}.")
            if gap_result.gap == 0 and not self.include_zero_gap:
                continue

            inputs = decision_inputs.get(gap_result.entity_id)
            if inputs is None:
                raise ValueError(
                    f"Paramètres TPI manquants pour la dimension {gap_result.entity_id}."
                )
            values = self._validate_decision_inputs(inputs, gap_result.entity_id)

            gap_normalized = min(float(gap_result.gap) / constants.SCORE_MAX, 1.0)
            normalized = {
                "gap": gap_normalized,
                "business_impact": self._normalize_scale(values["business_impact"]),
                "strategic_importance": self._normalize_scale(values["strategic_importance"]),
                "expected_roi": self._normalize_scale(values["expected_roi"]),
                "implementation_cost": 1 - self._normalize_scale(values["implementation_cost"]),
                "implementation_difficulty": 1
                - self._normalize_scale(values["implementation_difficulty"]),
            }
            score = round(
                sum(active_weights[name] * normalized[name] for name in self.WEIGHT_NAMES),
                3,
            )

            results.append(
                TPIResult(
                    dimension_id=gap_result.entity_id,
                    dimension_name=gap_result.entity_name,
                    tpi_score=score,
                    priority_category=self._get_priority_category(score),
                    gap=float(gap_result.gap),
                    business_impact=values["business_impact"],
                    strategic_importance=values["strategic_importance"],
                    expected_roi=values["expected_roi"],
                    implementation_cost=values["implementation_cost"],
                    implementation_difficulty=values["implementation_difficulty"],
                    details={
                        "normalized_parameters": {
                            name: round(value, 3) for name, value in normalized.items()
                        },
                        "weights_used": active_weights.copy(),
                        "gap_raw": gap_result.gap,
                    },
                )
            )

        return sorted(results, key=lambda result: result.tpi_score, reverse=True)

    def calculate_priority_matrix(
        self,
        dimension_results: Mapping[str, ScoreResult | Mapping[str, Any]],
        tpi_results: list[TPIResult],
    ) -> pd.DataFrame:
        """Construit une matrice prête pour le frontend ou un export Excel."""

        rows: list[dict[str, Any]] = []
        for tpi in tpi_results:
            result = dimension_results.get(tpi.dimension_id)
            if isinstance(result, ScoreResult):
                current_score, current_level = result.score, result.level
            elif isinstance(result, Mapping):
                current_score = result.get("score")
                current_level = result.get("level")
            else:
                current_score, current_level = None, None
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

    def get_roadmap_phases(
        self,
        tpi_results: list[TPIResult],
        phase_mapping: Optional[Mapping[str, str]] = None,
    ) -> dict[str, list[TPIResult]]:
        """Répartit les résultats dans les phases de roadmap."""

        mapping = dict(
            phase_mapping
            or {
                "Critique": "Phase 1 (< 6 mois)",
                "Haute": "Phase 2 (6-12 mois)",
                "Moyenne": "Phase 3 (12-24 mois)",
                "Faible": "Phase 4 (> 24 mois)",
                "Très faible": "Phase 4 (> 24 mois)",
            }
        )
        phases: dict[str, list[TPIResult]] = {}
        for result in tpi_results:
            phase = mapping.get(result.priority_category, "Phase 4 (> 24 mois)")
            phases.setdefault(phase, []).append(result)
        return phases

    @staticmethod
    def get_tpi_summary(tpi_results: list[TPIResult]) -> dict[str, Any]:
        if not tpi_results:
            return {"total_dimensions": 0, "priority_distribution": {}, "top_priority_dimensions": []}
        scores = [result.tpi_score for result in tpi_results]
        distribution: dict[str, int] = {}
        for result in tpi_results:
            distribution[result.priority_category] = (
                distribution.get(result.priority_category, 0) + 1
            )
        return {
            "total_dimensions": len(tpi_results),
            "average_tpi": round(sum(scores) / len(scores), 3),
            "max_tpi": round(max(scores), 3),
            "min_tpi": round(min(scores), 3),
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

    def _validate_decision_inputs(
        self, values: Mapping[str, Any], dimension_id: str
    ) -> dict[str, int]:
        if not isinstance(values, Mapping):
            raise TypeError(f"Les paramètres TPI de {dimension_id} doivent être un dictionnaire.")
        missing = set(self.PARAMETER_NAMES) - set(values)
        if missing:
            raise ValueError(f"Paramètres TPI manquants pour {dimension_id} : {sorted(missing)}")
        normalized: dict[str, int] = {}
        for name in self.PARAMETER_NAMES:
            value = values[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{dimension_id}/{name} doit être un entier entre 1 et 5.")
            if isinstance(value, float) and not value.is_integer():
                raise ValueError(f"{dimension_id}/{name} doit être un entier entre 1 et 5.")
            value = int(value)
            if not 1 <= value <= 5:
                raise ValueError(f"{dimension_id}/{name} doit être compris entre 1 et 5.")
            normalized[name] = value
        return normalized

    def _validate_weights(self, values: Mapping[str, Any]) -> dict[str, float]:
        if not isinstance(values, Mapping):
            raise TypeError("Les poids TPI doivent être un dictionnaire.")
        missing = set(self.WEIGHT_NAMES) - set(values)
        extra = set(values) - set(self.WEIGHT_NAMES)
        if missing or extra:
            raise ValueError(f"Clés de poids invalides (manquantes={sorted(missing)}, en trop={sorted(extra)}).")
        weights: dict[str, float] = {}
        for name in self.WEIGHT_NAMES:
            try:
                value = float(values[name])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Poids TPI invalide pour {name}: {values[name]!r}") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Poids TPI invalide pour {name}: {value!r}")
            weights[name] = value
        if abs(sum(weights.values()) - 1.0) > constants.WEIGHT_SUM_TOLERANCE:
            raise ValueError("La somme des poids TPI doit être égale à 1.0.")
        return weights

    def _load_priority_thresholds(self, custom: Any) -> list[tuple[float, str]]:
        if custom is None:
            return [(minimum, label) for minimum, _, label, _ in constants.TPI_PRIORITY_THRESHOLDS]
        if not isinstance(custom, Mapping):
            raise TypeError("priority_thresholds doit être un dictionnaire.")
        labels = {
            "critique": "Critique", "haute": "Haute", "moyenne": "Moyenne",
            "faible": "Faible", "tres_faible": "Très faible", "très faible": "Très faible",
        }
        thresholds = []
        for raw_label, raw_value in custom.items():
            label = labels.get(str(raw_label).lower())
            if label is None:
                raise ValueError(f"Catégorie TPI inconnue : {raw_label!r}")
            value = float(raw_value)
            if not 0 <= value <= 1:
                raise ValueError("Les seuils TPI doivent être compris entre 0 et 1.")
            thresholds.append((value, label))
        return sorted(thresholds, reverse=True)

    def _get_priority_category(self, score: float) -> str:
        for threshold, label in self.priority_thresholds:
            if score >= threshold:
                return label
        return "Très faible"

    @staticmethod
    def _normalize_scale(value: int) -> float:
        return (value - 1) / 4


TPICalculator = TPIEngine
