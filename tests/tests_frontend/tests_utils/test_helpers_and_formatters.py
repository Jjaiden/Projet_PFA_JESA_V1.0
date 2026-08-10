"""Tests des fonctions utilitaires pures et des formateurs."""

from __future__ import annotations

from utils.formatters import (
    camel_to_title,
    format_number,
    format_percentage,
    snake_to_title,
    truncate,
)
from utils.helpers import chunk, deep_copy, flatten, safe_cast, unique


def test_helpers_transform_data_without_mutating_input() -> None:
    original = {"values": [1, 2]}
    copied = deep_copy(original)
    copied["values"].append(3)

    assert flatten([1, [2, [3]]]) == [1, 2, 3]
    assert unique([3, 2, 3, 1]) == [3, 2, 1]
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert safe_cast("invalid", int, default=0) == 0
    assert original == {"values": [1, 2]}


def test_formatters_produce_display_ready_values() -> None:
    assert format_number(1234567.8) == "1 234 567.80"
    assert format_percentage(0.875) == "87.5%"
    assert snake_to_title("digital_maturity_score") == "Digital Maturity Score"
    assert camel_to_title("digitalMaturityScore") == "Digital Maturity Score"
    assert truncate("abcdefgh", 5) == "ab..."
