"""Tests de validation pour assets/styles/components.css.

Ce module valide la structure, la cohérence et la conformité du
fichier components.css avec le design system JESA DMAT défini dans
main.css et theme.py.

Les tests couvrent :
- la syntaxe CSS et l'appariement des accolades,
- l'absence de conflit avec utilities.css,
- l'extension cohérente des classes définies dans main.css,
- la réutilisation stricte des tokens du design system,
- la cohérence du namespace .dmat-* et de la méthodologie BEM,
- la présence des sections et composants obligatoires,
- la validité des propriétés critiques (focus, hover, transitions).
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


def _count_hardcoded_colors(css_text: str) -> list[tuple[int, str, str]]:
    """Retourne les couleurs hex codées en dur avec leur ligne."""
    results: list[tuple[int, str, str]] = []
    lines = css_text.split("\n")
    for i, line in enumerate(lines, 1):
        if "var(" in line or line.strip().startswith("/*"):
            continue
        matches = re.findall(r"#([0-9A-Fa-f]{3,8})", line)
        for m in matches:
            if m.upper() != "FFFFFF":
                results.append((i, m, line.strip()))
    return results


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def components_css() -> str:
    """Contenu brut de components.css."""
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "styles" / "components.css"
    )
    if not path.exists():
        pytest.skip("components.css not found")
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
def utilities_css() -> str:
    """Contenu brut de utilities.css (pour vérifier les conflits)."""
    path = (
        Path(__file__).resolve().parent.parent
        / "assets" / "styles" / "utilities.css"
    )
    if not path.exists():
        pytest.skip("utilities.css not found")
    return _read_css(path)


@pytest.fixture(scope="module")
def comp_rules(components_css: str) -> dict[str, dict[str, str]]:
    """Règles CSS parsées de components.css."""
    return _extract_rules(components_css)


@pytest.fixture(scope="module")
def main_vars(main_css: str) -> dict[str, str]:
    """Variables CSS définies dans main.css."""
    return _extract_css_vars(main_css)


@pytest.fixture(scope="module")
def main_rules(main_css: str) -> dict[str, dict[str, str]]:
    """Règles CSS parsées de main.css."""
    return _extract_rules(main_css)


# ---------------------------------------------------------------------------
# Tests de structure
# ---------------------------------------------------------------------------

class TestComponentsStructure:
    """Valide l'intégrité syntaxique et structurelle du fichier."""

    def test_file_exists(self, components_css: str) -> None:
        """Le fichier doit exister et être non vide."""
        assert components_css, "components.css is empty"

    def test_braces_balanced(self, components_css: str) -> None:
        """Les accolades doivent être parfaitement appariées."""
        assert components_css.count("{") == components_css.count("}"), (
            "Unbalanced braces in components.css"
        )

    def test_no_bom(self, components_css: str) -> None:
        """Le fichier ne doit pas contenir de BOM UTF-8."""
        assert not components_css.startswith("\ufeff"), (
            "components.css contains UTF-8 BOM"
        )

    def test_sections_documented(self, components_css: str) -> None:
        """Chaque section doit être précédée d'un commentaire numéroté."""
        sections = re.findall(
            r"/\*\s*={10,}\s*\n\s*(\d+)\.\s*(\w[\w /]+)\s*\n",
            components_css,
        )
        expected = [
            "CARDS", "METRIC CARDS", "BUTTONS", "BADGES",
            "ALERTS", "TABLES", "PANELS", "FORMS",
            "EMPTY STATES", "LOADING / SPINNER",
            "STATUS INDICATORS", "RESPONSIVE COMPONENT BEHAVIOR",
            "REDUCED MOTION",
        ]
        section_names = [s[1].upper() for s in sections]
        for section in expected:
            assert any(section in sn for sn in section_names), (
                f"Section '{section}' not found in components.css"
            )


# ---------------------------------------------------------------------------
# Tests de namespace et méthodologie BEM
# ---------------------------------------------------------------------------

class TestComponentsNamespace:
    """Valide le namespace .dmat-* et la méthodologie BEM."""

    def test_all_classes_use_dmat_prefix(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Toutes les classes doivent commencer par .dmat- ou être des media queries."""
        for selector in comp_rules:
            if selector.startswith("@"):
                continue
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                assert cls.startswith("dmat-"), (
                    f"Class '.{cls}' does not use 'dmat-' namespace"
                )

    def test_no_u_prefix_in_components(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Aucune classe ne doit utiliser le namespace réservé .u-*."""
        for selector in comp_rules:
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                assert not cls.startswith("u-"), (
                    f"Class '.{cls}' uses reserved 'u-' namespace"
                )

    def test_bem_element_naming(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les éléments BEM doivent utiliser __ (double underscore)."""
        for selector in comp_rules:
            if selector.startswith("@"):
                continue
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                if "__" in cls:
                    parts = cls.split("__")
                    assert len(parts) == 2, (
                        f"Invalid BEM element naming: .{cls}"
                    )
                    assert parts[0].startswith("dmat-"), (
                        f"BEM element without block prefix: .{cls}"
                    )

    def test_bem_modifier_naming(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les modificateurs BEM doivent utiliser -- (double dash)."""
        for selector in comp_rules:
            if selector.startswith("@"):
                continue
            classes = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", selector)
            for cls in classes:
                if "--" in cls:
                    parts = cls.split("--")
                    assert len(parts) == 2, (
                        f"Invalid BEM modifier naming: .{cls}"
                    )
                    assert parts[0].startswith("dmat-"), (
                        f"BEM modifier without block prefix: .{cls}"
                    )


# ---------------------------------------------------------------------------
# Tests de cohérence avec le design system
# ---------------------------------------------------------------------------

class TestComponentsDesignTokens:
    """Valide la réutilisation stricte des tokens du design system."""

    def test_only_known_css_vars_used(
        self, components_css: str, main_vars: dict[str, str]
    ) -> None:
        """Toutes les var(--dmat-*) utilisées doivent exister dans main.css."""
        used = _extract_used_vars(components_css)
        defined = set(main_vars.keys())
        unknown = used - defined
        assert not unknown, f"Unknown CSS variables used: {unknown}"

    def test_no_hardcoded_colors(self, components_css: str) -> None:
        """Aucune couleur hex ne doit être codée en dur (sauf #FFFFFF)."""
        hardcoded = _count_hardcoded_colors(components_css)
        assert not hardcoded, (
            f"Hardcoded colors found: {hardcoded[:5]}"
        )

    def test_uses_design_tokens_for_radius(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les radius doivent référencer les tokens du design system."""
        for sel, props in comp_rules.items():
            if "border-radius" in props:
                val = props["border-radius"]
                assert (
                    "var(--dmat-radius-" in val
                    or val == "50%"
                    or val == "9999px"
                ), f"{sel} uses hardcoded radius: {val}"

    def test_uses_design_tokens_for_shadows(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les ombres doivent référencer les tokens du design system."""
        for sel, props in comp_rules.items():
            if "box-shadow" in props:
                val = props["box-shadow"]
                if val != "none":
                    assert (
                        "var(--dmat-shadow-" in val
                        or "0 0 0 1px" in val
                    ), f"{sel} uses hardcoded shadow: {val}"

    def test_uses_design_tokens_for_fonts(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les font-family doivent référencer le token du design system."""
        for sel, props in comp_rules.items():
            if "font-family" in props:
                val = props["font-family"]
                assert "var(--dmat-font)" in val, (
                    f"{sel} uses hardcoded font-family: {val}"
                )

    def test_uses_design_tokens_for_transitions(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les transitions doivent utiliser des durées cohérentes."""
        for sel, props in comp_rules.items():
            if "transition" in props:
                val = props["transition"]
                durations = re.findall(r"(\d+(?:\.\d+)?)(ms|s)", val)
                for amount, unit in durations:
                    duration_ms = float(amount) * (
                        1000 if unit == "s" else 1
                    )
                    assert duration_ms <= 300, (
                        f"{sel} has excessive transition: {amount}{unit}"
                    )


# ---------------------------------------------------------------------------
# Tests d'extension cohérente de main.css
# ---------------------------------------------------------------------------

class TestComponentsExtendsMain:
    """Valide que components.css étend main.css sans écraser."""

    def test_card_classes_extended_not_overridden(
        self,
        comp_rules: dict[str, dict[str, str]],
        main_rules: dict[str, dict[str, str]],
    ) -> None:
        """Les classes .dmat-card* de main.css ne doivent pas être redéfinies."""
        main_card_classes = {
            s for s in main_rules if s.startswith(".dmat-card")
        }
        overridden = main_card_classes & set(comp_rules.keys())
        for cls in overridden:
            main_props = set(main_rules[cls].keys())
            comp_props = set(comp_rules[cls].keys())
            conflicts = main_props & comp_props
            assert not conflicts, (
                f"Class {cls} overrides properties from main.css: "
                f"{conflicts}"
            )

    def test_badge_classes_extended_not_overridden(
        self,
        comp_rules: dict[str, dict[str, str]],
        main_rules: dict[str, dict[str, str]],
    ) -> None:
        """Les classes .dmat-badge* de main.css ne doivent pas être redéfinies."""
        main_badge_classes = {
            s for s in main_rules if s.startswith(".dmat-badge")
        }
        overridden = main_badge_classes & set(comp_rules.keys())
        for cls in overridden:
            main_props = set(main_rules[cls].keys())
            comp_props = set(comp_rules[cls].keys())
            conflicts = main_props & comp_props
            assert not conflicts, (
                f"Class {cls} overrides properties from main.css: "
                f"{conflicts}"
            )


# ---------------------------------------------------------------------------
# Tests d'absence de conflit
# ---------------------------------------------------------------------------

class TestComponentsNoConflict:
    """Valide l'absence de conflit avec utilities.css."""

    def test_no_selector_conflict_with_utilities(
        self, components_css: str, utilities_css: str
    ) -> None:
        """Aucun sélecteur .dmat-* ne doit exister dans utilities.css."""
        comp_rules = _extract_rules(components_css)
        util_rules = _extract_rules(utilities_css)
        comp_selectors = {s for s in comp_rules if s.startswith(".dmat-")}
        util_selectors = set(util_rules.keys())
        conflicts = comp_selectors & util_selectors
        assert not conflicts, (
            f"Selector conflicts with utilities.css: {conflicts}"
        )


# ---------------------------------------------------------------------------
# Tests de complétude
# ---------------------------------------------------------------------------

class TestComponentsCompleteness:
    """Valide que les composants essentiels sont tous présents."""

    REQUIRED_COMPONENTS = [
        # Cards
        ".dmat-card__header", ".dmat-card__body", ".dmat-card__footer",
        ".dmat-card--highlighted", ".dmat-card--compact",
        ".dmat-card--chart",
        # Metrics
        ".dmat-metric", ".dmat-metric__label", ".dmat-metric__value",
        ".dmat-metric__delta", ".dmat-metric__icon",
        ".dmat-metric--positive", ".dmat-metric--negative",
        ".dmat-metric--warning", ".dmat-metric--neutral",
        # Buttons
        ".dmat-button", ".dmat-button--primary", ".dmat-button--secondary",
        ".dmat-button--success", ".dmat-button--warning",
        ".dmat-button--danger", ".dmat-button--ghost",
        ".dmat-button--sm", ".dmat-button--lg",
        ".dmat-button__icon",
        # Badges
        ".dmat-badge--info", ".dmat-badge--neutral",
        # Alerts
        ".dmat-alert", ".dmat-alert__icon", ".dmat-alert__content",
        ".dmat-alert--info", ".dmat-alert--success",
        ".dmat-alert--warning", ".dmat-alert--danger",
        # Tables
        ".dmat-table", ".dmat-table__header", ".dmat-table__row",
        ".dmat-table__cell", ".dmat-table--striped",
        ".dmat-table--compact",
        # Panels
        ".dmat-panel", ".dmat-panel__header", ".dmat-panel__title",
        ".dmat-panel__body", ".dmat-panel--highlighted",
        # Forms
        ".dmat-form", ".dmat-form__group", ".dmat-form__label",
        ".dmat-form__help", ".dmat-form__error",
        # Empty states
        ".dmat-empty-state", ".dmat-empty-state__icon",
        ".dmat-empty-state__title", ".dmat-empty-state__text",
        # Loading
        ".dmat-loading", ".dmat-spinner",
        # Status
        ".dmat-status", ".dmat-status--success",
        ".dmat-status--warning", ".dmat-status--danger",
        ".dmat-status--neutral",
    ]

    def test_all_required_components_present(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Tous les composants obligatoires doivent être définis."""
        for comp in self.REQUIRED_COMPONENTS:
            found = any(comp in sel for sel in comp_rules)
            assert found, f"Required component '{comp}' not found"

    def test_button_hover_states(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Tous les boutons doivent avoir des états hover définis."""
        variants = [
            "primary", "secondary", "success", "warning",
            "danger", "ghost",
        ]
        for variant in variants:
            hover_sel = f".dmat-button--{variant}:hover:not(:disabled)"
            found = any(hover_sel in sel for sel in comp_rules)
            assert found, (
                f"Missing hover state for .dmat-button--{variant}"
            )

    def test_button_focus_states(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les boutons doivent avoir un état focus-visible."""
        found = any(
            ".dmat-button:focus-visible" in sel
            for sel in comp_rules
        )
        assert found, "Missing focus-visible state for .dmat-button"

    def test_disabled_button_states(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les boutons doivent avoir un état disabled."""
        found = any(
            ".dmat-button:disabled" in sel
            for sel in comp_rules
        )
        assert found, "Missing disabled state for .dmat-button"

    def test_reduced_motion_present(self, components_css: str) -> None:
        """La requête prefers-reduced-motion doit être présente."""
        assert "prefers-reduced-motion" in components_css, (
            "Missing prefers-reduced-motion media query"
        )

    def test_responsive_breakpoint_present(
        self, components_css: str
    ) -> None:
        """Au moins un breakpoint responsive doit être défini."""
        assert "@media (max-width: 768px)" in components_css, (
            "Missing mobile breakpoint"
        )


# ---------------------------------------------------------------------------
# Tests d'accessibilité
# ---------------------------------------------------------------------------

class TestComponentsAccessibility:
    """Valide les critères d'accessibilité des composants."""

    def test_focus_visible_on_interactive_elements(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les éléments interactifs doivent avoir un focus visible."""
        interactive = [
            ".dmat-button", ".dmat-alert", ".dmat-table__row"
        ]
        for sel_base in interactive:
            has_focus = any(
                f"{sel_base}:focus" in sel
                or f"{sel_base}:focus-visible" in sel
                for sel in comp_rules
            )
            assert has_focus, (
                f"Missing focus state for {sel_base}"
            )

    def test_sufficient_contrast_on_buttons(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les boutons colorés doivent avoir du texte blanc."""
        colored_buttons = [
            ".dmat-button--primary", ".dmat-button--secondary",
            ".dmat-button--success", ".dmat-button--warning",
            ".dmat-button--danger",
        ]
        for sel in colored_buttons:
            if sel in comp_rules:
                color = comp_rules[sel].get("color", "")
                assert color == "#FFFFFF", (
                    f"{sel} should have white text, got: {color}"
                )

    def test_status_indicators_not_color_only(
        self, comp_rules: dict[str, dict[str, str]]
    ) -> None:
        """Les indicateurs de status utilisent un point visuel + texte."""
        for sel in comp_rules:
            if sel.startswith(".dmat-status--"):
                base = sel.split("--")[0]
                before_sel = f"{base}::before"
                has_before = any(before_sel in s for s in comp_rules)
                assert has_before, (
                    f"{sel} missing ::before visual indicator"
                )