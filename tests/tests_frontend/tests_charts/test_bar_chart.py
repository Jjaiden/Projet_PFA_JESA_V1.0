"""Tests de contrat pour le composant BarChart."""

from __future__ import annotations

import pytest

from charts import BarChart


def test_single_series_preserves_order_by_default() -> None:
    figure = BarChart(categories=["A", "B"], values=[1, 2]).create()

    assert list(figure.data[0].x) == ["A", "B"]
    assert list(figure.data[0].y) == [1, 2]
    assert figure.layout.barmode == "group"


def test_single_series_sorts_only_when_requested() -> None:
    figure = BarChart(categories=["A", "B", "C"], values=[10, 30, 20], sort=True).create()

    assert list(figure.data[0].x) == ["B", "C", "A"]
    assert list(figure.data[0].y) == [30, 20, 10]


@pytest.mark.parametrize(
    ("mode", "expected_barmode"),
    [("grouped", "group"), ("stacked", "stack"), ("relative", "relative")],
)
def test_multi_series_maps_application_modes_to_plotly(mode: str, expected_barmode: str) -> None:
    figure = BarChart(
        categories=["Infrastructure", "Data"],
        values=[[50, 60], [70, 80]],
        series_names=["Current", "Target"],
        mode=mode,
    ).create()

    assert len(figure.data) == 2
    assert figure.layout.barmode == expected_barmode
    assert figure.layout.showlegend is True


def test_horizontal_bar_uses_values_on_x_axis() -> None:
    figure = BarChart(
        categories=["Infrastructure", "Data"],
        values=[50, 60],
        orientation="horizontal",
    ).create()

    assert figure.data[0].orientation == "h"
    assert list(figure.data[0].x) == [50, 60]
    assert list(figure.data[0].y) == ["Infrastructure", "Data"]


def test_bar_chart_rejects_duplicate_categories() -> None:
    with pytest.raises(ValueError, match="Duplicate category"):
        BarChart(categories=["Data", "Data"], values=[50, 60]).create()
