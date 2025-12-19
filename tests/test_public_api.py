import pytest

import orchestrator as tw


def test_public_api_placeholders_raise_not_implemented():
    # Decorators are placeholders
    with pytest.raises(NotImplementedError):
        tw.mcp_tool()
    with pytest.raises(NotImplementedError):
        tw.a2a_agent()

    # Discovery is now implemented (Phase 1.6), so remove these assertions
    # get_available_tools(), search_tools(), get_tool_info() are available
    assert callable(tw.get_available_tools)
    assert callable(tw.search_tools)
    assert callable(tw.get_tool_info)

    # Skill bridge placeholders
    with pytest.raises(NotImplementedError):
        tw.save_as_skill()
    with pytest.raises(NotImplementedError):
        tw.load_from_skill()

    # Diagnostics placeholders
    with pytest.raises(NotImplementedError):
        tw.get_tool_health()
    with pytest.raises(NotImplementedError):
        tw.get_execution_stats()


def test_version_and_logger_public_surface():
    assert isinstance(tw.__version__, str)
    logger = tw.get_logger(__name__)
    logger.info("public api logger works")
