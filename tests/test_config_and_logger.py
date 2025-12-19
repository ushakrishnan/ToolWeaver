import os
from typing import List

from orchestrator import get_config, reset_config, validate_config, set_log_level, get_logger


def test_config_defaults_and_reset(monkeypatch):
    # Ensure defaults
    cfg = get_config()
    assert cfg.skill_path is not None
    assert cfg.log_level in {"INFO", "DEBUG", "WARNING", "ERROR"}

    # Change env var and reset to reload
    monkeypatch.setenv("TOOLWEAVER_LOG_LEVEL", "DEBUG")
    reset_config()
    cfg2 = get_config()
    assert cfg2.log_level == "DEBUG"


def test_validate_config_returns_list():
    issues = validate_config()
    assert isinstance(issues, list)


def test_logger_level_change():
    set_log_level("WARNING")
    logger = get_logger(__name__)
    assert logger.level in (0, 30, 40, 50)  # 0 means inherited
