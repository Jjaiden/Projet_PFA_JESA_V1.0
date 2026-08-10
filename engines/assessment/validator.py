"""
validator.py — Validation du référentiel et d'une évaluation JDMAF.

Deux niveaux de validation :

1. Référentiel
   - volumétrie
   - structure hiérarchique
   - pondérations
   - niveaux de maturité
   - niveaux cibles
   - doublons
   - identifiants orphelins
   - cellules obligatoires
   - version du référentiel

2. Assessment
   - Assessment_ID
   - cohérence avec le référentiel
   - Applicability
   - R1 : score entier [0,5]
   - R3 : présence d'une preuve
   - scores manquants

Convention :
    error   = bloque le calcul
    warning = n'empêche pas le calcul
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from config import constants, settings
from config.constants import RefSheets
from data.models import Assessment, Referentiel
from utils.excel_utils import (
    open_workbook,
    sheet_to_records,
)


logger = settings.get_logger(__name__)


# ============================================================================
# STRUCTURES DE RAPPORT
# ============================================================================


@dataclass
class ValidationIssue:
    """
    Une anomalie détectée pendant la validation.
    """

    code: str
    severity: str
    message: str
    context: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ValidationReport:
    """
    Rapport complet de validation.
    """

    issues: list[ValidationIssue] = field(
        default_factory=list
    )

    def add(
        self,
        code: str,
        severity: str,
        message: str,
        **context: Any,
    ) -> None:
        """
        Ajoute une anomalie au rapport.
        """

        if severity not in {
            "error",
            "warning",
        }:
            raise ValueError(
                "severity doit être 'error' ou 'warning'."
            )

        self.issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                context=context,
            )
        )

        log = (
            logger.error
            if severity == "error"
            else logger.warning
        )

        log(
            "[%s] %s",
            code,
            message,
        )

    @property
    def errors(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "warning"
        ]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"{len(self.errors)} erreur(s), "
            f"{len(self.warnings)} avertissement(s)"
        )


class ValidationBlockingError(Exception):
    """
    Exception levée lorsqu'une validation contient
    au moins une erreur bloquante.
    """

    def __init__(
        self,
        report: ValidationReport,
    ):
        self.report = report

        messages = "\n".join(
            f"  - [{issue.code}] {issue.message}"
            for issue in report.errors
        )

        super().__init__(
            "Validation échouée "
            f"({report.summary()}) :\n"
            f"{messages}"
        )


def ensure_valid(
    report: ValidationReport,
) -> None:
    """
    Bloque le traitement si le rapport contient une erreur.
    """

    if not report.is_valid:
        raise ValidationBlockingError(
            report
        )


# ============================================================================
# 1. VALIDATION DU REFERENTIEL
# ============================================================================


def validate_referentiel(
    ref: Referentiel,
    wb_path: Optional[Any] = None,
) -> ValidationReport:
    """
    Valide le référentiel chargé.

    Contrôles :
        QC-01 à QC-21
    """

    if not isinstance(ref, Referentiel):
        raise TypeError("ref doit être une instance de Referentiel.")

    report = ValidationReport()

    _qc_volumetry(
        ref,
        report,
    )

    _qc_weights(
        ref,
        report,
    )

    _qc_targets_and_ids(
        ref,
        report,
    )

    _qc_raw_workbook_checks(
        wb_path or settings.REFERENTIEL_FILE,
        report,
    )

    logger.info(
        "Validation référentiel terminée : %s",
        report.summary(),
    )

    return report


# ============================================================================
# QC-01 → QC-10
# ============================================================================


def _qc_volumetry(
    ref: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Vérifie la volumétrie du référentiel.
    """

    # QC-01
    _check_count(
        report,
        "QC-01",
        len(ref.pillars),
        len(constants.PILLARS),
        "piliers",
    )

    # QC-02
    _check_count(
        report,
        "QC-02",
        len(ref.dimensions),
        len(constants.DIMENSIONS),
        "dimensions",
    )

    # QC-03
    _check_count(
        report,
        "QC-03",
        len(ref.subdimensions),
        len(constants.SUBDIMENSIONS),
        "sous-dimensions",
    )

    # QC-04
    _check_count(
        report,
        "QC-04",
        len(ref.indicators),
        constants.EXPECTED_INDICATOR_COUNT,
        "indicateurs",
    )

    # QC-05
    total_matrix_rows = sum(
        len(levels)
        for levels in
        ref.dimension_maturity_matrices.values()
    )

    expected_matrix_rows = (
        len(constants.DIMENSIONS)
        * (
            constants.SCORE_MAX
            - constants.SCORE_MIN
            + 1
        )
    )

    _check_count(
        report,
        "QC-05",
        total_matrix_rows,
        expected_matrix_rows,
        "lignes DIMENSION_MATURITY_MATRICES",
    )

    # QC-06
    total_grid_rows = sum(
        len(levels)
        for levels in
        ref.indicator_scoring_grids.values()
    )

    expected_grid_rows = (
        constants.EXPECTED_INDICATOR_COUNT
        * (
            constants.SCORE_MAX
            - constants.SCORE_MIN
            + 1
        )
    )

    _check_count(
        report,
        "QC-06",
        total_grid_rows,
        expected_grid_rows,
        "lignes INDICATOR_SCORING_GRIDS",
    )

    # QC-07
    for (
        subdimension_id,
        subdimension,
    ) in ref.subdimensions.items():

        actual_count = len(
            subdimension.indicator_ids
        )

        if (
            actual_count
            != constants.INDICATORS_PER_SUBDIMENSION
        ):
            report.add(
                "QC-07",
                "error",
                f"Sous-dimension {subdimension_id} "
                f"a {actual_count} indicateur(s) "
                f"au lieu de "
                f"{constants.INDICATORS_PER_SUBDIMENSION}.",
                subdimension_id=subdimension_id,
            )

    # QC-08
    expected_levels = set(
        range(
            constants.SCORE_MIN,
            constants.SCORE_MAX + 1,
        )
    )

    for dimension_id in constants.DIMENSIONS:

        levels = set(
            ref.dimension_maturity_matrices.get(
                dimension_id,
                {},
            ).keys()
        )

        _check_levels_complete(
            report,
            "QC-08",
            dimension_id,
            levels,
            "dimension",
            expected_levels,
        )

    # QC-09
    for indicator_id in ref.indicators:

        levels = set(
            ref.indicator_scoring_grids.get(
                indicator_id,
                {},
            ).keys()
        )

        _check_levels_complete(
            report,
            "QC-09",
            indicator_id,
            levels,
            "indicateur",
            expected_levels,
        )

    # QC-10
    missing_targets = [
        dimension_id
        for (
            dimension_id,
            dimension,
        ) in ref.dimensions.items()
        if dimension.effective_target_level
        is None
    ]

    if missing_targets:
        report.add(
            "QC-10",
            "error",
            "Niveau cible manquant pour "
            f"{len(missing_targets)} dimension(s) : "
            f"{missing_targets}",
            dimensions=missing_targets,
        )


def _check_count(
    report: ValidationReport,
    code: str,
    actual: int,
    expected: int,
    label: str,
) -> None:
    """
    Vérifie un nombre attendu.
    """

    if actual != expected:
        report.add(
            code,
            "error",
            f"Nombre de {label} attendu : "
            f"{expected}, obtenu : {actual}.",
        )


def _check_levels_complete(
    report: ValidationReport,
    code: str,
    entity_id: str,
    levels: set,
    kind: str,
    expected_levels: set,
) -> None:
    """
    Vérifie qu'une entité possède exactement les niveaux 0 à 5.
    """

    if levels == expected_levels:
        return

    missing = (
        expected_levels
        - levels
    )

    extra = (
        levels
        - expected_levels
    )

    report.add(
        code,
        "error",
        f"{kind.capitalize()} {entity_id} : "
        "niveaux incomplets/incorrects "
        f"(manquants={sorted(missing)}, "
        f"en trop={sorted(extra)}).",
        entity_id=entity_id,
    )


# ============================================================================
# QC-11 → QC-13 : PONDERATIONS
# ============================================================================


def _qc_weights(
    ref: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Vérifie les sommes des pondérations.
    """

    tolerance = (
        constants.WEIGHT_SUM_TOLERANCE
    )

    # QC-11 : poids des piliers
    pillar_weights = ref.weights.get(
        "Pilier",
        {},
    )

    total = sum(
        weight.resolved_weight
        for weight in pillar_weights.values()
    )

    if abs(total - 1.0) > tolerance:
        report.add(
            "QC-11",
            "error",
            f"Somme des poids des piliers = "
            f"{total:.4f}, attendu 1.0 "
            f"(±{tolerance}).",
        )

    # QC-12 : dimensions par pilier
    dimension_weights = ref.weights.get(
        "Dimension",
        {},
    )

    for (
        pillar_id,
        pillar,
    ) in ref.pillars.items():

        total = sum(
            dimension_weights[
                dimension_id
            ].resolved_weight
            for dimension_id
            in pillar.dimension_ids
            if dimension_id
            in dimension_weights
        )

        if abs(total - 1.0) > tolerance:
            report.add(
                "QC-12",
                "error",
                f"Somme des poids des dimensions "
                f"du pilier {pillar_id} = "
                f"{total:.4f}, attendu 1.0 "
                f"(±{tolerance}).",
                pillar_id=pillar_id,
            )

    # QC-13 : SD par dimension
    subdimension_weights = ref.weights.get(
        "Sous-dimension",
        {},
    )

    for (
        dimension_id,
        dimension,
    ) in ref.dimensions.items():

        total = sum(
            subdimension_weights[
                subdimension_id
            ].resolved_weight
            for subdimension_id
            in dimension.subdimension_ids
            if subdimension_id
            in subdimension_weights
        )

        if abs(total - 1.0) > tolerance:
            report.add(
                "QC-13",
                "error",
                f"Somme des poids des "
                f"sous-dimensions de "
                f"{dimension_id} = "
                f"{total:.4f}, attendu 1.0 "
                f"(±{tolerance}).",
                dimension_id=dimension_id,
            )


# ============================================================================
# QC-18 → QC-20
# ============================================================================


def _qc_targets_and_ids(
    ref: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Vérifie les niveaux cibles et les références des indicateurs.
    """

    # QC-20
    for (
        dimension_id,
        dimension,
    ) in ref.dimensions.items():

        target_values = (
            (
                "Target_Level_Default",
                dimension.target_level_default,
            ),
            (
                "Target_Level_User",
                dimension.target_level_user,
            ),
            (
                "Effective_Target_Level",
                dimension.effective_target_level,
            ),
        )

        for (
            label,
            value,
        ) in target_values:

            if value is None:
                continue

            if not (
                constants.SCORE_MIN
                <= value
                <= constants.SCORE_MAX
            ):
                report.add(
                    "QC-20",
                    "error",
                    f"{label} de {dimension_id} "
                    f"hors bornes "
                    f"[{constants.SCORE_MIN}-"
                    f"{constants.SCORE_MAX}] : "
                    f"{value}.",
                    dimension_id=dimension_id,
                )

    # QC-18 / QC-19
    for (
        indicator_id,
        indicator,
    ) in ref.indicators.items():

        if (
            indicator.pillar_id
            not in constants.PILLARS
        ):
            report.add(
                "QC-18",
                "error",
                f"Indicateur {indicator_id} "
                f"référence un Pillar_ID "
                f"invalide : "
                f"{indicator.pillar_id}.",
                indicator_id=indicator_id,
            )

        if (
            indicator.dimension_id
            not in constants.DIMENSIONS
        ):
            report.add(
                "QC-19",
                "error",
                f"Indicateur {indicator_id} "
                f"référence un Dimension_ID "
                f"invalide : "
                f"{indicator.dimension_id}.",
                indicator_id=indicator_id,
            )


# ============================================================================
# QC-14 → QC-17 / QC-21
# ============================================================================


def _qc_raw_workbook_checks(
    wb_path: Any,
    report: ValidationReport,
) -> None:
    """
    Contrôles nécessitant les données Excel brutes avant leur
    transformation en dictionnaires.
    """

    try:
        workbook = open_workbook(
            wb_path
        )

    except FileNotFoundError:
        report.add(
            "QC-RAW",
            "warning",
            "Classeur introuvable pour "
            "les contrôles bruts : "
            f"{wb_path}.",
        )
        return

    # ------------------------------------------------------------------------
    # QC-14 : doublons Indicator_ID
    # ------------------------------------------------------------------------

    indicator_records = (
        sheet_to_records(
            workbook,
            RefSheets.INDICATORS,
        )
    )

    _check_no_duplicates(
        report,
        "QC-14",
        indicator_records,
        "Indicator_ID",
    )

    # ------------------------------------------------------------------------
    # QC-15 : doublons Evidence_ID
    # ------------------------------------------------------------------------

    evidence_records = (
        sheet_to_records(
            workbook,
            RefSheets.EVIDENCE_CATALOG,
        )
    )

    _check_no_duplicates(
        report,
        "QC-15",
        evidence_records,
        "Evidence_ID",
    )

    # ------------------------------------------------------------------------
    # QC-16 : Subdimension_ID orphelins
    # ------------------------------------------------------------------------

    hierarchy_records = (
        sheet_to_records(
            workbook,
            RefSheets.HIERARCHY,
        )
    )

    known_subdimension_ids = {
        record.get(
            "Subdimension_ID"
        )
        for record in hierarchy_records
        if record.get(
            "Subdimension_ID"
        )
    }

    orphans = {
        record.get(
            "Subdimension_ID"
        )
        for record in indicator_records
        if (
            record.get(
                "Subdimension_ID"
            )
            and
            record.get(
                "Subdimension_ID"
            )
            not in known_subdimension_ids
        )
    }

    if orphans:
        report.add(
            "QC-16",
            "error",
            "Subdimension_ID orphelin(s) "
            "référencé(s) dans INDICATORS : "
            f"{sorted(orphans)}.",
            subdimensions=sorted(
                orphans
            ),
        )

    # ------------------------------------------------------------------------
    # QC-17 : cellules obligatoires
    # ------------------------------------------------------------------------

    required_columns = (
        "Indicator_ID",
        "Pillar_ID",
        "Dimension_ID",
        "Subdimension_ID",
        "Assessment_Question",
    )

    for record in indicator_records:

        missing = [
            column
            for column in required_columns
            if not record.get(column)
        ]

        if missing:
            report.add(
                "QC-17",
                "error",
                f"Indicateur "
                f"{record.get('Indicator_ID', '?')} : "
                "colonnes obligatoires vides : "
                f"{missing}.",
                indicator_id=record.get(
                    "Indicator_ID"
                ),
            )

    # ------------------------------------------------------------------------
    # QC-21 : version du référentiel
    # ------------------------------------------------------------------------

    metadata_records = (
        sheet_to_records(
            workbook,
            RefSheets.ASSESSMENT_METADATA,
        )
    )

    version_row = next(
        (
            record
            for record
            in metadata_records
            if record.get(
                "Field_Name"
            )
            == "Reference_Framework_Version"
        ),
        None,
    )

    if (
        not version_row
        or not version_row.get(
            "Field_Value"
        )
    ):
        report.add(
            "QC-21",
            "warning",
            "Version du référentiel "
            "(Reference_Framework_Version) "
            "non renseignée.",
        )


def _check_no_duplicates(
    report: ValidationReport,
    code: str,
    records: list[dict],
    id_column: str,
) -> None:
    """
    Vérifie l'absence de doublons sur une colonne ID.
    """

    seen: dict[Any, int] = {}

    for record in records:

        value = record.get(
            id_column
        )

        if value is None:
            continue

        seen[value] = (
            seen.get(value, 0)
            + 1
        )

    duplicates = [
        value
        for (
            value,
            count,
        ) in seen.items()
        if count > 1
    ]

    if duplicates:
        report.add(
            code,
            "error",
            f"Doublons détectés sur "
            f"{id_column} : "
            f"{duplicates}.",
            duplicates=duplicates,
        )


# ============================================================================
# 2. VALIDATION D'UNE EVALUATION
# ============================================================================


def validate_assessment(
    assessment: Assessment,
    referentiel: Referentiel,
) -> ValidationReport:
    """
    Valide une campagne d'évaluation.

    Contrôles :
        - Assessment_ID
        - cohérence indicateurs
        - Applicability
        - score manquant
        - R1
        - R3

    R2 n'est pas automatisé car il dépend de l'observation
    et du jugement de l'évaluateur sur le terrain.
    """

    if not isinstance(assessment, Assessment):
        raise TypeError("assessment doit être une instance de Assessment.")

    if not isinstance(referentiel, Referentiel):
        raise TypeError("referentiel doit être une instance de Referentiel.")

    report = ValidationReport()

    # ------------------------------------------------------------------------
    # META
    # ------------------------------------------------------------------------

    assessment_id = getattr(
        assessment.metadata,
        "assessment_id",
        None,
    )

    if (
        not assessment_id
        or assessment_id == "UNKNOWN"
    ):
        report.add(
            "META-01",
            "error",
            "Assessment_ID manquant "
            "dans ASSESSMENT_METADATA.",
        )

    # ------------------------------------------------------------------------
    # COHERENCE
    # ------------------------------------------------------------------------

    _check_indicator_coherence(
        assessment,
        referentiel,
        report,
    )

    # ------------------------------------------------------------------------
    # SCORES
    # ------------------------------------------------------------------------

    _check_scores(
        assessment,
        report,
    )

    logger.info(
        "Validation évaluation terminée : %s",
        report.summary(),
    )

    return report


def _check_indicator_coherence(
    assessment: Assessment,
    referentiel: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Vérifie que l'évaluation correspond exactement
    aux indicateurs du référentiel.
    """

    expected_ids = set(
        referentiel.indicators.keys()
    )

    actual_ids = set(
        assessment.indicator_scores.keys()
    )

    # Indicateurs présents dans Assessment
    # mais absents du référentiel
    orphans = (
        actual_ids
        - expected_ids
    )

    if orphans:
        report.add(
            "COHERENCE-01",
            "error",
            "L'évaluation référence "
            "des indicateurs absents "
            "du référentiel : "
            f"{sorted(orphans)}.",
            indicators=sorted(
                orphans
            ),
        )

    # Indicateurs attendus mais absents
    missing = (
        expected_ids
        - actual_ids
    )

    if missing:
        report.add(
            "COHERENCE-02",
            "error",
            "Indicateurs du référentiel "
            "absents de l'évaluation : "
            f"{sorted(missing)}.",
            indicators=sorted(
                missing
            ),
        )

    # Les colonnes de hiérarchie de l'évaluation doivent correspondre au
    # référentiel. Sans ce contrôle, une ligne peut porter un bon Indicator_ID
    # mais être affichée sous une mauvaise dimension dans le questionnaire.
    for indicator_id in actual_ids & expected_ids:
        assessment_score = assessment.indicator_scores[indicator_id]
        reference_indicator = referentiel.indicators[indicator_id]

        if assessment_score.indicator_id != indicator_id:
            report.add(
                "COHERENCE-03",
                "error",
                f"Clé {indicator_id} incohérente avec Indicator_ID "
                f"de la ligne : {assessment_score.indicator_id!r}.",
                indicator_id=indicator_id,
            )

        for field_name, actual_value, expected_value in (
            ("Pillar_ID", assessment_score.pillar_id, reference_indicator.pillar_id),
            ("Dimension_ID", assessment_score.dimension_id, reference_indicator.dimension_id),
            (
                "Subdimension_ID",
                assessment_score.subdimension_id,
                reference_indicator.subdimension_id,
            ),
        ):
            if actual_value != expected_value:
                report.add(
                    "COHERENCE-04",
                    "error",
                    f"{indicator_id} : {field_name}={actual_value!r}, "
                    f"attendu {expected_value!r}.",
                    indicator_id=indicator_id,
                    field=field_name,
                )


def _check_scores(
    assessment: Assessment,
    report: ValidationReport,
) -> None:
    """
    Vérifie les scores et l'applicabilité.
    """

    for (
        indicator_id,
        indicator_score,
    ) in assessment.indicator_scores.items():

        applicability = (
            indicator_score.applicability
        )

        # --------------------------------------------------------------------
        # Applicability
        # --------------------------------------------------------------------

        if (
            applicability
            not in (
                constants.APPLICABILITY_APPLICABLE,
                constants.APPLICABILITY_NOT_APPLICABLE,
            )
        ):
            report.add(
                "APPLICABILITY-01",
                "error",
                f"{indicator_id} : "
                "valeur Applicability invalide : "
                f"{applicability!r}.",
                indicator_id=indicator_id,
            )

            # On ne peut pas interpréter la suite
            continue

        # --------------------------------------------------------------------
        # Non applicable
        # --------------------------------------------------------------------

        if (
            not indicator_score.is_applicable
        ):
            continue

        # --------------------------------------------------------------------
        # Score manquant
        # --------------------------------------------------------------------

        selected_score = (
            indicator_score.selected_score
        )

        if selected_score is None:

            severity = (
                "warning"
                if settings.ALLOW_MISSING_SCORE_ON_APPLICABLE
                else "error"
            )

            report.add(
                "R1-MISSING",
                severity,
                f"{indicator_id} : "
                "applicable mais aucune note "
                "saisie (Selected_Score vide).",
                indicator_id=indicator_id,
            )

            continue

        # --------------------------------------------------------------------
        # R1 : entier 0-5
        # --------------------------------------------------------------------

        valid_integer = (
            isinstance(
                selected_score,
                int,
            )
            and not isinstance(
                selected_score,
                bool,
            )
        )

        # Excel / pandas peut fournir 3.0
        # pour une valeur entière.
        if isinstance(
            selected_score,
            float,
        ):
            valid_integer = (
                selected_score.is_integer()
            )

        if not valid_integer:
            report.add(
                "R1",
                "error",
                f"{indicator_id} : "
                f"note {selected_score!r} "
                "non entière. "
                "Les notes doivent être "
                "des entiers de 0 à 5.",
                indicator_id=indicator_id,
            )

            continue

        numeric_score = int(
            selected_score
        )

        if (
            numeric_score
            not in constants.VALID_INDICATOR_SCORES
        ):
            report.add(
                "R1",
                "error",
                f"{indicator_id} : "
                f"note {numeric_score} "
                "hors de l'échelle valide "
                f"[{constants.SCORE_MIN}-"
                f"{constants.SCORE_MAX}].",
                indicator_id=indicator_id,
            )

        # --------------------------------------------------------------------
        # R3 : preuve
        # --------------------------------------------------------------------

        evidence_reference = (
            indicator_score.evidence_reference
        )

        if not evidence_reference:
            report.add(
                "R3",
                "warning",
                f"{indicator_id} : "
                f"note {numeric_score} saisie "
                "sans référence de preuve "
                "(Evidence_Reference).",
                indicator_id=indicator_id,
            )
