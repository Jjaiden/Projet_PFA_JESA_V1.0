"""
scoring.py — Moteur de calcul des scores du JDMAF.

Responsabilité :
    - calcul du score d'un indicateur
    - calcul des sous-dimensions
    - calcul des dimensions
    - calcul des piliers
    - calcul du DMI

Ce module ne contient aucune logique frontend.

Hiérarchie :
    Indicateur
        ↓
    Sous-dimension
        ↓
    Dimension
        ↓
    Pilier
        ↓
    DMI

Règles :
    R1 : score indicateur entier dans [0, 5]
    R2 : niveau choisi par l'évaluateur selon la grille de scoring
    R3 : preuve recommandée, contrôlée dans validator.py

Agrégation :
    SD        = moyenne plafonnée des indicateurs
    Dimension = moyenne pondérée des SD
    Pilier    = moyenne pondérée des dimensions
    DMI       = moyenne pondérée des piliers × 20
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from config import constants, settings


logger = settings.get_logger(__name__)


# ============================================================================
# RESULTAT DE CALCUL
# ============================================================================


@dataclass
class ScoreResult:
    """
    Résultat d'un calcul de score pour une entité de la hiérarchie.
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
        Convertit le résultat en dictionnaire exploitable par les autres
        modules du backend ou par le frontend.
        """

        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "score": round(self.score, settings.SCORE_DECIMAL_PRECISION),
            "level": self.level,
            "level_name": self.level_name,
            "parent_id": self.parent_id,
            "children_scores": self.children_scores,
            "applicability": self.applicability,
            "gap_to_target": self.gap_to_target,
            "details": self.details,
        }


# ============================================================================
# MOTEUR DE SCORING
# ============================================================================


class ScoringEngine:
    """
    Moteur de scoring du JDMAF.

    Il réalise uniquement les calculs mathématiques.
    L'orchestration globale est assurée par aggregation.py.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config:
                Configuration optionnelle contenant éventuellement :

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
    # CHARGEMENT DES POIDS
    # ------------------------------------------------------------------------

    def _load_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Charge les pondérations éventuellement fournies dans la configuration.

        Les poids du référentiel Excel sont normalement récupérés par
        aggregation.py via ReferenceLoader.
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
    # OUTILS INTERNES
    # ------------------------------------------------------------------------

    def _get_level_name(self, level: int) -> str:
        """Retourne le nom du niveau de maturité."""

        return self.maturity_levels.get(
            level,
            f"Niveau {level}",
        )

    def get_maturity_level_description(self, level: int) -> str:
        """
        Retourne la description du niveau de maturité.

        Les descriptions correspondent à l'échelle définie dans le référentiel.
        """

        descriptions = {
            0: (
                "Aucune initiative digitale identifiée. "
                "Les processus sont entièrement manuels ou analogiques."
            ),
            1: (
                "Des outils numériques sont déployés ponctuellement "
                "pour remplacer certaines tâches manuelles. "
                "Les solutions restent locales et peu standardisées."
            ),
            2: (
                "Les systèmes industriels et informatiques (OT/IT) "
                "sont interconnectés et échangent des données de manière fiable."
            ),
            3: (
                "Les données sont centralisées, historisées et accessibles "
                "en temps réel. Des indicateurs soutiennent le pilotage."
            ),
            4: (
                "Les données sont exploitées pour analyser les performances, "
                "identifier les causes des écarts et améliorer les opérations."
            ),
            5: (
                "Les systèmes assistent ou automatisent la prise de décision "
                "grâce à des analyses avancées et à l'intelligence artificielle."
            ),
        }

        return descriptions.get(
            level,
            "Niveau non défini",
        )

    def _validate_score(self, score: Any) -> None:
        """
        Vérifie qu'un score indicateur est un entier entre 0 et 5.

        Les booléens sont explicitement refusés car Python considère
        bool comme un sous-type de int.
        """

        if isinstance(score, bool):
            raise ValueError(
                "Le score ne peut pas être un booléen."
            )

        if not isinstance(score, int):
            raise ValueError(
                f"Le score doit être un entier. Valeur reçue : {score!r}"
            )

        if score not in constants.VALID_INDICATOR_SCORES:
            raise ValueError(
                f"Le score doit être compris entre "
                f"{constants.SCORE_MIN} et {constants.SCORE_MAX}. "
                f"Valeur reçue : {score}"
            )

    def _normalize_weights(
        self,
        component_ids: List[str],
        weights: Optional[Dict[str, float]],
        default_weight: float,
    ) -> List[float]:
        """
        Retourne une liste de poids normalisés.

        Les éléments exclus (ex. Non applicable) ne sont pas inclus dans
        component_ids. Les poids sont donc automatiquement renormalisés.

        Exemple :
            poids initiaux = [0.5, 0.5]
            deuxième élément N/A
            poids restants = [1.0]
        """

        if not component_ids:
            return []

        # Aucun poids fourni -> poids égaux
        if not weights:
            raw_weights = [default_weight] * len(component_ids)
        else:
            raw_weights = []

            for component_id in component_ids:
                value = weights.get(component_id, default_weight)

                if value is None:
                    value = default_weight

                try:
                    value = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Poids invalide pour {component_id}: {value!r}"
                    ) from exc

                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        f"Le poids de {component_id} doit être un nombre fini positif ou nul."
                    )

                raw_weights.append(value)

        total_weight = sum(raw_weights)

        if total_weight <= 0:
            raise ValueError(
                "La somme des poids applicables doit être strictement positive."
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
        Construit un résultat standard pour une entité entièrement
        non applicable.
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
    # INDICATEUR
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
        Calcule le score d'un indicateur.

        R1 :
            score entier dans [0,5]

        Args:
            indicator_id:
                ID de l'indicateur, ex. I-D1-01.

            selected_score:
                Note attribuée par l'évaluateur.

            scoring_grid:
                Informations de la grille de scoring correspondant
                au niveau sélectionné.

            indicator_name:
                Nom de l'indicateur.

            parent_id:
                Sous-dimension parente.

            applicability:
                Applicable / Non applicable.
        """

        if applicability == constants.APPLICABILITY_NOT_APPLICABLE:
            return self._build_non_applicable_result(
                entity_id=indicator_id,
                entity_name=indicator_name or indicator_id,
                entity_type="indicator",
                parent_id=parent_id,
                details={
                    "reason": "Indicateur marqué Non applicable"
                },
            )

        if applicability != constants.APPLICABILITY_APPLICABLE:
            raise ValueError(
                f"Applicability invalide pour {indicator_id}: "
                f"{applicability!r}"
            )

        self._validate_score(selected_score)

        grid = scoring_grid or {}

        level_name = self._get_level_name(selected_score)

        return ScoreResult(
            entity_id=indicator_id,
            entity_name=indicator_name or grid.get(
                "Indicator_Name",
                indicator_id,
            ),
            entity_type="indicator",
            score=float(selected_score),
            level=selected_score,
            level_name=level_name,
            parent_id=parent_id,
            applicability=constants.APPLICABILITY_APPLICABLE,
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
    # SOUS-DIMENSION
    # ------------------------------------------------------------------------

    def calculate_subdimension_score(
        self,
        subdimension_id: str,
        indicator_scores: List[ScoreResult],
        subdimension_name: Optional[str] = None,
    ) -> ScoreResult:
        """
        Calcule le score d'une sous-dimension.

        Règle :
            Score_SD =
                min(
                    moyenne(indicateurs applicables),
                    minimum(indicateurs applicables) + 1
                )

        Cette règle empêche une faiblesse critique d'être masquée
        par une moyenne élevée.
        """

        if not indicator_scores:
            return self._build_non_applicable_result(
                entity_id=subdimension_id,
                entity_name=subdimension_name or subdimension_id,
                entity_type="subdimension",
                details={
                    "error": "Aucun indicateur disponible"
                },
            )

        applicable_scores = [
            result
            for result in indicator_scores
            if result.applicability
            != constants.APPLICABILITY_NOT_APPLICABLE
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=subdimension_id,
                entity_name=subdimension_name or subdimension_id,
                entity_type="subdimension",
                details={
                    "reason": "Tous les indicateurs sont Non applicable",
                    "total_count": len(indicator_scores),
                },
            )

        scores = [
            result.score
            for result in applicable_scores
        ]

        mean_score = sum(scores) / len(scores)
        minimum_score = min(scores)

        # Règle de moyenne plafonnée
        cap = minimum_score + 1.0

        final_score = min(
            mean_score,
            cap,
        )

        final_score = round(
            final_score,
            settings.SCORE_DECIMAL_PRECISION,
        )

        level = int(math.floor(final_score))

        level = min(
            max(level, constants.SCORE_MIN),
            constants.SCORE_MAX,
        )

        # Détermination du parent à partir de constants.py
        parent_id = constants.SUBDIMENSIONS.get(
            subdimension_id,
            (None, None),
        )[0]

        return ScoreResult(
            entity_id=subdimension_id,
            entity_name=subdimension_name or subdimension_id,
            entity_type="subdimension",
            score=final_score,
            level=level,
            level_name=self._get_level_name(level),
            parent_id=parent_id,
            children_scores={
                result.entity_id: result.score
                for result in indicator_scores
            },
            applicability=constants.APPLICABILITY_APPLICABLE,
            details={
                "indicator_scores": scores,
                "mean_score": round(
                    mean_score,
                    settings.SCORE_DECIMAL_PRECISION,
                ),
                "minimum_score": minimum_score,
                "cap": cap,
                "applicable_count": len(applicable_scores),
                "total_count": len(indicator_scores),
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
        Calcule le score d'une dimension par moyenne pondérée
        des sous-dimensions applicables.
        """

        if not subdimension_scores:
            return self._build_non_applicable_result(
                entity_id=dimension_id,
                entity_name=dimension_name or dimension_id,
                entity_type="dimension",
                parent_id=constants.DIMENSIONS.get(
                    dimension_id,
                    (None, None),
                )[0],
                details={
                    "error": "Aucune sous-dimension disponible"
                },
            )

        applicable_scores = [
            result
            for result in subdimension_scores
            if result.applicability
            != constants.APPLICABILITY_NOT_APPLICABLE
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=dimension_id,
                entity_name=dimension_name or dimension_id,
                entity_type="dimension",
                parent_id=constants.DIMENSIONS.get(
                    dimension_id,
                    (None, None),
                )[0],
                details={
                    "reason": "Toutes les sous-dimensions sont Non applicable"
                },
            )

        component_ids = [
            result.entity_id
            for result in applicable_scores
        ]

        normalized_weights = self._normalize_weights(
            component_ids=component_ids,
            weights=weights,
            default_weight=constants.DEFAULT_WEIGHT_SUBDIMENSION_PER_DIMENSION,
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

        level = int(math.floor(final_score))

        level = min(
            max(level, constants.SCORE_MIN),
            constants.SCORE_MAX,
        )

        parent_id = constants.DIMENSIONS.get(
            dimension_id,
            (None, None),
        )[0]

        return ScoreResult(
            entity_id=dimension_id,
            entity_name=dimension_name or dimension_id,
            entity_type="dimension",
            score=final_score,
            level=level,
            level_name=self._get_level_name(level),
            parent_id=parent_id,
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=constants.APPLICABILITY_APPLICABLE,
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
                "applicable_count": len(applicable_scores),
                "total_count": len(subdimension_scores),
            },
        )

    # ------------------------------------------------------------------------
    # PILIER
    # ------------------------------------------------------------------------

    def calculate_pillar_score(
        self,
        pillar_id: str,
        dimension_scores: List[ScoreResult],
        pillar_name: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> ScoreResult:
        """
        Calcule le score d'un pilier par moyenne pondérée
        des dimensions applicables.
        """

        if not dimension_scores:
            return self._build_non_applicable_result(
                entity_id=pillar_id,
                entity_name=pillar_name or pillar_id,
                entity_type="pillar",
                details={
                    "error": "Aucune dimension disponible"
                },
            )

        applicable_scores = [
            result
            for result in dimension_scores
            if result.applicability
            != constants.APPLICABILITY_NOT_APPLICABLE
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id=pillar_id,
                entity_name=pillar_name or pillar_id,
                entity_type="pillar",
                details={
                    "reason": "Toutes les dimensions sont Non applicable"
                },
            )

        component_ids = [
            result.entity_id
            for result in applicable_scores
        ]

        normalized_weights = self._normalize_weights(
            component_ids=component_ids,
            weights=weights,
            default_weight=constants.DEFAULT_WEIGHT_DIMENSION_PER_PILLAR,
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

        level = int(math.floor(final_score))

        level = min(
            max(level, constants.SCORE_MIN),
            constants.SCORE_MAX,
        )

        return ScoreResult(
            entity_id=pillar_id,
            entity_name=pillar_name or pillar_id,
            entity_type="pillar",
            score=final_score,
            level=level,
            level_name=self._get_level_name(level),
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=constants.APPLICABILITY_APPLICABLE,
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
                "applicable_count": len(applicable_scores),
                "total_count": len(dimension_scores),
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
        Calcule le Digital Maturity Index.

        Formule :

            DMI_score = Σ(wi × Score_Pi)

            DMI_% = DMI_score × 20

        Le score interne reste sur [0,5].
        Le DMI affiché est exprimé sur [0,100].
        """

        if not pillar_scores:
            return self._build_non_applicable_result(
                entity_id="DMI",
                entity_name="Indice de Maturité Digitale",
                entity_type="dmi",
                details={
                    "error": "Aucun pilier disponible"
                },
            )

        applicable_scores = [
            result
            for result in pillar_scores
            if result.applicability
            != constants.APPLICABILITY_NOT_APPLICABLE
        ]

        if not applicable_scores:
            return self._build_non_applicable_result(
                entity_id="DMI",
                entity_name="Indice de Maturité Digitale",
                entity_type="dmi",
                details={
                    "reason": "Aucun pilier applicable"
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
            weighted_sum * constants.DMI_SCALE_FACTOR,
            settings.DMI_DECIMAL_PRECISION,
        )

        level = int(math.floor(weighted_sum))

        level = min(
            max(level, constants.SCORE_MIN),
            constants.SCORE_MAX,
        )

        return ScoreResult(
            entity_id="DMI",
            entity_name="Indice de Maturité Digitale",
            entity_type="dmi",
            score=dmi_percent,
            level=level,
            level_name=self._get_level_name(level),
            children_scores={
                result.entity_id: result.score
                for result in applicable_scores
            },
            applicability=constants.APPLICABILITY_APPLICABLE,
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
                "applicable_count": len(applicable_scores),
                "total_count": len(pillar_scores),
            },
        )
