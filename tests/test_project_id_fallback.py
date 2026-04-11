import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from allure_testops_mcp.config import config  # noqa: E402
from allure_testops_mcp.controllers._utils import resolve_project_id  # noqa: E402


def test_resolve_project_id_prefers_explicit_value(monkeypatch):
    monkeypatch.setattr(config, "_project_id", 77)
    assert resolve_project_id(15) == 15


def test_resolve_project_id_uses_config_default_when_missing(monkeypatch):
    monkeypatch.setattr(config, "_project_id", 77)
    assert resolve_project_id(None) == 77


def test_resolve_project_id_keeps_missing_when_no_default(monkeypatch):
    monkeypatch.setattr(config, "_project_id", None)
    assert resolve_project_id(None) is None
