import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_issue_controller import register_test_case_issue_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseIssueController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_issue_tools(self.mcp)

    def test_link_test_case_to_kaiten_issue_calls_post(self):
        tool = self.registered_tools["allure_linkTestCaseToKaitenIssue"]

        with patch("allure_testops_mcp.controllers.test_case_issue_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"ok": True})
            MockClient.return_value = mock_client

            run(tool(testcaseId=727870, kaitenIssueNumber="3138098"))

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/api/testcase/727870/issue"
            body = call_args[1]["json_data"]
            assert body == [{"integrationId": 31, "name": "3138098"}]
