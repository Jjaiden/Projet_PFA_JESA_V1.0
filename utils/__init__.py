# JESA_DMAT/utils/__init__.py
"""
Package ``utils`` de JESA DMAT.

Fournit des outils génériques et réutilisables pour l'application :
chargement de fichiers Excel, gestion de session, validation, formatage,
journalisation, cache, manipulation de fichiers et fonctions d'aide.

Ce package ne contient **aucune logique métier** liée à l'évaluation
de la maturité digitale ou au référentiel Industry 5.0. Ces éléments
sont réservés au package ``engines``.

Utilisation typique::

    from utils import excel_loader
    from utils.session_manager import init_session, get, set
    from utils.validators import validate_dataframe
    from utils.formatters import format_percentage
    from utils.logger import get_logger
    from utils.cache import clear_all_caches
    from utils.file_manager import ensure_directory
    from utils.helpers import normalize_text
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import settings

# --- Frontend modules ---
from .cache import clear_all_caches, clear_data_cache, clear_resource_cache
from .excel_loader import get_sheet_names, load_workbook, read_sheet
from .file_manager import (
    copy_file,
    delete_file,
    ensure_directory,
    file_exists,
    move_file,
    # Backend extensions (added)
    get_output_directory,
    resolve_path,
    directory_exists,
    ensure_file_exists,
    get_referentiel_path,
    get_recommendations_path,
    get_assessment_path,
    sanitize_filename,
    build_output_path,
    file_size as get_file_size,
    is_empty_file,
)
from .formatters import format_date, format_number, format_percentage
from .logger import get_logger, setup_logger
from .session_manager import get, init_session, reset, set
from .validators import (
    validate_dataframe,
    validate_file_extension,
    validate_no_missing_values,
    validate_numeric_range,
    validate_required_columns,
)

# --- Backend modules ---
from .excel_utils import (
    open_workbook,
    sheet_to_records,
    sheet_to_keyvalue,
    group_records_by,
    safe_int as excel_safe_int,
    safe_float as excel_safe_float,
    safe_str as excel_safe_str,
)
from .helpers import (
    normalize_text,
    normalize_id,
    is_blank,
    safe_int,
    safe_float,
    is_close,
    clamp,
    unique_preserve_order,
    chunked,
    get_nested,
    first_not_none,
    format_number,
    format_percentage,
)

__version__ = settings.APP_VERSION
__author__ = settings.APP_AUTHOR

__all__ = [
    # excel_loader (frontend)
    "load_workbook",
    "get_sheet_names",
    "read_sheet",

    # excel_utils (backend)
    "open_workbook",
    "sheet_to_records",
    "sheet_to_keyvalue",
    "group_records_by",
    "excel_safe_int",
    "excel_safe_float",
    "excel_safe_str",

    # session_manager
    "init_session",
    "get",
    "set",
    "reset",

    # validators
    "validate_file_extension",
    "validate_dataframe",
    "validate_required_columns",
    "validate_no_missing_values",
    "validate_numeric_range",

    # formatters
    "format_percentage",
    "format_date",
    "format_number",

    # logger
    "get_logger",
    "setup_logger",

    # cache
    "clear_data_cache",
    "clear_resource_cache",
    "clear_all_caches",

    # file_manager
    "ensure_directory",
    "delete_file",
    "file_exists",
    "copy_file",
    "move_file",
    "get_output_directory",
    "resolve_path",
    "directory_exists",
    "ensure_file_exists",
    "get_referentiel_path",
    "get_recommendations_path",
    "get_assessment_path",
    "sanitize_filename",
    "build_output_path",
    "get_file_size",
    "is_empty_file",

    # helpers
    "normalize_text",
    "normalize_id",
    "is_blank",
    "safe_int",
    "safe_float",
    "is_close",
    "clamp",
    "unique_preserve_order",
    "chunked",
    "get_nested",
    "first_not_none",
    "format_number",
    "format_percentage",
]
