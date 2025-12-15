"""
Integration tests for Phase 1: LargePlanner with ToolCatalog

Tests backward compatibility and new tool catalog features.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.planner import LargePlanner


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables for all tests"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
    monkeypatch.setenv("PLANNER_PROVIDER", "openai")
    monkeypatch.setenv("PLANNER_MODEL", "gpt-4o")


class TestPlannerBackwardCompatibility:
    """Test that existing code still works without changes"""
    
    def test_planner_without_catalog(self):
        """Planner should work without catalog parameter (uses default)"""
        # This is how existing code uses the planner
        planner = LargePlanner(provider="openai")
        
        # Should have default catalog
        catalog = planner._get_tool_catalog()
        assert catalog is not None
        assert len(catalog.tools) > 0
        assert catalog.source == "legacy_hardcoded"
    
    def test_default_catalog_has_expected_tools(self):
        """Default catalog should have receipt processing tools"""
        planner = LargePlanner(provider="openai")
        catalog = planner._get_tool_catalog()
        
        # Check for key tools
        assert "receipt_ocr" in catalog.tools
        assert "line_item_parser" in catalog.tools
        assert "compute_tax" in catalog.tools
        assert "code_exec" in catalog.tools
        
        # Check tool types
        assert catalog.get_tool("receipt_ocr").type == "mcp"
        assert catalog.get_tool("compute_tax").type == "function"
        assert catalog.get_tool("code_exec").type == "code_exec"
    
    def test_system_prompt_generation(self):
        """System prompt should be generated correctly"""
        planner = LargePlanner(provider="openai")
        prompt = planner._build_system_prompt()
        
        # Should contain tool descriptions
        assert "receipt_ocr" in prompt.lower()
        assert "compute_tax" in prompt.lower()
        assert "code_exec" in prompt.lower()
        
        # Should have guidelines
        assert "execution plan" in prompt.lower()
        assert "json" in prompt.lower()


class TestPlannerWithCustomCatalog:
    """Test Phase 1 feature: Custom tool catalog injection"""
    
    def test_planner_with_custom_catalog(self):
        """Planner should use injected catalog"""
        # Create custom catalog
        catalog = ToolCatalog(source="test_custom", version="1.0")
        catalog.add_tool(ToolDefinition(
            name="custom_tool",
            type="function",
            description="A custom tool for testing",
            parameters=[
                ToolParameter(name="input", type="string", description="Input data", required=True)
            ]
        ))
        
        # Create planner with catalog
        planner = LargePlanner(provider="openai", tool_catalog=catalog)
        
        # Should use custom catalog
        result_catalog = planner._get_tool_catalog()
        assert result_catalog.source == "test_custom"
        assert len(result_catalog.tools) == 1
        assert "custom_tool" in result_catalog.tools
    
    def test_custom_catalog_in_system_prompt(self):
        """Custom tools should appear in system prompt"""
        catalog = ToolCatalog(source="test", version="1.0")
        catalog.add_tool(ToolDefinition(
            name="special_analyzer",
            type="mcp",
            description="Analyzes special data",
            parameters=[
                ToolParameter(name="data", type="object", description="Data to analyze", required=True)
            ]
        ))
        
        planner = LargePlanner(provider="openai", tool_catalog=catalog)
        prompt = planner._build_system_prompt()
        
        # Custom tool should be in prompt
        assert "special_analyzer" in prompt.lower()
        assert "analyzes special data" in prompt.lower()


class TestPlannerWithSemanticSearch:
    """Test Phase 3 feature: Available tools from semantic search"""
    
    def test_planner_with_available_tools(self):
        """Planner should prioritize available_tools parameter"""
        # Create default catalog
        default_catalog = ToolCatalog(source="default", version="1.0")
        default_catalog.add_tool(ToolDefinition(
            name="default_tool",
            type="function",
            description="Default tool",
            parameters=[]
        ))
        
        # Create search results (simulating Phase 3)
        search_results = [
            ToolDefinition(
                name="search_result_1",
                type="mcp",
                description="Found by search",
                parameters=[
                    ToolParameter(name="query", type="string", description="Query", required=True)
                ]
            ),
            ToolDefinition(
                name="search_result_2",
                type="function",
                description="Also found by search",
                parameters=[]
            )
        ]
        
        planner = LargePlanner(provider="openai", tool_catalog=default_catalog)
        
        # When available_tools provided, should use those instead
        catalog = planner._get_tool_catalog(available_tools=search_results)
        assert catalog.source == "semantic_search"
        assert len(catalog.tools) == 2
        assert "search_result_1" in catalog.tools
        assert "default_tool" not in catalog.tools  # Default overridden
    
    def test_tool_priority_order(self):
        """Test priority: available_tools > tool_catalog > default"""
        # 1. No catalog, no available_tools -> default
        planner1 = LargePlanner(provider="openai")
        catalog1 = planner1._get_tool_catalog()
        assert catalog1.source == "legacy_hardcoded"
        
        # 2. With catalog, no available_tools -> use catalog
        custom_catalog = ToolCatalog(source="custom", version="1.0")
        planner2 = LargePlanner(provider="openai", tool_catalog=custom_catalog)
        catalog2 = planner2._get_tool_catalog()
        assert catalog2.source == "custom"
        
        # 3. With both, available_tools wins
        search_tools = [
            ToolDefinition(name="search_tool", type="function", description="Search", parameters=[])
        ]
        catalog3 = planner2._get_tool_catalog(available_tools=search_tools)
        assert catalog3.source == "semantic_search"


class TestToolCatalogToLLMFormat:
    """Test conversion to LLM function calling format"""
    
    def test_openai_format_conversion(self):
        """Tools should convert to OpenAI function calling format"""
        catalog = ToolCatalog(source="test", version="1.0")
        catalog.add_tool(ToolDefinition(
            name="test_function",
            type="function",
            description="A test function",
            parameters=[
                ToolParameter(name="input", type="string", description="Input data", required=True),
                ToolParameter(name="optional", type="integer", description="Optional param", required=False)
            ]
        ))
        
        llm_format = catalog.to_llm_format()
        assert len(llm_format) == 1
        
        tool_def = llm_format[0]
        assert tool_def["name"] == "test_function"
        assert tool_def["description"] == "A test function"
        assert "parameters" in tool_def
        assert "input" in tool_def["parameters"]["properties"]
        assert "optional" in tool_def["parameters"]["properties"]
        assert "input" in tool_def["parameters"]["required"]
        assert "optional" not in tool_def["parameters"]["required"]


class TestPlannerToolGrouping:
    """Test tool grouping by type in system prompt"""
    
    def test_tools_grouped_by_type(self):
        """System prompt should group tools by type (mcp, function, code_exec)"""
        catalog = ToolCatalog(source="test", version="1.0")
        
        # Add one of each type
        catalog.add_tool(ToolDefinition(
            name="mcp_tool",
            type="mcp",
            description="MCP tool",
            parameters=[]
        ))
        catalog.add_tool(ToolDefinition(
            name="func_tool",
            type="function",
            description="Function tool",
            parameters=[]
        ))
        catalog.add_tool(ToolDefinition(
            name="code_tool",
            type="code_exec",
            description="Code execution tool",
            parameters=[]
        ))
        
        planner = LargePlanner(provider="openai", tool_catalog=catalog)
        prompt = planner._build_system_prompt()
        
        # Prompt should organize tools
        assert "mcp_tools" in prompt.lower()
        assert "function_tools" in prompt.lower()
        assert "code_exec_tools" in prompt.lower()
