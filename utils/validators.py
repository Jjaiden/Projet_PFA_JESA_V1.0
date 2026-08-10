# JESA_DMAT/utils/validators.py
"""
Generic validation functions for the JESA DMAT application.

Provides a collection of pure, reusable validators for data types,
DataFrames, numeric ranges, and file extensions.

Additionally, this module contains domain‑specific validators for the
JESA digital maturity assessment: scores, identifiers, weights,
assessment data, files, TPI parameters, and general utilities.

All functions raise :class:`ValueError` or :class:`TypeError` with
descriptive messages when validation fails.

No business logic (scoring, recommendations, etc.) is included here.
"""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence

import pandas as pd
from pandas import DataFrame, Series

from config.constants import (
    SCORE_MIN,
    SCORE_MAX,
    PILLAR_IDS,
    DIMENSION_IDS,
    ERROR_MESSAGES,
)

# ----------------------------------------------------------------------
# Logger standard – sera automatiquement configuré par l'application
# ----------------------------------------------------------------------
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())  # Évite les avertissements si pas de config


# =============================================================================
# VALIDATIONS GÉNÉRIQUES (provenant du FRONTEND)
# =============================================================================

def validate_file_extension(
    file_path: Path,
    allowed_extensions: Sequence[str],
) -> bool:
    """Check if the file has one of the allowed extensions (case-insensitive).

    The file is **not** checked for existence – only its extension is examined.
    Use :func:`file_manager.file_exists` before calling this function if you
    need to verify the file is present.

    Args:
        file_path: Path to the file.
        allowed_extensions: Collection of allowed extensions,
            each starting with a dot (e.g. ``(".xlsx", ".csv")``).
            Must not be empty.

    Returns:
        ``True`` if the extension is valid.

    Raises:
        ValueError: If ``allowed_extensions`` is empty or if the file
            extension is not in the allowed list.
    """
    if not allowed_extensions:
        raise ValueError("allowed_extensions cannot be empty.")

    suffix = file_path.suffix.lower()
    allowed = tuple(ext.lower() for ext in allowed_extensions)

    if suffix not in allowed:
        msg = (
            f"Invalid file extension '{suffix}' for {file_path.name}. "
            f"Allowed: {allowed_extensions}"
        )
        _logger.warning(msg)
        raise ValueError(msg)

    _logger.debug("Validated file extension: %s", suffix)
    return True


def validate_dataframe(df: DataFrame) -> None:
    """Validate that the input is a non-empty pandas DataFrame.

    Args:
        df: Object to validate.

    Raises:
        TypeError: If ``df`` is not a pandas DataFrame.
        ValueError: If the DataFrame is empty (no rows or no columns).
    """
    if not isinstance(df, DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df).__name__}")

    if df.empty:
        raise ValueError("DataFrame is empty (no rows or columns).")

    _logger.debug("Validated DataFrame: %d rows, %d columns", *df.shape)


def validate_required_columns(
    df: DataFrame,
    required_columns: Sequence[str],
) -> None:
    """Ensure that all required columns are present in the DataFrame.

    Args:
        df: DataFrame to check.
        required_columns: Column names that must exist.

    Raises:
        TypeError: If ``df`` is not a DataFrame.
        ValueError: If any required column is missing.
    """
    validate_dataframe(df)

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        msg = f"Missing required columns: {missing}. Available: {list(df.columns)}"
        _logger.warning(msg)
        raise ValueError(msg)

    _logger.debug("All required columns present: %s", required_columns)


def validate_no_missing_values(
    df: DataFrame,
    columns: Sequence[str] | None = None,
) -> None:
    """Check for missing (NaN/None) values in the DataFrame.

    If ``columns`` is provided, those columns are first validated for
    existence, then checked for missing values. Otherwise the entire
    DataFrame is examined.

    Args:
        df: DataFrame to inspect.
        columns: Optional list of column names to check. If ``None``,
            all columns are checked.

    Raises:
        TypeError: If ``df`` is not a DataFrame.
        ValueError: If a required column is missing, or any missing value
            is detected.
    """
    validate_dataframe(df)

    if columns is not None:
        validate_required_columns(df, columns)
        subset = df[columns]
    else:
        subset = df

    if subset.isnull().any().any():
        null_counts = subset.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        details = ", ".join(f"{col}: {cnt}" for col, cnt in null_cols.items())
        msg = f"Found missing values in columns: {details}"
        _logger.warning(msg)
        raise ValueError(msg)

    _logger.debug("No missing values found in %d columns", len(subset.columns))


def validate_numeric_range(
    value: int | float,
    min_val: int | float = 0.0,
    max_val: int | float = 100.0,
    name: str = "Value",
) -> None:
    """Validate that a numeric value falls within an inclusive range.

    The default upper bound is 100.0 (a common reference for percentages),
    but callers should pass explicit limits when a specific range is required.
    The function is **not** tied to any business constant.

    Args:
        value: The numeric value to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive). Must be >= ``min_val``.
        name: Descriptive name for the value, used in error messages.

    Raises:
        TypeError: If any argument is not numeric.
        ValueError: If ``min_val > max_val`` or the value is outside the
            allowed range.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"`{name}` must be a number, got {type(value).__name__}")
    if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
        raise TypeError("`min_val` and `max_val` must be numbers")

    if min_val > max_val:
        raise ValueError(
            f"`min_val` ({min_val}) cannot be greater than `max_val` ({max_val})."
        )

    if value < min_val or value > max_val:
        msg = (
            f"`{name}` = {value} is out of range. "
            f"Allowed: [{min_val}, {max_val}]"
        )
        _logger.warning(msg)
        raise ValueError(msg)

    _logger.debug(
        "Validated numeric range for `%s`: %s in [%s, %s]",
        name, value, min_val, max_val
    )


# =============================================================================
# VALIDATION DES SCORES (BACKEND)
# =============================================================================

def validate_score(score: Any) -> bool:
    """
    Validate that a score is an integer between SCORE_MIN and SCORE_MAX.

    Args:
        score: Value to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If the score is invalid.
    """
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError(f"Score must be a number, received: {type(score)}")

    if isinstance(score, float):
        if not math.isfinite(score) or not score.is_integer():
            raise ValueError(f"Score must be an integer, received: {score}")
        score = int(score)

    if score < SCORE_MIN or score > SCORE_MAX:
        raise ValueError(
            f"Score must be between {SCORE_MIN} and {SCORE_MAX}, received: {score}"
        )

    return True


def validate_scores_list(scores: List[Any]) -> bool:
    """
    Validate a list of scores.

    Args:
        scores: List of scores to validate.

    Returns:
        True if all scores are valid.

    Raises:
        ValueError: If a score is invalid.
    """
    for score in scores:
        validate_score(score)
    return True


def validate_score_array(scores: Series) -> bool:
    """
    Validate a pandas Series of scores.

    Args:
        scores: Series of scores to validate.

    Returns:
        True if all scores are valid.

    Raises:
        ValueError: If a score is invalid.
    """
    for score in scores:
        if pd.isna(score):
            continue
        validate_score(score)
    return True


# =============================================================================
# VALIDATION DES IDENTIFIANTS (BACKEND)
# =============================================================================

def validate_indicator_id(indicator_id: str) -> bool:
    """
    Validate that an indicator ID has the correct format.

    Format: I-D{number}-{number} (e.g., I-D1-01)

    Args:
        indicator_id: Indicator ID.

    Returns:
        True if valid.

    Raises:
        ValueError: If the ID is invalid.
    """
    if not indicator_id or not isinstance(indicator_id, str):
        raise ValueError(ERROR_MESSAGES['invalid_indicator_id'])

    pattern = r'^I-D\d{1,2}-\d{2}$'
    if not re.match(pattern, indicator_id):
        raise ValueError(ERROR_MESSAGES['invalid_indicator_id'])

    return True


def validate_dimension_id(dimension_id: str) -> bool:
    """
    Validate that a dimension ID is correct.

    Args:
        dimension_id: Dimension ID.

    Returns:
        True if valid.

    Raises:
        ValueError: If the ID is invalid.
    """
    if not dimension_id or not isinstance(dimension_id, str):
        raise ValueError("Dimension ID must be a string")

    if dimension_id not in DIMENSION_IDS:
        raise ValueError(ERROR_MESSAGES['invalid_dimension'].format(dim_id=dimension_id))

    return True


def validate_pillar_id(pillar_id: str) -> bool:
    """
    Validate that a pillar ID is correct.

    Args:
        pillar_id: Pillar ID.

    Returns:
        True if valid.

    Raises:
        ValueError: If the ID is invalid.
    """
    if not pillar_id or not isinstance(pillar_id, str):
        raise ValueError("Pillar ID must be a string")

    if pillar_id not in PILLAR_IDS:
        raise ValueError(ERROR_MESSAGES['invalid_pillar'].format(pillar_id=pillar_id))

    return True


def validate_subdimension_id(subdimension_id: str) -> bool:
    """
    Validate that a sub‑dimension ID has the correct format.

    Format: SD{number}.{number} (e.g., SD1.1)

    Args:
        subdimension_id: Sub‑dimension ID.

    Returns:
        True if valid.

    Raises:
        ValueError: If the ID is invalid.
    """
    if not subdimension_id or not isinstance(subdimension_id, str):
        raise ValueError("Sub‑dimension ID must be a string")

    pattern = r'^SD\d{1,2}\.\d{1,2}$'
    if not re.match(pattern, subdimension_id):
        raise ValueError(f"Invalid sub‑dimension ID format: {subdimension_id}. Expected: SDx.y")

    return True


def validate_recommendation_id(recommendation_id: str) -> bool:
    """
    Validate that a recommendation ID has the correct format.

    Format: REC-D{number}-{band}-{number} (e.g., REC-D1-01-01)

    Args:
        recommendation_id: Recommendation ID.

    Returns:
        True if valid.

    Raises:
        ValueError: If the ID is invalid.
    """
    if not recommendation_id or not isinstance(recommendation_id, str):
        raise ValueError("Recommendation ID must be a string")

    pattern = r'^REC-D\d{1,2}-\d{2}-\d{2}$'
    if not re.match(pattern, recommendation_id):
        raise ValueError(f"Invalid recommendation ID format: {recommendation_id}")

    return True


# =============================================================================
# VALIDATION DES POIDS (BACKEND)
# =============================================================================

def validate_weights(weights: dict) -> bool:
    """
    Validate that the sum of weights equals 1.0.

    Args:
        weights: Dictionary of weights.

    Returns:
        True if valid.

    Raises:
        ValueError: If the sum is not 1.0 or any weight is negative.
    """
    if not weights:
        raise ValueError("Weights cannot be empty")

    total = sum(weights.values())

    # Tolerance for floating‑point rounding errors
    if abs(total - 1.0) > 0.001:
        raise ValueError(ERROR_MESSAGES['weight_sum_error'].format(sum=total))

    for key, value in weights.items():
        if value < 0:
            raise ValueError(f"Weight for {key} is negative: {value}")

    return True


def validate_weight_configuration(df: DataFrame) -> bool:
    """
    Validate the weight configuration in a DataFrame.

    Args:
        df: DataFrame containing weights.

    Returns:
        True if valid.

    Raises:
        ValueError: If the configuration is invalid.
    """
    required_columns = ['Parent_ID', 'Component_ID', 'Effective_Weight']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    for parent_id in df['Parent_ID'].unique():
        parent_df = df[df['Parent_ID'] == parent_id]
        total = parent_df['Effective_Weight'].sum()
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Sum of weights for {parent_id} is {total}, must be 1.0"
            )

    return True


# =============================================================================
# VALIDATION DES DONNÉES D'ÉVALUATION (BACKEND)
# =============================================================================

def validate_assessment_data(df: DataFrame) -> bool:
    """
    Validate assessment data.

    Args:
        df: DataFrame of assessment data.

    Returns:
        True if valid.

    Raises:
        ValueError: If the data is invalid.
    """
    required_columns = ['Indicator_ID', 'Selected_Score']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    for indicator_id in df['Indicator_ID']:
        if not pd.isna(indicator_id):
            validate_indicator_id(str(indicator_id))

    for score in df['Selected_Score']:
        if not pd.isna(score):
            validate_score(score)

    return True


def validate_target_levels(target_levels: dict) -> bool:
    """
    Validate target levels.

    Args:
        target_levels: Dictionary {dimension_id: target_level}.

    Returns:
        True if valid.

    Raises:
        ValueError: If target levels are invalid.
    """
    for dim_id, level in target_levels.items():
        validate_dimension_id(dim_id)
        validate_score(level)

    return True


# =============================================================================
# VALIDATION DES FICHIERS (BACKEND)
# =============================================================================

def validate_file_exists(file_path: str | Path) -> bool:
    """
    Validate that a file exists.

    Args:
        file_path: Path to the file.

    Returns:
        True if the file exists.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not Path(file_path).is_file():
        raise FileNotFoundError(ERROR_MESSAGES['file_not_found'].format(path=file_path))

    return True


def validate_excel_file(file_path: str, sheet_name: Optional[str] = None) -> bool:
    """
    Validate that an Excel file is valid.

    Args:
        file_path: Path to the file.
        sheet_name: Optional sheet name to verify.

    Returns:
        True if the file is valid.

    Raises:
        ValueError: If the file is invalid.
    """
    validate_file_exists(file_path)

    try:
        if sheet_name:
            pd.read_excel(file_path, sheet_name=sheet_name, nrows=1)
        else:
            sheets = pd.ExcelFile(file_path).sheet_names
            if not sheets:
                raise ValueError(f"File {file_path} contains no sheets")
    except Exception as e:
        raise ValueError(f"Error reading Excel file {file_path}: {e}")

    return True


# =============================================================================
# VALIDATION TPI (BACKEND)
# =============================================================================

def validate_tpi_parameters(params: dict) -> bool:
    """
    Validate TPI parameters.

    Args:
        params: Dictionary of TPI parameters.

    Returns:
        True if valid.

    Raises:
        ValueError: If a parameter is invalid.
    """
    required_params = [
        'business_impact', 'strategic_importance', 'expected_roi',
        'implementation_cost', 'implementation_difficulty'
    ]

    for param in required_params:
        if param not in params:
            raise ValueError(f"Missing TPI parameter: {param}")
        validate_score(params[param])

    return True


def validate_tpi_weights(weights: dict) -> bool:
    """
    Validate TPI weights.

    Args:
        weights: Dictionary of TPI weights.

    Returns:
        True if valid.

    Raises:
        ValueError: If weights are invalid.
    """
    required_params = [
        'gap', 'business_impact', 'strategic_importance',
        'expected_roi', 'implementation_cost', 'implementation_difficulty'
    ]

    for param in required_params:
        if param not in weights:
            raise ValueError(f"Missing TPI weight for: {param}")
        value = weights[param]
        if not isinstance(value, (int, float)):
            raise ValueError(f"Weight for {param} must be a number")
        if value < 0 or value > 1:
            raise ValueError(f"Weight for {param} must be between 0 and 1")

    return validate_weights(weights)


# =============================================================================
# VALIDATION UNIVERSELLE (BACKEND)
# =============================================================================

def validate_not_empty(value: Any, field_name: str) -> bool:
    """
    Validate that a value is not empty.

    Args:
        value: Value to check.
        field_name: Name of the field for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If the value is empty.
    """
    if value is None:
        raise ValueError(f"Field '{field_name}' cannot be None")

    if isinstance(value, str) and not value.strip():
        raise ValueError(f"Field '{field_name}' cannot be empty")

    if isinstance(value, (list, dict, Series)) and len(value) == 0:
        raise ValueError(f"Field '{field_name}' cannot be empty")

    return True


def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> bool:
    """
    Validate that a value is within a range.

    Args:
        value: Value to check.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        field_name: Name of the field for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If the value is out of range.
    """
    if value < min_val or value > max_val:
        raise ValueError(
            f"Field '{field_name}' must be between {min_val} and {max_val}, "
            f"received: {value}"
        )

    return True


def validate_type(value: Any, expected_type: type, field_name: str) -> bool:
    """
    Validate the type of a value.

    Args:
        value: Value to check.
        expected_type: Expected type.
        field_name: Name of the field for error messages.

    Returns:
        True if valid.

    Raises:
        TypeError: If the type is incorrect.
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, "
            f"received: {type(value).__name__}"
        )

    return True


def validate(value: Any,
             validators: Iterable[Callable[[Any], Any]],
             field_name: str = "value") -> bool:
    """
    Apply a list of validators to a value.

    Args:
        value: Value to validate.
        validators: List of validation functions.
        field_name: Name of the field for error messages.

    Returns:
        True if all validators pass.

    Raises:
        ValueError: If a validator fails.
    """
    for validator in validators:
        try:
            validator(value)
        except Exception as e:
            raise ValueError(f"Validation failed for '{field_name}': {e}")

    return True


# =============================================================================
# EXPORT PUBLIC API
# =============================================================================

__all__ = [
    # Generic validations (FRONTEND)
    "validate_file_extension",
    "validate_dataframe",
    "validate_required_columns",
    "validate_no_missing_values",
    "validate_numeric_range",

    # Score validations (BACKEND)
    "validate_score",
    "validate_scores_list",
    "validate_score_array",

    # Identifier validations (BACKEND)
    "validate_indicator_id",
    "validate_dimension_id",
    "validate_pillar_id",
    "validate_subdimension_id",
    "validate_recommendation_id",

    # Weight validations (BACKEND)
    "validate_weights",
    "validate_weight_configuration",

    # Assessment data validations (BACKEND)
    "validate_assessment_data",
    "validate_target_levels",

    # File validations (BACKEND)
    "validate_file_exists",
    "validate_excel_file",

    # TPI validations (BACKEND)
    "validate_tpi_parameters",
    "validate_tpi_weights",

    # General validations (BACKEND)
    "validate_not_empty",
    "validate_range",
    "validate_type",
    "validate",
]