"""
CommentController - MCP инструменты для работы с комментариями.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, delete_response, json_response


def register_comment_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты CommentController в MCP сервере."""

    @mcp.tool(
        name="allure_getComments",
        description="Найти все комментарии для тест-кейса. Возвращает список комментариев в формате JSON.",
    )
    async def allure_findAll_43(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        page: int | None = Field(
            default=None,
            description="Номер страницы (начиная с 0)",
            examples=[0, 1, 2],
        ),
        size: int | None = Field(
            default=None,
            description="Размер страницы",
            examples=[10, 20, 50],
        ),
        sort: list[str] | None = Field(
            default=None,
            description="Критерии сортировки в формате: property(,asc|desc)",
            examples=[["createdDate,desc"], ["id,asc"]],
        ),
    ) -> str:
        """
        Найти все комментарии для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            page: Номер страницы (опционально)
            size: Размер страницы (опционально)
            sort: Критерии сортировки (опционально)

        Returns:
            JSON с списком комментариев

        Raises:
            AllureTestOpsError: Ошибка при получении комментариев
        """
        client = AllureTestOpsClient()
        params = build_params(testCaseId=testCaseId, page=page, size=size, sort=sort)
        return await json_response(
            client.get("/api/comment", params=params),
            "Ошибка при получении комментариев",
        )

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

    @mcp.tool(
        name="allure_deleteComment",
        description="Удалить комментарий по ID.",
    )
    async def allure_delete_39(
        id: int = Field(
            ...,
            description="ID комментария",
            examples=[123],
        ),
    ) -> str:
        """
        Удалить комментарий по ID.

        Args:
            id: ID комментария

        Returns:
            Строка подтверждения удаления

        Raises:
            AllureTestOpsError: Ошибка при удалении комментария
        """
        client = AllureTestOpsClient()
        return await delete_response(
            client.delete(f"/api/comment/{id}"),
            "Ошибка при удалении комментария",
        )

    @mcp.tool(
        name="allure_getComment",
        description="Найти комментарий по ID. Возвращает комментарий в формате JSON.",
    )
    async def allure_findOne_33(
        id: int = Field(
            ...,
            description="ID комментария",
            examples=[123],
        ),
    ) -> str:
        """
        Найти комментарий по ID.

        Args:
            id: ID комментария

        Returns:
            JSON с данными комментария

        Raises:
            AllureTestOpsError: Ошибка при получении комментария
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(f"/api/comment/{id}"),
            "Ошибка при получении комментария",
        )

    @mcp.tool(
        name="allure_updateComment",
        description="Динамически обновить комментарий. Возвращает обновленный комментарий в формате JSON.",
    )
    async def allure_patch_45(
        id: int = Field(
            ...,
            description="ID комментария",
            examples=[123],
        ),
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными для обновления",
            examples=[{"text": "Обновленный текст комментария"}],
        ),
    ) -> str:
        """
        Динамически обновить комментарий.

        Args:
            id: ID комментария
            body: Тело запроса с данными для обновления

        Returns:
            JSON с обновленным комментарием

        Raises:
            AllureTestOpsError: Ошибка при обновлении комментария
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.patch(f"/api/comment/{id}", json_data=body),
            "Ошибка при обновлении комментария",
        )
