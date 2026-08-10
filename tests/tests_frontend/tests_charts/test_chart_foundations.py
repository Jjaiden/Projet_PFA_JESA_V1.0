"""Tests des utilitaires, palette, theme et classe de base des graphiques."""

from __future__ import annotations

import pytest
import plotly.graph_objects as go

from charts.base import BaseChart
from charts.palette import get_maturity_color, hex_to_rgba, is_valid_hex
from charts.theme import apply_theme, export_config
from charts.utils import clamp_percentage, normalize, validate_same_length


class _DemoChart(BaseChart):
    def _build(self) -> None:
        self.figure.add_trace(go.Bar(x=["A"], y=[1]))


def test_base_chart_builds_a_figure() -> None:
    chart = _DemoChart(title="Demo")

    assert chart.built is True
    assert len(chart.figure.data) == 1


def test_theme_and_export_configuration_are_valid() -> None:
    figure = apply_theme(go.Figure())
    config = export_config(width=600, height=400, format="svg")

    assert figure.layout.template is not None
    assert config == {"width": 600, "height": 400, "scale": 2.0, "format": "svg"}


def test_palette_and_chart_helpers() -> None:
    assert is_valid_hex("#2563EB")
    assert hex_to_rgba("#2563EB", 0.5) == "rgba(37, 99, 235, 0.5)"
    assert get_maturity_color(3) == "#EAB308"
    assert normalize([10, 20, 30]) == [0.0, 50.0, 100.0]
    assert clamp_percentage(120) == 100.0

    with pytest.raises(ValueError, match="same length"):
        validate_same_length(["A"], [1, 2])
