"""Tests de contrat pour le composant LineChart."""

from __future__ import annotations

import pytest

from charts import LineChart


def test_single_series_line_chart_creates_expected_trace() -> None:
    figure = LineChart(x=["T1", "T2", "T3"], y=[55, 60, 68], title="DMI").create()

    assert len(figure.data) == 1
    assert list(figure.data[0].x) == ["T1", "T2", "T3"]
    assert list(figure.data[0].y) == [55, 60, 68]
    assert figure.data[0].mode == "lines+markers"


def test_multi_series_supports_smoothing_fill_and_secondary_axis() -> None:
    figure = LineChart(
        x=["T1", "T2", "T3"],
        y=[[55, 60, 68], [70, 70, 70]],
        series_names=["Actual", "Target"],
        smooth=True,
        fill_area=True,
        secondary_y=True,
    ).create()

    assert len(figure.data) == 2
    assert figure.data[0].line.shape == "spline"
    assert figure.data[0].fill == "tozeroy"
    assert figure.data[1].yaxis == "y2"
    assert figure.layout.yaxis2.showgrid is False


def test_line_chart_rejects_invalid_annotations_and_secondary_axis_usage() -> None:
    with pytest.raises(ValueError, match="missing required keys"):
        LineChart(x=["T1", "T2"], y=[55, 60], annotations=[{"text": "Review"}]).create()

    with pytest.raises(ValueError, match="requires at least two"):
        LineChart(x=["T1", "T2"], y=[55, 60], secondary_y=True).create()


def test_line_chart_rejects_duplicate_x_labels() -> None:
    with pytest.raises(ValueError, match="Duplicate x label"):
        LineChart(x=["T1", "T1"], y=[55, 60]).create()


def test_line_chart_applies_custom_line_colors_and_marker_color() -> None:
    figure = LineChart(
        x=["T1", "T2", "T3"],
        y=[[55, 60, 68], [70, 72, 75]],
        series_names=["Actual", "Target"],
        line_colors=["#FF0000", "#00FF00"],
        marker_color="#0000FF",
        show_markers=True,
    ).create()

    assert len(figure.data) == 2
    assert figure.data[0].line.color == "#FF0000"
    assert figure.data[0].marker.color == "#0000FF"
    assert figure.data[1].line.color == "#00FF00"


def test_line_chart_rejects_invalid_line_style() -> None:
    with pytest.raises(ValueError, match="line_style must be one of"):
        LineChart(x=["T1", "T2"], y=[55, 60], line_style="invalid").create()


def test_line_chart_rejects_insufficient_line_colors() -> None:
    with pytest.raises(ValueError, match="line_colors must provide at least"):
        LineChart(
            x=["T1", "T2", "T3"],
            y=[[55, 60, 68], [70, 72, 75]],
            line_colors=["#FF0000"],
        ).create()
