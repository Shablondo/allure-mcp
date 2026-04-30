"""
TestCaseAttachmentController - MCP инструменты для работы с вложениями тест-кейсов.
"""

import base64
import mimetypes
from typing import Any

from fastmcp import FastMCP
from pydantic import Field
from pydantic.fields import FieldInfo

from ..client import AllureTestOpsClient
from ._utils import build_params, delete_response, dump_json, json_response, raw_response


def _decode_multipart_files(
    files: list[dict[str, str]],
    default_content_type: str = "application/octet-stream",
    infer_content_type_from_name: bool = True,
) -> list[tuple]:
    httpx_files: list[tuple] = []
    for f in files:
        raw_text = f.get("textContent") or f.get("text_content") or f.get("rawContent") or f.get("raw_content")
        if raw_text is not None:
            file_bytes = raw_text.encode("utf-8")
        elif "content" in f:
            file_bytes = base64.b64decode(f["content"])
        else:
            raise ValueError("Each file must contain either base64 content or raw textContent")
        explicit_content_type = f.get("contentType") or f.get("content_type")
        mime_type = None
        if infer_content_type_from_name:
            mime_type, _ = mimetypes.guess_type(f["name"])
        content_type = explicit_content_type or mime_type or default_content_type
        httpx_files.append(("file", (f["name"], file_bytes, content_type)))
    return httpx_files


def _extract_first_attachment_id(payload: Any) -> int:
    if isinstance(payload, list) and payload:
        return int(payload[0]["id"])
    if isinstance(payload, dict):
        if "id" in payload:
            return int(payload["id"])
        content = payload.get("content")
        if isinstance(content, list) and content:
            return int(content[0]["id"])
    raise ValueError("Allure attachment upload response does not contain attachment id")


def _last_root_step_id(scenario: dict[str, Any]) -> int | None:
    root = scenario.get("root") if isinstance(scenario.get("root"), dict) else {}
    children = root.get("children") or []
    if not children:
        return None
    return int(children[-1])


def _last_child_step_id(scenario: dict[str, Any], parent_step_id: int) -> int | None:
    steps = scenario.get("scenarioSteps") if isinstance(scenario.get("scenarioSteps"), dict) else {}
    parent_step = steps.get(str(parent_step_id)) or steps.get(parent_step_id)
    if not isinstance(parent_step, dict):
        return None
    children = parent_step.get("children") or []
    if not children:
        return None
    return int(children[-1])


def _optional_int(value: int | FieldInfo | None) -> int | None:
    if isinstance(value, FieldInfo):
        return None
    return value


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
            description="Список файлов для загрузки. Каждый файл: name и либо content (base64), либо textContent (raw UTF-8 текст).",
            examples=[
                [
                    {"name": "screenshot.png", "content": "iVBORw0KGgoAAAANSUhEUg..."},
                    {"name": "response.json", "textContent": "{\"name\":\"Тестовый товар\"}", "contentType": "application/json"},
                ]
            ],
        ),
    ) -> str:
        """
        Загрузить новые вложения для тест-кейса.

        Args:
            testCaseId: ID тест-кейса
            files: Список файлов (name + content base64 или textContent raw UTF-8)

        Returns:
            JSON с созданными вложениями

        Raises:
            AllureTestOpsError: Ошибка при загрузке вложений
        """
        client = AllureTestOpsClient()

        httpx_files = _decode_multipart_files(files)

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

    @mcp.tool(
        name="allure_uploadAttachmentAndLinkStep",
        description="Загрузить вложение в тест-кейс и добавить attachment-step в сценарий.",
    )
    async def allure_upload_attachment_and_link_step(
        testCaseId: int = Field(
            ...,
            description="ID тест-кейса",
            examples=[12345],
        ),
        files: list[dict[str, str]] = Field(
            ...,
            description=(
                "Файлы: name, contentType и либо textContent (raw UTF-8 для curl/json/text), "
                "либо content (base64 для бинарных файлов). Для curl/json вложений используй textContent и application/json."
            ),
            examples=[
                [
                    {
                        "name": "curl-command.json",
                        "textContent": "curl --location 'https://service.example/api'",
                        "contentType": "application/json",
                    }
                ]
            ],
        ),
        parentStepId: int | None = Field(
            default=None,
            description="ID родительского шага, если вложение нужно добавить внутрь шага",
        ),
        afterId: int | None = Field(
            default=None,
            description="ID шага, после которого вставить attachment-step",
        ),
    ) -> str:
        client = AllureTestOpsClient()
        upload_payload = await client.post(
            "/api/testcase/attachment",
            files=_decode_multipart_files(
                files,
                default_content_type="application/json",
                infer_content_type_from_name=False,
            ),
            params=build_params(testCaseId=testCaseId),
        )
        attachment_id = _extract_first_attachment_id(upload_payload)

        body: dict[str, Any] = {"attachmentId": attachment_id, "testCaseId": testCaseId}
        resolved_parent_step_id = _optional_int(parentStepId)
        if resolved_parent_step_id is not None:
            body["parentId"] = resolved_parent_step_id

        resolved_after_id = _optional_int(afterId)
        if resolved_after_id is None:
            scenario = await client.get(f"/api/testcase/{testCaseId}/step", use_cache=False)
            if resolved_parent_step_id is not None:
                resolved_after_id = _last_child_step_id(scenario, resolved_parent_step_id)
            else:
                resolved_after_id = _last_root_step_id(scenario)

        step_payload = await client.post(
            "/api/testcase/step",
            json_data=body,
            params=build_params(afterId=resolved_after_id),
        )
        return dump_json(
            {
                "attachment": upload_payload,
                "attachmentId": attachment_id,
                "step": step_payload,
                "afterId": resolved_after_id,
                "parentStepId": resolved_parent_step_id,
            }
        )
