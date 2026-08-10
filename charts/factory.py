# JESA_DMAT/charts/factory.py
"""
Chart factory for the JESA DMAT visualization package.

Provides a centralized factory to create chart figures based on a chart type
string and a dictionary of parameters. The factory uses the existing chart
classes defined in the `charts` package, ensuring consistency and reusability.

Usage:
    from charts.factory import ChartFactory

    fig = ChartFactory.create(
        chart_type="gauge",
        params={"value": 72, "title": "Maturity Score"}
    )
    fig.show()

Supported chart types:
    - "gauge"
    - "radar"
    - "bar"
    - "line"
    - "heatmap"
    - "decision_matrix"

Raises:
    ValueError: If the chart type is unknown or required parameters are missing.
    TypeError: If the parameter types are invalid (delegated to the chart class).
"""

from __future__ import annotations

from typing import Any, Dict, Literal

import plotly.graph_objects as go

from charts.bar import BarChart
from charts.decision_matrix import DecisionMatrix
from charts.gauge import GaugeChart
from charts.heatmap import HeatmapChart
from charts.line import LineChart
from charts.radar import RadarChart

# -----------------------------------------------------------------------------
# Type aliases for supported chart types
# -----------------------------------------------------------------------------
ChartType = Literal[
    "gauge",
    "radar",
    "bar",
    "line",
    "heatmap",
    "decision_matrix",
]


class ChartFactory:
    """Centralized factory for creating chart figures."""

    # Mapping from chart type string to the corresponding class.
    _CHART_CLASSES: Dict[str, Any] = {
        "gauge": GaugeChart,
        "radar": RadarChart,
        "bar": BarChart,
        "line": LineChart,
        "heatmap": HeatmapChart,
        "decision_matrix": DecisionMatrix,
    }

    @classmethod
    def create(cls, chart_type: ChartType, params: Dict[str, Any]) -> go.Figure:
        """
        Create and return a Plotly figure for the specified chart type.

        Args:
            chart_type: One of the supported chart type strings.
            params: Dictionary of parameters to pass to the chart constructor.

        Returns:
            go.Figure: The fully constructed chart figure.

        Raises:
            ValueError: If the chart type is unknown or required parameters
                are missing (delegated from the chart class).
            TypeError: If parameters have invalid types (delegated from the
                chart class).
        """
        # Validate chart type
        if chart_type not in cls._CHART_CLASSES:
            raise ValueError(
                f"Unknown chart type: {chart_type!r}. "
                f"Supported types: {list(cls._CHART_CLASSES.keys())}"
            )

        # Get the chart class
        chart_class = cls._CHART_CLASSES[chart_type]

        # Instantiate the chart with the provided parameters
        try:
            chart_instance = chart_class(**params)
        except TypeError as e:
            # Re-raise with a more descriptive message
            raise TypeError(
                f"Error instantiating {chart_class.__name__}: {e}"
            ) from e

        # Build and return the figure
        return chart_instance.create()

    @classmethod
    def supported_types(cls) -> list[str]:
        """Return the list of supported chart type strings."""
        return list(cls._CHART_CLASSES.keys())