"""
HTTP клиент для Allure TestOps API.

Асинхронный клиент для выполнения запросов к API Allure TestOps
с поддержкой connection pooling, retry, circuit breaker и кэширования.
"""

import asyncio
import httpx
import json
import time
from typing import Any, AsyncIterator
from contextlib import asynccontextmanager

from tenacity import retry, retry_if_exception, retry_if_exception_type, stop_after_attempt, wait_fixed

from .config import config


class AllureTestOpsError(Exception):
    """Базовое исключение для ошибок Allure TestOps API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AllureTestOpsError):
    """Ошибка аутентификации."""

    pass


class NotFoundError(AllureTestOpsError):
    """Ресурс не найден."""

    pass


class NetworkError(AllureTestOpsError):
    """Ошибка сети."""

    pass


class CircuitBreakerOpenError(Exception):
    """Circuit breaker открыт - запросы запрещены."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class CircuitBreakerState:
    """Состояние Circuit Breaker."""

    def __init__(self, failure_threshold: int, recovery_timeout: int) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state = "closed"
        self._probe_in_flight = False

    def success(self) -> None:
        """Фиксирует успешный запрос."""
        if self._state == "half_open":
            self._state = "closed"
            print(f"✓ Circuit Breaker: возвращаемся в CLOSED")
        self._failure_count = 0
        self._probe_in_flight = False

    def failure(self) -> None:
        """Фиксирует неуспешный запрос."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._probe_in_flight = False

        if self._state == "half_open" or self._failure_count >= self._failure_threshold:
            if self._state != "open":
                self._state = "open"
                print(f"✗ Circuit Breaker: переходим в OPEN (после {self._failure_count} failures)")

    def can_attempt(self) -> bool:
        """
        Проверяет, можно ли делать запрос.

        Returns:
            True если запрос разрешен, False если circuit breaker открыт
        """
        if self._state == "closed":
            return True

        if self._state == "open":
            if self._last_failure_time is None:
                return True

            elapsed = time.time() - self._last_failure_time
            if elapsed >= self._recovery_timeout and not self._probe_in_flight:
                self._state = "half_open"
                self._probe_in_flight = True
                print(f"⚡ Circuit Breaker: переходим в HALF_OPEN (пробуем один запрос)")
                return True
            return False

        if self._state == "half_open":
            return False

        return False

    def get_state_name(self) -> str:
        """Возвращает текущее состояние."""
        return self._state


# Глобальный Circuit Breaker — разделяется между всеми экземплярами клиента
_CIRCUIT_BREAKER: "CircuitBreakerState | None" = None
_SHARED_ASYNC_CLIENT: httpx.AsyncClient | None = None
_SHARED_ASYNC_CLIENT_LOCK = asyncio.Lock()

def _get_circuit_breaker() -> "CircuitBreakerState":
    global _CIRCUIT_BREAKER
    if _CIRCUIT_BREAKER is None:
        _CIRCUIT_BREAKER = CircuitBreakerState(
            failure_threshold=config.circuit_breaker_failures,
            recovery_timeout=config.circuit_breaker_timeout,
        )
    return _CIRCUIT_BREAKER


# Глобальный TTL-кэш для GET-запросов
_GET_CACHE: dict[str, tuple[Any, float]] = {}
_GET_CACHE_LOCK = asyncio.Lock()

async def _get_from_cache(key: str) -> "tuple[Any, bool]":
    """Возвращает (значение, найдено_в_кэше). TTL берётся из config.cache_ttl."""
    async with _GET_CACHE_LOCK:
        now = time.time()
        if key in _GET_CACHE:
            value, expires_at = _GET_CACHE[key]
            if now < expires_at:
                return value, True
            del _GET_CACHE[key]
    return None, False


async def _put_to_cache(key: str, value: Any) -> None:
    """Сохраняет значение в кэш с TTL из config.cache_ttl."""
    async with _GET_CACHE_LOCK:
        _GET_CACHE[key] = (value, time.time() + config.cache_ttl)


async def _clear_cache() -> None:
    """Сбрасывает GET-кэш после изменяющих запросов."""
    async with _GET_CACHE_LOCK:
        _GET_CACHE.clear()


def _cache_invalidation_prefixes(endpoint: str) -> tuple[str, ...]:
    """Возвращает префиксы ключей, которые нужно инвалидировать после мутации."""
    parts = [part for part in endpoint.split("/") if part]
    if len(parts) >= 2:
        return (f"/{parts[0]}/{parts[1]}", endpoint.rstrip("/"))
    return (endpoint.rstrip("/"),)


async def _invalidate_cache_for_endpoint(endpoint: str) -> None:
    """Удаляет только те GET-кэши, которые связаны с изменяемым ресурсом."""
    prefixes = tuple(prefix for prefix in _cache_invalidation_prefixes(endpoint) if prefix)
    async with _GET_CACHE_LOCK:
        keys_to_delete = [
            key
            for key in _GET_CACHE
            if any(key.startswith(prefix) for prefix in prefixes)
        ]
        for key in keys_to_delete:
            del _GET_CACHE[key]


def _should_retry_api_error(error: BaseException) -> bool:
    """Повторяем только transient API ошибки 5xx."""
    return isinstance(error, AllureTestOpsError) and error.status_code is not None and error.status_code >= 500


class AllureTestOpsClient:
    """Асинхронный HTTP клиент для Allure TestOps API."""

    def __init__(self) -> None:
        """Инициализация клиента."""
        self._base_url = config.url
        self._api_token = config.api_token
        self._timeout = config.timeout
        self._async_client: httpx.AsyncClient | None = None
        self._circuit_breaker = _get_circuit_breaker()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """
        Создает или возвращает существующий AsyncClient.

        Returns:
            AsyncClient с настройками connection pooling
        """
        global _SHARED_ASYNC_CLIENT
        if _SHARED_ASYNC_CLIENT is None or _SHARED_ASYNC_CLIENT.is_closed:
            async with _SHARED_ASYNC_CLIENT_LOCK:
                if _SHARED_ASYNC_CLIENT is None or _SHARED_ASYNC_CLIENT.is_closed:
                    limits = httpx.Limits(
                        max_keepalive_connections=20,
                        max_connections=100,
                    )
                    _SHARED_ASYNC_CLIENT = httpx.AsyncClient(
                        timeout=self._timeout,
                        limits=limits,
                        http2=True,
                    )
        self._async_client = _SHARED_ASYNC_CLIENT
        return _SHARED_ASYNC_CLIENT

    @asynccontextmanager
    async def _get_client_context(self) -> AsyncIterator[httpx.AsyncClient]:
        """
        Context manager для AsyncClient.

        Yields:
            AsyncClient
        """
        client = await self._ensure_client()
        try:
            yield client
        finally:
            pass

    async def __aenter__(self) -> "AllureTestOpsClient":
        """Вход в context manager."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Выход из context manager - закрытие клиента."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    async def close(self) -> None:
        """Закрывает HTTP клиент."""
        global _SHARED_ASYNC_CLIENT
        async with _SHARED_ASYNC_CLIENT_LOCK:
            if _SHARED_ASYNC_CLIENT is not None and not _SHARED_ASYNC_CLIENT.is_closed:
                await _SHARED_ASYNC_CLIENT.aclose()
            _SHARED_ASYNC_CLIENT = None
            self._async_client = None

    def _get_headers(self, files: list[tuple] | None = None) -> dict[str, str]:
        """Возвращает заголовки для запросов."""
        headers = {
            "Authorization": f"Api-Token {self._api_token}",
            "Accept": "application/json",
        }
        if not files:
            headers["Content-Type"] = "application/json"
        return headers

    def _is_transient_error(self, status_code: int | None) -> bool:
        """
        Проверяет, является ли ошибка временной.

        Args:
            status_code: HTTP статус код

        Returns:
            True если это 5xx ошибка, False иначе
        """
        return status_code is not None and status_code >= 500

    def _handle_response(self, response: httpx.Response, return_raw: bool = False) -> Any:
        """
        Обрабатывает HTTP ответ.

        Args:
            response: HTTP объект ответа
            return_raw: Если True, возвращает текст ответа вместо JSON

        Returns:
            dict[str, Any] или str с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            AllureTestOpsError: Другие ошибки API
        """
        if response.status_code in (401, 403):
            raise AuthenticationError(
                "Ошибка аутентификации: проверьте URL сервера и API токен в переменных окружения",
                response.status_code,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                "Запрашиваемый ресурс не найден. Проверьте правильность ID",
                response.status_code,
            )
        elif response.status_code >= 400:
            error_msg = response.text or f"HTTP ошибка: {response.status_code}"
            raise AllureTestOpsError(error_msg, response.status_code)

        if return_raw:
            return response.text
        return response.json()

    @staticmethod
    def _build_cache_key(endpoint: str, params: dict[str, Any] | None = None) -> str:
        """Строит стабильный ключ для GET-кэша."""
        return f"{endpoint}:{json.dumps(params, sort_keys=True) if params else ''}"

    @retry(
        stop=stop_after_attempt(config.network_retry_attempts),
        wait=wait_fixed(config.retry_delay),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def _make_request_network_retry(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        files: list[tuple] | None = None,
        return_raw: bool = False,
    ) -> Any:
        """
        Выполняет HTTP запрос с retry для сетевых ошибок.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query параметры
            json_data: JSON тело запроса
            files: Файлы для multipart/form-data загрузки
            return_raw: Вернуть сырой текст вместо JSON

        Returns:
            dict[str, Any] или str с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            AllureTestOpsError: Другие ошибки API
        """
        url = f"{self._base_url}{endpoint}"
        headers = self._get_headers(files=files)

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": params,
        }
        if files:
            request_kwargs["files"] = files
        else:
            request_kwargs["json"] = json_data

        async with self._get_client_context() as client:
            response = await client.request(**request_kwargs)

        if return_raw:
            return self._handle_response(response, return_raw=True)
        return self._handle_response(response)

    @retry(
        stop=stop_after_attempt(config.retry_attempts),
        wait=wait_fixed(config.retry_delay),
        retry=retry_if_exception(_should_retry_api_error),
        reraise=True,
    )
    async def _retry_5xx_errors(self, func) -> Any:
        """
        Retry wrapper для обработки 5xx ошибок.

        Args:
            func: Функция для выполнения

        Returns:
            Результат выполнения функции
        """
        return await func()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        files: list[tuple] | None = None,
        return_raw: bool = False,
    ) -> Any:
        """
        Выполняет HTTP запрос к API с circuit breaker.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query параметры
            json_data: JSON тело запроса
            files: Файлы для multipart/form-data загрузки
            return_raw: Вернуть сырой текст вместо JSON

        Returns:
            dict[str, Any] или str с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        if not self._circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError(
                f"Circuit Breaker is **OPEN** (состояние: {self._circuit_breaker.get_state_name()}). "
                f"Попробуйте через {config.circuit_breaker_timeout} секунд."
            )

        status_code = None

        async def make_request_with_retry_5xx() -> Any:
            nonlocal status_code
            try:
                result = await self._make_request_network_retry(
                    method, endpoint, params, json_data, files, return_raw
                )
                self._circuit_breaker.success()
                return result
            except (NotFoundError, AuthenticationError) as e:
                status_code = e.status_code
                raise
            except AllureTestOpsError as e:
                status_code = e.status_code
                if self._is_transient_error(status_code):
                    print(f"⚠ Transient error {status_code}: {e.message} - retrying...")
                    raise
                raise AllureTestOpsError(e.message, status_code)

        try:
            result = await self._retry_5xx_errors(make_request_with_retry_5xx)

            if self._is_transient_error(status_code):
                raise AllureTestOpsError(f"Unexpected error after retries: status {status_code}", status_code)

            return result

        except (NetworkError, AllureTestOpsError) as e:
            if self._is_transient_error(e.status_code):
                self._circuit_breaker.failure()
            raise
        except asyncio.CancelledError:
            raise
        except CircuitBreakerOpenError:
            raise
        except Exception as e:
            if isinstance(e, (httpx.TimeoutException, httpx.ConnectError)):
                self._circuit_breaker.failure()
                raise NetworkError(str(e)) from e
            raise AllureTestOpsError(f"Неожиданная ошибка при запросе к API: {e}")

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Выполняет GET запрос к API.

        Args:
            endpoint: API endpoint
            params: Query параметры
            use_cache: Использовать кэш (по умолчанию True)

        Returns:
            Словарь с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        if use_cache:
            cache_key = self._build_cache_key(endpoint, params)
            cached_value, found = await _get_from_cache(cache_key)
            if found:
                return cached_value
            result = await self._make_request("GET", endpoint, params=params)
            await _put_to_cache(cache_key, result)
            return result

        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: list[tuple] | None = None,
    ) -> dict[str, Any]:
        """
        Выполняет POST запрос к API.

        Args:
            endpoint: API endpoint
            json_data: JSON тело запроса
            params: Query параметры
            files: Файлы для multipart/form-data загрузки

        Returns:
            Словарь с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        result = await self._make_request("POST", endpoint, params=params, json_data=json_data, files=files)
        await _invalidate_cache_for_endpoint(endpoint)
        return result

    async def patch(
        self,
        endpoint: str,
        json_data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Выполняет PATCH запрос к API.

        Args:
            endpoint: API endpoint
            json_data: JSON тело запроса
            params: Query параметры

        Returns:
            Словарь с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        result = await self._make_request("PATCH", endpoint, params=params, json_data=json_data)
        await _invalidate_cache_for_endpoint(endpoint)
        return result

    async def put(
        self,
        endpoint: str,
        json_data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Выполняет PUT запрос к API.

        Args:
            endpoint: API endpoint
            json_data: JSON тело запроса
            params: Query параметры

        Returns:
            Словарь с данными ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        result = await self._make_request("PUT", endpoint, params=params, json_data=json_data)
        await _invalidate_cache_for_endpoint(endpoint)
        return result

    async def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """
        Выполняет DELETE запрос к API.

        Args:
            endpoint: API endpoint
            params: Query параметры

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        await self._make_request("DELETE", endpoint, params=params)
        await _invalidate_cache_for_endpoint(endpoint)

    async def get_raw(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """
        Выполняет GET запрос к API и возвращает сырой текст ответа.
        Используется для endpoints, которые возвращают text/plain вместо JSON.

        Args:
            endpoint: API endpoint
            params: Query параметры

        Returns:
            Строка с содержимым ответа

        Raises:
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
            NetworkError: Ошибка сети
            CircuitBreakerOpenError: Circuit breaker открыт
            AllureTestOpsError: Другие ошибки API
        """
        return await self._make_request("GET", endpoint, params=params, return_raw=True)


@asynccontextmanager
async def get_client() -> AsyncIterator[AllureTestOpsClient]:
    """
    Получает клиент как context manager.

    Yields:
        Экземпляр AllureTestOpsClient
    """
    client = AllureTestOpsClient()
    try:
        await client.__aenter__()
        yield client
    finally:
        await client.__aexit__(None, None, None)
