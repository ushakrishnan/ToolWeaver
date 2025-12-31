
import orchestrator as tw


def test_public_api_placeholders_raise_not_implemented():
    # Decorators are now implemented (Phase 2), so these should be callable
    assert callable(tw.tool)
    assert callable(tw.mcp_tool)
    assert callable(tw.a2a_agent)

    # Discovery is now implemented (Phase 1.6), so these are available
    assert callable(tw.get_available_tools)
    assert callable(tw.search_tools)
    assert callable(tw.get_tool_info)

    # Skill bridge is now implemented (Phase 1.5), so these are available
    assert callable(tw.save_tool_as_skill)
    assert callable(tw.load_tool_from_skill)
    assert callable(tw.get_tool_skill)
    assert callable(tw.sync_tool_with_skill)
    assert callable(tw.get_skill_backed_tools)

    # Plugin registry is now implemented (Phase 0.e)
    assert callable(tw.register_plugin)
    assert callable(tw.unregister_plugin)
    assert callable(tw.get_plugin)
    assert callable(tw.list_plugins)
    assert callable(tw.discover_plugins)

    # Configuration is now implemented (Phase 0.c)
    assert callable(tw.get_config)
    assert callable(tw.reset_config)
    assert callable(tw.validate_config)

    # Logging is now implemented (Phase 0.l)
    assert callable(tw.get_logger)
    assert callable(tw.set_log_level)
    assert callable(tw.enable_debug_mode)


def test_version_and_logger_public_surface():
    assert isinstance(tw.__version__, str)
    logger = tw.get_logger(__name__)
    logger.info("public api logger works")
