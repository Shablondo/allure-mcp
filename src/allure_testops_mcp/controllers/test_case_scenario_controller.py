"""
TestCaseScenarioController - MCP инструменты для работы со сценариями тест-кейсов.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, delete_response, json_response


def register_test_case_scenario_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseScenarioController в MCP сервере."""

    @mcp.tool(
        name="allure_createScenarioStep",
        description="""Создать шаг сценария. Возвращает созданный шаг в формате JSON.

Перед созданием шагов вызови allure_getScenario(id) для получения
текущей структуры сценария и актуальных числовых id шагов (scenarioSteps, ключи — это id шагов).""",
    )
    async def allure_create_16(
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными шага (ScenarioStepCreateDto)",
            examples=[
                {
                    "testCaseId": 12345,
                    "body": "Текст шага"
                }
            ],
        ),
        beforeId: int | None = Field(
            default=None,
            description="ID шага перед которым вставить",
            examples=[100],
        ),
        afterId: int | None = Field(
            default=None,
            description="ID шага после которого вставить",
            examples=[101],
        ),
        withExpectedResult: bool | None = Field(
            default=None,
            description="Включить ожидаемый результат",
            examples=[True, False],
        ),
    ) -> str:
        """
        Создать шаг сценария.

        Args:
            beforeId: ID шага перед которым вставить (опционально)
            afterId: ID шага после которого вставить (опционально)
            withExpectedResult: Включить ожидаемый результат (опционально)
            body: Тело запроса с данными шага

        Returns:
            JSON с созданным шагом

        Raises:
            AllureTestOpsError: Ошибка при создании шага
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post(
                "/api/testcase/step",
                json_data=body,
                params=build_params(
                    beforeId=beforeId,
                    afterId=afterId,
                    withExpectedResult=withExpectedResult,
                ),
            ),
            "Ошибка при создании шага",
        )

    @mcp.tool(
        name="allure_deleteScenarioStep",
        description="""Удалить шаг сценария по ID.

Перед удалением шагов вызови allure_getScenario(id) для получения
текущей структуры сценария и актуальных числовых id шагов (scenarioSteps, ключи — это id шагов).""",
    )
    async def allure_deleteById_1(
        id: int = Field(
            ...,
            description="ID шага",
            examples=[100],
        ),
    ) -> str:
        """
        Удалить шаг сценария по ID.

        Args:
            id: ID шага

        Returns:
            Строка подтверждения удаления

        Raises:
            AllureTestOpsError: Ошибка при удалении шага
        """
        client = AllureTestOpsClient()
        return await delete_response(
            client.delete(f"/api/testcase/step/{id}"),
            "Ошибка при удалении шага",
        )

    @mcp.tool(
        name="allure_updateScenarioStep",
        description="""Обновить шаг сценария. Возвращает обновленный шаг в формате JSON.

Перед изменением шагов вызови allure_getScenario(id) для получения
текущей структуры сценария и актуальных числовых id шагов (scenarioSteps, ключи — это id шагов).""",
    )
    async def allure_patchById(
        id: int = Field(
            ...,
            description="ID шага",
            examples=[100],
        ),
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными для обновления",
            examples=[{"name": "Обновленное название"}],
        ),
        withExpectedResult: bool | None = Field(
            default=None,
            description="Включить ожидаемый результат",
            examples=[True, False],
        ),
    ) -> str:
        """
        Обновить шаг сценария.

        Args:
            id: ID шага
            withExpectedResult: Включить ожидаемый результат (опционально)
            body: Тело запроса с данными для обновления

        Returns:
            JSON с обновленным шагом

        Raises:
            AllureTestOpsError: Ошибка при обновлении шага
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.patch(
                f"/api/testcase/step/{id}",
                json_data=body,
                params=build_params(withExpectedResult=withExpectedResult),
            ),
            "Ошибка при обновлении шага",
        )

    @mcp.tool(
        name="allure_getScenario",
        description="Получить сценарий для тест-кейса. Возвращает сценарий в формате JSON. Используй этот инструмент перед созданием/изменением/удалением шагов для получения актуальных числовых id шагов (ключи в scenarioSteps).",
    )
    async def allure_getNormalizedScenario(
        id: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
    ) -> str:
        """
        Получить сценарий для тест-кейса.

        Args:
            id: ID тест-кейса

        Returns:
            JSON с данными сценария

        Raises:
            AllureTestOpsError: Ошибка при получении сценария
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(f"/api/testcase/{id}/step", use_cache=False),
            "Ошибка при получении сценария",
        )
