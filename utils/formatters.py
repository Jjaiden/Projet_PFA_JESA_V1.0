"""
Generic formatting utilities for the JESA DMAT application.

Provides a collection of pure, reusable functions that transform
Python values into display-friendly strings. All functions are
stateless, deterministic, and free of any business logic.

This module is **completely generic** and can be reused in any Python
project without modification.

Usage::

    from utils.formatters import format_percentage, format_number, format_date

    print(format_percentage(0.875))          # "87.5%"
    print(format_number(1234567.89))         # "1 234 567.89"
    print(format_date(some_date))            # "2026-08-06"
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime, time
from typing import Literal

__all__ = [
    "format_number",
    "format_percentage",
    "format_currency",
    "format_bytes",
    "format_duration",
    "format_datetime",
    "format_date",
    "format_time",
    "format_bool",
    "format_yes_no",
    "format_none",
    "truncate",
    "title_case",
    "sentence_case",
    "snake_to_title",
    "camel_to_title",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DECIMAL_UNITS: tuple[str, ...] = ("B", "KB", "MB", "GB", "TB", "PB")
_BINARY_UNITS: tuple[str, ...] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
_SECONDS_PER_MINUTE: int = 60
_SECONDS_PER_HOUR: int = 3600
_SECONDS_PER_DAY: int = 86400

# CamelCase splitting regex – handles "XMLParser" → "XML Parser"
_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

# Multiple underscore collapsing regex for snake_to_title
_MULTI_UNDERSCORE_RE = re.compile(r"_+")


# ======================================================================
# Numeric formatters
# ======================================================================


def format_number(
    value: int | float,
    decimals: int = 2,
    thousands_sep: str = " ",
    decimal_sep: str = ".",
) -> str:
    """Format a number with configurable separators.

    Args:
        value: The number to format.
        decimals: Number of decimal places (default ``2``). Must be >= 0.
        thousands_sep: Thousands separator (default ``" "``).
        decimal_sep: Decimal separator (default ``"."``).

    Returns:
        Formatted string representation of the number.

    Raises:
        TypeError: If ``value`` is not an int or float.
        ValueError: If ``decimals`` is negative.

    Example:
        >>> format_number(1234567.89)
        '1 234 567.89'
        >>> format_number(-1000, thousands_sep=",", decimal_sep=".")
        '-1,000.00'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"Expected int or float, got {type(value).__name__}"
        )
    if decimals < 0:
        raise ValueError(f"decimals must be >= 0, got {decimals}")

    if decimals <= 0:
        formatted = f"{value:.0f}"
        int_part = formatted
        frac_part = ""
    else:
        formatted = f"{value:.{decimals}f}"
        int_part, frac_part = formatted.split(".")

    # Insert thousands separator
    sign = ""
    if int_part.startswith("-"):
        sign = "-"
        int_part = int_part[1:]

    if len(int_part) > 3:
        chunks = []
        while int_part:
            chunks.append(int_part[-3:])
            int_part = int_part[:-3]
        int_part = thousands_sep.join(reversed(chunks))

    result = sign + int_part
    if frac_part:
        result += decimal_sep + frac_part
    return result


def format_percentage(
    value: int | float,
    decimals: int = 1,
    include_sign: bool = False,
    *,
    scaled: bool = False,
) -> str:
    """Format a number as a percentage.

    Args:
        value: The number to format.
        decimals: Number of decimal places (default ``1``). Must be >= 0.
        include_sign: Prefix positive values with ``'+'`` (default ``False``).
        scaled: If ``True``, ``value`` is already in percent (e.g. 85 → "85%").
            If ``False``, ``value`` is a ratio (e.g. 0.85 → "85%"; default).

    Returns:
        Formatted percentage string ending with ``'%'``.

    Raises:
        TypeError: If ``value`` is not numeric.
        ValueError: If ``decimals`` is negative.

    Example:
        >>> format_percentage(0.875)
        '87.5%'
        >>> format_percentage(85, scaled=True, decimals=0)
        '85%'
        >>> format_percentage(12.456, decimals=2)
        '12.46%'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"Expected int or float, got {type(value).__name__}"
        )
    if decimals < 0:
        raise ValueError(f"decimals must be >= 0, got {decimals}")

    ratio = value if scaled else value * 100

    if decimals <= 0:
        formatted = f"{ratio:.0f}"
    else:
        formatted = f"{ratio:.{decimals}f}"

    if include_sign and ratio > 0:
        formatted = "+" + formatted

    return f"{formatted}%"


def format_currency(
    value: int | float,
    symbol: str = "$",
    position: Literal["before", "after"] = "before",
    decimals: int = 2,
    thousands_sep: str = ",",
    decimal_sep: str = ".",
) -> str:
    """Format a number as a currency string.

    Args:
        value: The monetary amount.
        symbol: Currency symbol (default ``"$"``).
        position: Where to place the symbol – ``"before"`` or ``"after"``
            (default ``"before"``).
        decimals: Decimal places (default ``2``). Must be >= 0.
        thousands_sep: Thousands separator (default ``","``).
        decimal_sep: Decimal separator (default ``"."``).

    Returns:
        Formatted currency string.

    Raises:
        TypeError: If ``value`` is not numeric.
        ValueError: If ``position`` is not ``"before"`` or ``"after"``,
            or if ``decimals`` is negative.

    Example:
        >>> format_currency(1250.0)
        '$1,250.00'
        >>> format_currency(1250, symbol="€", position="after", thousands_sep=" ")
        '1 250.00 €'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"Expected int or float, got {type(value).__name__}"
        )
    if position not in ("before", "after"):
        raise ValueError(
            f"position must be 'before' or 'after', got {position!r}"
        )
    if decimals < 0:
        raise ValueError(f"decimals must be >= 0, got {decimals}")

    num = format_number(
        value,
        decimals=decimals,
        thousands_sep=thousands_sep,
        decimal_sep=decimal_sep,
    )
    return f"{symbol}{num}" if position == "before" else f"{num} {symbol}"


def format_bytes(
    value: int,
    decimals: int = 1,
    binary: bool = False,
) -> str:
    """Convert a byte count into a human-readable string.

    Args:
        value: Number of bytes (must be non-negative).
        decimals: Decimal places for the result (default ``1``). Must be >= 0.
        binary: If ``True`` use binary units (1024 → KiB, MiB, etc.),
            otherwise decimal units (1000 → KB, MB, etc.; default).

    Returns:
        Human-readable string like ``"1.5 MB"`` or ``"1.4 MiB"``.

    Raises:
        TypeError: If ``value`` is not an int.
        ValueError: If ``value`` is negative or ``decimals`` is negative.

    Example:
        >>> format_bytes(1500)
        '1.5 KB'
        >>> format_bytes(1500, binary=True)
        '1.5 KiB'
        >>> format_bytes(0)
        '0 B'
    """
    if not isinstance(value, int):
        raise TypeError(f"Expected int, got {type(value).__name__}")
    if value < 0:
        raise ValueError("Byte count must be non-negative")
    if decimals < 0:
        raise ValueError(f"decimals must be >= 0, got {decimals}")

    if value == 0:
        return "0 B"

    divisor = 1024 if binary else 1000
    units = _BINARY_UNITS if binary else _DECIMAL_UNITS

    unit_idx = min(
        int(math.log(value) / math.log(divisor)),
        len(units) - 1,
    )
    converted = value / (divisor ** unit_idx)

    if converted.is_integer():
        formatted = str(int(converted))
    else:
        formatted = f"{converted:.{decimals}f}"

    return f"{formatted} {units[unit_idx]}"


def format_duration(
    seconds: int | float,
    compact: bool = False,
) -> str:
    """Convert a duration in seconds into a human-readable string.

    Args:
        seconds: Duration in seconds (non-negative). Fractional seconds
            are truncated (e.g. 59.9 → 59 sec).
        compact: If ``True``, use short unit labels (``d``, ``h``, ``m``,
            ``s``). Otherwise spell them out (``day``, ``hr``, ``min``,
            ``sec``; default).

    Returns:
        Formatted duration string.

    Raises:
        TypeError: If ``seconds`` is not numeric.
        ValueError: If ``seconds`` is negative.

    Example:
        >>> format_duration(3661)
        '1 hr 1 min 1 sec'
        >>> format_duration(3661, compact=True)
        '1h 1m 1s'
        >>> format_duration(45)
        '45 sec'
    """
    if not isinstance(seconds, (int, float)):
        raise TypeError(
            f"Expected int or float, got {type(seconds).__name__}"
        )
    if seconds < 0:
        raise ValueError("Duration must be non-negative")

    total = int(seconds)

    days = total // _SECONDS_PER_DAY
    total %= _SECONDS_PER_DAY
    hours = total // _SECONDS_PER_HOUR
    total %= _SECONDS_PER_HOUR
    minutes = total // _SECONDS_PER_MINUTE
    secs = total % _SECONDS_PER_MINUTE

    parts: list[str] = []
    if compact:
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if secs or not parts:
            parts.append(f"{secs}s")
    else:
        if days:
            label = "day" if days == 1 else "days"
            parts.append(f"{days} {label}")
        if hours:
            label = "hr" if hours == 1 else "hrs"
            parts.append(f"{hours} {label}")
        if minutes:
            label = "min" if minutes == 1 else "mins"
            parts.append(f"{minutes} {label}")
        if secs or not parts:
            label = "sec" if secs == 1 else "secs"
            parts.append(f"{secs} {label}")

    return " ".join(parts)


# ======================================================================
# Date / Time formatters
# ======================================================================


def format_datetime(
    value: datetime,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a :class:`datetime.datetime` object as a string.

    Args:
        value: The datetime to format.
        fmt: :meth:`strftime` format string (default ``"%Y-%m-%d %H:%M:%S"``).

    Returns:
        Formatted datetime string.

    Raises:
        TypeError: If ``value`` is not a :class:`datetime.datetime`.

    Example:
        >>> from datetime import datetime
        >>> format_datetime(datetime(2026, 8, 6, 14, 30))
        '2026-08-06 14:30:00'
    """
    if not isinstance(value, datetime):
        raise TypeError(
            f"Expected datetime, got {type(value).__name__}"
        )
    return value.strftime(fmt)


def format_date(
    value: date,
    fmt: str = "%Y-%m-%d",
) -> str:
    """Format a :class:`datetime.date` as a string (not datetime).

    Args:
        value: The date to format. Must be a pure ``date``, not ``datetime``.
        fmt: :meth:`strftime` format string (default ``"%Y-%m-%d"``).

    Returns:
        Formatted date string.

    Raises:
        TypeError: If ``value`` is a :class:`datetime.datetime` or not a
            :class:`datetime.date`.

    Example:
        >>> from datetime import date
        >>> format_date(date(2026, 8, 6))
        '2026-08-06'
    """
    if isinstance(value, datetime) or not isinstance(value, date):
        raise TypeError(
            f"Expected date (not datetime), got {type(value).__name__}"
        )
    return value.strftime(fmt)


def format_time(
    value: time,
    fmt: str = "%H:%M:%S",
) -> str:
    """Format a :class:`datetime.time` as a string.

    Args:
        value: The time to format.
        fmt: :meth:`strftime` format string (default ``"%H:%M:%S"``).

    Returns:
        Formatted time string.

    Raises:
        TypeError: If ``value`` is not a :class:`datetime.time`.

    Example:
        >>> from datetime import time
        >>> format_time(time(14, 30, 0))
        '14:30:00'
    """
    if not isinstance(value, time):
        raise TypeError(
            f"Expected time, got {type(value).__name__}"
        )
    return value.strftime(fmt)


# ======================================================================
# Boolean / None formatters
# ======================================================================


def format_bool(
    value: bool,
    true_label: str = "True",
    false_label: str = "False",
) -> str:
    """Format a boolean value with customisable labels.

    Args:
        value: The boolean to format.
        true_label: Label for ``True`` (default ``"True"``).
        false_label: Label for ``False`` (default ``"False"``).

    Returns:
        Formatted boolean string.

    Raises:
        TypeError: If ``value`` is not a bool.

    Example:
        >>> format_bool(True)
        'True'
        >>> format_bool(False, true_label="✓", false_label="✗")
        '✗'
    """
    if not isinstance(value, bool):
        raise TypeError(f"Expected bool, got {type(value).__name__}")
    return true_label if value else false_label


def format_yes_no(
    value: bool,
    yes_label: str = "Yes",
    no_label: str = "No",
) -> str:
    """Format a boolean as Yes/No with customisable labels.

    Args:
        value: The boolean to format.
        yes_label: Label for ``True`` (default ``"Yes"``).
        no_label: Label for ``False`` (default ``"No"``).

    Returns:
        Formatted string.

    Raises:
        TypeError: If ``value`` is not a bool.

    Example:
        >>> format_yes_no(True)
        'Yes'
        >>> format_yes_no(False, yes_label="Oui", no_label="Non")
        'Non'
    """
    if not isinstance(value, bool):
        raise TypeError(f"Expected bool, got {type(value).__name__}")
    return yes_label if value else no_label


def format_none(
    value: object,
    placeholder: str = "-",
) -> str:
    """Return a placeholder string when the value is ``None``.

    Args:
        value: Any Python object.
        placeholder: String to return if ``value`` is ``None``
            (default ``"-"``).

    Returns:
        The original value cast to ``str``, or ``placeholder`` if ``None``.

    Example:
        >>> format_none(None)
        '-'
        >>> format_none("Hello")
        'Hello'
        >>> format_none(None, placeholder="N/A")
        'N/A'
    """
    return placeholder if value is None else str(value)


# ======================================================================
# String formatters
# ======================================================================


def truncate(
    text: str,
    max_length: int = 50,
    suffix: str = "...",
) -> str:
    """Truncate a string to a maximum length, appending a suffix.

    Args:
        text: The string to truncate.
        max_length: Maximum number of characters to keep (default ``50``).
            Must be at least ``len(suffix)``.
        suffix: String to append when truncation occurs (default ``"..."``).

    Returns:
        Truncated string with suffix, or the original string if it fits.

    Raises:
        TypeError: If ``text`` is not a string.
        ValueError: If ``max_length`` is less than ``len(suffix)``.

    Example:
        >>> truncate("Hello World", max_length=8)
        'Hello...'
        >>> truncate("Short", max_length=10)
        'Short'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if max_length < len(suffix):
        raise ValueError(
            f"max_length ({max_length}) must be >= len(suffix) ({len(suffix)})"
        )

    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def title_case(text: str) -> str:
    """Convert a string to Title Case.

    Uses Python's built-in :meth:`str.title` after lowercasing, then
    fixes common possessive contractions (e.g. ``"S"`` → ``"'s"``).

    **Note:** :meth:`str.title` does not handle special cases like
    ``"McDonald"``, ``"iPhone"``, or ``"NASA"``. For those, a dedicated
    library or custom rules are required.

    Args:
        text: The string to convert.

    Returns:
        Title-cased string.

    Raises:
        TypeError: If ``text`` is not a string.

    Example:
        >>> title_case("hello world")
        'Hello World'
        >>> title_case("O'CONNOR")
        "O'Connor"
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    result = text.lower().title()
    result = result.replace("'S", "'s")
    return result


def sentence_case(text: str) -> str:
    """Capitalise the first character of a string while preserving whitespace.

    The rest of the string is lowercased. Leading and trailing whitespace
    are preserved, and capitalisation is applied to the first non-whitespace
    character.

    **Note:** This uses simple lowercasing and does not preserve
    acronyms. For example, ``"NASA"`` becomes ``"Nasa"``.

    Args:
        text: The string to convert.

    Returns:
        Sentence-cased string.

    Raises:
        TypeError: If ``text`` is not a string.

    Example:
        >>> sentence_case("hello World")
        'Hello world'
        >>> sentence_case("   TEST   ")
        '   Test   '
        >>> sentence_case("TEST")
        'Test'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    stripped = text.strip()
    if not stripped:
        return text

    prefix = text[: len(text) - len(text.lstrip())]
    suffix = text[len(text.rstrip()) :]

    return prefix + stripped[0].upper() + stripped[1:].lower() + suffix


def snake_to_title(text: str) -> str:
    """Convert a snake_case identifier to Title Case.

    Underscores are replaced with spaces, multiple consecutive
    underscores are collapsed into a single space, leading/trailing
    underscores are stripped, and each word is capitalised.

    Args:
        text: A snake_case string.

    Returns:
        Title Case representation.

    Raises:
        TypeError: If ``text`` is not a string.

    Example:
        >>> snake_to_title("digital_maturity_assessment")
        'Digital Maturity Assessment'
        >>> snake_to_title("user__name")
        'User Name'
        >>> snake_to_title("__value__")
        'Value'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    cleaned = _MULTI_UNDERSCORE_RE.sub("_", text).strip("_")
    return cleaned.replace("_", " ").title()


def camel_to_title(text: str) -> str:
    """Convert a CamelCase or PascalCase identifier to Title Case.

    Inserts spaces before uppercase letters that follow lowercase
    letters or digits, then applies :meth:`str.title`.

    **Note:** Because :meth:`str.title` lowercases sequences of uppercase
    letters, acronyms are not preserved. For example ``"parseXML"``
    becomes ``"Parse Xml"`` (not ``"Parse XML"``). If acronym preservation
    is needed, use a dedicated library.

    Args:
        text: A CamelCase or PascalCase string.

    Returns:
        Title Case representation.

    Raises:
        TypeError: If ``text`` is not a string.

    Example:
        >>> camel_to_title("DigitalMaturityAssessment")
        'Digital Maturity Assessment'
        >>> camel_to_title("parseXML")
        'Parse Xml'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    spaced = _CAMEL_RE.sub(" ", text)
    return spaced.title()