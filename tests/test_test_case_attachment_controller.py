import asyncio
import base64
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
