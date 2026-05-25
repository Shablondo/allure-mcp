"""
MCP сервер для Allure TestOps.

Предоставляет инструменты для работы с тест-кейсами и связанными сущностями.
"""

import sys

from fastmcp import FastMCP

from .config import config
from .controllers import register_all_controllers

# Создаем MCP сервер
mcp = FastMCP("allure-testops")

# Регистрируем все контроллеры
register_all_controllers(mcp)


def main() -> None:
    """
    Запускает MCP сервер.

    Проверяет конфигурацию перед запуском и выводит ошибки если они есть.
    """
    sys.stdout.reconfigure(encoding="utf-8")

    # Проверяем конфигурацию
    errors = config.validate()
    if errors:
        print("Ошибки конфигурации:")
        for error in errors:
            print(f"  - {error}")
        print("\nПожалуйста, исправьте ошибки в переменных окружения или в опциональном .env файле.")
        return

    print("✓ Конфигурация успешно загружена")
    print(f"✓ Circuit Breaker: failures={config.circuit_breaker_failures}, timeout={config.circuit_breaker_timeout}s")
    print(f"✓ Retry: attempts={config.retry_attempts}, delay={config.retry_delay}s")
    print(f"✓ Кэширование: TTL={config.cache_ttl}s")

    # Запускаем сервер
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
