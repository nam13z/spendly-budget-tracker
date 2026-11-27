"""Tests for environment settings validation and URL construction."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import ENV_FILE, Settings


def test_default_env_file_is_repository_root_path_independent_of_cwd(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_PASSWORD", "test-only-secret")
    monkeypatch.setenv("DB_PORT", "3310")

    settings = Settings()

    assert ENV_FILE.is_absolute()
    assert ENV_FILE.name == ".env"
    assert ENV_FILE == Path(__file__).resolve().parents[2] / ".env"
    assert Settings.model_config["env_file"] == ENV_FILE
    assert settings.db_password.get_secret_value() == "test-only-secret"
    assert settings.db_port == 3310


def test_settings_load_database_values_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "test-only-secret")
    monkeypatch.setenv("DB_PORT", "3307")

    settings = Settings(_env_file=None)

    assert settings.db_host == "127.0.0.1"
    assert settings.db_port == 3307
    assert settings.db_name == "spendly"
    assert settings.db_user == "spendly_app"
    assert "test-only-secret" not in str(settings)


def test_database_password_is_required(monkeypatch) -> None:
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_port_must_be_within_tcp_range() -> None:
    with pytest.raises(ValidationError):
        Settings(db_password="test-only-secret", db_port=65536, _env_file=None)


def test_sqlalchemy_url_escapes_credentials() -> None:
    settings = Settings(db_password="local@secret", _env_file=None)

    assert settings.sqlalchemy_url.drivername == "mysql+pymysql"
    assert settings.sqlalchemy_url.password == "local@secret"
    assert settings.sqlalchemy_url.port == 3307
    assert settings.sqlalchemy_url.render_as_string(hide_password=True).find("***") >= 0


def test_shared_settings_fixture_uses_isolated_test_configuration(settings: Settings) -> None:
    assert settings.app_env == "test"
    assert settings.db_name == "spendly_test"
    assert "synthetic-test-password" not in str(settings)
