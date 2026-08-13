# JESA_DMAT/components/tables.py

"""
Professional table components for JESA DMAT.

This module provides functions for displaying interactive data tables
in Streamlit pages, using the existing design system.

The components are specialized for digital maturity data:
scores, levels, statuses, etc.

Typical usage:
from components.tables import render_data_table, render_status_table, render_score_table

# Generic table
render_data_table(
    data=df,
    title="Assessment Results",
    height=400,
    hide_index=True,
)

# Status table
render_status_table(
    data=df,
    status_column="Status",
    title="Assessment Status",
)

# Score table (scores as percentages 0-100)
render_score_table(
    data=df,
    score_column="Score",
    level_column="Level",
    title="Digital Maturity by Pillar",
    score_scale="percentage",
    decimals=1,
)
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Literal

import pandas as pd
import streamlit as st


# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _validate_dataframe(df: pd.DataFrame) -> None:
    """
    Valide qu'un DataFrame n'est pas vide.

    Args:
        df: DataFrame à valider.

    Raises:
        ValueError: Si le DataFrame est vide.
    """
    if df.empty:
        raise ValueError("The DataFrame is empty.")


def _validate_column_exists(
    df: pd.DataFrame,
    column: str,
    param_name: str,
) -> None:
    """
    Valide qu'une colonne existe dans le DataFrame.

    Args:
        df: DataFrame.
        column: Nom de la colonne.
        param_name: Nom du paramètre pour le message d'erreur.

    Raises:
        ValueError: Si la colonne n'existe pas.
    """
    if column not in df.columns:
        raise ValueError(
            f"The column '{column}' specified for '{param_name}' "
            "does not exist in the DataFrame."
        )


def _prepare_column_config(
    config: Optional[dict[str, Any]] = None,
    column_order: Optional[Sequence[str]] = None,
) -> tuple[dict[str, Any], Optional[list[str]]]:
    """
    Prépare la configuration des colonnes pour st.dataframe.

    Args:
        config: Dictionnaire de configuration des colonnes (peut être None).
        column_order: Ordre des colonnes (peut être None).

    Returns:
        Tuple (column_config, column_order).
    """
    if config is None:
        config = {}

    return config, column_order


# ============================================================================
# PUBLIC COMPONENTS
# ============================================================================


def render_data_table(
    data: pd.DataFrame,
    title: Optional[str] = None,
    height: Optional[int] = None,
    hide_index: bool = True,
    column_order: Optional[Sequence[str]] = None,
    column_config: Optional[dict[str, Any]] = None,
    width: str | int = "stretch",
    key: Optional[str] = None,
    compact: bool = False,
    **kwargs: Any,
) -> None:
    """
    Affiche un tableau de données générique avec st.dataframe.

    Args:
        data (pd.DataFrame): Données à afficher.
        title (str, optionnel): Titre du tableau.
        height (int, optionnel): Hauteur en pixels.
        hide_index (bool): Si True, masque l'index. Par défaut True.
        column_order (Sequence[str], optionnel): Ordre des colonnes.
        column_config (dict, optionnel):
            Configuration des colonnes pour st.dataframe.
        width (str | int):
            Largeur du tableau. "stretch" pour utiliser tout l'espace,
            ou un nombre en pixels. Par défaut "stretch".
        key (str, optionnel): Clé unique pour le widget.
        compact (bool):
            Réservé pour une future extension CSS.
        **kwargs:
            Arguments supplémentaires passés à st.dataframe.

    Returns:
        None

    Raises:
        ValueError: Si le DataFrame est vide.
    """
    _validate_dataframe(data)

    # Préparer la configuration des colonnes
    config, order = _prepare_column_config(
        column_config,
        column_order,
    )

    # Afficher le titre si fourni
    if title:
        st.markdown(f"### {title}")

    # Utiliser st.dataframe avec l'API moderne
    st.dataframe(
        data,
        width=width,
        height=height,
        hide_index=hide_index,
        column_order=order,
        column_config=config,
        key=key,
        **kwargs,
    )


def render_status_table(
    data: pd.DataFrame,
    status_column: str,
    title: Optional[str] = None,
    height: Optional[int] = None,
    hide_index: bool = True,
    column_order: Optional[Sequence[str]] = None,
    column_config: Optional[dict[str, Any]] = None,
    width: str | int = "stretch",
    key: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Affiche un tableau avec une colonne de statut normalisée.

    Args:
        data (pd.DataFrame): Données à afficher.
        status_column (str): Nom de la colonne contenant les statuts.
        title (str, optionnel): Titre du tableau.
        height (int, optionnel): Hauteur en pixels.
        hide_index (bool): Si True, masque l'index. Par défaut True.
        column_order (Sequence[str], optionnel): Ordre des colonnes.
        column_config (dict, optionnel):
            Configuration des colonnes.
        width (str | int):
            Largeur du tableau. "stretch" pour utiliser tout l'espace,
            ou un nombre en pixels. Par défaut "stretch".
        key (str, optionnel): Clé unique pour le widget.
        **kwargs:
            Arguments supplémentaires passés à st.dataframe.

    Returns:
        None

    Raises:
        ValueError:
            Si le DataFrame est vide ou si status_column n'existe pas.
    """
    _validate_dataframe(data)
    _validate_column_exists(
        data,
        status_column,
        "status_column",
    )

    # Copier le DataFrame pour ne pas modifier l'original
    display_df = data.copy()

    # Préparer la configuration des colonnes
    config, order = _prepare_column_config(
        column_config,
        column_order,
    )

    # Si l'utilisateur n'a pas configuré la colonne status_column,
    # on ajoute une configuration par défaut
    if status_column not in config:
        config[status_column] = st.column_config.TextColumn(
            "Status",
            help="Status of the item",
        )

    # Afficher le tableau
    render_data_table(
        data=display_df,
        title=title,
        height=height,
        hide_index=hide_index,
        column_order=order,
        column_config=config,
        width=width,
        key=key,
        **kwargs,
    )


def render_score_table(
    data: pd.DataFrame,
    score_column: str,
    level_column: Optional[str] = None,
    title: Optional[str] = None,
    height: Optional[int] = None,
    hide_index: bool = True,
    column_order: Optional[Sequence[str]] = None,
    column_config: Optional[dict[str, Any]] = None,
    width: str | int = "stretch",
    key: Optional[str] = None,
    decimals: int = 0,
    score_scale: Literal["percentage", "ratio"] = "percentage",
    **kwargs: Any,
) -> None:
    """
    Affiche un tableau avec une colonne de score formatée en pourcentage.

    Args:
        data (pd.DataFrame): Données à afficher.
        score_column (str): Nom de la colonne contenant les scores.
        level_column (str, optionnel):
            Nom de la colonne contenant les niveaux.
        title (str, optionnel): Titre du tableau.
        height (int, optionnel): Hauteur en pixels.
        hide_index (bool):
            Si True, masque l'index. Par défaut True.
        column_order (Sequence[str], optionnel):
            Ordre des colonnes.
        column_config (dict, optionnel):
            Configuration des colonnes.
        width (str | int):
            Largeur du tableau. "stretch" pour utiliser tout l'espace,
            ou un nombre en pixels. Par défaut "stretch".
        key (str, optionnel):
            Clé unique pour le widget.
        decimals (int):
            Nombre de décimales pour l'affichage des pourcentages.
        score_scale (Literal["percentage", "ratio"]):
            Indique si les scores sont déjà en pourcentage (0-100)
            ou en ratio (0-1). Par défaut "percentage".
        **kwargs:
            Arguments supplémentaires passés à st.dataframe.

    Returns:
        None

    Raises:
        ValueError:
            Si le DataFrame est vide, si score_column n'existe pas,
            si decimals est négatif, ou si score_scale est invalide.
    """
    _validate_dataframe(data)
    _validate_column_exists(
        data,
        score_column,
        "score_column",
    )

    if decimals < 0:
        raise ValueError(
            "The number of decimal places cannot be negative."
        )

    if score_scale not in ("percentage", "ratio"):
        raise ValueError(
            "score_scale must be 'percentage' or 'ratio'."
        )

    # Copier le DataFrame pour ne pas modifier l'original
    display_df = data.copy()

    # Si les scores sont en ratio,
    # les multiplier par 100 pour les afficher en pourcentage
    if score_scale == "ratio":
        # Note: l'utilisateur est responsable de fournir
        # des ratios valides (0-1).
        display_df[score_column] = (
            display_df[score_column] * 100
        )

    # Configurer la colonne de score avec un format approprié
    config, order = _prepare_column_config(
        column_config,
        column_order,
    )

    # Format d'affichage pour les pourcentages
    format_str = f"%.{decimals}f%%"

    # Si l'utilisateur n'a pas configuré la colonne score_column,
    # on ajoute une configuration par défaut
    if score_column not in config:
        config[score_column] = st.column_config.NumberColumn(
            "Score",
            help="Maturity score",
            format=format_str,
        )

    # Configurer la colonne de niveau si fournie et non configurée
    if level_column:
        _validate_column_exists(
            data,
            level_column,
            "level_column",
        )

        if level_column not in config:
            config[level_column] = st.column_config.TextColumn(
                "Level",
                help="Maturity level",
            )

    # Afficher le tableau
    render_data_table(
        data=display_df,
        title=title,
        height=height,
        hide_index=hide_index,
        column_order=order,
        column_config=config,
        width=width,
        key=key,
        **kwargs,
    )


# ============================================================================
# PUBLIC EXPORT
# ============================================================================

__all__ = [
    "render_data_table",
    "render_status_table",
    "render_score_table",
]