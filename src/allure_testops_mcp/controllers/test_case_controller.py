"""
TestCaseController - MCP инструменты для работы с тест-кейсами.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, delete_response, json_response


def register_test_case_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseController в MCP сервере."""

    @mcp.tool(
        name="allure_getTestCases",
        description="Найти все тест-кейсы проекта. Возвращает список тест-кейсов в формате JSON.",
    )
    async def allure_findAll_12(
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
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
        Найти все тест-кейсы проекта.

        Args:
            projectId: ID проекта
            page: Номер страницы (опционально)
            size: Размер страницы (опционально)
            sort: Критерии сортировки (опционально)

        Returns:
            JSON с списком тест-кейсов

        Raises:
            AllureTestOpsError: Ошибка при получении тест-кейсов
        """
        client = AllureTestOpsClient()
        params = build_params(projectId=projectId, page=page, size=size, sort=sort)
        return await json_response(
            client.get("/api/testcase", params=params),
            "Ошибка при получении тест-кейсов",
        )

    @mcp.tool(
        name="allure_createTestCase",
        description="""Создать новый тест-кейс. Возвращает созданный тест-кейс в формате JSON.

Обязательные зависимости:
- projectId: ID проекта
- testLayerId (опционально): получи через GET /api/testlayer/suggest""",
    )
    async def allure_create_14(
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными тест-кейса",
            examples=[
                {
                    "name": "Название тест-кейса",
                    "description": "Описание тест-кейса",
                    "projectId": 38,
                }
            ],
        ),
    ) -> str:
        """
        Создать новый тест-кейс.

        Args:
            body: Тело запроса с данными тест-кейса

        Returns:
            JSON с созданным тест-кейсом

        Raises:
            AllureTestOpsError: Ошибка при создании тест-кейса
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post("/api/testcase", json_data=body),
            "Ошибка при создании тест-кейса",
        )

    @mcp.tool(
        name="allure_suggestTestCases",
        description="Поиск тест-кейсов по запросу. Возвращает список тест-кейсов в формате JSON.",
    )
    async def allure_suggest_7(
        query: str | None = Field(
            default=None,
            description="Поисковый запрос",
            examples=["test", "login"],
        ),
        projectId: int | None = Field(
            default=None,
            description="ID проекта",
            examples=[38],
        ),
        id: list[str] | None = Field(
            default=None,
            description="Список ID для исключения",
            examples=[["1", "2", "3"]],
        ),
        ignoreId: list[str] | None = Field(
            default=None,
            description="Список ID для игнорирования",
            examples=[["4", "5", "6"]],
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
        Поиск тест-кейсов по запросу.

        Args:
            query: Поисковый запрос (опционально)
            projectId: ID проекта (опционально)
            id: Список ID для исключения (опционально)
            ignoreId: Список ID для игнорирования (опционально)
            page: Номер страницы (опционально)
            size: Размер страницы (опционально)
            sort: Критерии сортировки (опционально)

        Returns:
            JSON с списком тест-кейсов

        Raises:
            AllureTestOpsError: Ошибка при поиске тест-кейсов
        """
        client = AllureTestOpsClient()
        params = build_params(
            query=query,
            projectId=projectId,
            id=id,
            ignoreId=ignoreId,
            page=page,
            size=size,
            sort=sort,
        )
        return await json_response(
            client.get("/api/testcase/suggest", params=params),
            "Ошибка при поиске тест-кейсов",
        )

    @mcp.tool(
        name="allure_deleteTestCase",
        description="Удалить тест-кейс по ID.",
    )
    async def allure_delete_13(
        id: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        force: bool | None = Field(
            default=None,
            description="Принудительное удаление",
            examples=[True, False],
        ),
    ) -> str:
        """
        Удалить тест-кейс по ID.

        Args:
            id: ID тест-кейса
            force: Принудительное удаление (опционально)

        Returns:
            Строка подтверждения удаления

        Raises:
            AllureTestOpsError: Ошибка при удалении тест-кейса
        """
        client = AllureTestOpsClient()
        return await delete_response(
            client.delete(f"/api/testcase/{id}", params=build_params(force=force)),
            "Ошибка при удалении тест-кейса",
        )

    @mcp.tool(
        name="allure_getTestCase",
        description="Найти тест-кейс по ID. Возвращает тест-кейс в формате JSON.",
    )
    async def allure_findOne_11(
        id: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
    ) -> str:
        """
        Найти тест-кейс по ID.

        Args:
            id: ID тест-кейса

        Returns:
            JSON с данными тест-кейса

        Raises:
            AllureTestOpsError: Ошибка при получении тест-кейса
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(f"/api/testcase/{id}"),
            "Ошибка при получении тест-кейса",
        )

    @mcp.tool(
        name="allure_updateTestCase",
        description="Обновить тест-кейс. Возвращает обновленный тест-кейс в формате JSON.",
    )
    async def allure_patch_13(
        id: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными для обновления",
            examples=[{"name": "Обновленное название"}],
        ),
    ) -> str:
        """
        Обновить тест-кейс.

        Args:
            id: ID тест-кейса
            body: Тело запроса с данными для обновления

        Returns:
            JSON с обновленным тест-кейсом

        Raises:
            AllureTestOpsError: Ошибка при обновлении тест-кейса
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.patch(f"/api/testcase/{id}", json_data=body),
            "Ошибка при обновлении тест-кейса",
        )
