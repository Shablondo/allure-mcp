"""
Конфигурация MCP сервера Allure TestOps.

Загружает и управляет переменными окружения для подключения к Allure TestOps API.
Поддерживает как переменные окружения процесса, так и опциональный `.env` файл.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# `.env` используется только как опциональный fallback.
# Переменные окружения, переданные процессу/контейнеру, имеют приоритет.
load_dotenv(override=False)


class Config:
    """Конфигурация для подключения к Allure TestOps API."""

    def __init__(self) -> None:
        """Инициализация конфигурации из переменных окружения."""
        self._url: str = os.getenv("ALLURE_TESTOPS_URL", "")
        self._api_token: str = os.getenv("ALLURE_TESTOPS_API_TOKEN", "")
        self._project_id: Optional[int] = self._parse_int_env("ALLURE_TESTOPS_PROJECT_ID")
        self._timeout: int = self._get_int_env_or_default("ALLURE_TESTOPS_TIMEOUT", 30)
        self._cache_ttl: int = self._get_int_env_or_default("ALLURE_TESTOPS_CACHE_TTL", 300)
        self._retry_attempts: int = self._get_int_env_or_default("ALLURE_TESTOPS_RETRY_ATTEMPTS", 3)
        self._network_retry_attempts: int = self._get_int_env_or_default(
            "ALLURE_TESTOPS_NETWORK_RETRY_ATTEMPTS", 1
        )
        self._retry_delay: int = self._get_int_env_or_default("ALLURE_TESTOPS_RETRY_DELAY", 2)
        self._circuit_breaker_failures: int = self._get_int_env_or_default(
            "ALLURE_TESTOPS_CIRCUIT_BREAKER_FAILURES", 5
        )
        self._circuit_breaker_timeout: int = self._get_int_env_or_default(
            "ALLURE_TESTOPS_CIRCUIT_BREAKER_TIMEOUT", 60
        )

    @staticmethod
    def _parse_int_env(env_var: str) -> Optional[int]:
        """Парсит целочисленное значение из переменной окружения."""
        value = os.getenv(env_var)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @classmethod
    def _get_int_env_or_default(cls, env_var: str, default: int) -> int:
        """Возвращает значение env-переменной или default, если переменная не задана/непарсится."""
        value = cls._parse_int_env(env_var)
        return default if value is None else value

    @property
    def url(self) -> str:
        """URL сервера Allure TestOps."""
        return self._url.rstrip("/")

    @property
    def api_token(self) -> str:
        """API токен для аутентификации."""
        return self._api_token

    @property
    def project_id(self) -> Optional[int]:
        """ID проекта по умолчанию."""
        return self._project_id

    @property
    def timeout(self) -> int:
        """Таймаут запросов в секундах."""
        return self._timeout

    @property
    def cache_ttl(self) -> int:
        """Время жизни кэша в секундах."""
        return self._cache_ttl

    @property
    def retry_attempts(self) -> int:
        """Количество попыток retry для transient ошибок."""
        return self._retry_attempts

    @property
    def network_retry_attempts(self) -> int:
        """Количество попыток retry для сетевых ошибок."""
        return self._network_retry_attempts

    @property
    def retry_delay(self) -> int:
        """Задержка между retry попытками в секундах."""
        return self._retry_delay

    @property
    def circuit_breaker_failures(self) -> int:
        """Порог срабатывания circuit breaker (количество sequential failures)."""
        return self._circuit_breaker_failures

    @property
    def circuit_breaker_timeout(self) -> int:
        """Таймаут recovery для circuit breaker в секундах."""
        return self._circuit_breaker_timeout

    def validate(self) -> list[str]:
        """
        Проверяет конфигурацию на валидность.

        Returns:
            Список ошибок валидации. Пустой список если конфигурация валидна.
        """
        errors: list[str] = []

        if not self._url:
            errors.append("ALLURE_TESTOPS_URL не задан. Укажите URL вашего сервера Allure TestOps.")
        elif not self._url.startswith(("http://", "https://")):
            errors.append("ALLURE_TESTOPS_URL должен начинаться с http:// или https://")

        if not self._api_token:
            errors.append("ALLURE_TESTOPS_API_TOKEN не задан. Укажите ваш API токен.")

        if self._timeout <= 0:
            errors.append("ALLURE_TESTOPS_TIMEOUT должен быть положительным числом.")

        if self._cache_ttl <= 0:
            errors.append("ALLURE_TESTOPS_CACHE_TTL должен быть положительным числом.")

        if self._retry_attempts <= 0:
            errors.append("ALLURE_TESTOPS_RETRY_ATTEMPTS должен быть положительным числом.")

        if self._network_retry_attempts <= 0:
            errors.append("ALLURE_TESTOPS_NETWORK_RETRY_ATTEMPTS должен быть положительным числом.")

        if self._retry_delay < 0:
            errors.append("ALLURE_TESTOPS_RETRY_DELAY должен быть неотрицательным числом.")

        if self._circuit_breaker_failures <= 0:
            errors.append("ALLURE_TESTOPS_CIRCUIT_BREAKER_FAILURES должен быть положительным числом.")

        if self._circuit_breaker_timeout <= 0:
            errors.append("ALLURE_TESTOPS_CIRCUIT_BREAKER_TIMEOUT должен быть положительным числом.")

        return errors


# Глобальный экземпляр конфигурации
config = Config()
