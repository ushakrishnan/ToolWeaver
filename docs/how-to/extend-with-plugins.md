# How to Extend with Plugins

Step-by-step guide to add tools to ToolWeaver at runtime without modifying core code using the plugin system.

## Prerequisites

- Working ToolWeaver project  
- Basic understanding of [MCP tools](add-a-tool.md)
- Familiarity with [Plugin Extension](../reference/deep-dives/plugin-extension.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Custom plugin with tools  
✅ Plugin registered at runtime  
✅ Plugin discovery and loading  
✅ Entry point for packaged plugins  
✅ Plugin validation and testing  

**Estimated time:** 25 minutes

---

## Step 1: Create a Plugin

### 1.1 Plugin Protocol

```python
from typing import Protocol, List, Dict, Any

class PluginProtocol(Protocol):
    """Required interface for plugins."""
    
    def get_tools(self) -> List[dict]:
        """Return list of tool definitions."""
        ...
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        """Execute a tool from this plugin."""
        ...
```

### 1.2 Basic Plugin Implementation

**File:** `plugins/weather_plugin.py`

```python
from typing import List, Dict, Any

class WeatherPlugin:
    """Plugin for weather-related tools."""
    
    def get_tools(self) -> List[dict]:
        """Return tool definitions."""
        return [
            {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "domain": "weather",
                "schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or coordinates"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_forecast",
                "description": "Get 7-day weather forecast",
                "domain": "weather",
                "schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        ]
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        """Execute tool."""
        
        if tool_name == "get_weather":
            return await self._get_weather(params)
        elif tool_name == "get_forecast":
            return await self._get_forecast(params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_weather(self, params: dict) -> dict:
        """Get current weather."""
        location = params["location"]
        units = params.get("units", "celsius")
        
        # Call weather API
        # (simplified example)
        return {
            "location": location,
            "temperature": 22,
            "units": units,
            "condition": "sunny",
            "humidity": 65
        }
    
    async def _get_forecast(self, params: dict) -> dict:
        """Get forecast."""
        location = params["location"]
        
        return {
            "location": location,
            "forecast": [
                {"day": 1, "temp": 22, "condition": "sunny"},
                {"day": 2, "temp": 20, "condition": "cloudy"},
                {"day": 3, "temp": 18, "condition": "rainy"}
            ]
        }
```

---

## Step 2: Register Plugin

### 2.1 Runtime Registration

```python
from orchestrator.plugins import register_plugin

# Create plugin instance
weather_plugin = WeatherPlugin()

# Register plugin
register_plugin("weather", weather_plugin)

print("✓ Weather plugin registered")

# List registered plugins
from orchestrator.plugins import list_plugins

plugins = list_plugins()
print(f"Registered plugins: {plugins}")
```

### 2.2 Get and Use Plugin

```python
from orchestrator.plugins import get_plugin

# Get plugin
plugin = get_plugin("weather")

# Get tools from plugin
tools = plugin.get_tools()
print(f"Available tools: {[t['name'] for t in tools]}")

# Execute tool
result = await plugin.execute("get_weather", {"location": "San Francisco"})
print(result)
# Output: {"location": "San Francisco", "temperature": 22, ...}
```

---

## Step 3: Plugin Discovery

### 3.1 Discover from Directory

```python
from orchestrator.plugins import discover_plugins
import importlib.util
from pathlib import Path

def discover_plugins_from_directory(plugin_dir: str = "plugins/"):
    """Discover and load plugins from directory."""
    
    plugin_path = Path(plugin_dir)
    discovered = []
    
    for py_file in plugin_path.glob("*_plugin.py"):
        # Load module
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes
        for name in dir(module):
            obj = getattr(module, name)
            
            # Check if it's a plugin class
            if (isinstance(obj, type) and 
                hasattr(obj, 'get_tools') and 
                hasattr(obj, 'execute')):
                
                # Instantiate and register
                plugin_instance = obj()
                plugin_name = py_file.stem.replace('_plugin', '')
                register_plugin(plugin_name, plugin_instance)
                
                discovered.append(plugin_name)
                print(f"✓ Discovered plugin: {plugin_name}")
    
    return discovered

# Usage
plugins = discover_plugins_from_directory("plugins/")
print(f"Discovered {len(plugins)} plugins: {plugins}")
```

### 3.2 Entry Point Discovery

**File:** `setup.py` (for packaged plugins)

```python
from setuptools import setup

setup(
    name="toolweaver-weather-plugin",
    version="1.0.0",
    py_modules=["weather_plugin"],
    entry_points={
        "toolweaver.plugins": [
            "weather = weather_plugin:WeatherPlugin"
        ]
    }
)
```

**Discovery code:**

```python
import pkg_resources

def discover_plugins_from_entry_points():
    """Discover plugins via entry points."""
    
    for entry_point in pkg_resources.iter_entry_points("toolweaver.plugins"):
        try:
            # Load plugin class
            plugin_class = entry_point.load()
            
            # Instantiate and register
            plugin_instance = plugin_class()
            register_plugin(entry_point.name, plugin_instance)
            
            print(f"✓ Loaded plugin: {entry_point.name}")
        
        except Exception as e:
            print(f"✗ Failed to load plugin {entry_point.name}: {e}")

# Usage
discover_plugins_from_entry_points()
```

---

## Step 4: Advanced Plugin Features

### 4.1 Plugin with Configuration

```python
class ConfigurablePlugin:
    """Plugin with configuration support."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url", "https://api.example.com")
    
    def get_tools(self) -> List[dict]:
        return [
            {
                "name": "api_call",
                "description": "Call external API",
                "schema": {
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"}
                    }
                }
            }
        ]
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        if tool_name == "api_call":
            # Use configured API key and base URL
            url = f"{self.base_url}/{params['endpoint']}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # Make API call...
            return {"status": "success"}
        
        raise ValueError(f"Unknown tool: {tool_name}")

# Usage with config
plugin = ConfigurablePlugin(config={
    "api_key": "sk-abc123",
    "base_url": "https://custom.api.com"
})

register_plugin("api", plugin)
```

### 4.2 Plugin with State

```python
class StatefulPlugin:
    """Plugin that maintains state."""
    
    def __init__(self):
        self.cache = {}
        self.call_count = 0
    
    def get_tools(self) -> List[dict]:
        return [
            {
                "name": "cached_fetch",
                "description": "Fetch with caching",
                "schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"}
                    }
                }
            }
        ]
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        if tool_name == "cached_fetch":
            self.call_count += 1
            key = params["key"]
            
            # Check cache
            if key in self.cache:
                return {
                    "value": self.cache[key],
                    "cached": True,
                    "call_count": self.call_count
                }
            
            # Fetch and cache
            value = f"fetched_{key}"
            self.cache[key] = value
            
            return {
                "value": value,
                "cached": False,
                "call_count": self.call_count
            }
        
        raise ValueError(f"Unknown tool: {tool_name}")
```

### 4.3 Plugin with Dependencies

```python
class PluginWithDependencies:
    """Plugin that requires other plugins."""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
    
    def get_tools(self) -> List[dict]:
        return [
            {
                "name": "weather_with_location",
                "description": "Get weather using location lookup",
                "schema": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string"}
                    }
                }
            }
        ]
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        if tool_name == "weather_with_location":
            # Use location plugin to geocode
            location_plugin = get_plugin("location")
            coords = await location_plugin.execute("geocode", {"address": params["address"]})
            
            # Use weather plugin
            weather_plugin = get_plugin("weather")
            weather = await weather_plugin.execute("get_weather", {"location": coords})
            
            return weather
        
        raise ValueError(f"Unknown tool: {tool_name}")
```

---

## Step 5: Validate Plugins

### 5.1 Plugin Validation

```python
from orchestrator.plugins import validate_plugin

def validate_plugin_interface(plugin) -> bool:
    """Validate plugin implements required interface."""
    
    # Check required methods
    if not hasattr(plugin, "get_tools"):
        print("✗ Missing get_tools() method")
        return False
    
    if not hasattr(plugin, "execute"):
        print("✗ Missing execute() method")
        return False
    
    # Check get_tools returns list
    try:
        tools = plugin.get_tools()
        if not isinstance(tools, list):
            print("✗ get_tools() must return list")
            return False
    except Exception as e:
        print(f"✗ get_tools() failed: {e}")
        return False
    
    # Validate tool definitions
    for tool in tools:
        required_fields = ["name", "description", "schema"]
        for field in required_fields:
            if field not in tool:
                print(f"✗ Tool missing field: {field}")
                return False
    
    print("✓ Plugin interface valid")
    return True

# Usage
plugin = WeatherPlugin()
is_valid = validate_plugin_interface(plugin)
```

### 5.2 Test Plugin Execution

```python
async def test_plugin(plugin, test_cases: list):
    """Test plugin with sample inputs."""
    
    tools = plugin.get_tools()
    print(f"Testing plugin with {len(tools)} tools...")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        tool_name = test["tool"]
        params = test["params"]
        
        try:
            result = await plugin.execute(tool_name, params)
            
            if test.get("expected"):
                if result == test["expected"]:
                    print(f"  ✓ {tool_name} passed")
                    passed += 1
                else:
                    print(f"  ✗ {tool_name} unexpected output")
                    failed += 1
            else:
                print(f"  ✓ {tool_name} executed")
                passed += 1
        
        except Exception as e:
            print(f"  ✗ {tool_name} failed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

# Usage
test_cases = [
    {
        "tool": "get_weather",
        "params": {"location": "San Francisco"}
    },
    {
        "tool": "get_forecast",
        "params": {"location": "New York"}
    }
]

await test_plugin(WeatherPlugin(), test_cases)
```

---

## Step 6: Unregister Plugins

### 6.1 Cleanup

```python
from orchestrator.plugins import unregister_plugin

# Unregister plugin
unregister_plugin("weather")

print("✓ Weather plugin unregistered")

# Verify
plugins = list_plugins()
assert "weather" not in plugins
```

---

## Step 7: Real-World Example

Complete plugin for third-party service integration.

**File:** `plugins/slack_plugin.py`

```python
import aiohttp
from typing import List, Dict, Any

class SlackPlugin:
    """Plugin for Slack integration."""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
    
    def get_tools(self) -> List[dict]:
        """Return Slack tools."""
        return [
            {
                "name": "send_message",
                "description": "Send message to Slack channel",
                "domain": "slack",
                "schema": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"}
                    },
                    "required": ["channel", "text"]
                }
            },
            {
                "name": "list_channels",
                "description": "List all Slack channels",
                "domain": "slack",
                "schema": {"type": "object"}
            }
        ]
    
    async def execute(self, tool_name: str, params: dict) -> Any:
        """Execute Slack tool."""
        
        if tool_name == "send_message":
            return await self._send_message(params)
        elif tool_name == "list_channels":
            return await self._list_channels()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _send_message(self, params: dict) -> dict:
        """Send Slack message."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                json={
                    "channel": params["channel"],
                    "text": params["text"]
                }
            ) as resp:
                result = await resp.json()
                return {
                    "success": result.get("ok", False),
                    "message_ts": result.get("ts")
                }
    
    async def _list_channels(self) -> dict:
        """List Slack channels."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {self.bot_token}"}
            ) as resp:
                result = await resp.json()
                return {
                    "channels": [
                        {"id": ch["id"], "name": ch["name"]}
                        for ch in result.get("channels", [])
                    ]
                }

# Usage
slack_plugin = SlackPlugin(bot_token="xoxb-your-token")
register_plugin("slack", slack_plugin)

# Send message
result = await slack_plugin.execute(
    "send_message",
    {"channel": "#general", "text": "Hello from ToolWeaver!"}
)
```

---

## Verification

Test your plugin system:

```python
async def verify_plugin_system():
    """Verify plugin registration and execution."""
    
    print("Testing plugin system...")
    
    # Test 1: Register plugin
    plugin = WeatherPlugin()
    register_plugin("weather", plugin)
    assert "weather" in list_plugins()
    print("✓ Plugin registration working")
    
    # Test 2: Get plugin
    retrieved = get_plugin("weather")
    assert retrieved is plugin
    print("✓ Plugin retrieval working")
    
    # Test 3: Get tools
    tools = plugin.get_tools()
    assert len(tools) > 0
    print("✓ Tool discovery working")
    
    # Test 4: Execute tool
    result = await plugin.execute("get_weather", {"location": "Test"})
    assert "temperature" in result
    print("✓ Tool execution working")
    
    # Test 5: Unregister
    unregister_plugin("weather")
    assert "weather" not in list_plugins()
    print("✓ Plugin unregistration working")
    
    print("\n✅ All checks passed!")

await verify_plugin_system()
```

---

## Common Issues

### Issue 1: Plugin Not Found

**Symptom:** `PluginNotFoundError`

**Solution:** Check plugin is registered

```python
plugins = list_plugins()
print(f"Registered plugins: {plugins}")

if "my_plugin" not in plugins:
    register_plugin("my_plugin", MyPlugin())
```

### Issue 2: Tool Name Collision

**Symptom:** Multiple plugins define same tool name

**Solution:** Enforce unique names or use namespacing

```python
def register_plugin_with_namespace(namespace: str, plugin):
    """Register plugin with namespaced tool names."""
    
    tools = plugin.get_tools()
    
    # Add namespace to tool names
    for tool in tools:
        tool["name"] = f"{namespace}.{tool['name']}"
    
    register_plugin(namespace, plugin)

# Usage
register_plugin_with_namespace("weather", WeatherPlugin())
# Tools: weather.get_weather, weather.get_forecast
```

### Issue 3: Async Execution Issues

**Symptom:** Plugin execute() not async

**Solution:** Ensure execute is async

```python
class CorrectPlugin:
    async def execute(self, tool_name: str, params: dict) -> Any:
        # Use async/await
        result = await self._async_operation()
        return result
```

---

## Next Steps

- **Deep Dive:** [Plugin Extension](../reference/deep-dives/plugin-extension.md) - Advanced patterns
- **Sample:** [31-plugin-extension](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/31-plugin-extension) - Complete example
- **Tutorial:** [Add a Tool](add-a-tool.md) - Create tools

## Related Guides

- [Create Skill Package](create-skill-package.md) - Package reusable tools
- [Add a Tool](add-a-tool.md) - Create MCP tools
- [Orchestrate with Code](orchestrate-with-code.md) - Use plugins in workflows
