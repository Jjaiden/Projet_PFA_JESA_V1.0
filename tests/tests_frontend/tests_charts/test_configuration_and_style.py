"""Tests de configuration et du design system Streamlit."""

from __future__ import annotations

from assets.styles.theme import CHART_COLORS, COLORS, get_pillar_color, get_plotly_layout, status_color
from config.constants import NUMBER_OF_PILLARS, Page, Pillar
from config.settings import settings


def test_configuration_exposes_expected_domain_constants() -> None:
    assert NUMBER_OF_PILLARS == 5
    assert len(Pillar) == 5
    assert Page.ordered_pages()[0] is Page.HOME
    assert settings.ASSESSMENT_FILE.name == "assessment.xlsx"


def test_style_helpers_return_consistent_values() -> None:
    layout = get_plotly_layout(title="Dashboard")

    assert layout["title"] == "Dashboard"
    assert get_pillar_color(len(CHART_COLORS)) == CHART_COLORS[0]
    assert status_color(30) == COLORS.danger
    assert status_color(50) == COLORS.warning
    assert status_color(80) == COLORS.success
