import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_tag_controller import register_test_case_tag_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseTagController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_tag_tools(self.mcp)

    def test_get_tags_calls_get(self):
        tool = self.registered_tools["allure_getTags"]

        with patch("allure_testops_mcp.controllers.test_case_tag_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=[{"id": 1, "name": "smoke"}])
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345))

            mock_client.get.assert_called_once_with("/api/testcase/12345/tag")

    def test_set_tags_calls_post(self):
        tool = self.registered_tools["allure_setTags"]
        body = [{"id": 1, "name": "smoke"}, {"id": 2, "name": "regression"}]

        with patch("allure_testops_mcp.controllers.test_case_tag_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"ok": True})
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, body=body))

            mock_client.post.assert_called_once_with("/api/testcase/12345/tag", json_data=body)
