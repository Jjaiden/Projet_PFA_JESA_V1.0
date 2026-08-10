# JESA_DMAT/utils/helpers.py
"""
Generic Python helper functions for the JESA DMAT application.

This module provides pure, reusable utilities that are independent
of any business domain. They can be safely imported and used in any
Python project without modification.

No external dependencies are required beyond the standard library.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any, Optional, TypeVar

from utils.logger import get_logger

__all__ = [
    # Frontend functions
    "is_none_or_empty",
    "ensure_list",
    "flatten",
    "unique",
    "chunk",
    "safe_cast",
    "coalesce",
    "safe_get",
    "merge_dicts",
    "deep_copy",
    "noop",
    # Backend functions
    "normalize_text",
    "normalize_id",
    "is_blank",
    "safe_int",
    "safe_float",
    "is_close",
    "clamp",
    "unique_preserve_order",
    "chunked",
    "get_nested",
    "first_not_none",
    "format_number",
    "format_percentage",
]

_logger = get_logger(__name__)
T = TypeVar("T")

# ----------------------------------------------------------------------
# Value inspection
# ----------------------------------------------------------------------

def is_none_or_empty(value: Any) -> bool:
    """Check whether a value is ``None`` or an empty collection/string.

    Uses :class:`~collections.abc.Collection` to detect empty containers,
    making the function compatible with any collection type that
    implements ``__len__``.

    Args:
        value: Any Python object.

    Returns:
        ``True`` if the value is ``None``, an empty string (including
        whitespace-only strings), or an empty collection.
        ``False`` otherwise.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Collection):
        return len(value) == 0
    return False


def is_blank(value: Any) -> bool:
    """
    Return True if a value is empty or equivalent to an empty value.

    Args:
        value: Any Python object.

    Returns:
        ``True`` if the value is ``None`` or an empty/whitespace string.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


# ----------------------------------------------------------------------
# List helpers
# ----------------------------------------------------------------------

def ensure_list(value: Any) -> list[Any]:
    """Wrap a value in a list if it is not already list-like.

    Args:
        value: Any Python object.

    Returns:
        - A copy of ``value`` if it is already a :class:`list`.
        - A list of elements if ``value`` is any non-string, non-mapping
          iterable (e.g. ``tuple``, ``set``, ``range``).
        - A list containing the single element otherwise.
        - An empty list if ``value`` is ``None``.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        return list(value)
    return [value]


def flatten(iterable: Iterable[Any]) -> list[Any]:
    """Recursively flatten a nested iterable into a single list.

    Treats strings, bytes, and mappings as leaf values (they are not
    further flattened).

    Args:
        iterable: Any iterable that may contain nested iterables.

    Returns:
        A flat list of all leaf elements.
    """
    result: list[Any] = []
    for item in iterable:
        if (
            isinstance(item, Iterable)
            and not isinstance(item, (str, bytes, Mapping))
        ):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def unique(sequence: Sequence[Any]) -> list[Any]:
    """Remove duplicates from a sequence while preserving order.

    **Important:** All elements must be hashable (e.g. numbers, strings,
    tuples). Non-hashable elements (like lists or dicts) will raise a
    :class:`TypeError` with a descriptive message.

    Args:
        sequence: Any sequence of hashable elements.

    Returns:
        A list of unique elements in the order they first appear.

    Raises:
        TypeError: If any element is not hashable.
    """
    seen: set[Any] = set()
    result: list[Any] = []
    for item in sequence:
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            raise TypeError(
                "unique() only supports hashable elements. "
                f"Got unhashable type: {type(item).__name__}"
            ) from None
    return result


def unique_preserve_order(values: Iterable[Any]) -> list[Any]:
    """
    Remove duplicates while preserving order.

    This version handles unhashable elements by falling back to
    membership testing in the result list.

    Args:
        values: Any iterable.

    Returns:
        A list of unique elements in their original order.
    """
    result: list[Any] = []
    seen: set[Any] = set()

    for value in values:
        try:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        except TypeError:
            # Unhashable: fall back to membership in result list
            if value not in result:
                result.append(value)

    return result


def chunk(sequence: Sequence[Any], size: int) -> list[list[Any]]:
    """Split a sequence into chunks of a given size.

    Args:
        sequence: The sequence to split.
        size: Maximum chunk size. Must be a positive integer.

    Returns:
        A list of chunks, each a list of up to ``size`` elements.

    Raises:
        TypeError: If ``size`` is not an integer.
        ValueError: If ``size`` is not positive.
    """
    if not isinstance(size, int):
        raise TypeError(f"Chunk size must be an integer, got {type(size).__name__}")
    if size <= 0:
        raise ValueError(f"Chunk size must be positive, got {size}")
    return [list(sequence[i : i + size]) for i in range(0, len(sequence), size)]


# Alias for backward compatibility
chunked = chunk


# ----------------------------------------------------------------------
# Type casting and value fallback
# ----------------------------------------------------------------------

def safe_cast(value: Any, target_type: type[T], default: T | Any = None) -> T | Any:
    """Attempt to cast a value to a target type without raising.

    Args:
        value: The value to cast.
        target_type: A callable type constructor (e.g. ``int``, ``float``).
        default: Value to return if the cast fails (default ``None``).

    Returns:
        ``target_type(value)`` on success, or ``default`` on failure.
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        _logger.debug(
            "safe_cast failed for value=%r, target=%s, returning default.",
            value,
            getattr(target_type, "__name__", repr(target_type)),
        )
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Convert a value to an integer safely.

    Unlike direct int() conversion, decimal values like 3.5 are NOT
    silently truncated to 3; they return the default.

    Examples:
        safe_int(3)       -> 3
        safe_int(3.0)     -> 3
        safe_int("3")     -> 3
        safe_int("3.0")   -> 3
        safe_int("3.5")   -> default
        safe_int(None)    -> default
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            return default
        return int(value) if value.is_integer() else default

    text = normalize_text(value)
    if not text:
        return default

    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(numeric):
        return default

    if not numeric.is_integer():
        return default

    return int(numeric)


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Convert a value to a float safely.

    Args:
        value: Any value.
        default: Value to return if conversion fails.

    Returns:
        The float value or the default.
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return default

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(numeric):
        return default

    return numeric


# ----------------------------------------------------------------------
# Comparisons and clamping
# ----------------------------------------------------------------------

def is_close(value_a: Any, value_b: Any, tolerance: float = 1e-9) -> bool:
    """
    Compare two numeric values with a tolerance.

    Args:
        value_a: First numeric value.
        value_b: Second numeric value.
        tolerance: Maximum allowed absolute difference.

    Returns:
        True if the values are within tolerance, False otherwise.
    """
    a = safe_float(value_a)
    b = safe_float(value_b)

    if a is None or b is None:
        return False

    if tolerance < 0:
        raise ValueError("tolerance must be non‑negative.")

    return abs(a - b) <= tolerance


def clamp(value: Any, minimum: float, maximum: float) -> float:
    """
    Clamp a numeric value to a given interval.

    Args:
        value: Value to clamp.
        minimum: Lower bound.
        maximum: Upper bound.

    Returns:
        The clamped value.

    Raises:
        ValueError: If the value cannot be converted to a float or if
            minimum > maximum.
    """
    numeric = safe_float(value)

    if numeric is None:
        raise ValueError(f"Invalid numeric value: {value!r}")

    if minimum > maximum:
        raise ValueError("minimum cannot be greater than maximum.")

    return max(minimum, min(numeric, maximum))


# ----------------------------------------------------------------------
# Dictionary helpers
# ----------------------------------------------------------------------

def safe_get(mapping: Mapping[Any, Any], key: Any, default: Any = None) -> Any:
    """Safely retrieve a value from a mapping.

    Similar to :meth:`dict.get`, but enforces that the first argument
    is a :class:`~collections.abc.Mapping`.

    Args:
        mapping: Any mapping (e.g. ``dict``, ``OrderedDict``).
        key: The key to look up.
        default: Value to return if the key is missing (default ``None``).

    Returns:
        The stored value, or ``default``.

    Raises:
        TypeError: If ``mapping`` is not a :class:`~collections.abc.Mapping`.
    """
    if not isinstance(mapping, Mapping):
        raise TypeError(f"Expected a Mapping, got {type(mapping).__name__}")
    return mapping.get(key, default)


def get_nested(data: Any, *keys: str, default: Any = None) -> Any:
    """
    Retrieve a value from a nested dictionary.

    Example:
        data = {"site": {"name": "Plant A"}}
        get_nested(data, "site", "name") -> "Plant A"
    """
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]

    return current


def merge_dicts(*dicts: Mapping[Any, Any]) -> dict[Any, Any]:
    """Merge multiple mappings into a new dictionary.

    Later mappings override keys from earlier ones. The original
    mappings are never modified.

    Args:
        *dicts: Any number of :class:`~collections.abc.Mapping` objects.

    Returns:
        A new dictionary combining all input mappings.

    Raises:
        TypeError: If any argument is not a mapping.
    """
    result: dict[Any, Any] = {}
    for mapping in dicts:
        if not isinstance(mapping, Mapping):
            raise TypeError(f"Expected a Mapping, got {type(mapping).__name__}")
        result.update(mapping)
    return result


# ----------------------------------------------------------------------
# Text normalization and identifiers
# ----------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    """
    Convert a value to clean text.

    - None -> ""
    - leading/trailing whitespace removed
    - multiple spaces collapsed to a single space

    Example:
        normalize_text("  Niveau   avancé  ") -> "Niveau avancé"
    """
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    return " ".join(text.split())


def normalize_id(value: Any) -> str:
    """
    Normalize a business or technical identifier.

    Identifiers are treated as strings.
    """
    return normalize_text(value)


# ----------------------------------------------------------------------
# Value selection
# ----------------------------------------------------------------------

def coalesce(*values: Any) -> Any:
    """Return the first value that is not ``None``.

    Args:
        *values: Any number of positional arguments.

    Returns:
        The first non-``None`` argument, or ``None`` if all are ``None``.
    """
    for v in values:
        if v is not None:
            return v
    return None


# Alias for backward compatibility
first_not_none = coalesce


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

def format_number(value: Any, decimals: int = 2) -> str:
    """
    Format a numeric value for display or report generation.

    Example:
        format_number(62.456, 1) -> "62.5"
    """
    if decimals < 0:
        raise ValueError("decimals must be non‑negative.")

    numeric = safe_float(value)

    if numeric is None:
        return ""

    return f"{numeric:.{decimals}f}"


def format_percentage(value: Any, decimals: int = 1) -> str:
    """
    Format a numeric value as a percentage.

    This function assumes the value is already expressed as a percentage
    (e.g. 62.4 -> "62.4 %").
    """
    formatted = format_number(value, decimals)

    if not formatted:
        return ""

    return f"{formatted} %"


# ----------------------------------------------------------------------
# Miscellaneous
# ----------------------------------------------------------------------

def deep_copy(obj: T) -> T:
    """Create a deep copy of any Python object.

    Wraps :func:`copy.deepcopy` with a debug log for traceability.

    Args:
        obj: The object to copy.

    Returns:
        A deep copy of ``obj``.
    """
    _logger.debug("Creating deep copy of object type: %s", type(obj).__name__)
    return deepcopy(obj)


def noop(*args: Any, **kwargs: Any) -> None:
    """No-operation function.

    Accepts any arguments and does nothing. Useful as a default
    callback or placeholder.
    """
    pass