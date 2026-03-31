"""
TestCaseCustomFieldController - MCP инструменты для работы с кастомными полями тест-кейсов.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, json_response


def register_test_case_custom_field_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseCustomFieldController в MCP сервере."""

    @mcp.tool(
        name="allure_getCustomFieldsForSelection",
        description="Найти кастомные поля с значениями для тест-кейсов. Возвращает результат в формате JSON.",
    )
    async def allure_getCustomFieldsWithValues_2(
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса по схеме TestCaseTreeSelectionDto",
            examples=[
                {
                    "projectId": 38,
                    "leafsInclude": [12345, 12346]
                }
            ],
        ),
    ) -> str:
        """
        Найти кастомные поля с значениями для тест-кейсов.

        Args:
            body: Тело запроса с ID тест-кейсов

        Returns:
            JSON с кастомными полями и значениями

        Raises:
            AllureTestOpsError: Ошибка при получении кастомных полей
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post("/api/testcase/cfv", json_data=body),
            "Ошибка при получении кастомных полей",
        )

    @mcp.tool(
        name="allure_getCustomFieldsForTestCase",
        description="""ПЕРВЫЙ ОБЯЗАТЕЛЬНЫЙ ШАГ перед обновлением кастомных полей тест-кейса.

Получает список кастомных полей проекта с допустимыми значениями для конкретного тест-кейса.
Ответ содержит:
- customField.id — числовой id поля (нужен для allure_updateCustomFields)
- customField.name — название поля для пользователя
- values[].id — числовой id конкретного значения
- values[].name — текст значения для пользователя

Используй результат этого вызова для формирования тела запроса allure_updateCustomFields.""",
    )
    async def allure_getCustomFieldsWithValues_3(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
        ),
    ) -> str:
        """
        Найти кастомные поля с значениями для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            projectId: ID проекта

        Returns:
            JSON с кастомными полями и значениями

        Raises:
            AllureTestOpsError: Ошибка при получении кастомных полей
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(
                f"/api/testcase/{testCaseId}/cfv",
                params=build_params(projectId=projectId),
            ),
            "Ошибка при получении кастомных полей",
        )

    @mcp.tool(
        name="allure_updateCustomFields",
        description="""Обновить значения кастомных полей тест-кейса.

ОБЯЗАТЕЛЬНЫЙ ПОРЯДОК ВЫЗОВОВ:
1. Сначала вызови allure_getCustomFieldsForTestCase(testCaseId, projectId) чтобы получить список всех кастомных полей и их допустимых значений с числовыми id.
2. Из ответа извлеки: customField.id (числовой id поля) и values[].id (числовые id допустимых значений).
3. Только после этого вызывай данный инструмент с корректными id.

Тело запроса — массив объектов CustomFieldWithValuesDto.""",
    )
    async def allure_updateCfvsOfTestCase(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        body: list[dict[str, Any]] = Field(
            ...,
            description="Массив объектов CustomFieldWithValuesDto",
            examples=[
                [{"customField": {"id": 123}, "values": [{"id": 456, "name": "значение"}]}]
            ],
        ),
    ) -> str:
        """
        Обновить кастомные поля тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            body: Массив объектов CustomFieldWithValuesDto

        Returns:
            JSON с результатом операции

        Raises:
            AllureTestOpsError: Ошибка при обновлении кастомных полей
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.patch(f"/api/testcase/{testCaseId}/cfv", json_data=body),
            "Ошибка при обновлении кастомных полей",
        )

    @mcp.tool(
        name="allure_suggestCustomFieldValues",
        description="""Поиск значений кастомного поля по строке запроса (query).

Используй для поиска конкретного значения кастомного поля по его названию.
Возвращает страницу с подходящими значениями кастомного поля.""",
    )
    async def allure_suggestCustomFieldValues(
        query: str = Field(
            ...,
            description="Строка для поиска значения кастомного поля (название поля)",
            examples=["Main Test Model"],
        ),
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
        ),
        page: int = Field(
            0,
            description="Номер страницы (начиная с 0)",
            examples=[0],
        ),
        size: int = Field(
            10,
            description="Количество результатов на странице",
            examples=[10],
        ),
    ) -> str:
        """
        Поиск значений кастомного поля по строке запроса.

        Args:
            query: Строка для поиска (название кастомного поля)
            projectId: ID проекта
            page: Номер страницы (начиная с 0)
            size: Количество результатов на странице

        Returns:
            JSON со списком подходящих значений кастомного поля

        Raises:
            AllureTestOpsError: Ошибка при поиске значений кастомного поля
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(
                "/api/cfv/suggest",
                params=build_params(
                    query=query,
                    projectId=projectId,
                    page=page,
                    size=size,
                ),
            ),
            "Ошибка при поиске значений кастомного поля",
        )

    @mcp.tool(
        name="allure_searchCustomFields",
        description="""Поиск кастомных полей проекта по строке запроса (query).

Используй для поиска самих кастомных полей (не значений) в проекте по названию.
Возвращает страницу с подходящими кастомными полями проекта.""",
    )
    async def allure_searchCustomFields(
        projectId: int = Field(
            ...,
            description="ID проекта",
            examples=[38],
        ),
        query: str = Field(
            "",
            description="Строка для поиска кастомного поля по названию",
            examples=["Folder 2"],
        ),
        page: int = Field(
            0,
            description="Номер страницы (начиная с 0)",
            examples=[0],
        ),
        size: int = Field(
            10,
            description="Количество результатов на странице",
            examples=[10],
        ),
        sort: str = Field(
            "id,ASC",
            description="Параметр сортировки в формате 'поле,направление'",
            examples=["id,ASC"],
        ),
    ) -> str:
        """
        Поиск кастомных полей проекта по строке запроса.

        Args:
            projectId: ID проекта
            query: Строка для поиска кастомного поля по названию
            page: Номер страницы (начиная с 0)
            size: Количество результатов на странице
            sort: Параметр сортировки в формате 'поле,направление'

        Returns:
            JSON со списком найденных кастомных полей проекта

        Raises:
            AllureTestOpsError: Ошибка при поиске кастомных полей
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(
                f"/api/project/{projectId}/cf",
                params=build_params(query=query, page=page, size=size, sort=sort),
            ),
            "Ошибка при поиске кастомных полей",
        )
