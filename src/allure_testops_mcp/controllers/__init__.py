"""
Контроллеры Allure TestOps MCP сервера.

Этот модуль экспортирует функции регистрации для всех MCP инструментов.
"""

from .comment_controller import register_comment_tools
from .test_case_attachment_controller import register_test_case_attachment_tools
from .test_case_controller import register_test_case_tools
from .test_case_custom_field_controller import register_test_case_custom_field_tools
from .test_case_example_controller import register_test_case_example_tools
from .test_case_issue_controller import register_test_case_issue_tools
from .test_case_overview_controller import register_test_case_overview_tools
from .test_case_scenario_controller import register_test_case_scenario_tools
from .test_case_search_controller import register_test_case_search_tools
from .test_case_tag_controller import register_test_case_tag_tools

_CONTROLLER_REGISTRARS = (
    register_comment_tools,
    register_test_case_attachment_tools,
    register_test_case_tools,
    register_test_case_custom_field_tools,
    register_test_case_example_tools,
    register_test_case_issue_tools,
    register_test_case_overview_tools,
    register_test_case_scenario_tools,
    register_test_case_search_tools,
    register_test_case_tag_tools,
)


def register_all_controllers(mcp) -> None:
    """
    Регистрирует все контроллеры в MCP сервере.

    Args:
        mcp: Экземпляр FastMCP сервера
    """
    for register_controller in _CONTROLLER_REGISTRARS:
        register_controller(mcp)
