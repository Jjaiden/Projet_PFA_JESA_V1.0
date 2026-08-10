"""
settings.py — Configuration globale de l'application JESA DMAT.

Ce module centralise tous les paramètres de l'application:

BACKEND (Sections 1–6):
- Chemins des fichiers et dossiers (référentiel, assessment, sorties)
- Précision numérique (scores, DMI, TPI)
- Comportement du moteur (validation des poids, scores manquants)
- Configuration du logging (console)

FRONTEND (Sections 7–11):
- Métadonnées de l'application (nom, version, auteur)
- Configuration Streamlit (layout, sidebar, icônes)
- Configuration des exports (PDF, Excel)
- Gestion des sessions et uploads
- Paramètres de cache et debug

Les fichiers sont résolus via des variables d'environnement (backend)
et des chemins statiques (frontend). Utilisez l'instance globale `settings`
pour accéder à tous les paramètres.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

# ── Chemins racines du projet ──────────────────────────────────────────────
_ROOT_DIR = Path(__file__).resolve().parent.parent


# ============================================================================
# =========================== BACKEND SETTINGS ===============================
# ============================================================================


@dataclass(frozen=True)
class BackendSettings:
    """
    Configuration du backend JDMAF.

    Tous les attributs sont figés après instanciation (frozen=True) pour
    éviter toute modification accidentelle en cours d'exécution.
    """

    # ========================================================================
    # 1. CHEMINS DU PROJET (BACKEND)
    # ========================================================================

    # Structure attendue :
    # JESA_DMAT/
    # ├── app.py
    # ├── config/
    # │   └── settings.py
    # ├── data/
    # ├── engines/
    # ├── pages/
    # └── outputs/

    BASE_DIR: Path = _ROOT_DIR
    """Racine du projet JESA_DMAT/."""

    DATA_DIR: Path = _ROOT_DIR / "data"
    """Dossier des données (référentiels, assessments)."""

    ASSESSMENT_DIR: Path = _ROOT_DIR / "data" / "assessment"
    """Dossier contenant les fichiers d'évaluation."""

    KNOWLEDGE_BASE_DIR: Path = _ROOT_DIR / "data" / "knowledge_base"
    """Dossier contenant la base de connaissances (recommandations)."""

    # ========================================================================
    # 2. FICHIERS EXCEL (BACKEND)
    # ========================================================================

    # Référentiel JESA.
    # Contient : HIERARCHY, GENERIC_MATURITY_SCALE, INDICATORS,
    # INDICATOR_SCORING_GRIDS, QUESTIONNAIRE_TEMPLATE, etc.

    REFERENTIEL_FILE: Path = Path(
        os.environ.get(
            "JDMAF_REFERENTIEL_FILE",
            str(
                _ROOT_DIR
                / "data"
                / "knowledge_base"
                / "REFERENTIEL_GRILLES_MATURITE_DIGITALE_JESA.xlsx"
            ),
        )
    )

    # Base de connaissances utilisée par les moteurs décisionnels :
    # recommandations, roadmap, dépendances, best practices, etc.

    RECOMMENDATIONS_FILE: Path = Path(
        os.environ.get(
            "JDMAF_RECOMMENDATIONS_FILE",
            str(
                _ROOT_DIR
                / "data"
                / "knowledge_base"
                / "BASE_CONNAISSANCES_RECOMMANDATIONS_JESA.xlsx"
            ),
        )
    )

    # Fichier d'évaluation.
    # Contient les réponses / scores de l'évaluation.
    # En production, ce fichier peut être fourni par l'utilisateur.

    ASSESSMENT_FILE: Path = Path(
        os.environ.get(
            "JDMAF_ASSESSMENT_FILE",
            str(_ROOT_DIR / "data" / "assessment" / "Assessment.xlsx"),
        )
    )

    # ========================================================================
    # 3. DOSSIER DE SORTIE (BACKEND)
    # ========================================================================

    # Tous les fichiers générés par le backend sont regroupés ici.
    # Exemple :
    # outputs/
    # ├── assessment_results.json
    # ├── assessment_report.pdf
    # └── assessment_export.xlsx

    OUTPUT_DIR: Path = Path(
        os.environ.get(
            "JDMAF_OUTPUT_DIR",
            str(_ROOT_DIR / "outputs"),
        )
    )

    # ========================================================================
    # 4. PRÉCISION NUMÉRIQUE (BACKEND)
    # ========================================================================

    # Scores de maturité : échelle 0-5.
    SCORE_DECIMAL_PRECISION: int = 3

    # DMI : score exprimé en pourcentage (ex: 62.4 %).
    DMI_DECIMAL_PRECISION: int = 1

    # TPI : indice compris entre 0 et 1.
    TPI_DECIMAL_PRECISION: int = 3

    # ========================================================================
    # 5. COMPORTEMENT DU MOTEUR (BACKEND)
    # ========================================================================

    # 5.1 Validation des pondérations
    # True : une somme de poids invalide provoque une erreur.
    # False : le moteur journalise un warning et normalise les poids.
    STRICT_WEIGHT_VALIDATION: bool = True

    # 5.2 Niveau cible inférieur au niveau actuel
    # Autorise une cible inférieure au niveau actuel (décision volontaire).
    ALLOW_TARGET_BELOW_CURRENT: bool = True

    # 5.3 Indicateurs non applicables
    # Applicability = "Non applicable" exclut l'indicateur du calcul.
    # Les poids des éléments restants sont renormalisés.
    RENORMALIZE_WEIGHTS_ON_NA: bool = True

    # 5.4 Score manquant
    # Applicability = "Applicable" mais Selected_Score vide :
    # l'évaluation est considérée comme incomplète.
    ALLOW_MISSING_SCORE_ON_APPLICABLE: bool = False

    # ========================================================================
    # 6. LOGGING (BACKEND)
    # ========================================================================

    LOG_LEVEL: str = os.environ.get(
        "JDMAF_LOG_LEVEL",
        "INFO",
    )

    def get_logger(self, name: str) -> logging.Logger:
        """
        Retourne un logger configuré de manière homogène pour le backend.

        Args:
            name: Nom du module appelant.

        Returns:
            Instance de logging.Logger.
        """
        logger = logging.getLogger(name)

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
                )
            )
            logger.addHandler(handler)

        logger.setLevel(self.LOG_LEVEL)
        return logger


# ============================================================================
# =========================== FRONTEND SETTINGS ==============================
# ============================================================================


@dataclass(frozen=True)
class FrontendSettings:
    """
    Configuration de l'interface utilisateur et des exports JESA DMAT.

    Tous les attributs sont figés après instanciation (frozen=True) pour
    éviter toute modification accidentelle en cours d'exécution.
    """

    # ========================================================================
    # 7. MÉTADONNÉES DE L'APPLICATION (FRONTEND)
    # ========================================================================

    APP_NAME: str = "JESA DMAT"
    """Nom complet de l'application."""

    APP_VERSION: str = "1.0.0"
    """Version actuelle (semver)."""

    APP_AUTHOR: str = "JESA"
    """Auteur / équipe de développement."""

    APP_COMPANY: str = "JESA"
    """Entreprise propriétaire de l'outil."""

    APP_DESCRIPTION: str = (
        "Outil d'évaluation de la maturité digitale "
        "basé sur le référentiel Industry 5.0."
    )
    """Description affichée dans l'interface et les exports."""

    # ========================================================================
    # 8. CONFIGURATION STREAMLIT (FRONTEND)
    # ========================================================================

    PAGE_TITLE: str = "JESA DMAT"
    """Titre de la page web (onglet navigateur)."""

    PAGE_ICON: str = str(_ROOT_DIR / "assets" / "logo" / "jesa_logo.png")
    """Icône de la page (chemin vers le logo). Accepte aussi un emoji."""

    LAYOUT: str = "wide"
    """Disposition Streamlit : 'centered' ou 'wide'."""

    SIDEBAR_STATE: str = "expanded"
    """État initial de la sidebar : 'auto', 'expanded', 'collapsed'."""

    WIDE_MODE_MAX_WIDTH: int = 1400
    """Largeur maximale du contenu en mode wide (px)."""

    # ========================================================================
    # 9. DOSSIERS D'EXPORT (FRONTEND)
    # ========================================================================

    EXPORTS_DIR: Path = _ROOT_DIR / "exports"
    """Dossier racine des exports."""

    EXPORT_PDF_DIR: Path = _ROOT_DIR / "exports" / "pdf"
    """Dossier des exports PDF."""

    EXPORT_EXCEL_DIR: Path = _ROOT_DIR / "exports" / "excel"
    """Dossier des exports Excel."""

    EXPORT_REPORT_DIR: Path = _ROOT_DIR / "exports" / "report"
    """Dossier des rapports générés."""

    # ========================================================================
    # 10. RESSOURCES STATIQUES (FRONTEND)
    # ========================================================================

    ASSETS_DIR: Path = _ROOT_DIR / "assets"
    """Dossier des ressources statiques."""

    LOGO_DIR: Path = _ROOT_DIR / "assets" / "logo"
    """Dossier contenant les logos."""

    IMAGES_DIR: Path = _ROOT_DIR / "assets" / "images"
    """Dossier des images (illustrations, schémas)."""

    STYLES_DIR: Path = _ROOT_DIR / "assets" / "styles"
    """Dossier des feuilles de style CSS."""

    UPLOAD_DIR: Path = _ROOT_DIR / "uploads"
    """Dossier des fichiers téléversés par l'utilisateur."""

    # ========================================================================
    # 11. CONFIGURATION DES EXPORTS (FRONTEND)
    # ========================================================================

    # 11.1 PDF
    PDF_PAGE_SIZE: str = "A4"
    """Format de page pour les rapports PDF."""

    PDF_ORIENTATION: str = "portrait"
    """Orientation : 'portrait' ou 'landscape'."""

    PDF_MARGIN_TOP: float = 15.0
    PDF_MARGIN_BOTTOM: float = 15.0
    PDF_MARGIN_LEFT: float = 12.0
    PDF_MARGIN_RIGHT: float = 12.0

    PDF_FONT_FAMILY: str = "Inter"
    """Police principale utilisée dans les PDF."""

    PDF_FONT_SIZE_BODY: int = 10
    """Taille du texte courant dans les PDF."""

    # 11.2 Excel
    EXCEL_SHEET_OVERVIEW: str = "Vue d'ensemble"
    EXCEL_SHEET_DETAIL: str = "Détail par pilier"
    EXCEL_TABLE_STYLE: str = "TableStyleMedium2"

    # ========================================================================
    # 12. CONFIGURATION DES GRAPHIQUES (FRONTEND)
    # ========================================================================

    PLOTLY_TEMPLATE: str = "plotly_white"
    """Template Plotly par défaut."""

    PLOTLY_DISPLAY_MODE_BAR: bool = False
    """Afficher la barre de mode Plotly."""

    # ========================================================================
    # 13. SAUVEGARDE DES SESSIONS (FRONTEND)
    # ========================================================================

    SESSION_SAVE_ENABLED: bool = True
    """Activer la sauvegarde automatique des sessions."""

    SESSION_SAVE_DIR: Path = _ROOT_DIR / "data" / "sessions"
    """Dossier des sessions sauvegardées."""

    SESSION_SAVE_FORMAT: str = "json"
    """Format de sauvegarde des sessions."""

    # ========================================================================
    # 14. UPLOADS UTILISATEUR (FRONTEND)
    # ========================================================================

    UPLOAD_ENABLED: bool = False
    """Activer les uploads utilisateur."""

    UPLOAD_MAX_SIZE_MB: int = 50
    """Taille maximale des fichiers uploadés (Mo)."""

    UPLOAD_ALLOWED_EXTENSIONS: tuple[str, ...] = ("csv", "xlsx", "json")
    """Extensions de fichiers autorisées pour les uploads."""

    # ========================================================================
    # 15. LOGS APPLICATIFS (FRONTEND)
    # ========================================================================

    LOG_ENABLED: bool = True
    """Activer la journalisation des événements."""

    LOG_DIR: Path = _ROOT_DIR / "logs"
    """Dossier contenant les fichiers de log."""

    LOG_FILENAME: str = "jesa_dmat.log"
    """Nom du fichier de log principal."""

    LOG_LEVEL_FRONTEND: str = "INFO"
    """Niveau de log par défaut (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""

    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    """Format des entrées de log."""

    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 Mo
    """Taille maximale d'un fichier de log avant rotation."""

    LOG_BACKUP_COUNT: int = 3
    """Nombre de fichiers de log de sauvegarde à conserver."""

    # ========================================================================
    # 16. DEBUG & DÉVELOPPEMENT (FRONTEND)
    # ========================================================================

    DEBUG: bool = False
    """Mode debug (affichage des erreurs détaillées)."""

    # ========================================================================
    # 17. PARAMÈTRES DE SESSION (FRONTEND)
    # ========================================================================

    SESSION_TIMEOUT_SECONDS: int = 3600
    """Timeout des sessions Streamlit (secondes)."""

    SESSION_STATE_KEYS: ClassVar[tuple[str, ...]] = (
        "selected_company",
        "assessment_data",
        "assessment_results",
        "dashboard_data",
        "gap_results",
        "recommendations",
        "decision_analysis",
        "roadmap",
        "export_settings",
        "current_step",
        "uploaded_file",
        "maturity_scores",
    )
    """Clés de session Streamlit à préserver / initialiser."""

    # ========================================================================
    # 18. PARAMÈTRES DE CACHE (FRONTEND)
    # ========================================================================

    CACHE_TTL_SECONDS: int = 600
    """Durée de vie du cache (secondes)."""

    CACHE_MAX_ENTRIES: int = 50
    """Nombre maximal d'entrées dans le cache."""


# ── Instance globale unique ─────────────────────────────────────────────────
class Settings:
    """
    Configuration globale de JESA DMAT.

    Regroupe les configurations backend et frontend en une seule instance.
    Utilisez l'instance globale `settings` pour accéder à tous les paramètres.
    """

    def __init__(self):
        self.backend = BackendSettings()
        self.frontend = FrontendSettings()

    # ========================================================================
    # Délégation des attributs backend
    # ========================================================================

    @property
    def BASE_DIR(self) -> Path:
        return self.backend.BASE_DIR

    @property
    def DATA_DIR(self) -> Path:
        return self.backend.DATA_DIR

    @property
    def ASSESSMENT_DIR(self) -> Path:
        return self.backend.ASSESSMENT_DIR

    @property
    def KNOWLEDGE_BASE_DIR(self) -> Path:
        return self.backend.KNOWLEDGE_BASE_DIR

    @property
    def REFERENTIEL_FILE(self) -> Path:
        return self.backend.REFERENTIEL_FILE

    @property
    def RECOMMENDATIONS_FILE(self) -> Path:
        return self.backend.RECOMMENDATIONS_FILE

    @property
    def ASSESSMENT_FILE(self) -> Path:
        return self.backend.ASSESSMENT_FILE

    @property
    def OUTPUT_DIR(self) -> Path:
        return self.backend.OUTPUT_DIR

    @property
    def SCORE_DECIMAL_PRECISION(self) -> int:
        return self.backend.SCORE_DECIMAL_PRECISION

    @property
    def DMI_DECIMAL_PRECISION(self) -> int:
        return self.backend.DMI_DECIMAL_PRECISION

    @property
    def TPI_DECIMAL_PRECISION(self) -> int:
        return self.backend.TPI_DECIMAL_PRECISION

    @property
    def STRICT_WEIGHT_VALIDATION(self) -> bool:
        return self.backend.STRICT_WEIGHT_VALIDATION

    @property
    def ALLOW_TARGET_BELOW_CURRENT(self) -> bool:
        return self.backend.ALLOW_TARGET_BELOW_CURRENT

    @property
    def RENORMALIZE_WEIGHTS_ON_NA(self) -> bool:
        return self.backend.RENORMALIZE_WEIGHTS_ON_NA

    @property
    def ALLOW_MISSING_SCORE_ON_APPLICABLE(self) -> bool:
        return self.backend.ALLOW_MISSING_SCORE_ON_APPLICABLE

    @property
    def LOG_LEVEL(self) -> str:
        return self.backend.LOG_LEVEL

    def get_logger(self, name: str) -> logging.Logger:
        """Délégation à BackendSettings.get_logger."""
        return self.backend.get_logger(name)

    # ========================================================================
    # Délégation des attributs frontend
    # ========================================================================

    @property
    def APP_NAME(self) -> str:
        return self.frontend.APP_NAME

    @property
    def APP_VERSION(self) -> str:
        return self.frontend.APP_VERSION

    @property
    def APP_AUTHOR(self) -> str:
        return self.frontend.APP_AUTHOR

    @property
    def APP_COMPANY(self) -> str:
        return self.frontend.APP_COMPANY

    @property
    def APP_DESCRIPTION(self) -> str:
        return self.frontend.APP_DESCRIPTION

    @property
    def PAGE_TITLE(self) -> str:
        return self.frontend.PAGE_TITLE

    @property
    def PAGE_ICON(self) -> str:
        return self.frontend.PAGE_ICON

    @property
    def LAYOUT(self) -> str:
        return self.frontend.LAYOUT

    @property
    def SIDEBAR_STATE(self) -> str:
        return self.frontend.SIDEBAR_STATE

    @property
    def WIDE_MODE_MAX_WIDTH(self) -> int:
        return self.frontend.WIDE_MODE_MAX_WIDTH

    @property
    def EXPORTS_DIR(self) -> Path:
        return self.frontend.EXPORTS_DIR

    @property
    def EXPORT_PDF_DIR(self) -> Path:
        return self.frontend.EXPORT_PDF_DIR

    @property
    def EXPORT_EXCEL_DIR(self) -> Path:
        return self.frontend.EXPORT_EXCEL_DIR

    @property
    def EXPORT_REPORT_DIR(self) -> Path:
        return self.frontend.EXPORT_REPORT_DIR

    @property
    def ASSETS_DIR(self) -> Path:
        return self.frontend.ASSETS_DIR

    @property
    def LOGO_DIR(self) -> Path:
        return self.frontend.LOGO_DIR

    @property
    def IMAGES_DIR(self) -> Path:
        return self.frontend.IMAGES_DIR

    @property
    def STYLES_DIR(self) -> Path:
        return self.frontend.STYLES_DIR

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.frontend.UPLOAD_DIR

    @property
    def PDF_PAGE_SIZE(self) -> str:
        return self.frontend.PDF_PAGE_SIZE

    @property
    def PDF_ORIENTATION(self) -> str:
        return self.frontend.PDF_ORIENTATION

    @property
    def PDF_MARGIN_TOP(self) -> float:
        return self.frontend.PDF_MARGIN_TOP

    @property
    def PDF_MARGIN_BOTTOM(self) -> float:
        return self.frontend.PDF_MARGIN_BOTTOM

    @property
    def PDF_MARGIN_LEFT(self) -> float:
        return self.frontend.PDF_MARGIN_LEFT

    @property
    def PDF_MARGIN_RIGHT(self) -> float:
        return self.frontend.PDF_MARGIN_RIGHT

    @property
    def PDF_FONT_FAMILY(self) -> str:
        return self.frontend.PDF_FONT_FAMILY

    @property
    def PDF_FONT_SIZE_BODY(self) -> int:
        return self.frontend.PDF_FONT_SIZE_BODY

    @property
    def EXCEL_SHEET_OVERVIEW(self) -> str:
        return self.frontend.EXCEL_SHEET_OVERVIEW

    @property
    def EXCEL_SHEET_DETAIL(self) -> str:
        return self.frontend.EXCEL_SHEET_DETAIL

    @property
    def EXCEL_TABLE_STYLE(self) -> str:
        return self.frontend.EXCEL_TABLE_STYLE

    @property
    def PLOTLY_TEMPLATE(self) -> str:
        return self.frontend.PLOTLY_TEMPLATE

    @property
    def PLOTLY_DISPLAY_MODE_BAR(self) -> bool:
        return self.frontend.PLOTLY_DISPLAY_MODE_BAR

    @property
    def SESSION_SAVE_ENABLED(self) -> bool:
        return self.frontend.SESSION_SAVE_ENABLED

    @property
    def SESSION_SAVE_DIR(self) -> Path:
        return self.frontend.SESSION_SAVE_DIR

    @property
    def SESSION_SAVE_FORMAT(self) -> str:
        return self.frontend.SESSION_SAVE_FORMAT

    @property
    def UPLOAD_ENABLED(self) -> bool:
        return self.frontend.UPLOAD_ENABLED

    @property
    def UPLOAD_MAX_SIZE_MB(self) -> int:
        return self.frontend.UPLOAD_MAX_SIZE_MB

    @property
    def UPLOAD_ALLOWED_EXTENSIONS(self) -> tuple[str, ...]:
        return self.frontend.UPLOAD_ALLOWED_EXTENSIONS

    @property
    def LOG_ENABLED(self) -> bool:
        return self.frontend.LOG_ENABLED

    @property
    def LOG_DIR(self) -> Path:
        return self.frontend.LOG_DIR

    @property
    def LOG_FILENAME(self) -> str:
        return self.frontend.LOG_FILENAME

    @property
    def LOG_LEVEL_FRONTEND(self) -> str:
        return self.frontend.LOG_LEVEL_FRONTEND

    @property
    def LOG_FORMAT(self) -> str:
        return self.frontend.LOG_FORMAT

    @property
    def LOG_MAX_BYTES(self) -> int:
        return self.frontend.LOG_MAX_BYTES

    @property
    def LOG_BACKUP_COUNT(self) -> int:
        return self.frontend.LOG_BACKUP_COUNT

    @property
    def DEBUG(self) -> bool:
        return self.frontend.DEBUG

    @property
    def SESSION_TIMEOUT_SECONDS(self) -> int:
        return self.frontend.SESSION_TIMEOUT_SECONDS

    @property
    def SESSION_STATE_KEYS(self) -> tuple[str, ...]:
        return self.frontend.SESSION_STATE_KEYS

    @property
    def CACHE_TTL_SECONDS(self) -> int:
        return self.frontend.CACHE_TTL_SECONDS

    @property
    def CACHE_MAX_ENTRIES(self) -> int:
        return self.frontend.CACHE_MAX_ENTRIES


# ── Instance globale unique ─────────────────────────────────────────────────
settings = Settings()

# ============================================================================
# FIN DU MODULE
# ============================================================================