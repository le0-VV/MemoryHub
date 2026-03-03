"""Tests for logging helpers."""

from memoryhub.utils import setup_logging


def test_setup_logging_prefers_memoryhub_tenant_id_alias(monkeypatch):
    """Structured logging should prefer the fork-native tenant env alias."""
    configured: dict[str, object] = {}

    monkeypatch.setenv("MEMORYHUB_ENV", "dev")
    monkeypatch.setenv("MEMORYHUB_TENANT_ID", "memoryhub-tenant")
    monkeypatch.setenv("BASIC_MEMORY_TENANT_ID", "legacy-tenant")

    monkeypatch.setattr("memoryhub.utils.logger.remove", lambda: None)
    monkeypatch.setattr("memoryhub.utils.logger.add", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "memoryhub.utils.logger.configure",
        lambda **kwargs: configured.update(kwargs),
    )

    setup_logging(structured_context=True)

    assert configured["extra"]["tenant_id"] == "memoryhub-tenant"
