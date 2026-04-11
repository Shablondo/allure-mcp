import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.client import (  # noqa: E402
    AuthenticationError,
    AllureTestOpsClient,
    CircuitBreakerState,
    _GET_CACHE,
    _clear_cache,
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
