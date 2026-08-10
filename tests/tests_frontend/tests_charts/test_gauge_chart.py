"""Tests du composant GaugeChart."""

from __future__ import annotations

import pytest

from charts import GaugeChart


def test_gauge_chart_creates_indicator() -> None:
    figure = GaugeChart(value=72, title="Score", threshold=70).create()

    assert len(figure.data) == 1
    assert figure.data[0].value == 72
    assert figure.data[0].gauge.axis.range == (0.0, 100.0)


@pytest.mark.parametrize("value", [-1, 101])
def test_gauge_chart_rejects_values_outside_bounds(value: float) -> None:
    with pytest.raises(ValueError, match="must be between"):
        GaugeChart(value=value).create()
