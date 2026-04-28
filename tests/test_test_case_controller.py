import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_controller import register_test_case_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_tools(self.mcp)

    def test_get_test_cases_calls_get(self):
        get_cases = self.registered_tools["allure_getTestCases"]

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            MockClient.return_value = mock_client

            run(get_cases(projectId=38, page=0, size=10))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase"
            assert call_args[1]["params"]["projectId"] == 38

    def test_create_test_case_calls_post_with_fallback(self):
        create_case = self.registered_tools["allure_createTestCase"]
        body = {"name": "New test", "projectId": 38}

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"id": 1, "name": "New test"})
            MockClient.return_value = mock_client

            run(create_case(body=body))

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json_data"]["name"] == "New test"

    def test_suggest_test_cases_calls_get(self):
        suggest = self.registered_tools["allure_suggestTestCases"]

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient, \
             patch("allure_testops_mcp.controllers.test_case_controller.resolve_project_id") as mock_resolve:
            mock_resolve.return_value = 38
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=[])
            MockClient.return_value = mock_client

            run(suggest(query="login", projectId=38))

            mock_client.get.assert_called_once()
            assert mock_client.get.call_args[0][0] == "/api/testcase/suggest"

    def test_delete_test_case_calls_delete(self):
        delete_case = self.registered_tools["allure_deleteTestCase"]

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.delete = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = run(delete_case(id=12345, force=True))

            mock_client.delete.assert_called_once()
            call_args = mock_client.delete.call_args
            assert call_args[0][0] == "/api/testcase/12345"
            assert call_args[1]["params"]["force"] is True
            assert result == "Successfully deleted"

    def test_get_test_case_calls_get(self):
        get_case = self.registered_tools["allure_getTestCase"]

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"id": 12345, "name": "Test"})
            MockClient.return_value = mock_client

            result = run(get_case(id=12345))

            mock_client.get.assert_called_once_with("/api/testcase/12345")

    def test_update_test_case_calls_patch(self):
        update_case = self.registered_tools["allure_updateTestCase"]
        body = {"name": "Updated name"}

        with patch("allure_testops_mcp.controllers.test_case_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.patch = AsyncMock(return_value={"id": 12345, "name": "Updated name"})
            MockClient.return_value = mock_client

            run(update_case(id=12345, body=body))

            mock_client.patch.assert_called_once_with("/api/testcase/12345", json_data=body)
