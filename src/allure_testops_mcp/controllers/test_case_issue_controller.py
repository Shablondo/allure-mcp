"""
TestCaseIssueController - MCP инструменты для работы с issues (связывание тест-кейсов с задачами Kaiten).
"""

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import json_response


def register_test_case_issue_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseIssueController в MCP сервере."""

    @mcp.tool(
        name="allure_linkTestCaseToKaitenIssue",
        description="""Привязать задачу Kaiten к тест-кейсу. Возвращает результат привязки в формате JSON.

Используется для связи тест-кейса с задачей в системе Kaiten через интеграцию Allure TestOps.
integrationId всегда равен 31 (интеграция с Kaiten).""",
    )
    async def allure_linkTestCaseToKaitenIssue(
        testcaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[727870],
        ),
        kaitenIssueNumber: str = Field(
            ...,
            description="Номер задачи в Kaiten",
            examples=["3138098"],
        ),
    ) -> str:
        """
        Привязать задачу Kaiten к тест-кейсу.

        Args:
            testcaseId: ID тест-кейса
            kaitenIssueNumber: Номер задачи в Kaiten

        Returns:
            JSON с результатом привязки

        Raises:
            AllureTestOpsError: Ошибка при привязке задачи
        """
        client = AllureTestOpsClient()
        body = [{"integrationId": 31, "name": kaitenIssueNumber}]
        return await json_response(
            client.post(f"/api/testcase/{testcaseId}/issue", json_data=body),
            "Ошибка при привязке задачи Kaiten",
        )
