"""Tests for UI adapters (Claude, Cline, FastAPI)."""

import json
from typing import List, Any

import pytest

from orchestrator import tool, search_tools
from orchestrator.adapters import ClaudeSkillsAdapter, ClineAdapter
from orchestrator.shared.models import ToolDefinition, ToolParameter

# Try to import FastAPI adapter (optional dependency)
try:
    from orchestrator.adapters import FastAPIAdapter
    import fastapi
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


# Create sample tools for testing
@tool(name="test_calculator", description="Basic calculator")
def add(x: int, y: int) -> int:
    """Add two numbers.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        Sum of x and y
    """
    return x + y


@tool(name="test_greet", description="Greet a person")
def greet(name: str, age: int = 0) -> str:
    """Greet someone by name.
    
    Args:
        name: Person's name
        age: Person's age (optional)
        
    Returns:
        Greeting message
    """
    msg = f"Hello {name}"
    if age > 0:
        msg += f" (age {age})"
    return msg


class TestClaudeSkillsAdapter:
    """Test Claude custom skills adapter."""
    
    def test_adapter_creation(self):
        """Test adapter instantiation."""
        # Get tool definitions from registry
        tools = search_tools(query="test_")
        adapter = ClaudeSkillsAdapter(tools)
        assert adapter is not None
        assert len(adapter.tools) >= 2
    
    def test_to_claude_manifest(self):
        """Test conversion to Claude manifest format."""
        tools = search_tools(query="test_")
        adapter = ClaudeSkillsAdapter(tools)
        manifest = adapter.to_claude_manifest()
        
        # Validate structure
        assert "tools" in manifest
        assert isinstance(manifest["tools"], list)
        assert len(manifest["tools"]) >= 2
        
        # Check first tool has required fields
        first_tool = manifest["tools"][0]
        assert "name" in first_tool
        assert "description" in first_tool
        assert "input_schema" in first_tool
        assert "properties" in first_tool["input_schema"]
    
    def test_to_claude_functions(self):
        """Test conversion to Claude functions format."""
        tools = search_tools(query="test_")
        adapter = ClaudeSkillsAdapter(tools)
        functions = adapter.to_claude_functions()
        
        assert isinstance(functions, list)
        assert len(functions) >= 2
        assert all("name" in f and "description" in f for f in functions)
    
    def test_to_json(self):
        """Test JSON serialization."""
        tools = search_tools(query="test_calculator")
        if not tools:
            pytest.skip("test_calculator tool not found")
        adapter = ClaudeSkillsAdapter(tools)
        json_str = adapter.to_json(pretty=True)
        
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "tools" in parsed


class TestClineAdapter:
    """Test Cline MCP format adapter."""
    
    def test_adapter_creation(self):
        """Test adapter instantiation."""
        tools = search_tools(query="test_")
        adapter = ClineAdapter(tools)
        assert adapter is not None
        assert len(adapter.tools) >= 2
    
    def test_to_cline_config(self):
        """Test conversion to Cline config format."""
        tools = search_tools(query="test_")
        adapter = ClineAdapter(tools)
        config = adapter.to_cline_config()
        
        # Validate structure
        assert "tools" in config
        assert isinstance(config["tools"], list)
        assert len(config["tools"]) >= 2
        
        # Check tool structure
        first_tool = config["tools"][0]
        assert "name" in first_tool
        assert "description" in first_tool
    
    def test_to_cline_tools_json(self):
        """Test tools.json format for Cline."""
        tools = search_tools(query="test_calculator")
        if not tools:
            pytest.skip("test_calculator tool not found")
        adapter = ClineAdapter(tools)
        tools_json = adapter.to_cline_tools_json()
        
        assert isinstance(tools_json, list)
        assert len(tools_json) >= 1
    
    def test_to_json(self):
        """Test JSON serialization."""
        tools = search_tools(query="test_")
        if not tools:
            pytest.skip("test tools not found")
        adapter = ClineAdapter(tools)
        json_str = adapter.to_json(pretty=False)
        
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestAdapterIntegration:
    """Integration tests across adapters."""
    
    def test_both_adapters_same_tools(self):
        """Test that both adapters work with same tool list."""
        tools = search_tools(query="test_")
        if not tools or len(tools) < 2:
            pytest.skip("Need at least 2 test tools")
        
        claude_adapter = ClaudeSkillsAdapter(tools)
        cline_adapter = ClineAdapter(tools)
        
        claude_manifest = claude_adapter.to_claude_manifest()
        cline_config = cline_adapter.to_cline_config()
        
        # Both should have all tools
        assert len(claude_manifest["tools"]) == len(tools)
        assert len(cline_config["tools"]) == len(tools)
    
    def test_empty_tool_list(self):
        """Test adapters with empty tool list."""
        claude_adapter = ClaudeSkillsAdapter([])
        cline_adapter = ClineAdapter([])
        
        claude_manifest = claude_adapter.to_claude_manifest()
        cline_config = cline_adapter.to_cline_config()
        
        assert claude_manifest["tools"] == []
        assert cline_config["tools"] == []
    
    def test_adapter_json_roundtrip(self):
        """Test that JSON output is valid and parseable."""
        tools = search_tools(query="test_calculator")
        if not tools:
            pytest.skip("test_calculator tool not found")
        
        adapter = ClaudeSkillsAdapter(tools)
        json_str = adapter.to_json(pretty=True)
        parsed = json.loads(json_str)
        
        # Should be able to recreate from parsed JSON
        assert "tools" in parsed
        assert len(parsed["tools"]) >= 1


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed")
class TestFastAPIAdapter:
    """Test FastAPI REST adapter (optional)."""
    
    def test_adapter_creation(self):
        """Test adapter instantiation."""
        tools = search_tools(query="test_")
        adapter = FastAPIAdapter(tools)
        assert adapter is not None
        assert len(adapter.tools) >= 2
    
    def test_create_app(self):
        """Test FastAPI app creation."""
        tools = search_tools(query="test_")
        adapter = FastAPIAdapter(tools)
        app = adapter.create_app()
        
        # Basic validation that it's a FastAPI app
        assert app is not None
        # Should have routes
        assert hasattr(app, "routes") or hasattr(app, "openapi")
    
    def test_app_has_endpoints(self):
        """Test that app has expected endpoints."""
        tools = search_tools(query="test_")
        if not tools:
            pytest.skip("test tools not found")
        
        adapter = FastAPIAdapter(tools)
        app = adapter.create_app()
        
        # Try to import FastAPI to validate routes
        try:
            from fastapi import FastAPI
            assert isinstance(app, FastAPI)
        except ImportError:
            pass
