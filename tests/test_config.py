from __future__ import annotations

from importlib import reload

import pytest

import allure_testops_mcp.config as config_module


def test_parse_int_env_returns_none_for_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLURE_TESTOPS_TIMEOUT", "abc")

    assert config_module.Config._parse_int_env("ALLURE_TESTOPS_TIMEOUT") is None


def test_config_normalizes_url_and_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLURE_TESTOPS_URL", "https://example.com/")
    monkeypatch.setenv("ALLURE_TESTOPS_API_TOKEN", "secret")
    monkeypatch.delenv("ALLURE_TESTOPS_TIMEOUT", raising=False)

    cfg = config_module.Config()

    assert cfg.url == "https://example.com"
    assert cfg.api_token == "secret"
    assert cfg.timeout == 30


def test_config_validate_reports_expected_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLURE_TESTOPS_URL", "ftp://example.com")
    monkeypatch.delenv("ALLURE_TESTOPS_API_TOKEN", raising=False)
    monkeypatch.setenv("ALLURE_TESTOPS_TIMEOUT", "-1")
    monkeypatch.setenv("ALLURE_TESTOPS_CACHE_TTL", "0")
    monkeypatch.setenv("ALLURE_TESTOPS_RETRY_ATTEMPTS", "0")
    monkeypatch.setenv("ALLURE_TESTOPS_NETWORK_RETRY_ATTEMPTS", "0")
    monkeypatch.setenv("ALLURE_TESTOPS_RETRY_DELAY", "-1")
    monkeypatch.setenv("ALLURE_TESTOPS_CIRCUIT_BREAKER_FAILURES", "0")
    monkeypatch.setenv("ALLURE_TESTOPS_CIRCUIT_BREAKER_TIMEOUT", "0")

    cfg = config_module.Config()

    errors = cfg.validate()

    assert "ALLURE_TESTOPS_URL должен начинаться с http:// или https://" in errors
    assert "ALLURE_TESTOPS_API_TOKEN не задан. Укажите ваш API токен." in errors
    assert "ALLURE_TESTOPS_TIMEOUT должен быть положительным числом." in errors
    assert "ALLURE_TESTOPS_CACHE_TTL должен быть положительным числом." in errors
    assert "ALLURE_TESTOPS_RETRY_ATTEMPTS должен быть положительным числом." in errors
    assert "ALLURE_TESTOPS_NETWORK_RETRY_ATTEMPTS должен быть положительным числом." in errors
    assert "ALLURE_TESTOPS_RETRY_DELAY должен быть неотрицательным числом." in errors
    assert "ALLURE_TESTOPS_CIRCUIT_BREAKER_FAILURES должен быть положительным числом." in errors
    assert "ALLURE_TESTOPS_CIRCUIT_BREAKER_TIMEOUT должен быть положительным числом." in errors


def test_module_level_config_picks_up_environment_after_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALLURE_TESTOPS_URL", "https://reloaded.example.com/")
    monkeypatch.setenv("ALLURE_TESTOPS_API_TOKEN", "reloaded-token")

    reloaded_module = reload(config_module)

    assert reloaded_module.config.url == "https://reloaded.example.com"
    assert reloaded_module.config.api_token == "reloaded-token"
