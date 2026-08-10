"""Tests de contrat pour le composant RadarChart."""

from __future__ import annotations

import pytest

from charts import RadarChart


def test_radar_chart_creates_a_closed_single_trace() -> None:
    """Le radar produit une trace Plotly fermée pour les cinq piliers."""
    chart = RadarChart(
        categories=["Infrastructure", "Operations", "Data", "Governance", "People"],
        values=[70, 55, 60, 65, 62],
        min_value=0,
        max_value=100,
        title="Profil de maturite",
    )

    figure = chart.create()

    assert len(figure.data) == 1
    assert list(figure.data[0].r) == [70, 55, 60, 65, 62, 70]
    assert list(figure.data[0].theta) == [
        "Infrastructure",
        "Operations",
        "Data",
        "Governance",
        "People",
        "Infrastructure",
    ]


def test_radar_chart_rejects_fewer_than_three_categories() -> None:
    """Un radar doit toujours représenter au moins trois dimensions."""
    chart = RadarChart(categories=["A", "B"], values=[10, 20])

    with pytest.raises(ValueError, match="at least 3"):
        chart.create()
