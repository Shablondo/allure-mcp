from __future__ import annotations

import pytest

from allure_testops_mcp.client import AllureTestOpsError
from allure_testops_mcp.controllers._utils import (
    build_params,
    delete_response,
    dump_json,
    json_response,
    raw_response,
)


def test_build_params_skips_none_values() -> None:
    assert build_params(project_id=10, query=None, deleted=False) == {
        "project_id": 10,
        "deleted": False,
    }


def test_dump_json_preserves_unicode() -> None:
    dumped = dump_json({"message": "Привет"})

    assert "Привет" in dumped
    assert "\\u041f" not in dumped


@pytest.mark.asyncio
async def test_json_response_wraps_error_message() -> None:
    async def failing_request():
        raise AllureTestOpsError("base failure")

    with pytest.raises(AllureTestOpsError) as exc_info:
        await json_response(failing_request(), "Не удалось получить данные")

    assert exc_info.value.message == "Не удалось получить данные: base failure"


@pytest.mark.asyncio
async def test_raw_response_returns_text() -> None:
    async def request() -> str:
        return "plain-text"

    assert await raw_response(request(), "unused") == "plain-text"


@pytest.mark.asyncio
async def test_delete_response_returns_success_message() -> None:
    async def request() -> None:
        return None

    assert await delete_response(request(), "unused", success_message="Deleted") == "Deleted"
