# JESA_DMAT/charts/base.py
"""
Abstract base class for all JESA DMAT charts.

Provides a consistent foundation built on Plotly's :class:`go.Figure`.
Every concrete chart (gauge, radar, bar, line) inherits from
:class:`BaseChart` and implements the protected :meth:`_build` method.

The base class handles:

* Automatic figure construction at init time.
* Theme application via registered Plotly template.
* Common metadata (title, subtitle, dimensions).
* Rendering helpers (``show``, ``to_html``, ``write_image``).
* Save helpers with automatic directory creation.
* Validation of constructor arguments.

**Important for subclass authors:**
Subclasses **must** initialize their own attributes **before** calling
``super().__init__()`` because ``_build()`` is invoked during
``__init__`` and may depend on those attributes.

Usage (concrete chart)::

    class MyChart(BaseChart):
        def __init__(self, categories, **kwargs):
            self.categories = categories   # <-- set BEFORE super()
            super().__init__(**kwargs)

        def _build(self) -> None:
            self._fig.add_trace(go.Bar(x=self.categories, y=[1,2,3]))

    chart = MyChart(categories=["A","B","C"], title="Sample")
    chart.show()           # figure is already built
    fig = chart.figure     # access underlying go.Figure (mutable)
"""

from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Final

import plotly.graph_objects as go
import plotly.io as pio

from charts.palette import TEXT_SECONDARY
from charts.theme import TEMPLATE, export_config
from utils.file_manager import ensure_directory

_logger = logging.getLogger(__name__)

__all__ = ["BaseChart"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_WIDTH: Final[int] = 800
_DEFAULT_HEIGHT: Final[int] = 450
_MIN_DIMENSION: Final[int] = 100
_DEFAULT_HTML_JS: Final[str] = "cdn"

# ---------------------------------------------------------------------------
# Register the JESA template so it can be used by name
# ---------------------------------------------------------------------------
_TEMPLATE_NAME: Final[str] = "jesa_dmat"
if _TEMPLATE_NAME not in pio.templates:
    pio.templates[_TEMPLATE_NAME] = TEMPLATE

# ---------------------------------------------------------------------------
# Module-level validation helpers
# ---------------------------------------------------------------------------


def _validate_str(name: str, value: object) -> None:
    """Raise TypeError if ``value`` is not a string."""
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be str, got {type(value).__name__}"
        )


def _validate_dimension(name: str, value: object) -> None:
    """Raise TypeError/ValueError if ``value`` is not a valid dimension."""
    if isinstance(value, bool) or type(value) is not int:
        raise TypeError(
            f"{name} must be an int (not bool), got {type(value).__name__}"
        )
    if value < _MIN_DIMENSION:
        raise ValueError(
            f"{name} must be >= {_MIN_DIMENSION}, got {value}"
        )


def _to_path(path: str | Path) -> Path:
    """Convert a string or Path to an expanded Path, raising on invalid types."""
    if isinstance(path, Path):
        return path.expanduser()
    if isinstance(path, str):
        return Path(path).expanduser()
    raise TypeError(
        f"Expected str or Path, got {type(path).__name__}"
    )


# ======================================================================
# BaseChart
# ======================================================================


class BaseChart(abc.ABC):
    """Abstract base for every JESA DMAT chart.

    Encapsulates a :class:`go.Figure`, applies the JESA theme
    automatically during ``__init__``, and exposes a uniform API for
    rendering and saving.

    Subclasses **must** override :meth:`_build` to populate the figure
    with data traces. The figure is fully constructed and ready to use
    immediately after instantiation.

    Args:
        title: Chart title displayed above the figure.
        subtitle: Optional subtitle string displayed below the main title
            via an annotation.
        width: Figure width in pixels. Must be >= 100.
        height: Figure height in pixels. Must be >= 100.
    """

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        width: int = _DEFAULT_WIDTH,
        height: int = _DEFAULT_HEIGHT,
    ) -> None:
        # -- validation --------------------------------------------------
        _validate_str("title", title)
        _validate_str("subtitle", subtitle)
        _validate_dimension("width", width)
        _validate_dimension("height", height)

        # -- private metadata --------------------------------------------
        self._title: str = title
        self._subtitle: str = subtitle
        self._width: int = width
        self._height: int = height
        self._built: bool = False

        # -- internal figure --------------------------------------------
        self._fig: go.Figure = self._create_figure()

        # -- auto-build (subclass populates traces here) -----------------
        # WARNING: _build() is called during __init__.
        # Subclasses MUST set their own attributes BEFORE super().__init__().
        _logger.debug("Building %s", self.__class__.__name__)
        try:
            self._build()
        except Exception:
            _logger.exception("_build() failed for %s", self.__class__.__name__)
            raise
        else:
            self._built = True
        self._add_subtitle()

        _logger.debug("Chart created (%s)", self.__class__.__name__)

    # ------------------------------------------------------------------
    # Properties (read-only)
    # ------------------------------------------------------------------

    @property
    def title(self) -> str:
        """Chart title."""
        return self._title

    @property
    def subtitle(self) -> str:
        """Chart subtitle."""
        return self._subtitle

    @property
    def width(self) -> int:
        """Figure width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Figure height in pixels."""
        return self._height

    @property
    def figure(self) -> go.Figure:
        """Return the underlying :class:`go.Figure` (mutable reference).

        The figure can be further modified (e.g. adding traces) but its
        identity remains owned by the chart instance.
        """
        return self._fig

    @property
    def built(self) -> bool:
        """Return ``True`` if ``_build()`` has completed successfully."""
        return self._built

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_figure(self) -> go.Figure:
        """Create and pre-style the Plotly figure."""
        return go.Figure(
            layout=dict(
                template=_TEMPLATE_NAME,
                width=self._width,
                height=self._height,
                title=dict(text=self._title) if self._title else None,
            )
        )

    def _add_subtitle(self) -> None:
        """Add the subtitle as an annotation below the main title."""
        if self._subtitle:
            self._fig.add_annotation(
                text=self._subtitle,
                xref="paper",
                yref="paper",
                x=0.5,
                y=1.05,
                xanchor="center",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=12, color=TEXT_SECONDARY),
            )

    def _add_annotation(
        self,
        text: str,
        x: float = 0.5,
        y: float = -0.15,
        font_size: int = 11,
        color: str = TEXT_SECONDARY,
    ) -> None:
        """Add a generic annotation below the chart (e.g. source, footnote).

        Args:
            text: Annotation text.
            x: Horizontal position in paper coordinates (0–1).
            y: Vertical position in paper coordinates.
            font_size: Font size.
            color: Text color (defaults to secondary text).
        """
        self._fig.add_annotation(
            text=text,
            xref="paper",
            yref="paper",
            x=x,
            y=y,
            xanchor="center",
            yanchor="top",
            showarrow=False,
            font=dict(size=font_size, color=color),
        )

    # ------------------------------------------------------------------
    # Abstract interface (protected – subclasses override this)
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _build(self) -> None:
        """Populate the figure with data traces.

        Subclasses **must** implement this method. It is called
        automatically during ``__init__`` after the base figure is
        created and themed.

        **Important:** All subclass-specific attributes (e.g. categories,
        data) must be set **before** ``super().__init__()`` is called.
        """
        ...

    # ------------------------------------------------------------------
    # Special methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"title={self._title!r}, "
            f"width={self._width}, "
            f"height={self._height}, "
            f"traces={len(self._fig.data)}, "
            f"built={self._built}"
            f")"
        )

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Display the figure using Plotly's default renderer."""
        self._fig.show()

    def to_html(
        self,
        include_plotlyjs: bool | str = _DEFAULT_HTML_JS,
        full_html: bool = True,
    ) -> str:
        """Return the figure as an HTML string.

        Args:
            include_plotlyjs: How to include Plotly.js. ``True`` embeds
                the full bundle, ``"cdn"`` uses a CDN link (default, lighter),
                ``False`` omits it entirely.
            full_html: If ``True``, return a complete HTML document;
                otherwise an inline ``<div>`` snippet.

        Returns:
            HTML representation of the figure.
        """
        return self._fig.to_html(
            include_plotlyjs=include_plotlyjs,
            full_html=full_html,
        )

    def write_image(self, file: str | Path, **kwargs: object) -> None:
        """Write the figure as a static image.

        Uses the default export configuration from
        :func:`charts.theme.export_config`. Extra keyword arguments are
        forwarded to ``fig.write_image()``.

        Args:
            file: Destination file path (any format supported by Plotly).
            **kwargs: Additional arguments passed to ``fig.write_image()``.

        Raises:
            RuntimeError: If Plotly/Kaleido fails to write the image.
        """
        config = export_config()
        config.update(kwargs)
        try:
            self._fig.write_image(str(file), **config)
        except Exception as exc:
            _logger.exception("Failed to write image to %s", file)
            raise RuntimeError(
                f"Failed to write image to {file!r}"
            ) from exc

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Return the figure as a JSON string."""
        return self._fig.to_json()

    def clone_figure(self) -> go.Figure:
        """Return a deep copy of the figure as a standalone Plotly object.

        Returns:
            A new :class:`go.Figure` identical to the current one.
        """
        return go.Figure(self._fig.to_dict())

    # ------------------------------------------------------------------
    # Save helpers (auto-create directories)
    # ------------------------------------------------------------------

    def save_html(self, path: str | Path) -> Path:
        """Save the figure as a standalone HTML file.

        Creates parent directories if they do not exist. Uses CDN for
        Plotly.js by default to keep file size small.

        Args:
            path: Destination file path (``.html`` extension recommended).

        Returns:
            Resolved :class:`Path` to the saved file.

        Raises:
            TypeError: If ``path`` is not a ``str`` or ``Path``.
        """
        dest = _to_path(path)
        ensure_directory(dest.parent)
        self._fig.write_html(str(dest), include_plotlyjs=_DEFAULT_HTML_JS)
        return dest.resolve()

    def save_image(self, path: str | Path, **kwargs: object) -> Path:
        """Save the figure as a static image file.

        Creates parent directories if they do not exist.

        Args:
            path: Destination file path (any format supported by Plotly).
            **kwargs: Additional arguments forwarded to :func:`export_config`.

        Returns:
            Resolved :class:`Path` to the saved file.

        Raises:
            TypeError: If ``path`` is not a ``str`` or ``Path``.
            RuntimeError: If the image cannot be written.
        """
        dest = _to_path(path)
        ensure_directory(dest.parent)
        self.write_image(dest, **kwargs)
        return dest.resolve()
    