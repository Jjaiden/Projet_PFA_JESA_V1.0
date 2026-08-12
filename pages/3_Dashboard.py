"""
Digital Maturity Dashboard for JESA DMAT.

Professional industrial dashboard focused on:
- Executive maturity snapshot
- Current vs target maturity position
- Radar maturity profile
- Pillar performance
- Transformation gaps
- Diagnostic insights
- Decision transition
"""

from __future__ import annotations

from html import escape

import streamlit as st

from components import render_footer, render_header
from charts import BarChart, GaugeChart, RadarChart


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


def _get_largest_gap(dimensions: list[dict]) -> dict | None:
    """Return the dimension with the largest negative gap."""

    negative_gaps = [
        dimension
        for dimension in dimensions
        if float(dimension.get("gap", 0)) < 0
    ]

    if not negative_gaps:
        return None

    return min(
        negative_gaps,
        key=lambda dimension: float(dimension.get("gap", 0)),
    )


def _count_attention_areas(
    dimensions: list[dict],
    threshold: float = -10,
) -> int:
    """Count dimensions whose negative gap exceeds the attention threshold."""

    return sum(
        1
        for dimension in dimensions
        if float(dimension.get("gap", 0)) < threshold
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
    """
    Convert a negative gap into a visual percentage.

    The visual bar is intentionally capped at 100%.
    """

    magnitude = abs(float(gap))

    return min(100.0, magnitude)


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
        <div class="dmat-section-heading">Executive Snapshot</div>
        <div class="dmat-section-line"></div>
    </div>
    """
)


dimensions = data.get("dimensions", [])

largest_gap_dim = _get_largest_gap(dimensions)
attention_count = _count_attention_areas(dimensions)

dmi = float(data.get("dmi", 0))
target_dmi = float(data.get("target_dmi", 0))
dmi_gap = float(data.get("dmi_gap", dmi - target_dmi))

maturity_level = str(data.get("maturity_level", "N/A"))
maturity_color = _maturity_color(dmi)


kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)


with kpi_col1:
    st.html(
        f"""
        <div class="dmat-kpi-card">
            <div class="dmat-kpi-label">Digital Maturity Index</div>
            <div class="dmat-kpi-value">{dmi:.1f}%</div>
            <div class="dmat-kpi-description">
                Current maturity score
            </div>
        </div>
        """
    )


with kpi_col2:
    st.html(
        f"""
        <div class="dmat-kpi-card">
            <div class="dmat-kpi-label">Maturity Level</div>
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


with kpi_col3:
    gap_class = "negative" if dmi_gap < 0 else "positive"

    st.html(
        f"""
        <div class="dmat-kpi-card {'danger' if dmi_gap < 0 else 'success'}">
            <div class="dmat-kpi-label">Overall Gap</div>
            <div class="dmat-kpi-value {gap_class}">
                {dmi_gap:+.1f} pts
            </div>
            <div class="dmat-kpi-description">
                Current maturity versus target
            </div>
        </div>
        """
    )


with kpi_col4:
    st.html(
        f"""
        <div class="dmat-kpi-card {'danger' if attention_count else 'success'}">
            <div class="dmat-kpi-label">Attention Areas</div>
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
        <div class="dmat-section-heading">Overall Maturity Position</div>
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
# MATURITY PROFILE — CURRENT VS TARGET
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">
        <div class="dmat-section-heading">Maturity Profile</div>
        <div class="dmat-section-line"></div>
        <div class="dmat-section-subtitle">
            Compare the current digital maturity profile with the strategic target.
        </div>
    </div>
    """
)


dim_names = [
    str(dimension.get("name", "Unknown"))
    for dimension in dimensions
]

current_scores = [
    float(dimension.get("current", 0))
    for dimension in dimensions
]

target_scores = [
    float(dimension.get("target", 0))
    for dimension in dimensions
]


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
                    Current Maturity
                </div>
                <div class="dmat-radar-subtitle">
                    Current performance across all digital dimensions.
                </div>
                <span class="dmat-radar-badge current">
                    CURRENT
                </span>
            </div>
        </div>
        """
    )

    current_radar = RadarChart(
        categories=dim_names,
        values=current_scores,
        fill=True,
        fill_color="rgba(37, 99, 235, 0.16)",
        line_color=PRIMARY,
        marker_color=PRIMARY,
        marker_size=7,
        line_width=2,
        min_value=0,
        max_value=100,
        background_color=SURFACE,
        paper_color=SURFACE,
        font_family="Century Gothic",
        font_size=12,
        width=700,
        height=430,
    )

    st.plotly_chart(
        current_radar.create(),
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
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
                    Target Maturity
                </div>
                <div class="dmat-radar-subtitle">
                    Strategic target across all digital dimensions.
                </div>
                <span class="dmat-radar-badge target">
                    TARGET
                </span>
            </div>
        </div>
        """
    )

    target_radar = RadarChart(
        categories=dim_names,
        values=target_scores,
        fill=True,
        fill_color="rgba(15, 157, 148, 0.12)",
        line_color=TEAL,
        marker_color=TEAL,
        marker_size=7,
        line_width=2,
        min_value=0,
        max_value=100,
        background_color=SURFACE,
        paper_color=SURFACE,
        font_family="Century Gothic",
        font_size=12,
        width=700,
        height=430,
    )

    st.plotly_chart(
        target_radar.create(),
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# ==============================================================================
# PILLAR PERFORMANCE
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">
        <div class="dmat-section-heading">Pillar Performance</div>
        <div class="dmat-section-line"></div>
        <div class="dmat-section-subtitle">
            Performance of the main digital transformation pillars.
        </div>
    </div>
    """
)


pillars = data.get("pillars", [])

sorted_pillars = sorted(
    pillars,
    key=lambda pillar: float(pillar.get("score", 0)),
    reverse=True,
)

pillar_names = [
    str(pillar.get("name", "Unknown"))
    for pillar in sorted_pillars
]

pillar_scores = [
    float(pillar.get("score", 0))
    for pillar in sorted_pillars
]


pillar_chart = BarChart(
    categories=pillar_names,
    values=pillar_scores,
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

st.plotly_chart(
    pillar_chart.create(),
    width="stretch",
    config={
        "displayModeBar": False,
        "responsive": True,
    },
)


# ==============================================================================
# TRANSFORMATION GAPS
# ==============================================================================

st.html(
    """
    <div class="dmat-dashboard-section">
        <div class="dmat-section-heading">Transformation Gaps</div>
        <div class="dmat-section-line"></div>
        <div class="dmat-section-subtitle">
            Dimensions with the largest distance from the strategic target.
        </div>
    </div>
    """
)


gap_dimensions = sorted(
    dimensions,
    key=lambda dimension: float(dimension.get("gap", 0)),
)


gap_col1, gap_col2 = st.columns(2)


for index, dimension in enumerate(gap_dimensions[:6]):

    name = str(dimension.get("name", "Unknown"))
    current = float(dimension.get("current", 0))
    target = float(dimension.get("target", 0))
    gap = float(dimension.get("gap", 0))

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
                <span>Current: {current:.1f}%</span>
                <span>Target: {target:.1f}%</span>
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
        <div class="dmat-section-heading">Diagnostic Insights</div>
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

        insight_type = str(insight.get("type", "warning"))

        if insight_type not in {"danger", "warning", "success"}:
            insight_type = "warning"

        icon = _insight_icon(insight_type)

        title = escape(str(insight.get("title", "Insight")))
        text = escape(str(insight.get("text", "")))

        insight_html = f"""
            <div class="dmat-insight-card">

                <div class="dmat-insight-icon {insight_type}">
                    {icon}
                </div>

                <div>
                    <div class="dmat-insight-title">
                        {title}
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
            <div class="dmat-insight-icon success">✓</div>
            <div>
                <div class="dmat-insight-title">
                    No additional diagnostic insight
                </div>
                <div class="dmat-insight-text">
                    The assessment does not currently provide additional
                    interpretation messages.
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
        <div class="dmat-section-heading">Next Decision</div>
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
            The current maturity position and transformation gaps have been
            established. The next step is to identify and prioritise the
            actions with the highest business impact.
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
            "url": "https://www.jesa.ma",
        },
        {
            "label": "ENSAM Casablanca",
            "url": "https://ensam-casablanca.ma",
        },
    ],
    align="center",
    compact=False,
    show_divider=True,
)