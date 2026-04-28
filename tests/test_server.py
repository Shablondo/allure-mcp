import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.server import main  # noqa: E402


class TestMain:
    def test_valid_config_runs_server(self, capsys):
        with patch("allure_testops_mcp.server.config") as mock_config, \
             patch("allure_testops_mcp.server.mcp") as mock_mcp:
            mock_config.validate.return_value = []
            mock_config.circuit_breaker_failures = 5
            mock_config.circuit_breaker_timeout = 60
            mock_config.retry_attempts = 3
            mock_config.retry_delay = 2
            mock_config.cache_ttl = 300

            main()

            captured = capsys.readouterr()
            assert "Конфигурация успешно загружена" in captured.out
            mock_mcp.run.assert_called_once_with(transport="stdio")

    def test_invalid_config_prints_errors(self, capsys):
        with patch("allure_testops_mcp.server.config") as mock_config, \
             patch("allure_testops_mcp.server.mcp") as mock_mcp:
            mock_config.validate.return_value = ["URL не задан", "Токен не задан"]

            main()

            captured = capsys.readouterr()
            assert "Ошибки конфигурации" in captured.out
            assert "URL не задан" in captured.out
            mock_mcp.run.assert_not_called()
