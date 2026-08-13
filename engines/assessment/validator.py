"""
validator.py — Validation of the reference framework and an assessment.

Two validation levels:

1. Reference framework

   - volume
   - hierarchical structure
   - weights
   - maturity levels
   - target levels
   - duplicates
   - orphan identifiers
   - mandatory cells
   - reference framework version

2. Assessment

   - Assessment_ID
   - consistency with the reference framework
   - Applicability
   - R1: integer score [0,5]
   - R3: evidence presence
   - missing scores

Convention:
error   = blocks calculation
warning = does not prevent calculation
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
# VALIDATION REPORT STRUCTURES
# ============================================================================


@dataclass
class ValidationIssue:
    """
    An issue detected during validation.
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
    Complete validation report.
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
        Add an issue to the validation report.
        """

        if severity not in {
            "error",
            "warning",
        }:
            raise ValueError(
                "severity must be 'error' or 'warning'."
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
            f"{len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)"
        )


class ValidationBlockingError(Exception):
    """
    Exception raised when validation contains
    at least one blocking error.
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
            "Validation failed "
            f"({report.summary()}):\n"
            f"{messages}"
        )


def ensure_valid(
    report: ValidationReport,
) -> None:
    """
    Stop processing if the validation report contains an error.
    """

    if not report.is_valid:
        raise ValidationBlockingError(
            report
        )


# ============================================================================
# 1. REFERENCE FRAMEWORK VALIDATION
# ============================================================================


def validate_referentiel(
    ref: Referentiel,
    wb_path: Optional[Any] = None,
) -> ValidationReport:
    """
    Validate the loaded reference framework.

    Controls:
        QC-01 to QC-21
    """

    if not isinstance(ref, Referentiel):
        raise TypeError(
            "ref must be an instance of Referentiel."
        )

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
        "Reference framework validation completed: %s",
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
    Validate the reference framework volume.
    """

    # QC-01
    _check_count(
        report,
        "QC-01",
        len(ref.pillars),
        len(constants.PILLARS),
        "pillars",
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
        "subdimensions",
    )

    # QC-04
    _check_count(
        report,
        "QC-04",
        len(ref.indicators),
        constants.EXPECTED_INDICATOR_COUNT,
        "indicators",
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
        "DIMENSION_MATURITY_MATRICES rows",
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
        "INDICATOR_SCORING_GRIDS rows",
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
                f"Subdimension {subdimension_id} "
                f"has {actual_count} indicator(s) "
                f"instead of "
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
            "indicator",
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
            "Target level missing for "
            f"{len(missing_targets)} dimension(s): "
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
    Validate an expected count.
    """

    if actual != expected:
        report.add(
            code,
            "error",
            f"Expected number of {label}: "
            f"{expected}, found: {actual}.",
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
    Validate that an entity contains exactly levels 0 to 5.
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
        f"{kind.capitalize()} {entity_id}: "
        "incomplete/invalid levels "
        f"(missing={sorted(missing)}, "
        f"extra={sorted(extra)}).",
        entity_id=entity_id,
    )


# ============================================================================
# QC-11 → QC-13: WEIGHTS
# ============================================================================


def _qc_weights(
    ref: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Validate weight sums.
    """

    tolerance = (
        constants.WEIGHT_SUM_TOLERANCE
    )

    # QC-11: pillar weights
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
            f"Pillar weight sum = "
            f"{total:.4f}, expected 1.0 "
            f"(±{tolerance}).",
        )

    # QC-12: dimensions per pillar
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
                f"Weight sum of dimensions "
                f"under pillar {pillar_id} = "
                f"{total:.4f}, expected 1.0 "
                f"(±{tolerance}).",
                pillar_id=pillar_id,
            )

    # QC-13: subdimensions per dimension
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
                f"Weight sum of "
                f"subdimensions under "
                f"{dimension_id} = "
                f"{total:.4f}, expected 1.0 "
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
    Validate target levels and indicator references.
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
                    f"{label} for {dimension_id} "
                    f"is outside the valid range "
                    f"[{constants.SCORE_MIN}-"
                    f"{constants.SCORE_MAX}]: "
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
                f"Indicator {indicator_id} "
                f"references an invalid "
                f"Pillar_ID: "
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
                f"Indicator {indicator_id} "
                f"references an invalid "
                f"Dimension_ID: "
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
    Perform checks requiring raw Excel data before
    transformation into dictionaries.
    """

    try:
        workbook = open_workbook(
            wb_path
        )

    except FileNotFoundError:
        report.add(
            "QC-RAW",
            "warning",
            "Reference workbook not found for "
            f"raw checks: {wb_path}.",
        )
        return

    # ------------------------------------------------------------------------
    # QC-14: duplicate Indicator_ID
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
    # QC-15: duplicate Evidence_ID
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
    # QC-16: orphan Subdimension_ID
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
            "Orphan Subdimension_ID(s) "
            "referenced in INDICATORS: "
            f"{sorted(orphans)}.",
            subdimensions=sorted(
                orphans
            ),
        )

    # ------------------------------------------------------------------------
    # QC-17: mandatory cells
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
                f"Indicator "
                f"{record.get('Indicator_ID', '?')}: "
                "mandatory columns are empty: "
                f"{missing}.",
                indicator_id=record.get(
                    "Indicator_ID"
                ),
            )

    # ------------------------------------------------------------------------
    # QC-21: reference framework version
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
            "Reference framework version "
            "(Reference_Framework_Version) "
            "is not specified.",
        )


def _check_no_duplicates(
    report: ValidationReport,
    code: str,
    records: list[dict],
    id_column: str,
) -> None:
    """
    Validate that no duplicate values exist in an ID column.
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
            f"Duplicates detected for "
            f"{id_column}: "
            f"{duplicates}.",
            duplicates=duplicates,
        )


# ============================================================================
# 2. ASSESSMENT VALIDATION
# ============================================================================


def validate_assessment(
    assessment: Assessment,
    referentiel: Referentiel,
) -> ValidationReport:
    """
    Validate an assessment campaign.

    Controls:
        - Assessment_ID
        - indicator consistency
        - Applicability
        - missing score
        - R1
        - R3

    R2 is not automated because it depends on field observation
    and evaluator judgment.
    """

    if not isinstance(assessment, Assessment):
        raise TypeError(
            "assessment must be an instance of Assessment."
        )

    if not isinstance(referentiel, Referentiel):
        raise TypeError(
            "referentiel must be an instance of Referentiel."
        )

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
            "Assessment_ID is missing "
            "from ASSESSMENT_METADATA.",
        )

    # ------------------------------------------------------------------------
    # CONSISTENCY
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
        "Assessment validation completed: %s",
        report.summary(),
    )

    return report


def _check_indicator_coherence(
    assessment: Assessment,
    referentiel: Referentiel,
    report: ValidationReport,
) -> None:
    """
    Validate that the assessment exactly matches
    the indicators defined in the reference framework.
    """

    expected_ids = set(
        referentiel.indicators.keys()
    )

    actual_ids = set(
        assessment.indicator_scores.keys()
    )

    # Indicators present in the assessment
    # but absent from the reference framework
    orphans = (
        actual_ids
        - expected_ids
    )

    if orphans:
        report.add(
            "COHERENCE-01",
            "error",
            "The assessment references "
            "indicators that are absent "
            "from the reference framework: "
            f"{sorted(orphans)}.",
            indicators=sorted(
                orphans
            ),
        )

    # Expected indicators that are missing
    missing = (
        expected_ids
        - actual_ids
    )

    if missing:
        report.add(
            "COHERENCE-02",
            "error",
            "Indicators from the reference framework "
            "are missing from the assessment: "
            f"{sorted(missing)}.",
            indicators=sorted(
                missing
            ),
        )

    # The hierarchy fields in the assessment must match
    # the reference framework. Without this check, a row could
    # contain a valid Indicator_ID but be displayed under
    # an incorrect dimension in the questionnaire.
    for indicator_id in actual_ids & expected_ids:

        assessment_score = (
            assessment.indicator_scores[
                indicator_id
            ]
        )

        reference_indicator = (
            referentiel.indicators[
                indicator_id
            ]
        )

        if (
            assessment_score.indicator_id
            != indicator_id
        ):
            report.add(
                "COHERENCE-03",
                "error",
                f"Key {indicator_id} is inconsistent "
                f"with the row's Indicator_ID: "
                f"{assessment_score.indicator_id!r}.",
                indicator_id=indicator_id,
            )

        for (
            field_name,
            actual_value,
            expected_value,
        ) in (
            (
                "Pillar_ID",
                assessment_score.pillar_id,
                reference_indicator.pillar_id,
            ),
            (
                "Dimension_ID",
                assessment_score.dimension_id,
                reference_indicator.dimension_id,
            ),
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
                    f"{indicator_id}: "
                    f"{field_name}={actual_value!r}, "
                    f"expected {expected_value!r}.",
                    indicator_id=indicator_id,
                    field=field_name,
                )


def _check_scores(
    assessment: Assessment,
    report: ValidationReport,
) -> None:
    """
    Validate scores and applicability.
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
                f"{indicator_id}: "
                "invalid Applicability value: "
                f"{applicability!r}.",
                indicator_id=indicator_id,
            )

            # The remaining checks cannot be interpreted
            continue

        # --------------------------------------------------------------------
        # Not applicable
        # --------------------------------------------------------------------

        if (
            not indicator_score.is_applicable
        ):
            continue

        # --------------------------------------------------------------------
        # Missing score
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
                f"{indicator_id}: "
                "applicable but no score "
                "has been entered "
                "(Selected_Score is empty).",
                indicator_id=indicator_id,
            )

            continue

        # --------------------------------------------------------------------
        # R1: integer 0-5
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

        # Excel / pandas may provide 3.0
        # for an integer value.
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
                f"{indicator_id}: "
                f"score {selected_score!r} "
                "is not an integer. "
                "Scores must be "
                "integers from 0 to 5.",
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
                f"{indicator_id}: "
                f"score {numeric_score} "
                "is outside the valid scale "
                f"[{constants.SCORE_MIN}-"
                f"{constants.SCORE_MAX}].",
                indicator_id=indicator_id,
            )

        # --------------------------------------------------------------------
        # R3: evidence
        # --------------------------------------------------------------------

        evidence_reference = (
            indicator_score.evidence_reference
        )

        if not evidence_reference:
            report.add(
                "R3",
                "warning",
                f"{indicator_id}: "
                f"score {numeric_score} entered "
                "without an evidence reference "
                "(Evidence_Reference).",
                indicator_id=indicator_id,
            )