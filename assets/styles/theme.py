"""
JESA DMAT - Design System (Python)
Centralise la palette, les tokens et les helpers d'injection de style.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import streamlit as st  # type: ignore[import]
except ImportError:
    class _StreamlitFallback:
        """Minimal fallback implementation of the streamlit API used in this module."""

        def set_page_config(
            self,
            page_title: str = "JESA DMAT",
            page_icon: str = "chart",
            layout: str = "wide",
            initial_sidebar_state: str = "expanded",
        ) -> None:
            print(
                f"Streamlit page config: title={page_title}, icon={page_icon}, layout={layout}, "
                f"initial_sidebar_state={initial_sidebar_state}"
            )

        def markdown(self, body: str, unsafe_allow_html: bool = False) -> None:
            if unsafe_allow_html:
                print(body)
            else:
                print(body)

        def write(self, *args: Any, **kwargs: Any) -> None:
            print(*args, **kwargs)

        def title(self, body: str) -> None:
            print(f"# {body}")

        def header(self, body: str) -> None:
            print(f"## {body}")

        def subheader(self, body: str) -> None:
            print(f"### {body}")

        def text(self, body: str) -> None:
            print(body)

        def info(self, body: str) -> None:
            print(f"[INFO] {body}")

        def success(self, body: str) -> None:
            print(f"[SUCCESS] {body}")

        def warning(self, body: str) -> None:
            print(f"[WARNING] {body}")

        def error(self, body: str) -> None:
            print(f"[ERROR] {body}")

        def caption(self, body: str) -> None:
            print(f"[CAPTION] {body}")

        @property
        def sidebar(self) -> "_StreamlitFallback":
            return self

        def __getattr__(self, name: str) -> Any:
            def _missing(*args: Any, **kwargs: Any) -> None:
                print(f"Streamlit fallback: ignored call to {name}({args}, {kwargs})")
                return None
            return _missing

    st = _StreamlitFallback()

ASSETS_DIR = Path(__file__).resolve().parent.parent
STYLES_DIR = ASSETS_DIR / "styles"
MAIN_CSS_PATH = STYLES_DIR / "main.css"


@dataclass(frozen=True)
class Colors:
    """Tokens de couleur de l'identite graphique JESA DMAT."""

    background: str = "#F5F7FA"
    surface: str = "#FFFFFF"
    sidebar: str = "#1E293B"
    primary: str = "#2563EB"
    secondary: str = "#3B82F6"
    border: str = "#E2E8F0"
    divider: str = "#CBD5E1"
    title: str = "#0F172A"
    text: str = "#334155"
    muted: str = "#64748B"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"


COLORS = Colors()

CHART_COLORS: list[str] = [
    "#2563EB",
    "#3B82F6",
    "#60A5FA",
    "#93C5FD",
    "#BFDBFE",
]

PILLAR_LABELS: list[str] = [
    "Pilier 1",
    "Pilier 2",
    "Pilier 3",
    "Pilier 4",
    "Pilier 5",
]

FONT_FAMILY = "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
}

BORDER_RADIUS = {
    "sm": "6px",
    "md": "10px",
    "lg": "16px",
    "full": "9999px",
}

SHADOWS = {
    "sm": "0 1px 2px rgba(15, 23, 42, 0.05)",
    "md": "0 4px 12px rgba(15, 23, 42, 0.08)",
    "lg": "0 10px 24px rgba(15, 23, 42, 0.12)",
}


def load_css() -> str:
    return MAIN_CSS_PATH.read_text(encoding="utf-8")


def inject_custom_css() -> None:
    css = load_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def get_plotly_layout(**overrides: Any) -> dict[str, Any]:
    layout: dict[str, Any] = {
        "font": {"family": FONT_FAMILY, "color": COLORS.text, "size": 13},
        "title": {"font": {"color": COLORS.title, "size": 18}},
        "paper_bgcolor": COLORS.surface,
        "plot_bgcolor": COLORS.surface,
        "colorway": CHART_COLORS,
        "margin": {"l": 48, "r": 24, "t": 56, "b": 48},
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
            "font": {"color": COLORS.muted},
        },
        "xaxis": {
            "gridcolor": COLORS.border,
            "linecolor": COLORS.divider,
            "tickfont": {"color": COLORS.muted},
        },
        "yaxis": {
            "gridcolor": COLORS.border,
            "linecolor": COLORS.divider,
            "tickfont": {"color": COLORS.muted},
        },
    }
    layout.update(overrides)
    return layout


def get_pillar_color(index: int) -> str:
    return CHART_COLORS[index % len(CHART_COLORS)]


def status_color(value: float, thresholds: tuple[float, float] = (40.0, 70.0)) -> str:
    low, high = thresholds
    if value >= high:
        return COLORS.success
    if value >= low:
        return COLORS.warning
    return COLORS.danger


def apply_page_config(
    page_title: str = "JESA DMAT",
    page_icon: str = "chart",
    layout: str = "wide",
    initial_sidebar_state: str = "expanded",
) -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )


def init_app_style(page_title: str = "JESA DMAT", **page_config_kwargs: Any) -> None:
    apply_page_config(page_title=page_title, **page_config_kwargs)
    inject_custom_css()