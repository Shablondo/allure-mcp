"""
TestCaseExampleController - MCP инструменты для работы с примерами (параметризованными данными) тест-кейсов.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, json_response


def register_test_case_example_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseExampleController в MCP сервере."""

    @mcp.tool(
        name="allure_getExamples",
        description="Получить примеры (параметризованные данные) тест-кейса. Возвращает страницу PageTestCaseExampleDto в формате JSON.",
    )
    async def allure_getExamples(
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
        Получить примеры тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            page: Номер страницы (опционально)
            size: Размер страницы (опционально)
            sort: Критерии сортировки (опционально)

        Returns:
            JSON с PageTestCaseExampleDto

        Raises:
            AllureTestOpsError: Ошибка при получении примеров
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(
                f"/api/testcase/{testCaseId}/example",
                params=build_params(page=page, size=size, sort=sort),
            ),
            "Ошибка при получении примеров",
        )

    @mcp.tool(
        name="allure_setExamples",
        description="Установить примеры (параметризованные данные) тест-кейса. Принимает массив строк параметров. Возвращает массив TestCaseExampleDto в формате JSON.",
    )
    async def allure_setExamples(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        body: list[list[dict[str, Any]]] = Field(
            ...,
            description="Массив строк примеров. Каждая строка — массив объектов ParameterValueDto с полями name и value.",
            examples=[
                [
                    [{"name": "browser", "value": "Chrome"}, {"name": "env", "value": "prod"}],
                    [{"name": "browser", "value": "Firefox"}, {"name": "env", "value": "staging"}]
                ]
            ],
        ),
    ) -> str:
        """
        Установить примеры тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            body: Массив строк параметров (массив массивов ParameterValueDto)

        Returns:
            JSON с массивом TestCaseExampleDto

        Raises:
            AllureTestOpsError: Ошибка при установке примеров
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post(f"/api/testcase/{testCaseId}/example", json_data=body),
            "Ошибка при установке примеров",
        )

    @mcp.tool(
        name="allure_renameParameter",
        description="Переименовать параметр в примерах тест-кейса. Возвращает массив TestCaseExampleDto в формате JSON.",
    )
    async def allure_renameParameter(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        oldName: str = Field(
            ...,
            description="Текущее имя параметра",
            examples=["browser"],
        ),
        newName: str = Field(
            ...,
            description="Новое имя параметра",
            examples=["Browser"],
        ),
    ) -> str:
        """
        Переименовать параметр в примерах тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            oldName: Текущее имя параметра
            newName: Новое имя параметра

        Returns:
            JSON с массивом TestCaseExampleDto

        Raises:
            AllureTestOpsError: Ошибка при переименовании параметра
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post(
                f"/api/testcase/{testCaseId}/example/rename-parameter",
                json_data={},
                params=build_params(oldName=oldName, newName=newName),
            ),
            "Ошибка при переименовании параметра",
        )

    @mcp.tool(
        name="allure_generateNwise",
        description="Генерировать N-wise комбинации параметров. Принимает список параметров с допустимыми значениями и возвращает все сгенерированные комбинации в виде массива TestCaseExampleDto.",
    )
    async def allure_generateNwise(
        body: list[dict[str, Any]] = Field(
            ...,
            description="Массив объектов TestCaseParameterValues — каждый содержит name (имя параметра) и values (список допустимых значений).",
            examples=[
                [
                    {"name": "browser", "values": ["Chrome", "Firefox", "Safari"]},
                    {"name": "env", "values": ["prod", "staging"]}
                ]
            ],
        ),
        n: int | None = Field(
            default=None,
            description="Степень N-wise покрытия (по умолчанию 1)",
            examples=[1, 2, 3],
        ),
    ) -> str:
        """
        Генерировать N-wise комбинации параметров.

        Args:
            body: Массив TestCaseParameterValues с параметрами и их допустимыми значениями
            n: Степень N-wise покрытия (опционально, по умолчанию 1)

        Returns:
            JSON с массивом TestCaseExampleDto

        Raises:
            AllureTestOpsError: Ошибка при генерации комбинаций
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.post(
                "/api/testcase/example/nwise",
                json_data=body,
                params=build_params(n=n),
            ),
            "Ошибка при генерации N-wise комбинаций",
        )
