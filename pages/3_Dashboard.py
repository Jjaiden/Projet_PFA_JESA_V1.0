from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from components import render_footer, render_header
from charts import BarChart, GaugeChart, RadarChart, HeatmapChart

from utils.helpers import (
    translate_entity_name,
    ENTITY_ENGLISH_NAMES,
)


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Digital Maturity Diagnostic",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# DESIGN TOKENS
# ==============================================================================

PRIMARY = "#2563EB"
PRIMARY_DARK = "#1E3A8A"
PRIMARY_LIGHT = "#DBEAFE"

TEAL = "#0F9D94"
TEAL_LIGHT = "#CCFBF1"

TEXT = "#0F172A"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748B"

BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
BORDER = "#E2E8F0"

SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"

SOFT_BLUE = "#EFF6FF"
SOFT_GREEN = "#ECFDF5"
SOFT_ORANGE = "#FFF7ED"
SOFT_RED = "#FEF2F2"


# ==============================================================================
# PAGE-SPECIFIC CSS
# ==============================================================================

st.html(
    f"""
    <style>

        /* ==============================================================
           GLOBAL DASHBOARD SPACING
           ============================================================== */

        .dmat-dashboard-section {{
            margin-top: 2.15rem;
            margin-bottom: 1rem;
        }}

        .dmat-section-heading {{
            color: {TEXT};
            font-family:
                "Century Gothic",
                "Segoe UI",
                Arial,
                sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin: 0;
        }}

        .dmat-section-subtitle {{
            color: {TEXT_MUTED};
            font-family:
                "Century Gothic",
                "Segoe UI",
                Arial,
                sans-serif;
            font-size: 0.82rem;
            margin-top: 0.28rem;
            margin-bottom: 1rem;
        }}

        .dmat-section-line {{
            width: 42px;
            height: 3px;
            border-radius: 99px;
            margin-top: 0.45rem;
            margin-bottom: 0.85rem;
            background: linear-gradient(
                90deg,
                {PRIMARY},
                {TEAL}
            );
        }}


        /* ==============================================================
           KPI CARDS
           ============================================================== */

        .dmat-kpi-card {{
            position: relative;
            min-height: 132px;
            padding: 1.15rem 1.25rem 1.05rem 1.35rem;
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.055);
            overflow: hidden;
        }}

        .dmat-kpi-card::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: {PRIMARY};
        }}

        .dmat-kpi-card.warning::before {{
            background: {WARNING};
        }}

        .dmat-kpi-card.danger::before {{
            background: {DANGER};
        }}

        .dmat-kpi-card.success::before {{
            background: {SUCCESS};
        }}

        .dmat-kpi-label {{
            color: {TEXT_MUTED};
            font-family:
                "Century Gothic",
                "Segoe UI",
                Arial,
                sans-serif;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }}

        .dmat-kpi-value {{
            color: {TEXT};
            font-family:
                "Century Gothic",
                "Segoe UI",
                Arial,
                sans-serif;
            font-size: 1.72rem;
            line-height: 1.15;
            font-weight: 700;
        }}

        .dmat-kpi-value.maturity {{
            font-size: 1.22rem;
            color: {PRIMARY};
            text-transform: uppercase;
        }}

        .dmat-kpi-value.negative {{
            color: {DANGER};
        }}

        .dmat-kpi-value.positive {{
            color: {SUCCESS};
        }}

        .dmat-kpi-description {{
            color: #94A3B8;
            font-size: 0.69rem;
            margin-top: 0.45rem;
        }}


        /* ==============================================================
           POSITION CARDS
           ============================================================== */

        .dmat-position-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1.15rem 1.25rem;
            min-height: 112px;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.045);
        }}

        .dmat-position-label {{
            color: {TEXT_MUTED};
            font-size: 0.72rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .dmat-position-value {{
            color: {TEXT};
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.1;
        }}

        .dmat-position-value.current {{
            color: {PRIMARY};
        }}

        .dmat-position-value.target {{
            color: {TEAL};
        }}

        .dmat-position-value.gap {{
            color: {DANGER};
        }}


        /* ==============================================================
           RADAR CARDS
           ============================================================== */

        .dmat-radar-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 15px;
            padding: 0.85rem 0.85rem 0.55rem 0.85rem;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.045);
        }}

        .dmat-radar-header {{
            padding: 0.25rem 0.45rem 0.2rem 0.45rem;
        }}

        .dmat-radar-title {{
            color: {TEXT};
            font-size: 0.95rem;
            font-weight: 700;
        }}

        .dmat-radar-subtitle {{
            color: {TEXT_MUTED};
            font-size: 0.68rem;
            margin-top: 0.18rem;
        }}

        .dmat-radar-badge {{
            display: inline-block;
            margin-top: 0.45rem;
            padding: 0.22rem 0.55rem;
            border-radius: 999px;
            font-size: 0.63rem;
            font-weight: 700;
        }}

        .dmat-radar-badge.current {{
            background: {SOFT_BLUE};
            color: {PRIMARY};
        }}

        .dmat-radar-badge.target {{
            background: {TEAL_LIGHT};
            color: {TEAL};
        }}


        /* ==============================================================
           GAP CARDS
           ============================================================== */

        .dmat-gap-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 13px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
        }}

        .dmat-gap-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .dmat-gap-name {{
            color: {TEXT};
            font-size: 0.82rem;
            font-weight: 700;
        }}

        .dmat-gap-value {{
            font-size: 0.78rem;
            font-weight: 700;
            white-space: nowrap;
        }}

        .dmat-gap-value.negative {{
            color: {DANGER};
        }}

        .dmat-gap-value.neutral {{
            color: {TEXT_MUTED};
        }}

        .dmat-gap-track {{
            width: 100%;
            height: 6px;
            margin-top: 0.65rem;
            background: #EAF0F6;
            border-radius: 99px;
            overflow: hidden;
        }}

        .dmat-gap-fill {{
            height: 100%;
            border-radius: 99px;
            background: linear-gradient(
                90deg,
                {DANGER},
                #F97316
            );
        }}

        .dmat-gap-meta {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.42rem;
            color: #94A3B8;
            font-size: 0.62rem;
        }}


        /* ==============================================================
           INSIGHT CARDS
           ============================================================== */

        .dmat-insight-card {{
            display: flex;
            gap: 0.9rem;
            align-items: flex-start;
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 13px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
        }}

        .dmat-insight-icon {{
            flex: 0 0 auto;
            width: 31px;
            height: 31px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 9px;
            font-size: 0.82rem;
            font-weight: 700;
        }}

        .dmat-insight-icon.danger {{
            background: {SOFT_RED};
            color: {DANGER};
        }}

        .dmat-insight-icon.warning {{
            background: {SOFT_ORANGE};
            color: {WARNING};
        }}

        .dmat-insight-icon.success {{
            background: {SOFT_GREEN};
            color: {SUCCESS};
        }}

        .dmat-insight-title {{
            color: {TEXT};
            font-size: 0.79rem;
            font-weight: 700;
        }}

        .dmat-insight-text {{
            color: {TEXT_SECONDARY};
            font-size: 0.72rem;
            line-height: 1.55;
            margin-top: 0.18rem;
        }}


        /* ==============================================================
           DECISION CARD
           ============================================================== */

        .dmat-decision-card {{
            background:
                linear-gradient(
                    135deg,
                    #F8FBFF 0%,
                    #EFF6FF 60%,
                    #F0FDFA 100%
                );
            border: 1px solid #CFE0F5;
            border-radius: 16px;
            padding: 1.25rem 1.35rem;
            margin-top: 0.5rem;
        }}

        .dmat-decision-title {{
            color: {TEXT};
            font-size: 1rem;
            font-weight: 700;
        }}

        .dmat-decision-text {{
            color: {TEXT_SECONDARY};
            font-size: 0.76rem;
            line-height: 1.55;
            margin-top: 0.35rem;
        }}


        /* ==============================================================
           STREAMLIT BUTTON
           ============================================================== */

        .stButton > button {{
            border-radius: 10px !important;
            min-height: 44px !important;
            background: {PRIMARY} !important;
            color: #FFFFFF !important;
            border: none !important;
            font-family:
                "Century Gothic",
                "Segoe UI",
                Arial,
                sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.18) !important;
        }}

        .stButton > button:hover {{
            background: {PRIMARY_DARK} !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }}

    </style>
    """
)


# ==============================================================================
# HELPERS
# ==============================================================================

def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _english_name(
    entity_id: Any,
    raw_name: Any,
    fallback: str = "",
) -> str:
    """
    Return the English display name for an entity.

    The translation helper is used first. Empty or undefined values
    are rejected so that 'Undefined', 'None', or empty labels do not
    reach the UI.
    """

    entity_id_str = str(entity_id or "").strip()
    raw_name_str = str(raw_name or "").strip()

    invalid_values = {
        "",
        "none",
        "null",
        "undefined",
        "nan",
        "unknown",
        "dimension",
        "sub-dimension",
    }

    if raw_name_str.lower() in invalid_values:
        raw_name_str = ""

    translated = translate_entity_name(
        entity_id_str,
        raw_name_str,
    )

    translated = str(translated or "").strip()

    if translated.lower() in invalid_values:
        translated = ""

    if translated:
        return translated

    if raw_name_str:
        return raw_name_str

    if entity_id_str:
        return entity_id_str

    return fallback


def _build_dimension_lookup(
    dimensions: list[dict],
) -> dict[str, str]:
    """Build a dimension ID -> English parent dimension name lookup."""

    lookup: dict[str, str] = {}

    for dimension in dimensions:
        dimension_id = str(
            dimension.get("id", "")
        ).strip()

        if not dimension_id:
            continue

        dimension_name = _english_name(
            dimension_id,
            dimension.get("name", ""),
        )

        if dimension_name:
            lookup[dimension_id] = dimension_name

    return lookup


def _get_largest_gap(
    dimensions: list[dict],
) -> dict | None:
    """Return the dimension with the largest negative gap."""

    negative_gaps = [
        dimension
        for dimension in dimensions
        if _safe_float(dimension.get("gap", 0)) < 0
    ]

    if not negative_gaps:
        return None

    return min(
        negative_gaps,
        key=lambda dimension: _safe_float(
            dimension.get("gap", 0)
        ),
    )


def _count_attention_areas(
    dimensions: list[dict],
    threshold: float = -10,
) -> int:
    """Count dimensions whose negative gap exceeds the attention threshold."""

    return sum(
        1
        for dimension in dimensions
        if _safe_float(dimension.get("gap", 0)) < threshold
    )


def _maturity_color(dmi: float) -> str:
    """Return a professional maturity color based on DMI."""

    if dmi < 40:
        return DANGER

    if dmi < 70:
        return PRIMARY

    return TEAL


def _insight_icon(insight_type: str) -> str:
    """Return a compact icon for an insight type."""

    return {
        "danger": "!",
        "warning": "!",
        "success": "✓",
    }.get(insight_type, "•")


def _gap_width(gap: float) -> float:
    """Convert a negative gap into a capped visual percentage."""

    return min(
        100.0,
        abs(_safe_float(gap)),
    )


def _clean_label(value: Any, fallback: str = "") -> str:
    """Return a clean non-empty display label."""

    if value is None:
        return fallback

    value = str(value).strip()

    if not value:
        return fallback

    return value


def _get_english_entity_name(
    entity_id: Any,
    fallback: str = "",
) -> str:
    """
    Return the English entity name.

    The translation helper is used first. If no translation exists,
    the original name is preserved instead of displaying
    'Undefined', 'Dimension', or another generic placeholder.
    """

    entity_id = _clean_label(entity_id)
    fallback = _clean_label(fallback)

    if entity_id:
        translated = translate_entity_name(
            entity_id,
            fallback,
        )

        translated = _clean_label(translated)

        if translated:
            return translated

    return fallback


# ==============================================================================
# LOAD DATA
# ==============================================================================

if not st.session_state.get("dashboard_data"):
    st.warning(
        "No assessment is currently loaded. "
        "Please start a new assessment from the Home page."
    )
    st.stop()


data = st.session_state["dashboard_data"]

dimensions = data.get("dimensions", [])
pillars = data.get("pillars", [])
sub_dims_data = data.get("sub_dimensions", [])


# ==============================================================================
# BUILD MASTER DIMENSION LOOKUP
# ==============================================================================

dimension_lookup = _build_dimension_lookup(dimensions)


# ==============================================================================
# HEADER
# ==============================================================================

render_header(
    title="Digital Maturity Diagnostic",
    subtitle="Industrial Plant · Assessment Overview",
    align="center",
    compact=False,
)


# ==============================================================================
# EXECUTIVE SNAPSHOT
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">
        <div class="dmat-section-heading">
            Executive Snapshot
        </div>

        <div class="dmat-section-line"></div>
    </div>
    """
)


largest_gap_dim = _get_largest_gap(dimensions)
attention_count = _count_attention_areas(dimensions)

dmi = _safe_float(data.get("dmi", 0))
target_dmi = _safe_float(data.get("target_dmi", 0))

dmi_gap = _safe_float(
    data.get(
        "dmi_gap",
        dmi - target_dmi,
    )
)

maturity_level = str(
    data.get("maturity_level", "N/A")
).strip()

if not maturity_level or maturity_level.lower() in {
    "undefined",
    "none",
    "null",
}:
    maturity_level = "N/A"

maturity_color = _maturity_color(dmi)


kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)


# ------------------------------------------------------------------------------
# KPI 1
# ------------------------------------------------------------------------------

with kpi_col1:

    st.html(
        f"""
        <div class="dmat-kpi-card">

            <div class="dmat-kpi-label">
                Digital Maturity Index
            </div>

            <div class="dmat-kpi-value">
                {dmi:.1f}%
            </div>

            <div class="dmat-kpi-description">
                Current maturity score
            </div>

        </div>
        """
    )


# ------------------------------------------------------------------------------
# KPI 2
# ------------------------------------------------------------------------------

with kpi_col2:

    st.html(
        f"""
        <div class="dmat-kpi-card">

            <div class="dmat-kpi-label">
                Maturity Level
            </div>

            <div
                class="dmat-kpi-value maturity"
                style="color:{maturity_color};"
            >
                {escape(maturity_level)}
            </div>

            <div class="dmat-kpi-description">
                Current maturity stage
            </div>

        </div>
        """
    )


# ------------------------------------------------------------------------------
# KPI 3
# ------------------------------------------------------------------------------

with kpi_col3:

    gap_class = "negative" if dmi_gap < 0 else "positive"
    card_class = "danger" if dmi_gap < 0 else "success"

    st.html(
        f"""
        <div class="dmat-kpi-card {card_class}">

            <div class="dmat-kpi-label">
                Overall Gap
            </div>

            <div class="dmat-kpi-value {gap_class}">
                {dmi_gap:+.1f} pts
            </div>

            <div class="dmat-kpi-description">
                Current maturity versus target
            </div>

        </div>
        """
    )


# ------------------------------------------------------------------------------
# KPI 4
# ------------------------------------------------------------------------------

with kpi_col4:

    card_class = "danger" if attention_count else "success"

    st.html(
        f"""
        <div class="dmat-kpi-card {card_class}">

            <div class="dmat-kpi-label">
                Attention Areas
            </div>

            <div class="dmat-kpi-value">
                {attention_count}
            </div>

            <div class="dmat-kpi-description">
                Dimensions requiring attention
            </div>

        </div>
        """
    )


# ==============================================================================
# OVERALL MATURITY POSITION
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Overall Maturity Position
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Current maturity against the strategic target.
        </div>

    </div>
    """
)


position_col1, position_col2 = st.columns([1.65, 1])


# ------------------------------------------------------------------------------
# GAUGE
# ------------------------------------------------------------------------------

with position_col1:

    gauge = GaugeChart(
        value=dmi,
        title="Digital Maturity Index",
        unit="%",
        height=370,
        show_threshold=False,
        threshold=None,
        steps=(
            (0, 40, "#E8EEF5"),
            (40, 70, "#DCEBFF"),
            (70, 100, "#D9F5EF"),
        ),
        bar_color=PRIMARY,
        background_color=SURFACE,
        paper_color=BACKGROUND,
        title_color=TEXT,
        font_family="Century Gothic",
        font_size=13,
    )

    st.plotly_chart(
        gauge.create(),
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# ------------------------------------------------------------------------------
# POSITION CARDS
# ------------------------------------------------------------------------------

with position_col2:

    st.html(
        f"""
        <div class="dmat-position-card">

            <div class="dmat-position-label">
                Current DMI
            </div>

            <div class="dmat-position-value current">
                {dmi:.1f}%
            </div>

        </div>

        <div style="height:0.65rem;"></div>

        <div class="dmat-position-card">

            <div class="dmat-position-label">
                Target DMI
            </div>

            <div class="dmat-position-value target">
                {target_dmi:.1f}%
            </div>

        </div>

        <div style="height:0.65rem;"></div>

        <div class="dmat-position-card">

            <div class="dmat-position-label">
                Remaining Gap
            </div>

            <div class="dmat-position-value gap">
                {dmi_gap:+.1f} pts
            </div>

        </div>
        """
    )


# ==============================================================================
# PILLAR PERFORMANCE
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Pillar Performance
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Performance of the main digital transformation pillars.
        </div>

    </div>
    """
)


sorted_pillars = sorted(
    pillars,
    key=lambda pillar: _safe_float(pillar.get("score", 0)),
    reverse=True,
)

pillar_names = [
    _english_name(
        pillar.get("id", ""),
        pillar.get("name", ""),
        fallback="Unknown",
    )
    for pillar in sorted_pillars
]

pillar_scores = [
    _safe_float(pillar.get("score", 0))
    for pillar in sorted_pillars
]


if pillar_names:

    pillar_chart = BarChart(
        categories=pillar_names,
        values=pillar_scores,
        title="Pillar Performance Scores",
        orientation="horizontal",
        show_values=True,
        text_position="outside",
        text_template="%{x:.1f}%",
        show_grid=True,
        show_legend=False,
        colors=[PRIMARY],
        background_color=SURFACE,
        paper_color=BACKGROUND,
        font_family="Century Gothic",
        font_size=12,
        width=1100,
        height=420,
    )

    pillar_fig = pillar_chart.create()

    pillar_fig.update_xaxes(title_text="")
    pillar_fig.update_yaxes(title_text="")

    st.plotly_chart(
        pillar_fig,
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )

else:

    st.info("No pillar data available for visualization.")


# ==============================================================================
# MATURITY PROFILE
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Maturity Profile
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Current versus target maturity scores across all dimensions.
        </div>

    </div>
    """
)


radar_dim_names = []
radar_current_scores = []
radar_target_scores = []


for dim in dimensions:

    dim_name = _english_name(
        dim.get("id", ""),
        dim.get("name", ""),
        fallback="Unknown",
    )

    if not dim_name:
        continue

    radar_dim_names.append(dim_name)
    radar_current_scores.append(_safe_float(dim.get("current", 0)))
    radar_target_scores.append(_safe_float(dim.get("target", 0)))


radar_col1, radar_col2 = st.columns(2)


# ------------------------------------------------------------------------------
# CURRENT RADAR
# ------------------------------------------------------------------------------

with radar_col1:

    st.html(
        """
        <div class="dmat-radar-card">

            <div class="dmat-radar-header">

                <div class="dmat-radar-title">
                    Current Dimension Scores
                </div>

                <div class="dmat-radar-subtitle">
                    Current maturity per dimension
                </div>

                <span class="dmat-radar-badge current">
                    Current
                </span>

            </div>

        </div>
        """
    )

    if radar_dim_names:

        radar_current_chart = RadarChart(
            categories=radar_dim_names,
            values=radar_current_scores,
            title="Current Maturity",
            max_value=100,
            fill=True,
            line_color=PRIMARY,
            fill_color=PRIMARY_LIGHT,
            background_color=SURFACE,
            paper_color=BACKGROUND,
            font_family="Century Gothic",
            font_size=12,
            height=380,
        )

        current_fig = radar_current_chart.create()
        current_fig.update_xaxes(title_text="")
        current_fig.update_yaxes(title_text="")

        st.plotly_chart(
            current_fig,
            width="stretch",
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    else:

        st.info(
            "No dimension data available for the current maturity profile."
        )


# ------------------------------------------------------------------------------
# TARGET RADAR
# ------------------------------------------------------------------------------

with radar_col2:

    st.html(
        """
        <div class="dmat-radar-card">

            <div class="dmat-radar-header">

                <div class="dmat-radar-title">
                    Target Dimension Scores
                </div>

                <div class="dmat-radar-subtitle">
                    Target maturity per dimension
                </div>

                <span class="dmat-radar-badge target">
                    Target
                </span>

            </div>

        </div>
        """
    )

    if radar_dim_names:

        radar_target_chart = RadarChart(
            categories=radar_dim_names,
            values=radar_target_scores,
            title="Target Maturity",
            max_value=100,
            fill=True,
            line_color=TEAL,
            fill_color=TEAL_LIGHT,
            background_color=SURFACE,
            paper_color=BACKGROUND,
            font_family="Century Gothic",
            font_size=12,
            height=380,
        )

        target_fig = radar_target_chart.create()
        target_fig.update_xaxes(title_text="")
        target_fig.update_yaxes(title_text="")

        st.plotly_chart(
            target_fig,
            width="stretch",
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    else:

        st.info(
            "No dimension data available for the target maturity profile."
        )


# ==============================================================================
# SUB-DIMENSION HEATMAP
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">
        <div class="dmat-section-heading">
            Sub-Dimension Heatmap
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Detailed maturity scores by parent dimension and sub-dimension.
        </div>
    </div>
    """
)


# ------------------------------------------------------------------------------
# EXTRACT SUB-DIMENSION DATA
# ------------------------------------------------------------------------------

sub_dims_data = []


# CASE 1 — top-level sub_dimensions key
top_level_sub_dimensions = data.get("sub_dimensions")

if isinstance(top_level_sub_dimensions, list):
    sub_dims_data.extend(top_level_sub_dimensions)


# CASE 2 — sub-dimensions nested inside each dimension
if not sub_dims_data:

    for dimension in data.get("dimensions", []):

        if not isinstance(dimension, dict):
            continue

        parent_dimension_id = (
            dimension.get("id")
            or dimension.get("dimension_id")
            or ""
        )

        parent_dimension_name = (
            dimension.get("name")
            or dimension.get("dimension_name")
            or ""
        )

        nested_sub_dimensions = (
            dimension.get("sub_dimensions")
            or dimension.get("subdimensions")
            or dimension.get("sub_dimensions_data")
            or []
        )

        if not isinstance(nested_sub_dimensions, list):
            continue

        for sub_dimension in nested_sub_dimensions:

            if not isinstance(sub_dimension, dict):
                continue

            sd = dict(sub_dimension)
            sd.setdefault("dimension_id", parent_dimension_id)
            sd.setdefault("dimension_name", parent_dimension_name)
            sub_dims_data.append(sd)


# CASE 3 — other common backend key names
if not sub_dims_data:

    for key in (
        "subDimensions",
        "sub_dimension_scores",
        "subdimension_scores",
        "subdimension_data",
    ):
        candidate = data.get(key)

        if isinstance(candidate, list):
            sub_dims_data.extend(candidate)
            break


# ------------------------------------------------------------------------------
# BUILD HEATMAP DATA
# ------------------------------------------------------------------------------

heatmap_entries = []

for sd in sub_dims_data:

    if not isinstance(sd, dict):
        continue

    sub_dimension_id = (
        sd.get("id")
        or sd.get("sub_dimension_id")
        or sd.get("subdimension_id")
        or ""
    )

    sub_dimension_raw_name = (
        sd.get("name")
        or sd.get("sub_dimension_name")
        or sd.get("subdimension_name")
        or ""
    )

    sub_dimension_name = _get_english_entity_name(
        sub_dimension_id,
        sub_dimension_raw_name,
    )

    if not sub_dimension_name:
        continue

    if sub_dimension_name.lower() in {
        "undefined",
        "unknown",
        "unknown dimension",
        "sub-dimension",
        "subdimension",
    }:
        continue

    dimension_id = (
        sd.get("dimension_id")
        or sd.get("parent_dimension_id")
        or sd.get("parent_id")
        or ""
    )

    dimension_raw_name = (
        sd.get("dimension_name")
        or sd.get("parent_dimension_name")
        or sd.get("parent_name")
        or ""
    )

    if not dimension_raw_name and dimension_id:

        for dimension in data.get("dimensions", []):

            if not isinstance(dimension, dict):
                continue

            current_dimension_id = str(
                dimension.get("id")
                or dimension.get("dimension_id")
                or ""
            )

            if current_dimension_id == str(dimension_id):

                dimension_raw_name = (
                    dimension.get("name")
                    or dimension.get("dimension_name")
                    or ""
                )

                break

    parent_dimension_name = _get_english_entity_name(
        dimension_id,
        dimension_raw_name,
    )

    if not parent_dimension_name:
        continue

    if parent_dimension_name.lower() in {
        "undefined",
        "unknown",
        "unknown dimension",
        "dimension",
    }:
        continue

    score = (
        sd.get("score")
        if sd.get("score") is not None
        else sd.get("current")
    )

    if score is None:
        score = sd.get("value")

    if score is None:
        continue

    score = _safe_float(score)

    heatmap_entries.append(
        {
            "parent_dimension": parent_dimension_name,
            "sub_dimension": sub_dimension_name,
            "score": score,
        }
    )


# ------------------------------------------------------------------------------
# REMOVE DUPLICATES
# ------------------------------------------------------------------------------

unique_entries = {}

for entry in heatmap_entries:
    key = (entry["parent_dimension"], entry["sub_dimension"])
    unique_entries[key] = entry

heatmap_entries = list(unique_entries.values())


# ------------------------------------------------------------------------------
# RENDER HEATMAP
# ------------------------------------------------------------------------------

if heatmap_entries:

    parent_dimensions = sorted(
        {entry["parent_dimension"] for entry in heatmap_entries}
    )

    sub_dimensions = sorted(
        {entry["sub_dimension"] for entry in heatmap_entries}
    )

    score_lookup = {
        (entry["parent_dimension"], entry["sub_dimension"]): entry["score"]
        for entry in heatmap_entries
    }

    heatmap_matrix = []

    for parent_dimension in parent_dimensions:

        row = []

        for sub_dimension in sub_dimensions:

            value = score_lookup.get(
                (parent_dimension, sub_dimension),
                None,
            )

            row.append(value)

        heatmap_matrix.append(row)

    hover_template = (
        "<b>Parent Dimension:</b> %{y}<br>"
        "<b>Sub-Dimension:</b> %{x}<br>"
        "<b>Maturity Score:</b> %{z:.1f}%"
        "<extra></extra>"
    )

    heatmap_chart = HeatmapChart(
        matrix=heatmap_matrix,
        row_labels=parent_dimensions,
        col_labels=sub_dimensions,
        # FIX: pass a single space so the chart component never
        # falls back to a default "undefined" or generic title.
        # The title is fully removed via update_layout below.
        title=" ",
        yaxis_title="",
        colorscale="RdYlGn",
        show_values=True,
        text_format=".1f",
        zmin=0,
        zmax=100,
        width=1100,
        height=max(420, len(parent_dimensions) * 70),
        font_family="Century Gothic",
        font_size=12,
        hover_template=hover_template,
    )

    fig = heatmap_chart.create()

    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")

    # FIX: explicitly wipe the title text and collapse its font size
    # so nothing is rendered even if the component set a default.
    fig.update_layout(
        title=dict(
            text="",
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )

else:

    st.warning(
        "Sub-dimension scores are not available in the current assessment results."
    )


# ==============================================================================
# TRANSFORMATION GAPS
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Transformation Gaps
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Dimensions with the largest distance from the strategic target.
        </div>

    </div>
    """
)


gap_dimensions = sorted(
    dimensions,
    key=lambda dimension: _safe_float(dimension.get("gap", 0)),
)

gap_col1, gap_col2 = st.columns(2)

for index, dimension in enumerate(gap_dimensions[:6]):

    name = _english_name(
        dimension.get("id", ""),
        dimension.get("name", ""),
        fallback="Unknown",
    )

    current = _safe_float(dimension.get("current", 0))
    target = _safe_float(dimension.get("target", 0))
    gap = _safe_float(dimension.get("gap", 0))

    gap_class = "negative" if gap < 0 else "neutral"
    fill_width = _gap_width(gap)

    card_html = f"""
        <div class="dmat-gap-card">

            <div class="dmat-gap-top">

                <div class="dmat-gap-name">
                    {escape(name)}
                </div>

                <div class="dmat-gap-value {gap_class}">
                    {gap:+.1f} pts
                </div>

            </div>

            <div class="dmat-gap-track">

                <div
                    class="dmat-gap-fill"
                    style="width:{fill_width:.1f}%;">
                </div>

            </div>

            <div class="dmat-gap-meta">

                <span>
                    Current: {current:.1f}%
                </span>

                <span>
                    Target: {target:.1f}%
                </span>

            </div>

        </div>
    """

    if index % 2 == 0:
        with gap_col1:
            st.html(card_html)
    else:
        with gap_col2:
            st.html(card_html)


# ==============================================================================
# DIAGNOSTIC INSIGHTS
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Diagnostic Insights
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Key observations derived from the maturity assessment.
        </div>

    </div>
    """
)


insights = data.get("insights", [])

if insights:

    insight_col1, insight_col2 = st.columns(2)

    for index, insight in enumerate(insights):

        insight_type = str(
            insight.get("type", "warning")
        ).lower()

        if insight_type not in {"danger", "warning", "success"}:
            insight_type = "warning"

        icon = _insight_icon(insight_type)

        title = str(insight.get("title", "Insight")).strip()

        if not title or title.lower() in {"undefined", "none", "null"}:
            title = "Diagnostic Insight"

        raw_text = str(insight.get("text", ""))

        translated_text = raw_text

        for entity_id, english_name in ENTITY_ENGLISH_NAMES.items():

            entity_id_str = str(entity_id)

            if entity_id_str in translated_text:
                translated_text = translated_text.replace(
                    entity_id_str,
                    str(english_name),
                )

        text = escape(translated_text)

        insight_html = f"""
            <div class="dmat-insight-card">

                <div class="dmat-insight-icon {insight_type}">
                    {icon}
                </div>

                <div>

                    <div class="dmat-insight-title">
                        {escape(title)}
                    </div>

                    <div class="dmat-insight-text">
                        {text}
                    </div>

                </div>

            </div>
        """

        if index % 2 == 0:
            with insight_col1:
                st.html(insight_html)
        else:
            with insight_col2:
                st.html(insight_html)

else:

    st.html(
        """
        <div class="dmat-insight-card">

            <div class="dmat-insight-icon success">
                ✓
            </div>

            <div>

                <div class="dmat-insight-title">
                    No additional diagnostic insight
                </div>

                <div class="dmat-insight-text">
                    The assessment does not currently provide
                    additional interpretation messages.
                </div>

            </div>

        </div>
        """
    )


# ==============================================================================
# NEXT DECISION
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">

        <div class="dmat-section-heading">
            Next Decision
        </div>

        <div class="dmat-section-line"></div>

        <div class="dmat-section-subtitle">
            Move from diagnosis to transformation prioritisation.
        </div>

    </div>

    <div class="dmat-decision-card">

        <div class="dmat-decision-title">
            Diagnosis complete
        </div>

        <div class="dmat-decision-text">
            The current maturity position and transformation gaps
            have been established. The next step is to identify
            and prioritise the actions with the highest business impact.
        </div>

    </div>
    """
)

st.html("<div style='height:0.7rem;'></div>")

button_col1, button_col2, button_col3 = st.columns([1, 2, 1])

with button_col2:

    if st.button(
        "ANALYZE & PRIORITIZE  →",
        key="to_decision",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/4_Decision_analysis.py")


# ==============================================================================
# FOOTER
# ==============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {
            "label": "JESA",
            "url": "https://www.jesagroup.com/",
        },
        {
            "label": "ENSAM Casablanca",
            "url": "https://ensam-casa.ma/",
        },
    ],
    align="center",
    compact=False,
    show_divider=True,
)