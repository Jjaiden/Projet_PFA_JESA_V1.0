# JESA_DMAT/utils/session_manager.py
"""
Generic Streamlit session state manager for the JESA DMAT application.

Encapsulates all interactions with ``st.session_state`` so that pages
never access the session state directly. Provides safe defaults,
logging of state changes, and a clean API for initialisation,
retrieval, update, and reset of session variables.

This module is **completely generic** and contains no business logic.
It can be reused in any Streamlit project.

Usage::

    from utils.session_manager import init_session, get, set, clear

    init_session({"assessment_data": None, "current_step": 1})
    set("current_step", 2)
    step = get("current_step")

Functions:
    init_session(defaults) -> None
    has_key(key) -> bool
    exists(key) -> bool
    get(key, default=None) -> Any
    set(key, value) -> None
    set_many(mapping) -> None
    remove(key) -> bool
    pop(key, default=None) -> Any
    clear() -> None
    reset(defaults) -> None
    get_all() -> dict[str, Any]
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import streamlit as st

from utils.logger import get_logger

__all__ = [
    "init_session",
    "has_key",
    "exists",
    "get",
    "set",
    "set_many",
    "remove",
    "pop",
    "clear",
    "reset",
    "get_all",
]

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
_logger = get_logger(__name__)


def _validate_key(key: Any) -> str:
    """Ensure the provided key is a non-empty string.

    Args:
        key: The key to validate.

    Returns:
        The key if it is a valid non-empty string.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is an empty string.
    """
    if not isinstance(key, str):
        raise TypeError(f"Expected key to be str, got {type(key).__name__}")
    if not key.strip():
        raise ValueError("Session key cannot be an empty string.")
    return key


def init_session(defaults: Mapping[str, Any] | None = None) -> None:
    """Initialise session variables that are not already present.

    Iterates over the provided defaults and adds any key that does not
    yet exist in ``st.session_state``. Existing keys are **never** overwritten.
    If ``defaults`` is ``None`` or empty, the function does nothing.

    Args:
        defaults: Mapping of default key-value pairs to initialise.

    Raises:
        TypeError: If ``defaults`` is not a mapping.

    Example:
        >>> init_session({"user": None, "step": 1})
        Session initialized with 2 default keys.
    """
    if defaults is None:
        _logger.debug("init_session called with no defaults, nothing to do.")
        return

    if not isinstance(defaults, Mapping):
        raise TypeError(
            f"Expected a Mapping for defaults, got {type(defaults).__name__}"
        )

    added_count = 0
    for key, value in defaults.items():
        _validate_key(key)
        if key not in st.session_state:
            st.session_state[key] = value
            added_count += 1
            _logger.debug("Session key added: '%s'", key)

    if added_count:
        _logger.info(
            "Session initialized with %d new keys out of %d provided.",
            added_count,
            len(defaults),
        )
    else:
        _logger.debug("All %d session keys already exist.", len(defaults))


def has_key(key: str) -> bool:
    """Check whether a key exists in the session state.

    Args:
        key: The key to look for.

    Returns:
        ``True`` if the key is in ``st.session_state``, ``False`` otherwise.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> has_key("current_step")
        True
    """
    _validate_key(key)
    return key in st.session_state


def exists(key: str) -> bool:
    """Alias for :func:`has_key`.

    Args:
        key: The key to look for.

    Returns:
        ``True`` if the key exists.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> exists("assessment_data")
        False
    """
    return has_key(key)


def get(key: str, default: Any = None) -> Any:
    """Retrieve a value from the session state safely.

    Args:
        key: The key to retrieve.
        default: Value to return if the key does not exist (default ``None``).

    Returns:
        The stored value, or ``default`` if the key is absent.
        This function **never** raises an exception for missing keys.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> get("current_step", 1)
        3
    """
    _validate_key(key)
    return st.session_state.get(key, default)


def set(key: str, value: Any) -> None:
    """Store a value in the session state.

    Logs whether the key was newly created or updated.

    Args:
        key: The key under which to store the value.
        value: The value to store.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> set("selected_company", "Acme Corp")
        Session key 'selected_company' created.
    """
    _validate_key(key)
    created = key not in st.session_state
    st.session_state[key] = value
    _logger.debug(
        "Session key '%s' %s.",
        key,
        "created" if created else "updated",
    )


def set_many(mapping: Mapping[str, Any]) -> None:
    """Update multiple session state keys from a dictionary.

    Delegates to :func:`set` for each key-value pair, then logs a summary.

    Args:
        mapping: A mapping of key-value pairs to update.

    Raises:
        TypeError: If ``mapping`` is not a :class:`collections.abc.Mapping`.
        ValueError: If any key is empty.

    Example:
        >>> set_many({"step": 2, "company": "Acme"})
        Applied 2 session updates.
    """
    if not isinstance(mapping, Mapping):
        raise TypeError(
            f"Expected a Mapping for set_many, got {type(mapping).__name__}"
        )

    for key, value in mapping.items():
        set(key, value)

    _logger.info("Applied %d session updates.", len(mapping))


def remove(key: str) -> bool:
    """Remove a key from the session state if it exists.

    Args:
        key: The key to remove.

    Returns:
        ``True`` if the key was removed, ``False`` if it did not exist.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> removed = remove("temp_data")
        >>> if removed:
        ...     print("Cleaned up")
        Session key 'temp_data' removed.
    """
    _validate_key(key)
    if key in st.session_state:
        del st.session_state[key]
        _logger.debug("Session key '%s' removed.", key)
        return True
    else:
        _logger.debug("Attempted to remove non-existent session key '%s'.", key)
        return False


def pop(key: str, default: Any = None) -> Any:
    """Retrieve a value and remove it from the session state.

    Uses the native :meth:`dict.pop` method of ``st.session_state``,
    which is atomic and efficient. Logs only when the key actually existed.

    Args:
        key: The key to retrieve and remove.
        default: Value to return if the key does not exist.

    Returns:
        The value that was stored under ``key``, or ``default`` if absent.

    Raises:
        TypeError: If ``key`` is not a string.
        ValueError: If ``key`` is empty.

    Example:
        >>> company = pop("selected_company")
        >>> print(company)
        'Acme Corp'
    """
    _validate_key(key)
    existed = key in st.session_state
    value = st.session_state.pop(key, default)
    if existed:
        _logger.debug("Session key '%s' popped.", key)
    return value


def clear() -> None:
    """Clear the **entire** session state and log the action.

    Does nothing and logs a debug message if the state is already empty.

    Example:
        >>> clear()
        Session state cleared.
    """
    if not st.session_state:
        _logger.debug("Session state already empty, nothing to clear.")
        return

    key_count = len(st.session_state)
    st.session_state.clear()
    _logger.info("Session state cleared (%d keys removed).", key_count)


def reset(defaults: Mapping[str, Any] | None = None) -> None:
    """Clear the session state and re-initialise with the provided defaults.

    Args:
        defaults: Mapping of default values to re-initialise after clearing.

    Example:
        >>> reset({"current_step": 1})
        Session state cleared (5 keys removed).
        Session initialized with 1 new keys.
    """
    clear()
    init_session(defaults)


def get_all() -> dict[str, Any]:
    """Return a deep copy of the entire session state as a dictionary.

    The original ``st.session_state`` is **not** exposed directly to callers.

    Returns:
        Deep copy of all session variables.

    Example:
        >>> state = get_all()
        >>> print(state.keys())
    """
    return deepcopy(dict(st.session_state))