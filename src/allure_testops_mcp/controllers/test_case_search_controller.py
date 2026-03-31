"""
TestCaseSearchController - MCP инструменты для поиска тест-кейсов.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, json_response


def register_test_case_search_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseSearchController в MCP сервере."""

    @mcp.tool(
        name="allure_searchTestCases",
        description="Найти все тест-кейсы по заданному RQL. Возвращает список тест-кейсов в формате JSON.",
    )
    async def allure_search_1(
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
        ),
        rql: str = Field(
            ...,
            description="""RQL-запрос (Rockable Query Language) для фильтрации тест-кейсов.
Примеры RQL:
- name like '%login%' — поиск по части имени
- status = 'ACTIVE' — фильтр по статусу
- tag = 'smoke' — фильтр по тегу
- automated = true — только автоматизированные

Для предварительной валидации запроса используй allure_validateSearchQuery.""",
            examples=["name like '%login%'", "status = 'ACTIVE'", "tag = 'smoke'"],
        ),
        deleted: bool | None = Field(
            default=None,
            description="Искать в удаленных тест-кейсах",
            examples=[True, False],
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
        Найти все тест-кейсы по заданному RQL.

        Args:
            projectId: ID проекта
            rql: RQL запрос для поиска
            deleted: Искать в удаленных тест-кейсах (опционально)
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
            projectId=projectId,
            rql=rql,
            deleted=deleted,
            page=page,
            size=size,
            sort=sort,
        )
        return await json_response(
            client.get("/api/testcase/__search", params=params),
            "Ошибка при поиске тест-кейсов",
        )

    @mcp.tool(
        name="allure_validateSearchQuery",
        description="Валидировать запрос для поиска тест-кейсов. Возвращает результат в формате JSON.",
    )
    async def allure_validateQuery_1(
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
        ),
        rql: str = Field(
            ...,
            description="RQL запрос для валидации",
            examples=["name like '%test%'"],
        ),
        deleted: bool | None = Field(
            default=None,
            description="Валидировать для удаленных тест-кейсов",
            examples=[True, False],
        ),
    ) -> str:
        """
        Валидировать запрос для поиска тест-кейсов.

        Args:
            projectId: ID проекта
            rql: RQL запрос для валидации
            deleted: Валидировать для удаленных тест-кейсов (опционально)

        Returns:
            JSON с результатом валидации

        Raises:
            AllureTestOpsError: Ошибка при валидации запроса
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(
                "/api/testcase/query/validate",
                params=build_params(projectId=projectId, rql=rql, deleted=deleted),
            ),
            "Ошибка при валидации запроса",
        )
