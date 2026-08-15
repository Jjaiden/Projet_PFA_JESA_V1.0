# JESA_DMAT/charts/__init__.py
"""
Visualization package for the JESA DMAT application.

Exposes a consistent, theme-aware interface for building industrial-grade
charts used in digital maturity assessments, dashboards, and exports.

Public API::

    from charts import (
        BaseChart,
        GaugeChart,
        RadarChart,
        BarChart,
        HeatmapChart,
    )
"""

from __future__ import annotations

from .base import BaseChart
from .bar import BarChart
from .gauge import GaugeChart
from .heatmap import HeatmapChart
from .radar import RadarChart

# Factory is being implemented progressively. It is not imported until its
# public class exists, so that ``import charts`` remains usable while the
# package is under development.
__all__ = [
    "BaseChart",
    "GaugeChart",
    "RadarChart",
    "BarChart",
    "HeatmapChart",
]
