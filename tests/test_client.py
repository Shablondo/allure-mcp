from __future__ import annotations

import httpx
import pytest

from allure_testops_mcp.client import (
    AllureTestOpsClient,
    AllureTestOpsError,
    AuthenticationError,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    NotFoundError,
)


def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreakerState(failure_threshold=2, recovery_timeout=60)

    breaker.failure()
    assert breaker.get_state_name() == "closed"
    assert breaker.can_attempt() is True

    breaker.failure()
    assert breaker.get_state_name() == "open"
    assert breaker.can_attempt() is False


def test_circuit_breaker_moves_to_half_open_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=5)

    breaker.failure()
    monkeypatch.setattr("allure_testops_mcp.client.time.time", lambda: 106.0)
    breaker._last_failure_time = 100.0

    assert breaker.can_attempt() is True
    assert breaker.get_state_name() == "half_open"


def test_handle_response_maps_status_codes_to_domain_errors() -> None:
    client = AllureTestOpsClient()

    with pytest.raises(AuthenticationError):
        client._handle_response(httpx.Response(401))

    with pytest.raises(NotFoundError):
        client._handle_response(httpx.Response(404))

    with pytest.raises(AllureTestOpsError) as exc_info:
        client._handle_response(httpx.Response(500, text="boom"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "boom"


def test_handle_response_returns_text_or_json() -> None:
    client = AllureTestOpsClient()

    json_response = httpx.Response(200, json={"ok": True})
    text_response = httpx.Response(200, text="plain")

    assert client._handle_response(json_response) == {"ok": True}
    assert client._handle_response(text_response, return_raw=True) == "plain"


@pytest.mark.asyncio
async def test_get_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AllureTestOpsClient()
    calls: list[str] = []

    async def fake_make_request(method: str, endpoint: str, params=None, json_data=None, return_raw=False):
        calls.append(f"{method}:{endpoint}")
        return {"endpoint": endpoint, "params": params}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    first = await client.get("/api/test-cases", params={"page": 1})
    second = await client.get("/api/test-cases", params={"page": 1})

    assert first == second
    assert calls == ["GET:/api/test-cases"]


@pytest.mark.asyncio
async def test_get_skips_cache_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AllureTestOpsClient()
    calls: list[str] = []

    async def fake_make_request(method: str, endpoint: str, params=None, json_data=None, return_raw=False):
        calls.append(f"{method}:{endpoint}")
        return {"call": len(calls)}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    first = await client.get("/api/test-cases", use_cache=False)
    second = await client.get("/api/test-cases", use_cache=False)

    assert first == {"call": 1}
    assert second == {"call": 2}
    assert calls == ["GET:/api/test-cases", "GET:/api/test-cases"]


@pytest.mark.asyncio
async def test_make_request_raises_when_circuit_breaker_is_open() -> None:
    client = AllureTestOpsClient()
    client._circuit_breaker = CircuitBreakerState(failure_threshold=1, recovery_timeout=60)
    client._circuit_breaker.failure()

    with pytest.raises(CircuitBreakerOpenError):
        await client._make_request("GET", "/api/test-cases")
