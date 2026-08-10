# JESA_DMAT/utils/cache.py
"""
Generic cache management utilities for the JESA DMAT application.

Provides safe, logged wrappers around Streamlit's ``st.cache_data``
and ``st.cache_resource`` clearing functions. This module does **not**
define any cached business functions; it only manages the cache
lifecycle.

Usage::

    from utils.cache import clear_data_cache, clear_resource_cache, clear_all_caches

    clear_data_cache()          # Clear data caches only
    clear_resource_cache()      # Clear resource caches only
    clear_all_caches()          # Clear everything
"""

from __future__ import annotations

import streamlit as st

from utils.logger import get_logger

__all__ = [
    "clear_data_cache",
    "clear_resource_cache",
    "clear_all_caches",
]

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
_logger = get_logger(__name__)


def clear_data_cache() -> None:
    """Clear all ``@st.cache_data`` caches.

    Uses the official Streamlit :func:`st.cache_data.clear` method.
    After this call, all data-backed cached functions will re-execute
    on the next invocation.

    Raises:
        Exception: Re-raises the original Streamlit exception if the
            clear operation fails.

    Example:
        >>> clear_data_cache()
        Data cache cleared.
    """
    _logger.debug("Clearing Streamlit data cache.")
    try:
        st.cache_data.clear()
    except Exception:
        _logger.exception("Failed to clear data cache.")
        raise
    _logger.info("Data cache cleared.")


def clear_resource_cache() -> None:
    """Clear all ``@st.cache_resource`` caches.

    Uses the official Streamlit :func:`st.cache_resource.clear` method.
    After this call, all resource-backed cached functions will
    re-initialise on the next invocation.

    Raises:
        Exception: Re-raises the original Streamlit exception if the
            clear operation fails.

    Example:
        >>> clear_resource_cache()
        Resource cache cleared.
    """
    _logger.debug("Clearing Streamlit resource cache.")
    try:
        st.cache_resource.clear()
    except Exception:
        _logger.exception("Failed to clear resource cache.")
        raise
    _logger.info("Resource cache cleared.")


def clear_all_caches() -> None:
    """Clear both ``@st.cache_data`` and ``@st.cache_resource`` caches.

    Provides a single function to reset the entire Streamlit caching
    layer. Logs a summary when complete.

    Raises:
        Exception: Re-raises the original Streamlit exception if any
            clear operation fails.

    Example:
        >>> clear_all_caches()
        Data cache cleared.
        Resource cache cleared.
        All caches cleared.
    """
    _logger.debug("Clearing all Streamlit caches.")
    clear_data_cache()
    clear_resource_cache()
    _logger.info("All caches cleared.")