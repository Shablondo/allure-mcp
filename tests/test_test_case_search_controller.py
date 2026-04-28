import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_search_controller import register_test_case_search_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseSearchController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_search_tools(self.mcp)

    def test_search_test_cases_calls_get(self):
        tool = self.registered_tools["allure_searchTestCases"]

        with patch("allure_testops_mcp.controllers.test_case_search_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"items": []})
            MockClient.return_value = mock_client

            run(tool(projectId=38, rql="name like '%test%'", page=0, size=10))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase/__search"
            assert call_args[1]["params"]["projectId"] == 38
            assert call_args[1]["params"]["rql"] == "name like '%test%'"

    def test_validate_search_query_calls_get(self):
        tool = self.registered_tools["allure_validateSearchQuery"]

        with patch("allure_testops_mcp.controllers.test_case_search_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"valid": True})
            MockClient.return_value = mock_client

            run(tool(projectId=38, rql="name like '%test%'"))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase/query/validate"
            assert call_args[1]["params"]["projectId"] == 38
            assert call_args[1]["params"]["rql"] == "name like '%test%'"
