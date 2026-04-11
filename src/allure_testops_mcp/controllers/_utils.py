"""
Общие утилиты для MCP-контроллеров.
"""

import json
from typing import Any, Awaitable

from ..client import AllureTestOpsError
from ..config import config


def build_params(**kwargs: Any) -> dict[str, Any]:
    """Собирает query-параметры, пропуская значения None."""
    return {key: value for key, value in kwargs.items() if value is not None}


def resolve_project_id(project_id: int | None) -> int | None:
    """Возвращает явный projectId или fallback из конфига, если он задан."""
    return project_id if project_id is not None else config.project_id


def apply_project_id_fallback(body: dict[str, Any]) -> dict[str, Any]:
    """Подставляет projectId из конфига в тело запроса, не переписывая явное значение."""
    if body.get("projectId") is not None:
        return body

    project_id = resolve_project_id(None)
    if project_id is None:
        return body

    return {**body, "projectId": project_id}


def dump_json(data: Any) -> str:
    """Сериализует ответ API в читаемый JSON."""
    return json.dumps(data, ensure_ascii=False, indent=2)


async def json_response(request: Awaitable[Any], error_message: str) -> str:
    """Выполняет запрос и возвращает JSON-строку с единым форматом ошибок."""
    try:
        return dump_json(await request)
    except AllureTestOpsError as error:
        raise AllureTestOpsError(f"{error_message}: {error.message}") from error


async def raw_response(request: Awaitable[str], error_message: str) -> str:
    """Выполняет запрос, который возвращает текстовый ответ."""
    try:
        return await request
    except AllureTestOpsError as error:
        raise AllureTestOpsError(f"{error_message}: {error.message}") from error


async def delete_response(
    request: Awaitable[Any],
    error_message: str,
    success_message: str = "Successfully deleted",
) -> str:
    """Выполняет delete-запрос и возвращает стандартное сообщение об успехе."""
    try:
        await request
        return success_message
    except AllureTestOpsError as error:
        raise AllureTestOpsError(f"{error_message}: {error.message}") from error
