"""
maturity.py — Gestion des niveaux de maturité du JDMAF.

Responsabilité :
    Interpréter les scores déjà calculés par le moteur de scoring
    et déterminer le niveau de maturité correspondant.

Hiérarchie :
    Indicateur       -> score 0..5
    Sous-dimension   -> score 0..5
    Dimension        -> score 0..5
    Pilier           -> score 0..5
    DMI              -> score interne 0..5 / affichage 0..100 %

Important :
    Ce module NE calcule PAS les agrégations.
    Les calculs sont réalisés dans scoring.py.
    L'orchestration est réalisée dans aggregation.py.

Ce module ne contient aucune logique frontend.
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
# RESULTAT DE MATURITE
# ============================================================================


@dataclass(frozen=True)
class MaturityResult:
    """
    Résultat standardisé d'une interprétation de maturité.

    Attributes:
        score:
            Score numérique sur l'échelle 0..5.

        level:
            Niveau entier de maturité 0..5.

        level_name:
            Nom du niveau.

        description:
            Description du niveau.

        evaluation_principle:
            Principe d'évaluation associé au niveau.

        minimum_evidence_principle:
            Principe concernant les preuves minimales attendues.

        source:
            Origine de la définition :
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
# MOTEUR DE MATURITE
# ============================================================================


class MaturityEngine:
    """
    Moteur d'interprétation des niveaux de maturité.

    Il utilise les données du Referentiel :

        - GENERIC_MATURITY_SCALE
        - DIMENSION_MATURITY_MATRICES
        - INDICATOR_SCORING_GRIDS

    Il ne réalise aucune agrégation.
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
                "referentiel doit être une instance de Referentiel."
            )

        self.referentiel = referentiel
        self.config = config or {}

        logger.info("MaturityEngine initialisé.")

    # ========================================================================
    # SCORE -> NIVEAU
    # ========================================================================

    def level_from_score(
        self,
        score: Optional[float],
    ) -> Optional[int]:
        """
        Convertit un score 0..5 en niveau entier 0..5.

        Règle :
            niveau = partie entière du score

        Exemples :
            0.0 -> 0
            1.0 -> 1
            2.7 -> 2
            3.9 -> 3
            5.0 -> 5

        Cette règle est cohérente avec scoring.py qui utilise
        math.floor() pour déterminer le niveau.
        """

        if score is None:
            return None

        try:
            numeric_score = float(score)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Score de maturité invalide : {score!r}"
            ) from exc

        self._validate_score(numeric_score)

        return int(math.floor(numeric_score))

    # ========================================================================
    # MATURITE GENERIQUE
    # ========================================================================

    def get_generic_maturity(
        self,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Retourne la maturité générique correspondant à un score 0..5.
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
                "Niveau %s absent du référentiel de maturité.",
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
    # MATURITE DIMENSION
    # ========================================================================

    def get_dimension_maturity(
        self,
        dimension_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Retourne la maturité spécifique à une dimension.

        Priorité :
            1. matrice spécifique de la dimension
            2. échelle générique du référentiel
        """

        if not dimension_id:
            raise ValueError(
                "dimension_id ne peut pas être vide."
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
            "Description spécifique absente pour %s niveau %s. "
            "Utilisation de la maturité générique.",
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
    # MATURITE INDICATEUR
    # ========================================================================

    def get_indicator_maturity(
        self,
        indicator_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Retourne la définition de maturité d'un indicateur.

        La grille INDICATOR_SCORING_GRIDS est prioritaire.
        """

        if not indicator_id:
            raise ValueError(
                "indicator_id ne peut pas être vide."
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
            "Grille de scoring absente pour %s niveau %s. "
            "Utilisation de la maturité générique.",
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
    # MATURITE DMI
    # ========================================================================

    def get_dmi_maturity(
        self,
        dmi_score: Optional[float],
    ) -> MaturityResult:
        """
        Interprète le DMI.

        aggregation.py / scoring.py stockent le DMI affiché sur 0..100.

        Conversion :
            DMI % / 20 = score interne 0..5

        Exemple :
            0 %   -> 0.0 -> niveau 0
            20 %  -> 1.0 -> niveau 1
            50 %  -> 2.5 -> niveau 2
            80 %  -> 4.0 -> niveau 4
            100 % -> 5.0 -> niveau 5
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
    # INTERPRETATION D'UNE EVALUATION
    # ========================================================================

    def assess_indicator(
        self,
        assessment: Assessment,
        indicator_id: str,
    ) -> MaturityResult:
        """
        Interprète le niveau de maturité d'un indicateur
        dans une évaluation.
        """

        if not isinstance(assessment, Assessment):
            raise TypeError(
                "assessment doit être une instance de Assessment."
            )

        indicator_score = assessment.indicator_scores.get(
            indicator_id
        )

        if indicator_score is None:
            raise KeyError(
                f"Indicateur absent de l'évaluation : {indicator_id}"
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
    # INTERPRETATION DIMENSION
    # ========================================================================

    def assess_dimension(
        self,
        dimension_id: str,
        score: Optional[float],
    ) -> MaturityResult:
        """
        Interprète le niveau de maturité d'une dimension.
        """

        if dimension_id not in self.referentiel.dimensions:
            raise KeyError(
                f"Dimension inconnue dans le référentiel : {dimension_id}"
            )

        return self.get_dimension_maturity(
            dimension_id=dimension_id,
            score=score,
        )

    # ========================================================================
    # RESUME MULTI-NIVEAUX
    # ========================================================================

    def build_maturity_summary(
        self,
        indicator_scores: Optional[dict[str, float]] = None,
        dimension_scores: Optional[dict[str, float]] = None,
        pillar_scores: Optional[dict[str, float]] = None,
        dmi_score: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Construit un résumé des niveaux de maturité.

        Aucun score n'est calculé ici.
        Les scores sont supposés avoir déjà été calculés
        par scoring.py / aggregation.py.
        """

        summary: dict[str, Any] = {
            "indicators": {},
            "dimensions": {},
            "pillars": {},
            "dmi": None,
        }

        # ------------------------------------------------------------------
        # INDICATEURS
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
        # PILIERS
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
        Vérifie qu'un score respecte l'échelle 0..5.
        """

        if not math.isfinite(score):
            raise ValueError(
                f"Score invalide : {score}. "
                "Le score doit être une valeur numérique finie."
            )

        if not (
            self.MIN_LEVEL
            <= score
            <= self.MAX_LEVEL
        ):
            raise ValueError(
                f"Score hors limites : {score}. "
                f"Le score doit être compris entre "
                f"{self.MIN_LEVEL} et {self.MAX_LEVEL}."
            )

    @staticmethod
    def _validate_dmi(
        dmi_score: float,
    ) -> float:
        """
        Vérifie que le DMI est compris entre 0 et 100 %.
        """

        try:
            dmi_percent = float(dmi_score)

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"DMI invalide : {dmi_score!r}"
            ) from exc

        if not math.isfinite(dmi_percent):

            raise ValueError(
                f"DMI invalide : {dmi_score!r}. "
                "Le DMI doit être une valeur numérique finie."
            )

        if not 0 <= dmi_percent <= 100:

            raise ValueError(
                f"DMI invalide : {dmi_score!r}. "
                "Intervalle attendu : 0..100."
            )

        return dmi_percent

    # ========================================================================
    # CONVERSION DES MODELES
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
        Nom de secours si le référentiel ne contient pas le niveau.
        """

        return constants.MATURITY_LEVELS.get(
            level,
            f"Niveau {level}",
        )

    # ========================================================================
    # SERIALISATION
    # ========================================================================

    @staticmethod
    def _result_to_dict(
        result: MaturityResult,
    ) -> dict[str, Any]:
        """
        Transforme un MaturityResult en dictionnaire.
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
# FONCTIONS UTILITAIRES PUBLIQUES
# ============================================================================


def get_maturity_level(
    score: Optional[float],
) -> Optional[int]:
    """
    Retourne le niveau 0..5 correspondant à un score 0..5.
    """

    if score is None:
        return None

    try:
        numeric_score = float(score)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            f"Score invalide : {score!r}"
        ) from exc

    if not math.isfinite(numeric_score):

        raise ValueError(
            f"Score invalide : {score!r}. "
            "Le score doit être une valeur numérique finie."
        )

    if not (
        constants.SCORE_MIN
        <= numeric_score
        <= constants.SCORE_MAX
    ):

        raise ValueError(
            f"Score hors limites : {numeric_score}. "
            f"Intervalle attendu : "
            f"{constants.SCORE_MIN}..{constants.SCORE_MAX}."
        )

    return int(math.floor(numeric_score))


def get_maturity_name(
    referentiel: Referentiel,
    level: Optional[int],
) -> str:
    """
    Retourne le nom d'un niveau de maturité depuis le référentiel.
    """

    if level is None:
        return ""

    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError(
            f"Niveau de maturité invalide : {level!r}"
        )

    if not (
        constants.SCORE_MIN
        <= level
        <= constants.SCORE_MAX
    ):
        raise ValueError(
            f"Niveau de maturité invalide : {level}"
        )

    entry = referentiel.maturity_scale.get(level)

    if entry is not None:
        return entry.name

    return MaturityEngine._fallback_level_name(level)