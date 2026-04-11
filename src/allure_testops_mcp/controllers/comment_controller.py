"""
CommentController - MCP инструменты для работы с комментариями.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import json_response


def register_comment_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты CommentController в MCP сервере."""

    @mcp.tool(
        name="allure_createComment",
        description="Создать новый комментарий. Возвращает созданный комментарий в формате JSON.",
    )
    async def allure_create_49(
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными комментария",
            examples=[
                {
                    "testCaseId": 12345,
                    "text": "Текст комментария",
                }
            ],
        ),
    ) -> str:
        """
        Создать новый комментарий.

        Args:
            body: Тело запроса с данными комментария

        Returns:
            JSON с созданным комментарием

        Raises:
            AllureTestOpsError: Ошибка при создании комментария
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post("/api/comment", json_data=body),
            "Ошибка при создании комментария",
        )
