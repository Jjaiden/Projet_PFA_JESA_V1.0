# JESA_DMAT/charts/utils.py
"""
Generic utility functions for the JESA DMAT visualization package.

Provides pure, reusable helpers for validation, normalization, statistics,
color generation, label formatting, and value clamping. All functions are
stateless, independently testable, and free of any chart-specific logic.

Usage::

    from charts.utils import normalize, validate_same_length, clamp_percentage

    scores = normalize([1.5, 3.2, 4.8], new_min=0, new_max=100)
    validate_same_length(["A", "B"], [10, 20, 30])  # raises ValueError
    clamped = clamp_percentage(125.0)                # returns 100.0
"""

from __future__ import annotations

import textwrap
from typing import Sequence

__all__ = [
    # Validation
    "validate_numeric_sequence",
    "validate_labels",
    "validate_same_length",
    "is_empty_sequence",
    # Normalization
    "normalize",
    # Percentage helpers
    "clamp_percentage",
    "format_percentage",
    "is_ratio",
    # Bounds
    "compute_bounds",
    # Colors
    "repeat_color",
    "generate_colors",
    "alternate_colors",
    # Text
    "truncate_label",
    "wrap_label",
    "unique_labels",
    # Statistics
    "mean",
    "median",
    "span",
    "safe_max",
    "safe_min",
    "all_equal",
    "has_negative_values",
    # Arithmetic
    "safe_divide",
    "round_if_close",
]

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_numeric_sequence(
    values: Sequence[int | float],
    name: str = "values",
) -> None:
    """Ensure ``values`` is a non-empty sequence of numbers.

    Args:
        values: The sequence to validate. Strings are explicitly rejected.
        name: Human-readable name used in error messages.

    Raises:
        TypeError: If ``values`` is not a sequence, is a string, or
            contains non-numeric items.
        ValueError: If ``values`` is empty.

    Example:
        >>> validate_numeric_sequence([1, 2, 3])
        >>> validate_numeric_sequence([])  # ValueError
        >>> validate_numeric_sequence("123")  # TypeError
    """
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise TypeError(
            f"{name} must be a sequence of numbers (not a string), "
            f"got {type(values).__name__}"
        )
    if len(values) == 0:
        raise ValueError(f"{name} must not be empty")
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise TypeError(
                f"{name}[{i}] must be int or float, got {type(v).__name__} "
                f"(value={v!r})"
            )


def validate_labels(
    labels: Sequence[str],
    name: str = "labels",
) -> None:
    """Ensure ``labels`` is a non-empty sequence of non-empty strings.

    Args:
        labels: The sequence to validate. Strings are explicitly rejected.
        name: Human-readable name used in error messages.

    Raises:
        TypeError: If ``labels`` is not a sequence of strings or is itself
            a string.
        ValueError: If ``labels`` is empty or contains empty/whitespace strings.

    Example:
        >>> validate_labels(["A", "B", "C"])
        >>> validate_labels(["A", ""])  # ValueError
        >>> validate_labels("ABC")  # TypeError
    """
    if not isinstance(labels, Sequence) or isinstance(labels, (str, bytes)):
        raise TypeError(
            f"{name} must be a sequence of strings (not a string), "
            f"got {type(labels).__name__}"
        )
    if len(labels) == 0:
        raise ValueError(f"{name} must not be empty")
    for i, label in enumerate(labels):
        if not isinstance(label, str):
            raise TypeError(
                f"{name}[{i}] must be str, got {type(label).__name__} "
                f"(value={label!r})"
            )
        if label.strip() == "":
            raise ValueError(
                f"{name}[{i}] must not be an empty or whitespace-only string"
            )


def validate_same_length(
    labels: Sequence[object],
    values: Sequence[object],
    label_name: str = "labels",
    value_name: str = "values",
) -> None:
    """Ensure two sequences have the same length.

    Args:
        labels: First sequence.
        values: Second sequence.
        label_name: Name for the first sequence in error messages.
        value_name: Name for the second sequence in error messages.

    Raises:
        ValueError: If the sequences have different lengths.

    Example:
        >>> validate_same_length(["A", "B"], [10, 20])
        >>> validate_same_length(["A", "B"], [10])  # ValueError
    """
    if len(labels) != len(values):
        raise ValueError(
            f"{label_name} and {value_name} must have the same length: "
            f"{len(labels)} != {len(values)}"
        )


def is_empty_sequence(seq: Sequence[object] | None) -> bool:
    """Return ``True`` if ``seq`` is ``None`` or an empty sequence.

    Args:
        seq: Any sequence or ``None``.

    Returns:
        ``True`` if ``seq`` is ``None`` or has length 0.

    Raises:
        TypeError: If ``seq`` is not a sequence or ``None``.

    Example:
        >>> is_empty_sequence([])
        True
        >>> is_empty_sequence(None)
        True
        >>> is_empty_sequence([1, 2])
        False
    """
    if seq is None:
        return True
    if not isinstance(seq, Sequence) or isinstance(seq, (str, bytes)):
        raise TypeError(
            f"Expected a Sequence or None, got {type(seq).__name__}"
        )
    return len(seq) == 0


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize(
    values: Sequence[int | float],
    new_min: float = 0.0,
    new_max: float = 100.0,
) -> list[float]:
    """Linearly normalize a sequence to a new range.

    Uses min-max normalization. If all values are identical, every
    element is mapped to the midpoint of the target range.

    Args:
        values: Numeric values to normalize (non-empty).
        new_min: Lower bound of the target range.
        new_max: Upper bound of the target range. Must be > ``new_min``.

    Returns:
        List of normalized values in ``[new_min, new_max]``.

    Raises:
        ValueError: If ``values`` is empty or ``new_min >= new_max``.

    Example:
        >>> normalize([10, 20, 30], 0, 100)
        [0.0, 50.0, 100.0]
        >>> normalize([5, 5, 5], 0, 100)
        [50.0, 50.0, 50.0]
    """
    validate_numeric_sequence(values, "values")
    if new_min >= new_max:
        raise ValueError(
            f"new_min ({new_min}) must be < new_max ({new_max})"
        )

    old_min = min(values)
    old_max = max(values)

    if old_min == old_max:
        mid = (new_min + new_max) / 2.0
        return [mid] * len(values)

    scale = (new_max - new_min) / (old_max - old_min)
    return [new_min + (v - old_min) * scale for v in values]


# ---------------------------------------------------------------------------
# Percentage helpers
# ---------------------------------------------------------------------------


def clamp_percentage(
    value: float,
    lower: float = 0.0,
    upper: float = 100.0,
) -> float:
    """Clamp a value to a percentage range.

    Args:
        value: The value to clamp.
        lower: Minimum allowed value (default ``0.0``).
        upper: Maximum allowed value (default ``100.0``).

    Returns:
        ``value`` constrained to ``[lower, upper]``.

    Raises:
        ValueError: If ``lower > upper``.

    Example:
        >>> clamp_percentage(125.0)
        100.0
        >>> clamp_percentage(-10.0)
        0.0
    """
    if lower > upper:
        raise ValueError(
            f"lower ({lower}) must be <= upper ({upper})"
        )
    return max(lower, min(upper, value))


def format_percentage(
    value: float,
    decimals: int = 1,
    include_sign: bool = False,
) -> str:
    """Format a number as a human-readable percentage string.

    Accepts values already expressed in percent (e.g. ``82.5`` → ``"82.5%"``).
    For ratio-based values (0–1), use :func:`is_ratio` to check first.

    Args:
        value: The value to format (e.g. ``82.5`` for 82.5%).
        decimals: Number of decimal places (default ``1``).
        include_sign: If ``True``, prefix positive values with ``'+'``.

    Returns:
        Formatted percentage string ending with ``'%'``.

    Example:
        >>> format_percentage(82.5)
        '82.5%'
        >>> format_percentage(82.5, decimals=0)
        '83%'
        >>> format_percentage(-5.0)
        '-5.0%'
    """
    formatted = f"{value:.{decimals}f}"
    if include_sign and value > 0:
        formatted = "+" + formatted
    return f"{formatted}%"


def is_ratio(value: float) -> bool:
    """Return ``True`` if ``value`` is a ratio between 0.0 and 1.0 inclusive.

    A ratio is a value that represents a fraction of a whole (e.g. 0.75 = ¾).
    This is distinct from a percentage value like 75.

    Args:
        value: The value to test.

    Returns:
        ``True`` if ``0.0 <= value <= 1.0``.

    Example:
        >>> is_ratio(0.75)
        True
        >>> is_ratio(75.0)
        False
    """
    return 0.0 <= value <= 1.0


# ---------------------------------------------------------------------------
# Automatic bounds
# ---------------------------------------------------------------------------


def compute_bounds(
    values: Sequence[int | float],
    margin: float = 0.05,
    symmetric: bool = False,
) -> tuple[float, float]:
    """Compute (ymin, ymax) for a chart axis with a configurable margin.

    Args:
        values: Numeric values (non-empty).
        margin: Fraction of the data span to add as padding on each side.
            Must be in ``[0.0, 1.0]`` (e.g. ``0.05`` = 5% padding).
        symmetric: If ``True``, the axis will be symmetric around zero
            (useful for bar charts with positive/negative values).

    Returns:
        Tuple of ``(ymin, ymax)``.

    Raises:
        ValueError: If ``values`` is empty or ``margin`` is out of range.

    Example:
        >>> compute_bounds([10, 20, 30], margin=0.1)
        (8.0, 32.0)
        >>> compute_bounds([-5, 10], symmetric=True)
        (-12.5, 12.5)
    """
    validate_numeric_sequence(values, "values")
    if not 0.0 <= margin <= 1.0:
        raise ValueError(
            f"margin must be between 0.0 and 1.0, got {margin}"
        )

    vmin = min(values)
    vmax = max(values)
    span_val = vmax - vmin if vmax != vmin else 1.0
    padding = span_val * margin

    ymin = vmin - padding
    ymax = vmax + padding

    if symmetric:
        abs_max = max(abs(ymin), abs(ymax))
        ymin = -abs_max
        ymax = abs_max

    return (float(ymin), float(ymax))


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def repeat_color(
    color: str,
    count: int,
) -> list[str]:
    """Return a list of ``count`` identical colors.

    Args:
        color: A hex color string (e.g. ``"#2563EB"``).
        count: Number of repetitions. Must be >= 0.

    Returns:
        List of ``count`` identical color strings.

    Raises:
        ValueError: If ``count`` is negative.

    Example:
        >>> repeat_color("#2563EB", 3)
        ['#2563EB', '#2563EB', '#2563EB']
    """
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    return [color] * count


def generate_colors(
    colors: Sequence[str],
    count: int,
) -> list[str]:
    """Cycle through ``colors`` to produce a list of ``count`` entries.

    Args:
        colors: Palette of colors to cycle through (non-empty).
        count: Number of colors to generate. Must be >= 0.

    Returns:
        List of ``count`` colors cycling through the palette.

    Raises:
        ValueError: If ``colors`` is empty or ``count`` is negative.

    Example:
        >>> generate_colors(["#FF0000", "#00FF00", "#0000FF"], 5)
        ['#FF0000', '#00FF00', '#0000FF', '#FF0000', '#00FF00']
    """
    if len(colors) == 0:
        raise ValueError("colors must not be empty")
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    return [colors[i % len(colors)] for i in range(count)]


def alternate_colors(
    colors: Sequence[str],
    count: int,
) -> list[str]:
    """Create a strictly alternating pattern of two colors.

    Uses only the first two colors of ``colors`` (ignoring any extras)
    and alternates them: ``[A, B, A, B, …]``. If only one color is
    provided, it is repeated.

    Args:
        colors: Palette of at least 1 color.
        count: Number of colors to generate. Must be >= 0.

    Returns:
        List of ``count`` alternating colors.

    Raises:
        ValueError: If ``colors`` is empty or ``count`` is negative.

    Example:
        >>> alternate_colors(["#2563EB", "#10B981"], 5)
        ['#2563EB', '#10B981', '#2563EB', '#10B981', '#2563EB']
    """
    if len(colors) == 0:
        raise ValueError("colors must not be empty")
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    a = colors[0]
    b = colors[1] if len(colors) > 1 else a
    return [a if i % 2 == 0 else b for i in range(count)]


# ---------------------------------------------------------------------------
# Label / text helpers
# ---------------------------------------------------------------------------


def truncate_label(
    label: str,
    max_length: int = 15,
    suffix: str = "...",
) -> str:
    """Truncate a label to a maximum length, appending a suffix.

    Args:
        label: The original label.
        max_length: Maximum number of characters (including suffix).
        suffix: String appended when truncation occurs.

    Returns:
        Truncated label or the original if it fits.

    Raises:
        ValueError: If ``max_length < len(suffix)``.

    Example:
        >>> truncate_label("Digital Maturity Assessment", max_length=12)
        'Digital M...'
    """
    if max_length < len(suffix):
        raise ValueError(
            f"max_length ({max_length}) must be >= len(suffix) ({len(suffix)})"
        )
    if len(label) <= max_length:
        return label
    return label[: max_length - len(suffix)] + suffix


def wrap_label(
    label: str,
    width: int = 20,
) -> str:
    """Wrap a long label by inserting HTML ``<br>`` line breaks on spaces.

    Uses :func:`textwrap.fill` to break the label at word boundaries,
    then replaces newlines with ``<br>`` for Plotly HTML labels.

    Args:
        label: The original label.
        width: Maximum characters per line.

    Returns:
        Label with ``<br>`` inserted at word-wrapped line breaks.

    Raises:
        ValueError: If ``width <= 0``.

    Example:
        >>> wrap_label("Digital Maturity Assessment Tool", width=12)
        'Digital<br>Maturity<br>Assessment<br>Tool'
    """
    if width <= 0:
        raise ValueError(f"width must be > 0, got {width}")
    wrapped = textwrap.fill(label, width=width, break_long_words=False)
    return wrapped.replace("\n", "<br>")


def unique_labels(labels: Sequence[str]) -> list[str]:
    """Return a deduplicated list of labels preserving insertion order.

    Validates the input via :func:`validate_labels` first.

    Args:
        labels: A sequence of string labels.

    Returns:
        List of unique labels in their original order.

    Example:
        >>> unique_labels(["A", "B", "A", "C"])
        ['A', 'B', 'C']
    """
    validate_labels(labels)
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


# ---------------------------------------------------------------------------
# Statistics (no NumPy dependency)
# ---------------------------------------------------------------------------


def mean(values: Sequence[int | float]) -> float:
    """Compute the arithmetic mean of numeric values.

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Arithmetic mean as a float.

    Raises:
        ValueError: If ``values`` is empty.

    Example:
        >>> mean([1, 2, 3, 4])
        2.5
    """
    validate_numeric_sequence(values, "values")
    return sum(values) / len(values)


def median(values: Sequence[int | float]) -> float:
    """Compute the median of numeric values.

    For an even number of elements, returns the average of the two
    middle values.

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Median as a float.

    Raises:
        ValueError: If ``values`` is empty.

    Example:
        >>> median([1, 2, 3, 4])
        2.5
        >>> median([1, 2, 3])
        2.0
    """
    validate_numeric_sequence(values, "values")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
    return float(sorted_vals[mid])


def span(values: Sequence[int | float]) -> float:
    """Return the span (max - min) of a numeric sequence.

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Difference between the maximum and minimum values.

    Raises:
        ValueError: If ``values`` is empty.

    Example:
        >>> span([10, 3, 8, 15])
        12.0
    """
    validate_numeric_sequence(values, "values")
    return float(max(values) - min(values))


def safe_max(values: Sequence[int | float], default: float = 0.0) -> float:
    """Return the maximum value, or ``default`` if the sequence is empty.

    Args:
        values: A sequence of numbers (may be empty).
        default: Value returned when ``values`` is empty.

    Returns:
        Maximum value or ``default``.

    Example:
        >>> safe_max([3, 1, 2])
        3.0
        >>> safe_max([], default=-1.0)
        -1.0
    """
    if is_empty_sequence(values):
        return default
    return float(max(values))


def safe_min(values: Sequence[int | float], default: float = 0.0) -> float:
    """Return the minimum value, or ``default`` if the sequence is empty.

    Args:
        values: A sequence of numbers (may be empty).
        default: Value returned when ``values`` is empty.

    Returns:
        Minimum value or ``default``.

    Example:
        >>> safe_min([3, 1, 2])
        1.0
        >>> safe_min([], default=100.0)
        100.0
    """
    if is_empty_sequence(values):
        return default
    return float(min(values))


def all_equal(values: Sequence[int | float]) -> bool:
    """Return ``True`` if all values in the sequence are equal.

    Args:
        values: A sequence of numbers (may be empty).

    Returns:
        ``True`` if all elements are equal or the sequence has 0 or 1 elements.

    Raises:
        TypeError: If ``values`` is not a sequence of numbers.

    Example:
        >>> all_equal([5, 5, 5])
        True
        >>> all_equal([1, 2, 3])
        False
    """
    if is_empty_sequence(values):
        return True
    validate_numeric_sequence(values, "values")
    if len(values) <= 1:
        return True
    first = values[0]
    return all(v == first for v in values)


def has_negative_values(values: Sequence[int | float]) -> bool:
    """Return ``True`` if any value in the sequence is negative.

    Args:
        values: A sequence of numbers (may be empty).

    Returns:
        ``True`` if at least one element is < 0.

    Raises:
        TypeError: If ``values`` is not a sequence of numbers.

    Example:
        >>> has_negative_values([3, -1, 2])
        True
        >>> has_negative_values([1, 2, 3])
        False
    """
    if is_empty_sequence(values):
        return False
    validate_numeric_sequence(values, "values")
    return any(v < 0 for v in values)


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------


def safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """Divide two numbers, returning a default value when the denominator is 0.

    Args:
        numerator: The dividend.
        denominator: The divisor.
        default: Value to return if ``denominator == 0`` (default ``0.0``).

    Returns:
        Result of the division, or ``default`` if the denominator is 0.

    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, default=float("nan"))
        nan
    """
    if denominator == 0:
        return default
    return numerator / denominator


def round_if_close(
    value: float,
    threshold: float = 1e-9,
) -> float:
    """Round a float to 0.0 if it is within ``threshold`` of 0.

    Useful for cleaning up floating-point artifacts near zero.

    Args:
        value: The value to check.
        threshold: Tolerance around zero (default ``1e-9``).

    Returns:
        ``0.0`` if ``abs(value) <= threshold``, otherwise ``value`` unchanged.

    Example:
        >>> round_if_close(1e-12)
        0.0
        >>> round_if_close(1e-9)
        0.0
        >>> round_if_close(0.5)
        0.5
    """
    if abs(value) <= threshold:
        return 0.0
    return value 