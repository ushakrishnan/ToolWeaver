"""
Tests for plugin registry system.

Phase 0.e: Verify plugin registration, discovery, and execution.
"""

import pytest
from orchestrator.plugins import (
    register_plugin,
    unregister_plugin,
    get_plugin,
    list_plugins,
    get_registry,
    PluginRegistry,
    PluginNotFoundError,
    PluginAlreadyRegisteredError,
    InvalidPluginError,
)


# ============================================================
# Test Plugins
# ============================================================

class ValidPlugin:
    """A valid plugin implementation."""
    
    def get_tools(self):
        return [
            {
                "name": "test_tool_1",
                "description": "Test tool 1",
                "parameters": {"param1": "string"}
            }
        ]
    
    async def execute(self, tool_name: str, params: dict):
        return {"result": f"Executed {tool_name} with {params}"}


class AnotherValidPlugin:
    """Another valid plugin."""
    
    def get_tools(self):
        return [
            {
                "name": "test_tool_2",
                "description": "Test tool 2",
                "parameters": {}
            }
        ]
    
    async def execute(self, tool_name: str, params: dict):
        return {"result": "success"}


class InvalidPlugin:
    """Plugin missing required methods."""
    
    def some_method(self):
        pass


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def clean_registry():
    """Provide a clean registry for each test."""
    registry = get_registry()
    registry.clear()
    yield registry
    registry.clear()


# ============================================================
# Test Global Convenience Functions
# ============================================================

def test_global_convenience_functions(clean_registry):
    """Test global convenience functions (register_plugin, get_plugin, list_plugins, unregister_plugin)."""
    # Register a plugin using global functions
    register_plugin("test_global", ValidPlugin())
    
    assert "test_global" in list_plugins()
    assert isinstance(get_plugin("test_global"), ValidPlugin)
    
    # Attempting to register duplicate should raise error
    with pytest.raises(PluginAlreadyRegisteredError):
        register_plugin("test_global", ValidPlugin())
    
    # Unregister should work
    unregister_plugin("test_global")
    
    # Plugin should no longer be in registry
    with pytest.raises(PluginNotFoundError):
        get_plugin("test_global")


# ============================================================
# Test Basic Registration
# ============================================================

def test_register_plugin(clean_registry):
    """Test registering a valid plugin."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    assert "test" in list_plugins()
    assert get_plugin("test") is plugin


def test_register_multiple_plugins(clean_registry):
    """Test registering multiple plugins."""
    plugin1 = ValidPlugin()
    plugin2 = AnotherValidPlugin()
    
    register_plugin("plugin1", plugin1)
    register_plugin("plugin2", plugin2)
    
    plugins = list_plugins()
    assert len(plugins) == 2
    assert "plugin1" in plugins
    assert "plugin2" in plugins


def test_register_duplicate_plugin(clean_registry):
    """Test that registering duplicate plugin raises error."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    with pytest.raises(PluginAlreadyRegisteredError):
        register_plugin("test", plugin)


def test_register_duplicate_plugin_with_replace(clean_registry):
    """Test replacing existing plugin."""
    plugin1 = ValidPlugin()
    plugin2 = AnotherValidPlugin()
    
    register_plugin("test", plugin1)
    register_plugin("test", plugin2, replace=True)
    
    assert get_plugin("test") is plugin2


def test_register_invalid_plugin_no_get_tools(clean_registry):
    """Test that plugin without get_tools() is rejected."""
    class NoGetTools:
        async def execute(self, tool_name, params):
            pass
    
    with pytest.raises(InvalidPluginError, match="must implement get_tools"):
        register_plugin("invalid", NoGetTools())


def test_register_invalid_plugin_no_execute(clean_registry):
    """Test that plugin without execute() is rejected."""
    class NoExecute:
        def get_tools(self):
            return []
    
    with pytest.raises(InvalidPluginError, match="must implement execute"):
        register_plugin("invalid", NoExecute())


# ============================================================
# Test Plugin Retrieval
# ============================================================

def test_get_plugin_success(clean_registry):
    """Test getting registered plugin."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    retrieved = get_plugin("test")
    assert retrieved is plugin


def test_get_plugin_not_found(clean_registry):
    """Test that getting non-existent plugin raises error."""
    with pytest.raises(PluginNotFoundError, match="Plugin 'nonexistent' not found"):
        get_plugin("nonexistent")


def test_list_plugins_empty(clean_registry):
    """Test listing plugins when registry is empty."""
    assert list_plugins() == []


def test_list_plugins_with_plugins(clean_registry):
    """Test listing plugins."""
    register_plugin("plugin1", ValidPlugin())
    register_plugin("plugin2", AnotherValidPlugin())
    
    plugins = list_plugins()
    assert len(plugins) == 2
    assert set(plugins) == {"plugin1", "plugin2"}


# ============================================================
# Test Plugin Unregistration
# ============================================================

def test_unregister_plugin(clean_registry):
    """Test unregistering a plugin."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    assert "test" in list_plugins()
    
    unregister_plugin("test")
    
    assert "test" not in list_plugins()
    with pytest.raises(PluginNotFoundError):
        get_plugin("test")


def test_unregister_nonexistent_plugin(clean_registry):
    """Test that unregistering non-existent plugin raises error."""
    with pytest.raises(PluginNotFoundError):
        unregister_plugin("nonexistent")


# ============================================================
# Test Plugin Functionality
# ============================================================

def test_plugin_get_tools(clean_registry):
    """Test calling get_tools() on registered plugin."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    retrieved = get_plugin("test")
    tools = retrieved.get_tools()
    
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool_1"


@pytest.mark.asyncio
async def test_plugin_execute(clean_registry):
    """Test calling execute() on registered plugin."""
    plugin = ValidPlugin()
    register_plugin("test", plugin)
    
    retrieved = get_plugin("test")
    result = await retrieved.execute("test_tool_1", {"param1": "value1"})
    
    assert result["result"] == "Executed test_tool_1 with {'param1': 'value1'}"


# ============================================================
# Test Registry Methods
# ============================================================

def test_registry_has_method(clean_registry):
    """Test PluginRegistry.has() method."""
    register_plugin("test", ValidPlugin())
    
    assert clean_registry.has("test")
    assert not clean_registry.has("nonexistent")


def test_registry_clear_method(clean_registry):
    """Test PluginRegistry.clear() method."""
    register_plugin("plugin1", ValidPlugin())
    register_plugin("plugin2", AnotherValidPlugin())
    
    assert len(list_plugins()) == 2
    
    clean_registry.clear()
    
    assert list_plugins() == []


def test_registry_get_all_tools(clean_registry):
    """Test PluginRegistry.get_all_tools() method."""
    register_plugin("plugin1", ValidPlugin())
    register_plugin("plugin2", AnotherValidPlugin())
    
    all_tools = clean_registry.get_all_tools()
    
    assert "plugin1" in all_tools
    assert "plugin2" in all_tools
    assert len(all_tools["plugin1"]) == 1
    assert len(all_tools["plugin2"]) == 1
    assert all_tools["plugin1"][0]["name"] == "test_tool_1"
    assert all_tools["plugin2"][0]["name"] == "test_tool_2"


def test_registry_get_all_tools_with_error(clean_registry):
    """Test that registration fails for plugins that raise on get_tools()."""
    class BrokenPlugin:
        def get_tools(self):
            raise ValueError("Broken!")
        
        async def execute(self, tool_name, params):
            pass
    
    # Registration should fail for broken plugin
    with pytest.raises(InvalidPluginError, match="get_tools\\(\\) failed"):
        register_plugin("broken", BrokenPlugin())
    
    # Working plugin should register fine
    register_plugin("working", ValidPlugin())
    all_tools = clean_registry.get_all_tools()
    
    # Only working plugin should be in registry
    assert "broken" not in all_tools
    assert "working" in all_tools
    assert len(all_tools["working"]) == 1


# ============================================================
# Test Thread Safety
# ============================================================

def test_registry_thread_safety():
    """Test that registry operations are thread-safe."""
    import threading
    
    registry = PluginRegistry()
    errors = []
    counter = {"value": 0}  # Shared counter for unique indices
    counter_lock = threading.Lock()
    
    def register_many():
        try:
            for _ in range(100):
                # Get a globally unique index
                with counter_lock:
                    idx = counter["value"]
                    counter["value"] += 1
                
                # Create a unique plugin for this registration
                class UniquePlugin:
                    def __init__(self, plugin_idx):
                        self.plugin_idx = plugin_idx
                    
                    def get_tools(self):
                        return [
                            {
                                "name": f"tool_{self.plugin_idx}",
                                "description": f"Tool {self.plugin_idx}"
                            }
                        ]
                    
                    async def execute(self, tool_name, params):
                        return {"result": f"executed {tool_name}"}
                
                registry.register(f"plugin_{idx}", UniquePlugin(idx), replace=False)
        except Exception as e:
            errors.append(e)
    
    # Start multiple threads
    threads = [threading.Thread(target=register_many) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # No errors should occur
    assert len(errors) == 0
    
    # All 500 plugins should be registered (5 threads * 100 each)
    assert len(registry.list()) == 500


# ============================================================
# Test Global Registry Singleton
# ============================================================

def test_get_registry_singleton(clean_registry):
    """Test that get_registry() returns the same instance."""
    registry1 = get_registry()
    registry2 = get_registry()
    
    assert registry1 is registry2


# ============================================================
# Integration Test
# ============================================================

def test_plugin_workflow(clean_registry):
    """Test complete plugin workflow."""
    # 1. Register plugins
    plugin1 = ValidPlugin()
    plugin2 = AnotherValidPlugin()
    
    register_plugin("jira", plugin1)
    register_plugin("slack", plugin2)
    
    # 2. List plugins
    plugins = list_plugins()
    assert len(plugins) == 2
    
    # 3. Get all tools
    all_tools = clean_registry.get_all_tools()
    assert len(all_tools) == 2
    
    # 4. Get specific plugin
    jira = get_plugin("jira")
    assert jira is plugin1
    
    # 5. Use plugin
    tools = jira.get_tools()
    assert len(tools) == 1
    
    # 6. Unregister plugin
    unregister_plugin("slack")
    assert len(list_plugins()) == 1
    
    # 7. Clear all
    clean_registry.clear()
    assert list_plugins() == []
