"""Tests de contrat pour le composant HeatmapChart."""

from __future__ import annotations

import math

import pytest

from charts import HeatmapChart


def test_heatmap_chart_creates_expected_matrix_trace() -> None:
    figure = HeatmapChart(
        matrix=[
            [85, 72, 65],
            [90, 88, 70],
            [60, 75, 95],
        ],
        row_labels=["Strategy", "Technology", "People"],
        col_labels=["Q1", "Q2", "Q3"],
        title="Maturity Heatmap",
    ).create()

    assert len(figure.data) == 1
    assert list(figure.data[0].x) == ["Q1", "Q2", "Q3"]
    assert list(figure.data[0].y) == ["Strategy", "Technology", "People"]
    assert figure.data[0].showscale is True
    assert figure.data[0].z[0][0] == 85


def test_heatmap_chart_handles_missing_values_and_custom_scale() -> None:
    figure = HeatmapChart(
        matrix=[[1, None], [3, 4]],
        row_labels=["A", "B"],
        col_labels=["X", "Y"],
        colorscale=[(0, "#EF4444"), (0.5, "#F59E0B"), (1, "#10B981")],
        missing_value_color="#94A3B8",
    ).create()

    assert len(figure.data) == 2
    assert [list(entry) for entry in figure.data[0].colorscale] == [
        [0, "#EF4444"],
        [0.5, "#F59E0B"],
        [1, "#10B981"],
    ]
    assert math.isnan(figure.data[0].z[0][1])
    assert [list(entry) for entry in figure.data[1].colorscale] == [
        [0, "#94A3B8"],
        [1, "#94A3B8"],
    ]


def test_heatmap_chart_rejects_inconsistent_row_lengths() -> None:
    with pytest.raises(ValueError, match="All rows in matrix must have the same length"):
        HeatmapChart(
            matrix=[[1, 2], [3]],
            row_labels=["A", "B"],
            col_labels=["X", "Y"],
        ).create()


def test_heatmap_chart_rejects_duplicate_labels() -> None:
    with pytest.raises(ValueError, match="Duplicate row label"):
        HeatmapChart(
            matrix=[[1, 2], [3, 4]],
            row_labels=["A", "A"],
            col_labels=["X", "Y"],
        ).create()
