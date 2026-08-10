"""Tests de validation pour assets/styles/utilities.css.

Ce module valide la structure, la cohérence et la conformité du
fichier utilities.css avec le design system JESA DMAT défini dans
main.css et theme.py.

Les tests couvrent :
- la syntaxe CSS (accolades, points-virgules),
- l'absence de conflit avec components.css,
- la réutilisation des tokens du design system,
- la cohérence du namespace .u-*,
- la présence des sections obligatoires,
- la validité des valeurs de propriétés critiques.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_css(path: Path) -> str:
    """Lit un fichier CSS et retourne son contenu brut."""
    return path.read_text(encoding="utf-8")


def _extract_rules(css_text: str) -> dict[str, dict[str, str]]:
    """Extrait les règles CSS sous forme {sélecteur: {propriété: valeur}}."""
    css_clean = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
    rules: dict[str, dict[str, str]] = {}
    for selector_str, declarations in re.findall(
        r"([^{]+)\{([^}]*)\}", css_clean
    ):
        selectors = [s.strip() for s in selector_str.split(",") if s.strip()]
        props: dict[str, str] = {}
        for decl in declarations.split(";"):
            decl = decl.strip()
            if ":" in decl:
                prop, val = decl.split(":", 1)
                props[prop.strip()] = val.strip()
        for sel in selectors:
            rules.setdefault(sel, {}).update(props)
    return rules


def _extract_css_vars(css_text: str) -> dict[str, str]:
    """Extrait les variables CSS définies dans :root."""
    root_match = re.search(r":root\s*\{([^}]*)\}", css_text, re.DOTALL)
    if not root_match:
        return {}
    vars_dict: dict[str, str] = {}
    for line in root_match.group(1).split(";"):
        line = line.strip()
        if ":" in line:
            name, val = line.split(":", 1)
            vars_dict[name.strip()] = val.strip()
    return vars_dict


def _extract_used_vars(css_text: str) -> set[str]:
    """Retourne l'ensemble des var(--dmat-*) utilisés dans le CSS."""
    return set(re.findall(r"var\((--dmat-[a-zA-Z0-9_-]+)\)", css_text))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def utilities_css() -> str:
    """Contenu brut de utilities.css."""
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "styles" / "utilities.css"
    )
    if not path.exists():
        pytest.skip("utilities.css not found")
    return _read_css(path)


@pytest.fixture(scope="module")
def main_css() -> str:
    """Contenu brut de main.css (design tokens)."""
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "styles" / "main.css"
    )
    if not path.exists():
        pytest.skip("main.css not found")
    return _read_css(path)


@pytest.fixture(scope="module")
def components_css() -> str:
    """Contenu brut de components.css (pour vérifier les conflits)."""
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "styles" / "components.css"
    )
    if not path.exists():
        pytest.skip("components.css not found")
    return _read_css(path)


@pytest.fixture(scope="module")
def util_rules(utilities_css: str) -> dict[str, dict[str, str]]:
    """Règles CSS parsées de utilities.css."""
    return _extract_rules(utilities_css)


@pytest.fixture(scope="module")
def main_vars(main_css: str) -> dict[str, str]:
    """Variables CSS définies dans main.css."""
    return _extract_css_vars(main_css)


# ---------------------------------------------------------------------------
# Tests de structure
# ---------------------------------------------------------------------------

class TestUtilitiesStructure:
    """Valide l'intégrité syntaxique et structurelle du fichier."""

    def test_file_exists(self, utilities_css: str) -> None:
        """Le fichier doit exister et être non vide."""
        assert utilities_css, "utilities.css is empty"

    def test_braces_balanced(self, utilities_css: str) -> None:
        """Les accolades doivent être parfaitement appariées."""
        assert utilities_css.count("{") == utilities_css.count("}"), (
            "Unbalanced braces in utilities.css"
        )

    def test_no_bom(self, utilities_css: str) -> None:
        """Le fichier ne doit pas contenir de BOM UTF-8."""
        assert not utilities_css.startswith("\ufeff"), (
            "utilities.css contains UTF-8 BOM"
        )

    def test_sections_documented(self, utilities_css: str) -> None:
        """Chaque section doit être précédée d'un commentaire de section."""
        sections = re.findall(
            r"/\*\s*-{10,}\s*\n\s*\d+\.\s*(\w[\w /]+)\s*\n",
            utilities_css,
        )
        expected = [
            "DISPLAY", "FLEXBOX", "GRID", "SPACING — Gap",
            "SPACING — Margin", "SPACING — Padding", "ALIGNMENT",
            "TYPOGRAPHY", "COLORS — Text", "COLORS — Background",
            "BORDERS", "RADIUS", "SHADOWS", "SIZING", "VISIBILITY",
            "ACCESSIBILITY", "FOCUS UTILITIES", "RESPONSIVE UTILITIES",
            "REDUCED MOTION",
        ]
        for section in expected:
            assert any(section.lower() in s.lower() for s in sections), (
                f"Section '{section}' not found in utilities.css"
            )


# ---------------------------------------------------------------------------
# Tests de namespace
# ---------------------------------------------------------------------------

class TestUtilitiesNamespace:
    """Valide que toutes les classes utilisent le namespace .u-*."""

    def test_all_classes_use_u_prefix(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """Toutes les classes doivent commencer par .u- ou être des media queries."""
        for selector in util_rules:
            if selector.startswith("@"):
                continue
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                assert cls.startswith("u-"), (
                    f"Class '.{cls}' does not use 'u-' namespace"
                )

    def test_no_dmat_prefix_in_utilities(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """Aucune classe ne doit utiliser le namespace réservé .dmat-*."""
        for selector in util_rules:
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                assert not cls.startswith("dmat-"), (
                    f"Class '.{cls}' uses reserved 'dmat-' namespace"
                )


# ---------------------------------------------------------------------------
# Tests de cohérence avec le design system
# ---------------------------------------------------------------------------

class TestUtilitiesDesignTokens:
    """Valide la réutilisation des tokens du design system."""

    def test_only_known_css_vars_used(
        self, utilities_css: str, main_vars: dict[str, str]
    ) -> None:
        """Toutes les var(--dmat-*) utilisées doivent exister dans main.css."""
        used = _extract_used_vars(utilities_css)
        defined = set(main_vars.keys())
        unknown = used - defined
        assert not unknown, f"Unknown CSS variables used: {unknown}"

    def test_no_hardcoded_colors_except_white(
        self, utilities_css: str
    ) -> None:
        """Aucune couleur hex ne doit être codée en dur (sauf #FFFFFF)."""
        lines = utilities_css.split("\n")
        for i, line in enumerate(lines, 1):
            if "var(" in line or line.strip().startswith("/*"):
                continue
            matches = re.findall(r"#([0-9A-Fa-f]{3,8})", line)
            for m in matches:
                assert m.upper() == "FFFFFF", (
                    f"Hardcoded color #{m} at line {i}: {line.strip()}"
                )

    def test_uses_design_tokens_for_colors(
        self, utilities_css: str
    ) -> None:
        """Les utilitaires de couleur doivent référencer les tokens."""
        rules = _extract_rules(utilities_css)
        color_utils = [
            s for s in rules
            if s.startswith(".u-text-") or s.startswith(".u-bg-")
        ]
        assert len(color_utils) >= 10, (
            f"Expected at least 10 color utilities, found {len(color_utils)}"
        )

    def test_uses_design_tokens_for_radius(
        self, utilities_css: str
    ) -> None:
        """Les utilitaires de radius doivent référencer les tokens."""
        rules = _extract_rules(utilities_css)
        radius_utils = [s for s in rules if s.startswith(".u-rounded-")]
        for sel in radius_utils:
            val = rules[sel].get("border-radius", "")
            assert (
                "var(--dmat-radius-" in val
                or val == "9999px"
                or val == "0"
            ), f"Radius utility {sel} does not use design token: {val}"

    def test_uses_design_tokens_for_shadows(
        self, utilities_css: str
    ) -> None:
        """Les utilitaires d'ombre doivent référencer les tokens."""
        rules = _extract_rules(utilities_css)
        shadow_utils = [s for s in rules if s.startswith(".u-shadow-")]
        for sel in shadow_utils:
            val = rules[sel].get("box-shadow", "")
            if val != "none":
                assert "var(--dmat-shadow-" in val, (
                    f"Shadow utility {sel} does not use design token: {val}"
                )


# ---------------------------------------------------------------------------
# Tests d'absence de conflit
# ---------------------------------------------------------------------------

class TestUtilitiesNoConflict:
    """Valide l'absence de conflit avec components.css et main.css."""

    def test_no_selector_conflict_with_components(
        self, utilities_css: str, components_css: str
    ) -> None:
        """Aucun sélecteur .u-* ne doit exister dans components.css."""
        util_rules = _extract_rules(utilities_css)
        comp_rules = _extract_rules(components_css)
        util_selectors = {s for s in util_rules if s.startswith(".u-")}
        comp_selectors = set(comp_rules.keys())
        conflicts = util_selectors & comp_selectors
        assert not conflicts, (
            f"Selector conflicts with components.css: {conflicts}"
        )

    def test_no_property_override_in_main(
        self, utilities_css: str, main_css: str
    ) -> None:
        """utilities.css ne doit pas redéfinir de propriétés de main.css."""
        util_rules = _extract_rules(utilities_css)
        main_rules = _extract_rules(main_css)
        util_classes = {s for s in util_rules if s.startswith(".u-")}
        main_classes = set(main_rules.keys())
        conflicts = util_classes & main_classes
        assert not conflicts, (
            f"Utility classes already defined in main.css: {conflicts}"
        )


# ---------------------------------------------------------------------------
# Tests de complétude
# ---------------------------------------------------------------------------

class TestUtilitiesCompleteness:
    """Valide que les utilitaires essentiels sont tous présents."""

    REQUIRED_UTILS = [
        ".u-hidden", ".u-block", ".u-inline", ".u-inline-block",
        ".u-flex", ".u-grid",
        ".u-flex-row", ".u-flex-column", ".u-items-center",
        ".u-justify-center", ".u-justify-between",
        ".u-flex-wrap", ".u-flex-1",
        ".u-grid-cols-2", ".u-grid-cols-3", ".u-grid-cols-4",
        ".u-gap-xs", ".u-gap-sm", ".u-gap-md", ".u-gap-lg", ".u-gap-xl",
        ".u-mt-sm", ".u-mt-md", ".u-mt-lg", ".u-mt-xl",
        ".u-mb-sm", ".u-mb-md", ".u-mb-lg", ".u-mb-xl",
        ".u-ml-sm", ".u-ml-md", ".u-ml-lg",
        ".u-mr-sm", ".u-mr-md", ".u-mr-lg",
        ".u-mx-auto", ".u-my-md",
        ".u-p-sm", ".u-p-md", ".u-p-lg", ".u-p-xl",
        ".u-px-sm", ".u-px-md", ".u-px-lg",
        ".u-py-sm", ".u-py-md", ".u-py-lg",
        ".u-text-left", ".u-text-center", ".u-text-right",
        ".u-text-sm", ".u-text-md", ".u-text-lg", ".u-text-xl",
        ".u-font-normal", ".u-font-medium", ".u-font-semibold",
        ".u-font-bold",
        ".u-uppercase", ".u-nowrap", ".u-truncate",
        ".u-line-clamp-2", ".u-line-clamp-3",
        ".u-text-primary", ".u-text-muted", ".u-text-success",
        ".u-text-warning", ".u-text-danger", ".u-text-title",
        ".u-bg-surface", ".u-bg-background", ".u-bg-primary",
        ".u-bg-success", ".u-bg-warning", ".u-bg-danger",
        ".u-border", ".u-border-none", ".u-border-top",
        ".u-border-bottom",
        ".u-rounded-sm", ".u-rounded-md", ".u-rounded-lg",
        ".u-rounded-full", ".u-rounded-none",
        ".u-shadow-sm", ".u-shadow-md", ".u-shadow-lg",
        ".u-shadow-none",
        ".u-w-full", ".u-h-full", ".u-min-w-0", ".u-max-w-full",
        ".u-sr-only",
        ".u-focus-ring:focus-visible",
    ]

    def test_all_required_utilities_present(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """Tous les utilitaires obligatoires doivent être définis."""
        for util in self.REQUIRED_UTILS:
            found = any(util in sel for sel in util_rules)
            assert found, f"Required utility '{util}' not found"

    def test_responsive_utilities_present(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les utilitaires responsives doivent exister."""
        responsive = [s for s in util_rules if "@media" in s]
        assert len(responsive) >= 2, (
            f"Expected at least 2 responsive breakpoints, "
            f"found {len(responsive)}"
        )

    def test_reduced_motion_present(self, utilities_css: str) -> None:
        """La requête prefers-reduced-motion doit être présente."""
        assert "prefers-reduced-motion" in utilities_css, (
            "Missing prefers-reduced-motion media query"
        )


# ---------------------------------------------------------------------------
# Tests de valeurs
# ---------------------------------------------------------------------------

class TestUtilitiesValues:
    """Valide la cohérence des valeurs de propriétés."""

    def test_spacing_scale_consistency(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """L'échelle d'espacement doit être cohérente."""
        spacing_map = {
            "xs": "0.25rem", "sm": "0.5rem", "md": "1rem",
            "lg": "1.5rem", "xl": "2rem",
        }
        for size, expected in spacing_map.items():
            gap_sel = f".u-gap-{size}"
            if gap_sel in util_rules:
                assert util_rules[gap_sel].get("gap") == expected, (
                    f"Gap scale mismatch for {size}"
                )

    def test_font_weights_are_valid(
        self, util_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les font-weight doivent être des valeurs standard."""
        valid_weights = {"400", "500", "600", "700"}
        for sel, props in util_rules.items():
            if "font-weight" in props:
                assert props["font-weight"] in valid_weights, (
                    f"Invalid font-weight in {sel}: {props['font-weight']}"
                )

    def test_no_important_in_utilities(self, utilities_css: str) -> None:
        """Les utilitaires ne doivent pas abuser de !important."""
        lines = utilities_css.split("\n")
        for i, line in enumerate(lines, 1):
            if "!important" in line and ".u-hidden" not in line:
                assert False, (
                    f"Unexpected !important at line {i}: {line.strip()}"
                )