import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_custom_field_controller import register_test_case_custom_field_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseCustomFieldController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_custom_field_tools(self.mcp)

    def test_get_custom_fields_for_selection_calls_post(self):
        tool = self.registered_tools["allure_getCustomFieldsForSelection"]
        body = {"projectId": 38, "leafsInclude": [1, 2]}

        with patch("allure_testops_mcp.controllers.test_case_custom_field_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"fields": []})
            MockClient.return_value = mock_client

            run(tool(body=body))

            mock_client.post.assert_called_once_with("/api/testcase/cfv", json_data=body)

    def test_get_custom_fields_for_test_case_calls_get(self):
        tool = self.registered_tools["allure_getCustomFieldsForTestCase"]

        with patch("allure_testops_mcp.controllers.test_case_custom_field_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"fields": []})
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, projectId=38))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase/12345/cfv"
            assert call_args[1]["params"]["projectId"] == 38

    def test_update_custom_fields_calls_patch(self):
        tool = self.registered_tools["allure_updateCustomFields"]
        body = [{"customField": {"id": 1}, "values": [{"id": 2}]}]

        with patch("allure_testops_mcp.controllers.test_case_custom_field_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.patch = AsyncMock(return_value={"ok": True})
            MockClient.return_value = mock_client

            run(tool(testCaseId=12345, body=body))

            mock_client.patch.assert_called_once_with("/api/testcase/12345/cfv", json_data=body)

    def test_suggest_custom_field_values_calls_get(self):
        tool = self.registered_tools["allure_suggestCustomFieldValues"]

        with patch("allure_testops_mcp.controllers.test_case_custom_field_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"values": []})
            MockClient.return_value = mock_client

            run(tool(query="Test", projectId=38, page=0, size=10))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/cfv/suggest"
            assert call_args[1]["params"]["query"] == "Test"

    def test_search_custom_fields_calls_get(self):
        tool = self.registered_tools["allure_searchCustomFields"]

        with patch("allure_testops_mcp.controllers.test_case_custom_field_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"fields": []})
            MockClient.return_value = mock_client

            run(tool(projectId=38, query="Folder", page=0, size=10, sort="id,ASC"))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/project/38/cf"
            assert call_args[1]["params"]["query"] == "Folder"
