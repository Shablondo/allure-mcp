"""
TestCaseAttachmentController - MCP инструменты для работы с вложениями тест-кейсов.
"""

import base64
import mimetypes
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ..client import AllureTestOpsClient
from ._utils import build_params, delete_response, json_response, raw_response


def register_test_case_attachment_tools(mcp: FastMCP) -> None:
    """Регистрирует все инструменты TestCaseAttachmentController в MCP сервере."""

    @mcp.tool(
        name="allure_getAttachments",
        description="Найти все вложения для тест-кейса. Возвращает список вложений в формате JSON.",
    )
    async def allure_findAll_14(
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
        Найти все вложения для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            page: Номер страницы (опционально)
            size: Размер страницы (опционально)
            sort: Критерии сортировки (опционально)

        Returns:
            JSON с списком вложений

        Raises:
            AllureTestOpsError: Ошибка при получении вложений
        """
        client = AllureTestOpsClient()
        params = build_params(testCaseId=testCaseId, page=page, size=size, sort=sort)
        return await json_response(
            client.get("/api/testcase/attachment", params=params),
            "Ошибка при получении вложений",
        )

    @mcp.tool(
        name="allure_uploadAttachment",
        description="Загрузить новые вложения для тест-кейса через multipart/form-data. Возвращает созданные вложения в формате JSON.",
    )
    async def allure_create_17(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        files: list[dict[str, str]] = Field(
            ...,
            description="Список файлов для загрузки. Каждый файл: name (имя с расширением) и content (base64-закодированное содержимое)",
            examples=[
                [
                    {"name": "screenshot.png", "content": "iVBORw0KGgoAAAANSUhEUg..."},
                    {"name": "log.txt", "content": "TG9nIGNvbnRlbnQ="},
                ]
            ],
        ),
    ) -> str:
        """
        Загрузить новые вложения для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            files: Список файлов (name и base64-контент)

        Returns:
            JSON с созданными вложениями

        Raises:
            AllureTestOpsError: Ошибка при загрузке вложений
        """
        client = AllureTestOpsClient()

        httpx_files: list[tuple] = []
        for f in files:
            file_bytes = base64.b64decode(f["content"])
            mime_type, _ = mimetypes.guess_type(f["name"])
            httpx_files.append(("file", (f["name"], file_bytes, mime_type or "application/octet-stream")))

        return await json_response(
            client.post(
                "/api/testcase/attachment",
                files=httpx_files,
                params=build_params(testCaseId=testCaseId),
            ),
            "Ошибка при загрузке вложений",
        )

    @mcp.tool(
        name="allure_deleteAttachment",
        description="Удалить вложение тест-кейса.",
    )
    async def allure_delete_15(
        id: int = Field(
            ...,
            description="ID вложения",
            examples=[123],
        ),
    ) -> str:
        """
        Удалить вложение тест-кейса.

        Args:
            id: ID вложения

        Returns:
            Строка подтверждения удаления

        Raises:
            AllureTestOpsError: Ошибка при удалении вложения
        """
        client = AllureTestOpsClient()
        return await delete_response(
            client.delete(f"/api/testcase/attachment/{id}"),
            "Ошибка при удалении вложения",
        )

    @mcp.tool(
        name="allure_updateAttachment",
        description="Обновить вложение тест-кейса. Возвращает обновленное вложение в формате JSON.",
    )
    async def allure_patch_15(
        id: int = Field(
            ...,
            description="ID вложения",
            examples=[123],
        ),
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с данными для обновления",
            examples=[{"name": "Обновленное название"}],
        ),
    ) -> str:
        """
        Обновить вложение тест-кейса.

        Args:
            id: ID вложения
            body: Тело запроса с данными для обновления

        Returns:
            JSON с обновленным вложением

        Raises:
            AllureTestOpsError: Ошибка при обновлении вложения
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.patch(f"/api/testcase/attachment/{id}", json_data=body),
            "Ошибка при обновлении вложения",
        )

    @mcp.tool(
        name="allure_getAttachmentContent",
        description="Получить содержимое вложения по ID. Возвращает содержимое в формате JSON.",
    )
    async def allure_readContent_2(
        id: int = Field(
            ...,
            description="ID вложения",
            examples=[123],
        ),
    ) -> str:
        """
        Получить содержимое вложения по ID.

        Args:
            id: ID вложения

        Returns:
            JSON с содержимым вложения или сырой текст

        Raises:
            AllureTestOpsError: Ошибка при получении содержимого вложения
        """
        client = AllureTestOpsClient()
        return await raw_response(
            client.get_raw(f"/api/testcase/attachment/{id}/content"),
            "Ошибка при получении содержимого вложения",
        )

    @mcp.tool(
        name="allure_updateAttachmentContent",
        description="Обновить содержимое вложения тест-кейса. Возвращает результат в формате JSON.",
    )
    async def allure_updateContent_2(
        id: int = Field(
            ...,
            description="ID вложения",
            examples=[123],
        ),
        body: dict[str, Any] = Field(
            ...,
            description="Тело запроса с новым содержимым",
            examples=[{"content": "base64_encoded_content"}],
        ),
    ) -> str:
        """
        Обновить содержимое вложения тест-кейса.

        Args:
            id: ID вложения
            body: Тело запроса с новым содержимым

        Returns:
            JSON с результатом операции

        Raises:
            AllureTestOpsError: Ошибка при обновлении содержимого вложения
        """
        client = AllureTestOpsClient()
        return await json_response(
            client.put(f"/api/testcase/attachment/{id}/content", json_data=body),
            "Ошибка при обновлении содержимого вложения",
        )
