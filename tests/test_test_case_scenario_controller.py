import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_scenario_controller import register_test_case_scenario_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseScenarioController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_scenario_tools(self.mcp)

    def test_create_scenario_step_calls_post(self):
        tool = self.registered_tools["allure_createScenarioStep"]
        body = {"testCaseId": 12345, "body": "Step text"}

        with patch("allure_testops_mcp.controllers.test_case_scenario_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"id": 1})
            MockClient.return_value = mock_client

            run(tool(body=body, beforeId=100, afterId=None, withExpectedResult=True))

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/api/testcase/step"
            assert call_args[1]["json_data"] == body
            assert call_args[1]["params"]["beforeId"] == 100
            assert call_args[1]["params"]["withExpectedResult"] is True

    def test_delete_scenario_step_calls_delete(self):
        tool = self.registered_tools["allure_deleteScenarioStep"]

        with patch("allure_testops_mcp.controllers.test_case_scenario_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.delete = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = run(tool(id=100))

            mock_client.delete.assert_called_once_with("/api/testcase/step/100")
            assert result == "Successfully deleted"

    def test_update_scenario_step_calls_patch(self):
        tool = self.registered_tools["allure_updateScenarioStep"]
        body = {"body": "Updated step"}

        with patch("allure_testops_mcp.controllers.test_case_scenario_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.patch = AsyncMock(return_value={"id": 100, "body": "Updated step"})
            MockClient.return_value = mock_client

            run(tool(id=100, body=body, withExpectedResult=False))

            mock_client.patch.assert_called_once()
            call_args = mock_client.patch.call_args
            assert call_args[0][0] == "/api/testcase/step/100"
            assert call_args[1]["json_data"] == body
            assert call_args[1]["params"]["withExpectedResult"] is False

    def test_get_scenario_calls_get_with_no_cache(self):
        tool = self.registered_tools["allure_getScenario"]

        with patch("allure_testops_mcp.controllers.test_case_scenario_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value={"scenarioSteps": {}})
            MockClient.return_value = mock_client

            run(tool(id=12345))

            mock_client.get.assert_called_once_with("/api/testcase/12345/step", use_cache=False)
