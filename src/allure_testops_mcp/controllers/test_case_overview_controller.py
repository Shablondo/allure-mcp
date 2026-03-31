"""
TestCaseOverviewController - MCP инструменты для работы с обзором тест-кейсов.
"""

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import json_response


def register_test_case_overview_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseOverviewController в MCP сервере."""

    @mcp.tool(
        name="allure_getOverview",
        description="Получить обзор тест-кейса. Возвращает обзор в формате JSON.",
    )
    async def allure_getOverview(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
    ) -> str:
        """
        Получить обзор тест-кейса.

        Args:
            testCaseId: ID тест-кейса

        Returns:
            JSON с обзором тест-кейса

        Raises:
            AllureTestOpsError: Ошибка при получении обзора тест-кейса
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.get(f"/api/testcase/{testCaseId}/overview"),
            "Ошибка при получении обзора тест-кейса",
        )
