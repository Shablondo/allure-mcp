import asyncio
import base64
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.test_case_attachment_controller import register_test_case_attachment_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestTestCaseAttachmentController:
    def setup_method(self):
        self.mcp = MagicMock()
        self.registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                self.registered_tools[kwargs["name"]] = func
                return func
            return decorator

        self.mcp.tool = capture_tool
        register_test_case_attachment_tools(self.mcp)

    def test_get_attachments_calls_get(self):
        get_attachments = self.registered_tools["allure_getAttachments"]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=[{"id": 1}])
            MockClient.return_value = mock_client

            run(get_attachments(testCaseId=12345, page=0, size=10))

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "/api/testcase/attachment"
            assert call_args[1]["params"]["testCaseId"] == 12345

    def test_upload_attachment_decodes_base64(self):
        upload = self.registered_tools["allure_uploadAttachment"]
        content = base64.b64encode(b"file content").decode()
        files = [{"name": "test.txt", "content": content}]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=[{"id": 1}])
            MockClient.return_value = mock_client

            run(upload(testCaseId=12345, files=files))

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["params"]["testCaseId"] == 12345
            assert len(call_kwargs["files"]) == 1
            assert call_kwargs["files"][0][1][0] == "test.txt"

    def test_delete_attachment_calls_delete(self):
        delete = self.registered_tools["allure_deleteAttachment"]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.delete = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = run(delete(id=99))

            mock_client.delete.assert_called_once_with("/api/testcase/attachment/99")
            assert result == "Successfully deleted"

    def test_update_attachment_calls_patch(self):
        update = self.registered_tools["allure_updateAttachment"]
        body = {"name": "Updated name"}

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.patch = AsyncMock(return_value={"id": 99, "name": "Updated name"})
            MockClient.return_value = mock_client

            run(update(id=99, body=body))

            mock_client.patch.assert_called_once_with("/api/testcase/attachment/99", json_data=body)

    def test_get_attachment_content_calls_get_raw(self):
        get_content = self.registered_tools["allure_getAttachmentContent"]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_raw = AsyncMock(return_value="raw content")
            MockClient.return_value = mock_client

            result = run(get_content(id=99))

            mock_client.get_raw.assert_called_once_with("/api/testcase/attachment/99/content")
            assert result == "raw content"

    def test_update_attachment_content_calls_put(self):
        update_content = self.registered_tools["allure_updateAttachmentContent"]
        body = {"content": "base64_data"}

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.put = AsyncMock(return_value={"ok": True})
            MockClient.return_value = mock_client

            run(update_content(id=99, body=body))

            mock_client.put.assert_called_once_with("/api/testcase/attachment/99/content", json_data=body)

    def test_upload_attachment_and_link_step_is_registered(self):
        assert "allure_uploadAttachmentAndLinkStep" in self.registered_tools

    def test_upload_attachment_and_link_step_uploads_then_creates_step(self):
        tool = self.registered_tools["allure_uploadAttachmentAndLinkStep"]
        content = base64.b64encode(b'{"openapi": "attachment"}').decode()
        files = [{"name": "openapi.json", "content": content}]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    [{"id": 3500635, "name": "openapi.json"}],
                    {"createdStepId": 4570097},
                ]
            )
            mock_client.get = AsyncMock(
                return_value={
                    "root": {"children": [101, 102]},
                    "scenarioSteps": {
                        "101": {"id": 101, "children": []},
                        "102": {"id": 102, "children": []},
                    },
                }
            )
            MockClient.return_value = mock_client

            result = json.loads(run(tool(testCaseId=644594, files=files)))

            assert result["attachmentId"] == 3500635
            assert result["afterId"] == 102
            assert result["step"] == {"createdStepId": 4570097}
            assert mock_client.post.call_args_list[0][0][0] == "/api/testcase/attachment"
            assert mock_client.post.call_args_list[0][1]["params"]["testCaseId"] == 644594
            assert mock_client.get.call_args_list[0][0][0] == "/api/testcase/644594/step"
            assert mock_client.get.call_args_list[0][1]["use_cache"] is False
            assert mock_client.post.call_args_list[1][0][0] == "/api/testcase/step"
            assert mock_client.post.call_args_list[1][1]["json_data"] == {
                "attachmentId": 3500635,
                "testCaseId": 644594,
            }
            assert mock_client.post.call_args_list[1][1]["params"]["afterId"] == 102

    def test_upload_attachment_and_link_step_defaults_attachment_content_type_to_json(self):
        tool = self.registered_tools["allure_uploadAttachmentAndLinkStep"]
        content = base64.b64encode(b'{"curl": "curl --location https://service.example/api"}').decode()
        files = [{"name": "curl-command.sh", "content": content}]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    [{"id": 3500635, "name": "curl-command.sh"}],
                    {"createdStepId": 4570097},
                ]
            )
            mock_client.get = AsyncMock(return_value={"root": {"children": []}, "scenarioSteps": {}})
            MockClient.return_value = mock_client

            run(tool(testCaseId=644594, files=files))

            uploaded_files = mock_client.post.call_args_list[0][1]["files"]
            assert uploaded_files[0][1][2] == "application/json"

    def test_upload_attachment_and_link_step_accepts_utf8_text_content(self):
        tool = self.registered_tools["allure_uploadAttachmentAndLinkStep"]
        raw_text = '{\n    "id": "550e8400-e29b-41d4-a716-446655440001",\n    "name": "Тестовый товар"\n}'
        files = [{"name": "response.json", "textContent": raw_text, "contentType": "application/json"}]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    [{"id": 3500635, "name": "response.json"}],
                    {"createdStepId": 4570097},
                ]
            )
            mock_client.get = AsyncMock(return_value={"root": {"children": []}, "scenarioSteps": {}})
            MockClient.return_value = mock_client

            run(tool(testCaseId=644594, files=files))

            uploaded_files = mock_client.post.call_args_list[0][1]["files"]
            assert uploaded_files[0][1][0] == "response.json"
            assert uploaded_files[0][1][1].decode("utf-8") == raw_text
            assert uploaded_files[0][1][2] == "application/json"

    def test_upload_attachment_and_link_step_uses_last_child_after_id_for_parent_step(self):
        tool = self.registered_tools["allure_uploadAttachmentAndLinkStep"]
        content = base64.b64encode(b"curl --location 'https://service.example/api'").decode()
        files = [{"name": "curl-POST-api.sh", "content": content}]

        with patch("allure_testops_mcp.controllers.test_case_attachment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    [{"id": 3500636, "name": "curl-POST-api.sh"}],
                    {"createdStepId": 4570098},
                ]
            )
            mock_client.get = AsyncMock(
                return_value={
                    "root": {"children": [101, 102]},
                    "scenarioSteps": {
                        "101": {"id": 101, "children": [201, 202]},
                        "102": {"id": 102, "children": []},
                        "201": {"id": 201, "children": []},
                        "202": {"id": 202, "children": []},
                    },
                }
            )
            MockClient.return_value = mock_client

            result = json.loads(run(tool(testCaseId=644594, files=files, parentStepId=101)))

            assert result["attachmentId"] == 3500636
            assert result["parentStepId"] == 101
            assert result["afterId"] == 202
            assert mock_client.post.call_args_list[1][1]["json_data"] == {
                "attachmentId": 3500636,
                "parentId": 101,
                "testCaseId": 644594,
            }
            assert mock_client.post.call_args_list[1][1]["params"]["afterId"] == 202
