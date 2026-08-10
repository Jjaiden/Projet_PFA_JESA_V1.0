"""Tests des adaptateurs Streamlit et du logger, sans session réelle."""

from __future__ import annotations

from types import SimpleNamespace

from utils import cache, session_manager
from utils.logger import get_logger


class _Clearable:
    def __init__(self) -> None:
        self.calls = 0

    def clear(self) -> None:
        self.calls += 1


def test_session_manager_uses_injected_session_state(monkeypatch) -> None:
    fake_streamlit = SimpleNamespace(session_state={})
    monkeypatch.setattr(session_manager, "st", fake_streamlit)

    session_manager.init_session({"step": 1})
    session_manager.set("step", 2)

    assert session_manager.get("step") == 2
    assert session_manager.pop("step") == 2
    assert not session_manager.has_key("step")


def test_cache_helpers_clear_both_streamlit_caches(monkeypatch) -> None:
    data_cache = _Clearable()
    resource_cache = _Clearable()
    monkeypatch.setattr(
        cache,
        "st",
        SimpleNamespace(cache_data=data_cache, cache_resource=resource_cache),
    )

    cache.clear_all_caches()

    assert data_cache.calls == 1
    assert resource_cache.calls == 1


def test_logger_returns_named_logger() -> None:
    assert get_logger("jesa.tests").name == "jesa.tests"
