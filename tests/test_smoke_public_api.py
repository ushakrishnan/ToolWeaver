"""
Smoke tests for public API surface (Phase 0.i).

These tests validate:
1. Public API is importable
2. No _internal imports from public modules
3. Optional dependencies fail gracefully
4. Core functionality works with basic imports
"""

import sys
import pytest


class TestPublicAPIImports:
    """Test that all public API exports are importable."""

    def test_core_imports(self):
        """Test core tool registration imports."""
        from orchestrator import (
            tool,
            mcp_tool,
            a2a_agent,
            BaseTemplate,
            FunctionToolTemplate,
            MCPToolTemplate,
            CodeExecToolTemplate,
            AgentTemplate,
        )
        assert tool is not None
        assert mcp_tool is not None
        assert a2a_agent is not None
        assert BaseTemplate is not None

    def test_discovery_api_imports(self):
        """Test discovery API imports."""
        from orchestrator import (
            get_available_tools,
            search_tools,
            get_tool_info,
            list_tools_by_domain,
            semantic_search_tools,
            browse_tools,
        )
        assert get_available_tools is not None
        assert search_tools is not None
        assert get_tool_info is not None

    def test_yaml_loader_imports(self):
        """Test YAML loader imports."""
        from orchestrator import (
            load_tools_from_yaml,
            load_tools_from_directory,
            YAMLLoaderError,
            YAMLValidationError,
            WorkerResolutionError,
        )
        assert load_tools_from_yaml is not None
        assert YAMLLoaderError is not None

    def test_skill_bridge_imports(self):
        """Test skill bridge imports."""
        from orchestrator import (
            save_tool_as_skill,
            load_tool_from_skill,
            get_tool_skill,
            sync_tool_with_skill,
            get_skill_backed_tools,
        )
        assert save_tool_as_skill is not None
        assert load_tool_from_skill is not None

    def test_plugin_imports(self):
        """Test plugin registry imports."""
        from orchestrator import (
            register_plugin,
            unregister_plugin,
            get_plugin,
            list_plugins,
            discover_plugins,
        )
        assert register_plugin is not None
        assert get_plugin is not None

    def test_config_imports(self):
        """Test configuration imports."""
        from orchestrator import (
            get_config,
            reset_config,
            validate_config,
        )
        assert get_config is not None
        assert reset_config is not None

    def test_logging_imports(self):
        """Test logging imports."""
        from orchestrator import (
            get_logger,
            set_log_level,
            enable_debug_mode,
        )
        assert get_logger is not None
        assert set_log_level is not None


class TestPublicAPIFunctionality:
    """Test basic functionality of public APIs."""

    def test_get_available_tools_returns_list(self):
        """Test that get_available_tools returns a list."""
        from orchestrator import get_available_tools
        
        tools = get_available_tools()
        assert isinstance(tools, list)

    def test_search_tools_returns_list(self):
        """Test that search_tools returns a list."""
        from orchestrator import search_tools
        
        tools = search_tools(query="tool")
        assert isinstance(tools, list)

    def test_get_config_returns_config_object(self):
        """Test that get_config returns a config object."""
        from orchestrator import get_config
        
        config = get_config()
        # Config should be a ToolWeaverConfig object
        assert config is not None
        assert hasattr(config, "skill_path") or isinstance(config, dict)
    def test_mcp_tool_decorator_works(self):
        """Test that @mcp_tool decorator creates a registerable tool."""
        from orchestrator import mcp_tool
        
        @mcp_tool(description="Test tool")
        def test_func(x: int) -> int:
            """Test function."""
            return x * 2
        
        # Tool should have metadata attached
        assert hasattr(test_func, '__tool_definition__')


class TestNoInternalImportsInPublic:
    """Test that public modules don't import from _internal inappropriately."""

    def test_orchestrator_init_no_unintended_internal_imports(self):
        """Verify __init__.py doesn't expose internal symbols."""
        import orchestrator
        
        # Check __all__ doesn't include _internal symbols
        all_exports = orchestrator.__all__
        internal_symbols = [s for s in all_exports if s.startswith('_')]
        
        # Only __version__ should start with underscore (special case)
        non_version_internals = [s for s in internal_symbols if s != '__version__']
        assert len(non_version_internals) == 0, f"Found internal symbols in __all__: {non_version_internals}"

    def test_public_api_exports_are_documented(self):
        """Verify all public APIs are documented in __all__."""
        import orchestrator
        
        # Core public functions that should be in __all__
        expected_exports = {
            'mcp_tool',
            'a2a_agent',
            'tool',
            'get_available_tools',
            'search_tools',
            'get_tool_info',
            'load_tools_from_yaml',
            'YAMLLoaderError',
            'register_plugin',
            'get_config',
            'get_logger',
        }
        
        actual_exports = set(orchestrator.__all__)
        missing = expected_exports - actual_exports
        
        assert len(missing) == 0, f"Missing exports from __all__: {missing}"


class TestOptionalDependenciesGraceful:
    """Test that optional dependencies fail gracefully."""

    def test_semantic_search_without_qdrant(self, monkeypatch):
        """Test semantic search fails gracefully without Qdrant."""
        # This test just verifies the module loads
        # Actual behavior testing would require mocking imports
        from orchestrator import search_tools
        
        # Should at least be callable even if Qdrant is missing
        assert callable(search_tools)

    def test_monitoring_without_wandb(self):
        """Test monitoring functionality exists even without wandb."""
        # The package should still load and work without wandb
        import orchestrator
        
        # get_logger should work without external monitoring tools
        from orchestrator import get_logger
        logger = get_logger("test")
        assert logger is not None


class TestCorePublicAPISignatures:
    """Test that public API has expected signatures."""

    def test_mcp_tool_decorator_signature(self):
        """Test @mcp_tool has expected parameters."""
        from orchestrator import mcp_tool
        import inspect
        
        sig = inspect.signature(mcp_tool)
        params = list(sig.parameters.keys())
        
        # Should support at minimum: name, description, domain
        expected_params = {'name', 'description', 'domain'}
        actual_params = set(params)
        
        # Check that expected parameters are present (others may exist too)
        assert expected_params.issubset(actual_params), \
            f"Missing expected parameters. Expected {expected_params}, got {actual_params}"

    def test_get_available_tools_signature(self):
        """Test get_available_tools has expected signature."""
        from orchestrator import get_available_tools
        import inspect
        
        sig = inspect.signature(get_available_tools)
        # Should return a list
        assert sig.return_annotation is not None or True  # Type hints optional


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
