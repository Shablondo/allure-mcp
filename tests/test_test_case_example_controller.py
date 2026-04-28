import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_example_controller import register_test_case_example_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseExampleController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_example_tools(self.mcp)

    def test_get_examples_calls_get(self):
        tool = self.registered_tools["allure_getExamples"]

        with patch("allure_testops_mcp.controllers.test_case_example_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"items": []})
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, page=0, size=10))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase/12345/example"

    def test_set_examples_calls_post(self):
        tool = self.registered_tools["allure_setExamples"]
        body = [[{"name": "browser", "value": "Chrome"}]]

        with patch("allure_testops_mcp.controllers.test_case_example_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=[])
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, body=body))

            mock_client.post.assert_called_once_with("/api/testcase/12345/example", json_data=body)

    def test_rename_parameter_calls_post(self):
        tool = self.registered_tools["allure_renameParameter"]

        with patch("allure_testops_mcp.controllers.test_case_example_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=[])
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, oldName="browser", newName="Browser"))

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/api/testcase/12345/example/rename-parameter"
            assert call_args[1]["params"]["oldName"] == "browser"
            assert call_args[1]["params"]["newName"] == "Browser"

    def test_generate_nwise_calls_post(self):
        tool = self.registered_tools["allure_generateNwise"]
        body = [{"name": "browser", "values": ["Chrome", "Firefox"]}]

        with patch("allure_testops_mcp.controllers.test_case_example_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=[])
            MockClient.return_value = mock_client

            run(tool(body=body, n=2))

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/api/testcase/example/nwise"
            assert call_args[1]["params"]["n"] == 2
