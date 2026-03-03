"""Tests for CLI promo suppression helpers."""

from memoryhub.cli.promo import _promos_disabled_by_env


def test_promos_disabled_by_memoryhub_alias(monkeypatch):
    """MEMORYHUB_NO_PROMOS should disable the one-time init line."""
    monkeypatch.setenv("MEMORYHUB_NO_PROMOS", "true")
    monkeypatch.delenv("BASIC_MEMORY_NO_PROMOS", raising=False)

    assert _promos_disabled_by_env() is True


def test_promos_disabled_alias_takes_precedence(monkeypatch):
    """The MemoryHub alias should win when both env names are set."""
    monkeypatch.setenv("BASIC_MEMORY_NO_PROMOS", "false")
    monkeypatch.setenv("MEMORYHUB_NO_PROMOS", "yes")

    assert _promos_disabled_by_env() is True
