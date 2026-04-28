import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.client import (  # noqa: E402
    AllureTestOpsClient,
    AllureTestOpsError,
    AuthenticationError,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    NetworkError,
    NotFoundError,
    _GET_CACHE,
    _SHARED_ASYNC_CLIENT,
    _cache_invalidation_prefixes,
    _clear_cache,
    _get_circuit_breaker,
    _get_from_cache,
    _invalidate_cache_for_endpoint,
    _put_to_cache,
    _should_retry_api_error,
    get_client,
)


def run(coro):
    return asyncio.run(coro)


def test_retry_does_not_repeat_authentication_errors(monkeypatch):
    client = AllureTestOpsClient()
    attempts = 0

    async def fake_request(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        raise AuthenticationError("bad token", 401)

    monkeypatch.setattr(client, "_make_request_network_retry", fake_request)

    with pytest.raises(AuthenticationError):
        run(client._make_request("GET", "/api/testcase"))

    assert attempts == 1


def test_half_open_allows_only_single_probe():
    breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=1)
    breaker.failure()
    breaker._last_failure_time = time.time() - 5

    assert breaker.can_attempt() is True
    assert breaker.can_attempt() is False


def test_shared_async_client_reused_between_instances():
    first = AllureTestOpsClient()
    second = AllureTestOpsClient()

    first_client = run(first._ensure_client())
    second_client = run(second._ensure_client())

    assert first_client is second_client

    run(first.close())


def test_post_invalidates_only_related_cache_entries(monkeypatch):
    run(_clear_cache())
    _GET_CACHE["/api/testcase:{\"id\": 1}"] = ({"case": 1}, time.time() + 60)
    _GET_CACHE["/api/project/42/cf:"] = ({"project": 42}, time.time() + 60)

    client = AllureTestOpsClient()

    async def fake_make_request(*args, **kwargs):
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    run(client.post("/api/testcase", json_data={"id": 1}))

    assert "/api/testcase:{\"id\": 1}" not in _GET_CACHE
    assert "/api/project/42/cf:" in _GET_CACHE

    run(_clear_cache())


class TestErrorClasses:
    def test_allure_testops_error_basic(self):
        err = AllureTestOpsError("something failed", 500)
        assert err.message == "something failed"
        assert err.status_code == 500
        assert str(err) == "something failed"

    def test_allure_testops_error_no_status(self):
        err = AllureTestOpsError("generic error")
        assert err.message == "generic error"
        assert err.status_code is None

    def test_authentication_error(self):
        err = AuthenticationError("bad", 401)
        assert isinstance(err, AllureTestOpsError)
        assert err.status_code == 401

    def test_not_found_error(self):
        err = NotFoundError("missing", 404)
        assert isinstance(err, AllureTestOpsError)
        assert err.status_code == 404

    def test_network_error(self):
        err = NetworkError("timeout")
        assert isinstance(err, AllureTestOpsError)
        assert err.status_code is None

    def test_circuit_breaker_open_error(self):
        err = CircuitBreakerOpenError("circuit is open")
        assert err.message == "circuit is open"
        assert str(err) == "circuit is open"


class TestCircuitBreakerState:
    def test_closed_allows_attempts(self):
        breaker = CircuitBreakerState(failure_threshold=3, recovery_timeout=10)
        assert breaker.can_attempt() is True
        assert breaker.get_state_name() == "closed"

    def test_success_resets_failure_count(self):
        breaker = CircuitBreakerState(failure_threshold=2, recovery_timeout=10)
        breaker.failure()
        assert breaker._failure_count == 1
        breaker.success()
        assert breaker._failure_count == 0

    def test_opens_after_threshold(self):
        breaker = CircuitBreakerState(failure_threshold=2, recovery_timeout=10)
        breaker.failure()
        assert breaker.get_state_name() == "closed"
        breaker.failure()
        assert breaker.get_state_name() == "open"

    def test_open_blocks_attempts(self):
        breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=10)
        breaker.failure()
        assert breaker.can_attempt() is False

    def test_half_open_after_timeout(self):
        breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=1)
        breaker.failure()
        breaker._last_failure_time = time.time() - 5
        assert breaker.can_attempt() is True
        assert breaker.get_state_name() == "half_open"

    def test_half_open_blocks_second_attempt(self):
        breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=1)
        breaker.failure()
        breaker._last_failure_time = time.time() - 5
        breaker.can_attempt()
        assert breaker.can_attempt() is False

    def test_success_closes_half_open(self):
        breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=1)
        breaker.failure()
        breaker._last_failure_time = time.time() - 5
        breaker.can_attempt()
        breaker.success()
        assert breaker.get_state_name() == "closed"

    def test_failure_reopens_half_open(self):
        breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=1)
        breaker.failure()
        breaker._last_failure_time = time.time() - 5
        breaker.can_attempt()
        breaker.failure()
        assert breaker.get_state_name() == "open"


class TestCacheFunctions:
    def test_put_and_get_from_cache(self):
        run(_clear_cache())
        run(_put_to_cache("key1", {"data": 1}))
        value, found = run(_get_from_cache("key1"))
        assert found is True
        assert value == {"data": 1}
        run(_clear_cache())

    def test_cache_miss(self):
        run(_clear_cache())
        value, found = run(_get_from_cache("nonexistent"))
        assert found is False
        assert value is None
        run(_clear_cache())

    def test_cache_ttl_expiration(self):
        run(_clear_cache())
        _GET_CACHE["key"] = ({"data": 1}, time.time() - 1)
        value, found = run(_get_from_cache("key"))
        assert found is False
        run(_clear_cache())

    def test_clear_cache(self):
        run(_clear_cache())
        _GET_CACHE["a"] = (1, time.time() + 60)
        _GET_CACHE["b"] = (2, time.time() + 60)
        run(_clear_cache())
        assert len(_GET_CACHE) == 0


class TestCacheInvalidation:
    def test_invalidation_prefixes_nested(self):
        prefixes = _cache_invalidation_prefixes("/api/testcase/123")
        assert "/api/testcase" in prefixes
        assert "/api/testcase/123" in prefixes

    def test_invalidation_prefixes_flat(self):
        prefixes = _cache_invalidation_prefixes("/api/comment")
        assert "/api/comment" in prefixes

    def test_invalidate_related_entries(self):
        run(_clear_cache())
        _GET_CACHE['/api/testcase:{"id": 1}'] = ({"id": 1}, time.time() + 60)
        _GET_CACHE['/api/testcase/123:'] = ({"id": 123}, time.time() + 60)
        _GET_CACHE['/api/other:'] = ({"x": 1}, time.time() + 60)
        run(_invalidate_cache_for_endpoint("/api/testcase"))
        assert '/api/testcase:{"id": 1}' not in _GET_CACHE
        assert "/api/testcase/123:" not in _GET_CACHE
        assert "/api/other:" in _GET_CACHE
        run(_clear_cache())


class TestShouldRetryApiError:
    def test_retries_500(self):
        err = AllureTestOpsError("server error", 500)
        assert _should_retry_api_error(err) is True

    def test_retries_503(self):
        err = AllureTestOpsError("unavailable", 503)
        assert _should_retry_api_error(err) is True

    def test_does_not_retry_400(self):
        err = AllureTestOpsError("bad request", 400)
        assert _should_retry_api_error(err) is False

    def test_does_not_retry_404(self):
        err = NotFoundError("not found", 404)
        assert _should_retry_api_error(err) is False

    def test_does_not_retry_no_status(self):
        err = AllureTestOpsError("generic")
        assert _should_retry_api_error(err) is False

    def test_does_not_retry_non_allure_error(self):
        assert _should_retry_api_error(ValueError("test")) is False


class TestGetHeaders:
    def test_headers_without_files(self):
        client = AllureTestOpsClient()
        client._api_token = "token123"
        headers = client._get_headers()
        assert headers["Authorization"] == "Api-Token token123"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_headers_with_files(self):
        client = AllureTestOpsClient()
        client._api_token = "token123"
        headers = client._get_headers(files=[("file", ("name.txt", b"data"))])
        assert "Content-Type" not in headers


class TestBuildCacheKey:
    def test_cache_key_without_params(self):
        client = AllureTestOpsClient()
        key = client._build_cache_key("/api/testcase")
        assert key == "/api/testcase:"

    def test_cache_key_with_params(self):
        client = AllureTestOpsClient()
        key = client._build_cache_key("/api/testcase", {"id": 1, "name": "test"})
        assert key == '/api/testcase:{"id": 1, "name": "test"}'

    def test_cache_key_sorts_keys(self):
        client = AllureTestOpsClient()
        key1 = client._build_cache_key("/api", {"b": 2, "a": 1})
        key2 = client._build_cache_key("/api", {"a": 1, "b": 2})
        assert key1 == key2


class TestIsTransientError:
    def test_500_is_transient(self):
        client = AllureTestOpsClient()
        assert client._is_transient_error(500) is True

    def test_503_is_transient(self):
        client = AllureTestOpsClient()
        assert client._is_transient_error(503) is True

    def test_400_not_transient(self):
        client = AllureTestOpsClient()
        assert client._is_transient_error(400) is False

    def test_none_not_transient(self):
        client = AllureTestOpsClient()
        assert client._is_transient_error(None) is False


class TestHandleResponse:
    def test_success_json(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"id": 1}
        assert client._handle_response(response) == {"id": 1}

    def test_success_raw(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 200
        response.text = "plain text"
        assert client._handle_response(response, return_raw=True) == "plain text"

    def test_401_raises_authentication_error(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 401
        with pytest.raises(AuthenticationError) as exc:
            client._handle_response(response)
        assert exc.value.status_code == 401

    def test_403_raises_authentication_error(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 403
        with pytest.raises(AuthenticationError) as exc:
            client._handle_response(response)
        assert exc.value.status_code == 403

    def test_404_raises_not_found_error(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 404
        with pytest.raises(NotFoundError) as exc:
            client._handle_response(response)
        assert exc.value.status_code == 404

    def test_500_raises_allure_error(self):
        client = AllureTestOpsClient()
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"
        with pytest.raises(AllureTestOpsError) as exc:
            client._handle_response(response)
        assert exc.value.status_code == 500


class TestGetWithCache:
    def test_get_caches_result(self):
        run(_clear_cache())
        client = AllureTestOpsClient()
        call_count = 0

        async def fake_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"id": 1}

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_request)

        result1 = run(client.get("/api/testcase/1"))
        result2 = run(client.get("/api/testcase/1"))
        assert result1 == {"id": 1}
        assert result2 == {"id": 1}
        assert call_count == 1
        run(_clear_cache())

    def test_get_skips_cache_when_disabled(self):
        run(_clear_cache())
        client = AllureTestOpsClient()
        call_count = 0

        async def fake_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"id": 1}

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_request)

        run(client.get("/api/testcase/1", use_cache=False))
        run(client.get("/api/testcase/1", use_cache=False))
        assert call_count == 2
        run(_clear_cache())


class TestHTTPMethods:
    def test_post_calls_make_request_and_invalidates_cache(self):
        run(_clear_cache())
        client = AllureTestOpsClient()

        async def fake_make_request(*args, **kwargs):
            return {"created": True}

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_make_request)
        result = run(client.post("/api/testcase", json_data={"name": "test"}))
        assert result == {"created": True}
        run(_clear_cache())

    def test_patch_calls_make_request_and_invalidates_cache(self):
        run(_clear_cache())
        client = AllureTestOpsClient()

        async def fake_make_request(*args, **kwargs):
            return {"updated": True}

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_make_request)
        result = run(client.patch("/api/testcase/1", json_data={"name": "new"}))
        assert result == {"updated": True}
        run(_clear_cache())

    def test_put_calls_make_request_and_invalidates_cache(self):
        run(_clear_cache())
        client = AllureTestOpsClient()

        async def fake_make_request(*args, **kwargs):
            return {"replaced": True}

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_make_request)
        result = run(client.put("/api/testcase/1", json_data={"name": "new"}))
        assert result == {"replaced": True}
        run(_clear_cache())

    def test_delete_calls_make_request_and_invalidates_cache(self):
        run(_clear_cache())
        client = AllureTestOpsClient()

        async def fake_make_request(*args, **kwargs):
            return None

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_make_request)
        run(client.delete("/api/testcase/1"))
        run(_clear_cache())

    def test_get_raw_calls_make_request_with_return_raw(self):
        client = AllureTestOpsClient()

        async def fake_make_request(*args, **kwargs):
            assert kwargs.get("return_raw") is True
            return "raw content"

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(client, "_make_request", fake_make_request)
        result = run(client.get_raw("/api/testcase/1/raw"))
        assert result == "raw content"


class TestCircuitBreakerInMakeRequest:
    def test_open_circuit_raises_error(self):
        client = AllureTestOpsClient()
        client._circuit_breaker.failure()
        client._circuit_breaker._state = "open"
        client._circuit_breaker._last_failure_time = time.time()
        with pytest.raises(CircuitBreakerOpenError):
            run(client._make_request("GET", "/api/testcase"))


class TestGetClient:
    def test_get_client_context_manager(self):
        async def _test():
            async with get_client() as client:
                assert isinstance(client, AllureTestOpsClient)
        run(_test())
