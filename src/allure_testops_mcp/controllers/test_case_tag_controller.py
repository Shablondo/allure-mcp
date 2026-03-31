"""
TestCaseTagController - MCP инструменты для работы с тегами тест-кейсов.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import json_response


def register_test_case_tag_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseTagController в MCP сервере."""

    @mcp.tool(
        name="allure_getTags",
        description="Найти теги для тест-кейса. Возвращает список тегов в формате JSON.",
    )
    async def allure_getTags(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
    ) -> str:
        """
        Найти теги для тест-кейса.

        Args:
            testCaseId: ID тест-кейса

        Returns:
            JSON с списком тегов

        Raises:
            AllureTestOpsError: Ошибка при получении тегов
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(f"/api/testcase/{testCaseId}/tag"),
            "Ошибка при получении тегов",
        )

    @mcp.tool(
        name="allure_setTags",
        description="""Установить теги для тест-кейса. Заменяет все существующие теги.

ВАЖНО: тело запроса — МАССИВ объектов {id: number, name: string}.
Для получения существующих тегов с их id:
- Вызови allure_getTags(testCaseId) чтобы увидеть текущие теги тест-кейса
- Или используй GET /api/tag/suggest для поиска тегов по имени

Пример тела: [{"id": 1, "name": "smoke"}, {"id": 2, "name": "regression"}]""",
    )
    async def allure_setTags(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        body: list[dict[str, Any]] = Field(
            ...,
            description="Массив тегов — каждый тег содержит id и name",
            examples=[
                [{"id": 1, "name": "smoke"}, {"id": 2, "name": "regression"}]
            ],
        ),
    ) -> str:
        """
        Установить теги для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            body: Массив тегов

        Returns:
            JSON с результатом операции

        Raises:
            AllureTestOpsError: Ошибка при установке тегов
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post(f"/api/testcase/{testCaseId}/tag", json_data=body),
            "Ошибка при установке тегов",
        )
