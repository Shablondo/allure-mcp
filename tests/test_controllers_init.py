import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.controllers import (  # noqa: E402
    _CONTROLLER_REGISTRARS,
    register_all_controllers,
)


class TestRegisterAllControllers:
    def test_registers_all_controllers(self):
        assert len(_CONTROLLER_REGISTRARS) == 10

    def test_register_all_calls_each_registrar(self):
        mcp = MagicMock()
        register_all_controllers(mcp)
        assert mcp.tool.call_count > 0
