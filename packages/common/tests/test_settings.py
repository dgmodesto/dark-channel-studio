import pytest

from dcs_common.settings import ConfigError, load_settings


def test_missing_required_names_variable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://secret-host:6379/0")
    with pytest.raises(ConfigError) as exc:
        load_settings()
    assert "DATABASE_URL" in exc.value.missing
    assert exc.value.code == "config.missing"
    assert "secret-host" not in str(exc.value)


def test_invalid_value_never_echoed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:hunter2@db/x")
    monkeypatch.setenv("REDIS_URL", "redis://r:6379/0")
    monkeypatch.setenv("LOG_LEVEL", "NOPE-hunter2")
    with pytest.raises(ConfigError) as exc:
        load_settings()
    assert "LOG_LEVEL" in exc.value.invalid
    assert "hunter2" not in str(exc.value)


def test_valid_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db/x")
    monkeypatch.setenv("REDIS_URL", "redis://r:6379/0")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s = load_settings()
    assert s.log_level == "INFO"
