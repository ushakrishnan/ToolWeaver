import logging

import pytest

from orchestrator._internal.errors import (
    MissingDependencyError,
    get_install_suggestion,
    optional_feature,
    require_package,
    require_packages,
)


def test_require_package_raises_for_missing():
    missing_pkg = "this_package_does_not_exist_12345"

    @require_package(missing_pkg)
    def uses_missing():
        return True

    with pytest.raises(MissingDependencyError) as exc:
        uses_missing()
    # Suggestion should say pip install <pkg>
    assert f"pip install {missing_pkg}" in str(exc.value)


def test_require_packages_aggregates_missing():
    @require_packages("redis_nonexistent_1", "redis_nonexistent_2", extra="redis")
    def uses_multi():
        return True

    with pytest.raises(MissingDependencyError) as exc:
        uses_multi()
    msg = str(exc.value)
    assert "Missing packages:" in msg
    assert "pip install toolweaver[redis]" in msg


def test_optional_feature_logs_and_continues(caplog):
    caplog.set_level(logging.WARNING)
    logger = logging.getLogger("toolweaver-test")

    with optional_feature("not_installed_pkg_zz", extra="monitoring", logger=logger) as available:
        assert available is False
        # Any ImportError inside should be suppressed
        try:
            __import__("not_installed_pkg_zz")  # noqa: F401
        except ImportError:
            # Context manager __exit__ should suppress this if used within 'with'
            pass

    # Ensure a warning was logged with a helpful install hint
    combined = "\n".join(r.message for r in caplog.records)
    assert "toolweaver[monitoring]" in combined


def test_get_install_suggestion_map_and_fallback():
    assert get_install_suggestion("wandb") == "pip install toolweaver[monitoring]"
    assert get_install_suggestion("some_unknown_package") == "pip install some_unknown_package"
