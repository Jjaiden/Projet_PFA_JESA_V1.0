"""Unit tests for the DecisionMatrix chart component."""

from __future__ import annotations

import pytest
import plotly.graph_objects as go

from charts.decision_matrix import DecisionMatrix, Recommendation


def _sample_recommendations() -> list[Recommendation]:
    return [
        Recommendation(name="Deploy MES", impact=92, effort=81, category="Technology"),
        Recommendation(name="Train Staff", impact=75, effort=30, category="People"),
        Recommendation(name="Upgrade ERP", impact=60, effort=85, category="Technology"),
        Recommendation(name="Audit Process", impact=40, effort=25, category="Process"),
    ]


def test_decision_matrix_builds_figure() -> None:
    recs = _sample_recommendations()
    matrix = DecisionMatrix(recommendations=recs, title="Prioritisation")
    fig = matrix.create()

    assert isinstance(fig, go.Figure)
    # one trace per unique category (Technology, People, Process)
    assert len(fig.data) == 3
    # four quadrant background rectangles (there may also be line shapes)
    assert hasattr(fig.layout, "shapes")
    rect_count = sum(1 for s in fig.layout.shapes if getattr(s, "type", None) == "rect")
    assert rect_count == 4
    # quadrant annotations present
    assert hasattr(fig.layout, "annotations")
    assert len(fig.layout.annotations) == 4
    # axis ranges default to 0-100
    assert list(fig.layout.xaxis.range) == [0.0, 100.0]
    assert list(fig.layout.yaxis.range) == [0.0, 100.0]


def test_empty_recommendations_raises() -> None:
    matrix = DecisionMatrix(recommendations=[])
    with pytest.raises(ValueError, match="must not be empty"):
        matrix.create()


def test_duplicate_names_raise() -> None:
    recs = [
        Recommendation(name="Same", impact=10, effort=20, category="A"),
        Recommendation(name="Same", impact=30, effort=40, category="B"),
    ]
    matrix = DecisionMatrix(recommendations=recs)
    with pytest.raises(ValueError, match="Duplicate recommendation name"):
        matrix.create()


def test_category_colors_missing_entry_raises() -> None:
    recs = _sample_recommendations()
    # provide a mapping missing the 'People' category
    matrix = DecisionMatrix(recommendations=recs, category_colors={"Technology": "#ff0000", "Process": "#00ff00"})
    with pytest.raises(ValueError, match="category_colors is missing"):
        matrix.create()


def test_hover_template_type_validation() -> None:
    recs = _sample_recommendations()
    matrix = DecisionMatrix(recommendations=recs, hover_template=123)  # invalid type
    with pytest.raises(TypeError, match="hover_template must be str or None"):
        matrix.create()
