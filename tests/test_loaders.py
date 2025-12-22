"""
Tests for YAML tool loader.

Phase 3: Verify YAML-based tool registration works correctly.
"""

import pytest
from pathlib import Path
import tempfile
import sys
from typing import Dict, Any

# Add current directory to path for importing test worker functions
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.tools.loaders import (
    load_tools_from_yaml,
    load_tools_from_directory,
    YAMLLoaderError,
    YAMLValidationError,
    WorkerResolutionError,
)
from orchestrator.plugins.registry import get_registry


# Sample worker functions for testing - register them in a module-like way
def sample_worker_sync(employee_id: str, year: int = 2025) -> Dict[str, Any]:
    """Sample synchronous worker function."""
    return {"employee_id": employee_id, "year": year, "expenses": []}


async def sample_worker_async(repo: str, title: str) -> Dict[str, Any]:
    """Sample async worker function."""
    return {"repo": repo, "title": title, "pr_number": 123}


# Register these in the current module so they can be imported
__all__ = ["sample_worker_sync", "sample_worker_async"]


@pytest.fixture
def clean_registry():
    """Ensure clean registry for each test."""
    registry = get_registry()
    registry.clear()
    yield registry
    registry.clear()


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


def test_load_simple_tool(clean_registry, temp_yaml_file):
    """Test loading a simple tool definition."""
    yaml_content = """
tools:
  - name: get_expenses
    type: function
    domain: finance
    description: "Fetch employee expenses"
    worker: test_loaders:sample_worker_sync
    parameters:
      - name: employee_id
        type: string
        description: "Employee identifier"
        required: true
      - name: year
        type: integer
        description: "Fiscal year"
        required: false
        default: 2025
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 1
    
    plugin = clean_registry.get("yaml_tools")
    tools = plugin.get_tools()
    
    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "get_expenses"
    assert tool["type"] == "function"
    assert tool["domain"] == "finance"
    assert tool["source"] == "yaml"
    
    # Check parameters
    params = {p["name"]: p for p in tool["parameters"]}
    assert "employee_id" in params
    assert params["employee_id"]["required"] is True
    assert params["year"]["required"] is False
    assert params["year"]["default"] == 2025


@pytest.mark.asyncio
async def test_execute_yaml_tool_sync(clean_registry, temp_yaml_file):
    """Test executing a synchronous YAML tool."""
    yaml_content = """
tools:
  - name: get_expenses
    worker: test_loaders:sample_worker_sync
    parameters:
      - name: employee_id
        type: string
        required: true
"""
    temp_yaml_file.write_text(yaml_content)
    
    load_tools_from_yaml(temp_yaml_file)
    
    plugin = clean_registry.get("yaml_tools")
    result = await plugin.execute("get_expenses", {"employee_id": "E123", "year": 2024})
    
    assert result["employee_id"] == "E123"
    assert result["year"] == 2024
    assert result["expenses"] == []


@pytest.mark.asyncio
async def test_execute_yaml_tool_async(clean_registry, temp_yaml_file):
    """Test executing an async YAML tool."""
    yaml_content = """
tools:
  - name: create_pr
    worker: test_loaders:sample_worker_async
    parameters:
      - name: repo
        type: string
        required: true
      - name: title
        type: string
        required: true
"""
    temp_yaml_file.write_text(yaml_content)
    
    load_tools_from_yaml(temp_yaml_file)
    
    plugin = clean_registry.get("yaml_tools")
    result = await plugin.execute("create_pr", {"repo": "toolweaver", "title": "Fix bug"})
    
    assert result["repo"] == "toolweaver"
    assert result["title"] == "Fix bug"
    assert result["pr_number"] == 123


def test_load_multiple_tools(clean_registry, temp_yaml_file):
    """Test loading multiple tools from one file."""
    yaml_content = """
tools:
  - name: tool1
    worker: test_loaders:sample_worker_sync
  - name: tool2
    worker: test_loaders:sample_worker_async
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 2
    
    plugin = clean_registry.get("yaml_tools")
    tools = plugin.get_tools()
    assert len(tools) == 2
    
    names = {t["name"] for t in tools}
    assert names == {"tool1", "tool2"}


def test_missing_name_field(clean_registry, temp_yaml_file):
    """Test error when tool name is missing."""
    yaml_content = """
tools:
  - worker: tests.test_loaders:sample_worker_sync
"""
    temp_yaml_file.write_text(yaml_content)
    
    # Should load 0 tools (error logged but continues)
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 0


def test_missing_worker_field(clean_registry, temp_yaml_file):
    """Test error when worker is missing."""
    yaml_content = """
tools:
  - name: bad_tool
    description: "Missing worker"
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 0


def test_invalid_worker_path(clean_registry, temp_yaml_file):
    """Test error when worker path cannot be resolved."""
    yaml_content = """
tools:
  - name: bad_tool
    worker: nonexistent.module:function
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 0


def test_file_not_found():
    """Test error when YAML file doesn't exist."""
    with pytest.raises(YAMLLoaderError, match="not found"):
        load_tools_from_yaml("nonexistent.yaml")


def test_invalid_yaml(temp_yaml_file):
    """Test error when YAML is malformed."""
    temp_yaml_file.write_text("{ invalid yaml [")
    
    with pytest.raises(YAMLLoaderError, match="Failed to parse"):
        load_tools_from_yaml(temp_yaml_file)


def test_missing_tools_key(temp_yaml_file):
    """Test error when 'tools' key is missing."""
    temp_yaml_file.write_text("some_key: value")
    
    with pytest.raises(YAMLValidationError, match="must contain a 'tools' key"):
        load_tools_from_yaml(temp_yaml_file)


def test_tools_not_list(temp_yaml_file):
    """Test error when 'tools' is not a list."""
    temp_yaml_file.write_text("tools: not_a_list")
    
    with pytest.raises(YAMLValidationError, match="must be a list"):
        load_tools_from_yaml(temp_yaml_file)


def test_load_from_directory(clean_registry, temp_yaml_file):
    """Test loading all YAML files from a directory."""
    temp_dir = temp_yaml_file.parent
    
    # Create multiple YAML files
    file1 = temp_dir / "tools1.yaml"
    file1.write_text("""
tools:
  - name: tool1
    worker: test_loaders:sample_worker_sync
""")
    
    file2 = temp_dir / "tools2.yaml"
    file2.write_text("""
tools:
  - name: tool2
    worker: test_loaders:sample_worker_async
""")
    
    try:
        count = load_tools_from_directory(temp_dir)
        # Should load at least our 2 tools (may load more if temp dir has other yamls)
        assert count >= 2
        
        plugin = clean_registry.get("yaml_tools")
        tools = plugin.get_tools()
        names = {t["name"] for t in tools}
        assert "tool1" in names
        assert "tool2" in names
    finally:
        file1.unlink(missing_ok=True)
        file2.unlink(missing_ok=True)


def test_colon_separator_in_worker_path(clean_registry, temp_yaml_file):
    """Test worker path with colon separator."""
    yaml_content = """
tools:
  - name: test_tool
    worker: test_loaders:sample_worker_sync
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 1


def test_dot_separator_in_worker_path(clean_registry, temp_yaml_file):
    """Test worker path with dot separator."""
    yaml_content = """
tools:
  - name: test_tool
    worker: test_loaders.sample_worker_sync
"""
    temp_yaml_file.write_text(yaml_content)
    
    count = load_tools_from_yaml(temp_yaml_file)
    assert count == 1


def test_metadata_preservation(clean_registry, temp_yaml_file):
    """Test that metadata is preserved."""
    yaml_content = """
tools:
  - name: test_tool
    worker: test_loaders:sample_worker_sync
    metadata:
      version: "1.0"
      tags:
        - finance
        - expenses
"""
    temp_yaml_file.write_text(yaml_content)
    
    load_tools_from_yaml(temp_yaml_file)
    
    plugin = clean_registry.get("yaml_tools")
    tools = plugin.get_tools()
    tool = tools[0]
    
    assert tool["metadata"]["version"] == "1.0"
    assert tool["metadata"]["tags"] == ["finance", "expenses"]


def test_optional_fields_defaults(clean_registry, temp_yaml_file):
    """Test default values for optional fields."""
    yaml_content = """
tools:
  - name: minimal_tool
    worker: test_loaders:sample_worker_sync
"""
    temp_yaml_file.write_text(yaml_content)
    
    load_tools_from_yaml(temp_yaml_file)
    
    plugin = clean_registry.get("yaml_tools")
    tools = plugin.get_tools()
    tool = tools[0]
    
    assert tool["type"] == "function"  # default type
    assert tool["domain"] == "general"  # default domain
    assert tool["source"] == "yaml"
