import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers.comment_controller import register_comment_tools  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class TestCommentController:
    def test_create_comment_calls_post(self):
        mcp = MagicMock()
        registered_tools = {}

        def capture_tool(**kwargs):
            def decorator(func):
                registered_tools[kwargs["name"]] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_comment_tools(mcp)

        create_comment = registered_tools["allure_createComment"]
        body = {"testCaseId": 12345, "text": "Test comment"}

        with patch("allure_testops_mcp.controllers.comment_controller.AllureTestOpsClient") as MockClient:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value={"id": 1, "text": "Test comment"})
            MockClient.return_value = mock_client

            result = run(create_comment(body=body))

            mock_client.post.assert_called_once_with("/api/comment", json_data=body)
            assert '"Test comment"' in result
