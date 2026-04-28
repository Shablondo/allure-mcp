import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.client import AllureTestOpsError  # noqa: E402
from allure_testops_mcp.controllers._utils import (  # noqa: E402
    apply_project_id_fallback,
    build_params,
    delete_response,
    dump_json,
    json_response,
    raw_response,
    resolve_project_id,
)


def run(coro):
    return asyncio.run(coro)


class TestBuildParams:
    def test_filters_none_values(self):
        result = build_params(a=1, b=None, c=3)
        assert result == {"a": 1, "c": 3}

    def test_keeps_all_non_none(self):
        result = build_params(x=10, y="test", z=[1, 2])
        assert result == {"x": 10, "y": "test", "z": [1, 2]}

    def test_empty_when_all_none(self):
        result = build_params(a=None, b=None)
        assert result == {}

    def test_empty_when_no_args(self):
        result = build_params()
        assert result == {}

    def test_keeps_false_and_zero(self):
        result = build_params(a=False, b=0, c="")
        assert result == {"a": False, "b": 0, "c": ""}


class TestResolveProjectId:
    def test_returns_explicit_value(self, monkeypatch):
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", MagicMock(project_id=77))
        assert resolve_project_id(15) == 15

    def test_returns_config_when_none(self, monkeypatch):
        mock_config = MagicMock(project_id=42)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        assert resolve_project_id(None) == 42

    def test_returns_none_when_no_default(self, monkeypatch):
        mock_config = MagicMock(project_id=None)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        assert resolve_project_id(None) is None


class TestApplyProjectIdFallback:
    def test_keeps_explicit_project_id(self, monkeypatch):
        mock_config = MagicMock(project_id=99)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        body = {"name": "test", "projectId": 10}
        result = apply_project_id_fallback(body)
        assert result["projectId"] == 10

    def test_applies_config_fallback(self, monkeypatch):
        mock_config = MagicMock(project_id=42)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        body = {"name": "test"}
        result = apply_project_id_fallback(body)
        assert result["projectId"] == 42

    def test_no_change_when_no_default(self, monkeypatch):
        mock_config = MagicMock(project_id=None)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        body = {"name": "test"}
        result = apply_project_id_fallback(body)
        assert "projectId" not in result

    def test_explicit_none_gets_fallback(self, monkeypatch):
        mock_config = MagicMock(project_id=42)
        monkeypatch.setattr("allure_testops_mcp.controllers._utils.config", mock_config)
        body = {"name": "test", "projectId": None}
        result = apply_project_id_fallback(body)
        assert result["projectId"] == 42


class TestDumpJson:
    def test_serializes_dict(self):
        result = dump_json({"key": "value"})
        assert json.loads(result) == {"key": "value"}

    def test_indent_2(self):
        result = dump_json({"a": 1})
        assert "  " in result

    def test_ensure_ascii_false(self):
        result = dump_json({"text": "привет"})
        assert "привет" in result

    def test_serializes_list(self):
        result = dump_json([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]


class TestJsonResponse:
    def test_returns_json_on_success(self):
        async def fake_request():
            return {"id": 1, "name": "test"}

        result = run(json_response(fake_request(), "error msg"))
        parsed = json.loads(result)
        assert parsed == {"id": 1, "name": "test"}

    def test_wraps_error(self):
        async def fake_request():
            raise AllureTestOpsError("api failed", 500)

        with pytest.raises(AllureTestOpsError) as exc:
            run(json_response(fake_request(), "context error"))
        assert "context error" in str(exc.value)
        assert "api failed" in str(exc.value)


class TestRawResponse:
    def test_returns_string_on_success(self):
        async def fake_request():
            return "raw content"

        result = run(raw_response(fake_request(), "error msg"))
        assert result == "raw content"

    def test_wraps_error(self):
        async def fake_request():
            raise AllureTestOpsError("api failed", 404)

        with pytest.raises(AllureTestOpsError) as exc:
            run(raw_response(fake_request(), "context error"))
        assert "context error" in str(exc.value)


class TestDeleteResponse:
    def test_returns_success_message(self):
        async def fake_request():
            return None

        result = run(delete_response(fake_request(), "error msg"))
        assert result == "Successfully deleted"

    def test_custom_success_message(self):
        async def fake_request():
            return None

        result = run(delete_response(fake_request(), "error msg", success_message="Removed"))
        assert result == "Removed"

    def test_wraps_error(self):
        async def fake_request():
            raise AllureTestOpsError("not found", 404)

        with pytest.raises(AllureTestOpsError) as exc:
            run(delete_response(fake_request(), "delete error"))
        assert "delete error" in str(exc.value)
