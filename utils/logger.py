# JESA_DMAT/utils/logger.py
"""
Centralized logging system for the JESA DMAT application.

Configures and provides loggers for all modules in the project.
The logger is set up only once via :func:`setup_logger`, which creates
a rotating file handler and a console stream handler with a unified format.

All configuration values are read from ``config.settings`` to keep the
application configuration centralized.

Usage::

    # In app.py (once at startup)
    from utils.logger import setup_logger
    setup_logger()

    # In any other module
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Module loaded successfully")
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.settings import settings

__all__ = [
    "setup_logger",
    "get_logger",
]

# ----------------------------------------------------------------------
# Internal state – ensures setup happens only once
# ----------------------------------------------------------------------
_is_configured: bool = False

# Format professionnel
_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    level: int | None = None,
    log_directory: Optional[Path] = None,
    log_filename: Optional[str] = None,
    max_bytes: int | None = None,
    backup_count: int | None = None,
) -> None:
    """Configure the application-wide logger.

    Creates the log directory if needed, sets up a rotating file handler
    and a console stream handler. This function is idempotent: calling it
    multiple times has no effect after the first successful configuration.

    All parameters are optional; defaults are taken from ``config.settings``.

    Args:
        level: Minimum log level (default: ``settings.LOG_LEVEL`` as int).
        log_directory: Directory where log files are stored
            (default: ``settings.LOG_DIR``).
        log_filename: Name of the log file
            (default: ``settings.LOG_FILENAME``).
        max_bytes: Maximum size in bytes before rotation
            (default: ``settings.LOG_MAX_BYTES``).
        backup_count: Number of rotated log files to keep
            (default: ``settings.LOG_BACKUP_COUNT``).

    Example:
        >>> setup_logger(level=logging.DEBUG)
        Logger configured successfully.
    """
    global _is_configured

    if _is_configured:
        return  # Idempotent : ne rien faire si déjà configuré

    # Résoudre les paramètres avec settings comme fallback
    resolved_level = level if level is not None else _level_to_int(settings.LOG_LEVEL)
    resolved_directory = log_directory if log_directory is not None else settings.LOG_DIR
    resolved_filename = log_filename if log_filename is not None else settings.LOG_FILENAME
    resolved_max_bytes = max_bytes if max_bytes is not None else settings.LOG_MAX_BYTES
    resolved_backup_count = backup_count if backup_count is not None else settings.LOG_BACKUP_COUNT

    # Racine du logger
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    # Supprimer les handlers existants (sécurité)
    root_logger.handlers.clear()

    # Formateur commun
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # --- File handler avec rotation ---
    resolved_directory.mkdir(parents=True, exist_ok=True)
    log_file_path = resolved_directory / resolved_filename
    file_handler = RotatingFileHandler(
        str(log_file_path),
        maxBytes=resolved_max_bytes,
        backupCount=resolved_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(resolved_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # --- Console handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(resolved_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _is_configured = True

    # Confirmation
    root_logger.info("Logger configured successfully.")
    root_logger.debug(
        "Log file: %s (max %d bytes, %d backups)",
        log_file_path,
        resolved_max_bytes,
        resolved_backup_count,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name.

    The logger inherits the configuration from the root logger set up
    by :func:`setup_logger`. If ``setup_logger`` has not been called yet,
    the standard logging defaults apply.

    Args:
        name: Typically ``__name__`` from the calling module.

    Returns:
        Configured :class:`logging.Logger` instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Assessment loaded")
        2026-08-05 18:42:10 | INFO     | my_module | Assessment loaded
    """
    return logging.getLogger(name)


# ----------------------------------------------------------------------
# Helper – convertit les niveaux de log de settings (chaînes) en int
# ----------------------------------------------------------------------
def _level_to_int(level: str) -> int:
    """Convert a log level string (e.g. 'DEBUG', 'INFO') to its int value."""
    return getattr(logging, level.upper(), logging.INFO)