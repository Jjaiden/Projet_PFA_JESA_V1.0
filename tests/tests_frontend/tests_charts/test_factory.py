# JESA_DMAT/tests/test_factory.py
"""
Tests for the ChartFactory in charts/factory.py.
"""

from __future__ import annotations

import pytest

from charts.decision_matrix import Recommendation
from charts.factory import ChartFactory


def test_factory_supported_types() -> None:
    """Test that supported_types returns the correct list."""
    types = ChartFactory.supported_types()
    expected = ["gauge", "radar", "bar", "line", "heatmap", "decision_matrix"]
    assert set(types) == set(expected)


def test_factory_create_gauge() -> None:
    """Test creating a gauge chart via factory."""
    fig = ChartFactory.create("gauge", {"value": 75, "title": "Test Gauge"})
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.data[0].value == 75


def test_factory_create_radar() -> None:
    """Test creating a radar chart via factory."""
    fig = ChartFactory.create(
        "radar",
        {
            "categories": ["A", "B", "C"],
            "values": [10, 20, 30],
            "title": "Test Radar",
        },
    )
    assert fig is not None
    assert len(fig.data) == 1
    assert list(fig.data[0].r) == [10, 20, 30, 10]  # closed polygon


def test_factory_create_bar() -> None:
    """Test creating a bar chart via factory."""
    fig = ChartFactory.create(
        "bar",
        {"categories": ["X", "Y", "Z"], "values": [1, 2, 3], "title": "Test Bar"},
    )
    assert fig is not None
    assert len(fig.data) == 1
    assert list(fig.data[0].x) == ["X", "Y", "Z"]
    assert list(fig.data[0].y) == [1, 2, 3]


def test_factory_create_line() -> None:
    """Test creating a line chart via factory."""
    fig = ChartFactory.create(
        "line",
        {"x": ["A", "B", "C"], "y": [10, 20, 30], "title": "Test Line"},
    )
    assert fig is not None
    assert len(fig.data) == 1
    assert list(fig.data[0].x) == ["A", "B", "C"]
    assert list(fig.data[0].y) == [10, 20, 30]


def test_factory_create_heatmap() -> None:
    """Test creating a heatmap chart via factory."""
    fig = ChartFactory.create(
        "heatmap",
        {
            "matrix": [[1, 2], [3, 4]],
            "row_labels": ["R1", "R2"],
            "col_labels": ["C1", "C2"],
            "title": "Test Heatmap",
        },
    )
    assert fig is not None
    assert len(fig.data) == 1
    assert list(fig.data[0].x) == ["C1", "C2"]
    assert list(fig.data[0].y) == ["R1", "R2"]


def test_factory_create_decision_matrix() -> None:
    """Test creating a decision matrix via factory with Recommendation objects."""
    recs = [
        Recommendation(name="A", impact=80, effort=30, category="Tech"),
        Recommendation(name="B", impact=60, effort=70, category="People"),
    ]
    fig = ChartFactory.create(
        "decision_matrix",
        {"recommendations": recs, "title": "Test Matrix"},
    )
    assert fig is not None
    # Number of traces = number of unique categories (2)
    assert len(fig.data) == 2


def test_factory_create_decision_matrix_from_dicts_unsupported() -> None:
    """
    Test that passing dicts to recommendations raises TypeError,
    because DecisionMatrix expects Recommendation objects.
    """
    rec_dicts = [
        {"name": "A", "impact": 80, "effort": 30, "category": "Tech"},
        {"name": "B", "impact": 60, "effort": 70, "category": "People"},
    ]
    with pytest.raises(TypeError):
        ChartFactory.create(
            "decision_matrix",
            {"recommendations": rec_dicts, "title": "Test Matrix Dict"},
        )


def test_factory_unknown_type() -> None:
    """Test that an unknown chart type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown chart type"):
        ChartFactory.create("unknown", {})


def test_factory_missing_required_params() -> None:
    """Test that missing required parameters raise TypeError (from chart class)."""
    # Radar requires categories and values
    with pytest.raises(TypeError, match="missing"):
        ChartFactory.create("radar", {"title": "Missing params"})

    # Gauge requires value
    with pytest.raises(TypeError, match="missing"):
        ChartFactory.create("gauge", {"title": "Missing value"})