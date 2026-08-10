"""
aggregation.py — Moteur d'agrégation du JDMAF.

Responsabilité :
    Orchestrer le calcul complet :

        indicateurs
              ↓
        sous-dimensions
              ↓
        dimensions
              ↓
        piliers
              ↓
        DMI

Ce module appartient exclusivement au backend.
Il ne contient aucune interface frontend.

Architecture utilisée :
    data.loader.load_referentiel() -> Referentiel
    data.loader.load_assessment()  -> Assessment

Le moteur travaille directement avec les objets définis dans
data/models.py. Il n'utilise pas de DataFrame pandas et ne dépend
pas d'un ReferenceLoader.
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
    Moteur d'agrégation du modèle d'évaluation.

    Le moteur reçoit un Referentiel déjà chargé par data.loader
    et utilise le ScoringEngine pour effectuer les calculs.

    Hiérarchie :

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
        Initialise le moteur.

        Args:
            referentiel:
                Objet Referentiel retourné par load_referentiel().

            config:
                Configuration optionnelle du moteur de scoring.
        """

        if not isinstance(referentiel, Referentiel):
            raise TypeError(
                "referentiel doit être une instance de Referentiel."
            )

        self.referentiel = referentiel
        self.config = config or {}
        self.validate_before_aggregation = self.config.get(
            "validate_before_aggregation",
            True,
        )

        self.scoring_engine = ScoringEngine(self.config)

        logger.info(
            "AggregationEngine initialisé : "
            "%d piliers, %d dimensions, %d sous-dimensions, %d indicateurs.",
            len(self.referentiel.pillars),
            len(self.referentiel.dimensions),
            len(self.referentiel.subdimensions),
            len(self.referentiel.indicators),
        )

    # ========================================================================
    # API PRINCIPALE
    # ========================================================================

    def aggregate_scores(
        self,
        assessment: Assessment,
    ) -> Dict[str, Any]:
        """
        Calcule l'intégralité de l'évaluation.

        Args:
            assessment:
                Objet Assessment retourné par load_assessment().

        Returns:
            Dictionnaire contenant :

                indicators
                subdimensions
                dimensions
                pillars
                dmi
                metadata
        """

        if not isinstance(assessment, Assessment):
            raise TypeError(
                "assessment doit être une instance de Assessment."
            )

        if self.validate_before_aggregation:
            validation_report = validate_assessment(
                assessment,
                self.referentiel,
            )
            ensure_valid(validation_report)

        logger.info(
            "Début de l'agrégation de l'évaluation %s.",
            assessment.metadata.assessment_id,
        )

        # ------------------------------------------------------------------
        # 1. Indicateurs
        # ------------------------------------------------------------------

        indicator_results = self._calculate_indicator_scores(
            assessment
        )

        # ------------------------------------------------------------------
        # 2. Sous-dimensions
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
        # 4. Piliers
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
            "Agrégation terminée : DMI=%s.",
            (
                dmi_result.score
                if dmi_result is not None
                else None
            ),
        )

        return results

    # ========================================================================
    # INDICATEURS
    # ========================================================================

    def _calculate_indicator_scores(
        self,
        assessment: Assessment,
    ) -> Dict[str, ScoreResult]:
        """
        Calcule les scores individuels des indicateurs.

        Un indicateur Non Applicable est exclu des agrégations
        supérieures selon la logique définie dans le ScoringEngine.

        Un score manquant pour un indicateur Applicable bloque
        le calcul si settings.ALLOW_MISSING_SCORE_ON_APPLICABLE
        est False.
        """

        results: Dict[str, ScoreResult] = {}

        for indicator_id, indicator_score in (
            assessment.indicator_scores.items()
        ):
            indicator_id = str(indicator_id).strip()

            # --------------------------------------------------------------
            # Vérification de l'existence de l'indicateur
            # --------------------------------------------------------------

            indicator = self.referentiel.indicators.get(
                indicator_id
            )

            if indicator is None:
                raise ValueError(
                    f"Indicateur inconnu dans l'évaluation : "
                    f"{indicator_id}"
                )

            # --------------------------------------------------------------
            # Applicabilité
            # --------------------------------------------------------------

            applicability = (
                indicator_score.applicability
                or constants.APPLICABILITY_APPLICABLE
            )

            applicability = str(
                applicability
            ).strip()

            if applicability == constants.APPLICABILITY_NOT_APPLICABLE:

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

            if applicability != constants.APPLICABILITY_APPLICABLE:
                raise ValueError(
                    f"{indicator_id} : Applicability invalide : "
                    f"{applicability!r}"
                )

            # --------------------------------------------------------------
            # Score manquant
            # --------------------------------------------------------------

            selected_score = indicator_score.selected_score

            if selected_score is None:

                if settings.ALLOW_MISSING_SCORE_ON_APPLICABLE:
                    logger.warning(
                        "%s : score manquant mais autorisé par settings.",
                        indicator_id,
                    )
                    continue

                raise ValueError(
                    f"{indicator_id} : indicateur applicable "
                    "mais Selected_Score est vide."
                )

            # --------------------------------------------------------------
            # Normalisation du score
            # --------------------------------------------------------------

            selected_score = self._normalize_score(
                indicator_id,
                selected_score,
            )

            # --------------------------------------------------------------
            # Grille de scoring
            # --------------------------------------------------------------

            scoring_grid = self._get_scoring_grid(
                indicator_id,
                selected_score,
            )

            # --------------------------------------------------------------
            # Calcul du score indicateur
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
    # SOUS-DIMENSIONS
    # ========================================================================

    def _calculate_subdimension_scores(
        self,
        indicator_results: Dict[str, ScoreResult],
    ) -> Dict[str, ScoreResult]:
        """
        Agrège les indicateurs vers les sous-dimensions.

        Les sous-dimensions sont récupérées directement depuis
        le Referentiel afin de ne perdre aucune sous-dimension,
        même lorsqu'elle contient uniquement des indicateurs N/A.
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
        Agrège les sous-dimensions vers les dimensions.
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
                level="Sous-dimension",
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
    # PILIERS
    # ========================================================================

    def _calculate_pillar_scores(
        self,
        dimension_results: Dict[str, ScoreResult],
    ) -> Dict[str, ScoreResult]:
        """
        Agrège les dimensions vers les piliers.
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
        Calcule le DMI à partir des piliers.
        """

        if not pillar_results:
            return None

        pillar_scores = list(
            pillar_results.values()
        )

        weights = self._get_weights_for_level(
            level="Pilier",
            parent_id="DMI",
        )

        return self.scoring_engine.calculate_dmi(
            pillar_scores=pillar_scores,
            weights=weights,
        )

    # ========================================================================
    # OUTILS INDICATEURS
    # ========================================================================

    def _normalize_score(
        self,
        indicator_id: str,
        selected_score: Any,
    ) -> int:
        """
        Convertit le score en entier valide.

        Excel peut par exemple fournir 3.0 alors que la valeur
        métier attendue est 3.
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
                f"{indicator_id} : score invalide "
                f"{selected_score!r}."
            ) from exc

        if not numeric_score.is_integer():
            raise ValueError(
                f"{indicator_id} : le score "
                f"{numeric_score} n'est pas entier."
            )

        score = int(
            numeric_score
        )

        if score < 0 or score > 5:
            raise ValueError(
                f"{indicator_id} : score hors limites "
                f"(0-5) : {score}."
            )

        return score

    # ========================================================================
    # GRILLE DE SCORING
    # ========================================================================

    def _get_scoring_grid(
        self,
        indicator_id: str,
        selected_score: int,
    ) -> Dict[str, Any]:
        """
        Retourne la ligne de grille correspondant à un indicateur
        et à son score.

        Le Referentiel contient directement :

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
                f"Aucune grille de scoring trouvée "
                f"pour l'indicateur {indicator_id}."
            )

        grid_entry = indicator_grids.get(
            selected_score
        )

        if grid_entry is None:
            raise ValueError(
                f"Grille de scoring absente pour "
                f"{indicator_id}, score {selected_score}."
            )

        # Le ScoringEngine peut recevoir un dictionnaire.
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
    # PONDERATIONS
    # ========================================================================

    def _get_weights_for_level(
        self,
        level: str,
        parent_id: str,
    ) -> Optional[Dict[str, float]]:
        """
        Récupère les pondérations depuis Referentiel.weights.

        Structure :

            referentiel.weights[
                hierarchy_level
            ][component_id] -> WeightEntry

        La recherche utilise également parent_id afin de ne
        conserver que les composants appartenant au parent demandé.
        """

        level_weights = self.referentiel.weights.get(
            level
        )

        if not level_weights:
            logger.warning(
                "Aucune pondération trouvée pour le niveau %s.",
                level,
            )
            return None

        weights: Dict[str, float] = {}

        for component_id, entry in level_weights.items():

            # Vérification du parent.
            if entry.parent_id != parent_id:
                continue

            weight = entry.resolved_weight

            if weight < 0:
                raise ValueError(
                    f"Poids négatif pour {component_id} : "
                    f"{weight}"
                )

            weights[component_id] = float(
                weight
            )

        if not weights:
            logger.warning(
                "Aucune pondération trouvée pour "
                "%s/%s. Les poids par défaut du "
                "ScoringEngine seront utilisés.",
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
                f"Somme des poids invalide pour "
                f"{level}/{parent_id} : "
                f"{total:.6f}"
            )

            if settings.STRICT_WEIGHT_VALIDATION:
                raise ValueError(
                    message
                )

            logger.warning(
                "%s. Normalisation automatique.",
                message,
            )

            weights = {
                component_id: weight / total
                for component_id, weight
                in weights.items()
            }

        return weights

    # ========================================================================
    # RESUME
    # ========================================================================

    def get_summary(
        self,
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produit un résumé backend facilement exploitable
        par les futures pages frontend.

        Cette méthode ne contient aucune logique frontend.
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
        # Piliers
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
        # Forces / faiblesses
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
