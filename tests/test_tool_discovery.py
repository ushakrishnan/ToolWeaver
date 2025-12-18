"""
Test the tool discovery system
"""

import pytest
import asyncio
from orchestrator.infra.mcp_client import MCPClientShim
from orchestrator.tools.tool_discovery import discover_tools, ToolDiscoveryOrchestrator
from orchestrator.dispatch import workers
from orchestrator.dispatch import functions


@pytest.mark.asyncio
async def test_tool_discovery_basic():
    print("=" * 60)
    print("ToolWeaver - Tool Discovery Test")
    print("=" * 60)
    
    # Initialize MCP client
    mcp_client = MCPClientShim()
    
    print("\n1. Discovering tools...")
    print(f"   - MCP tools from MCPClientShim")
    print(f"   - Functions from 'workers' module")
    print(f"   - Functions from 'functions' module")
    print(f"   - Code execution capability")
    
    # Discover all tools (will use cache if available)
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    print(f"\n2. Discovery Results:")
    print(f"   Total tools: {len(catalog.tools)}")
    print(f"   Discovered at: {catalog.discovered_at}")
    
    # Show metrics if available
    if "discovery_metrics" in catalog.metadata:
        metrics = catalog.metadata["discovery_metrics"]
        print(f"   Duration: {metrics['discovery_duration_ms']:.0f}ms")
        print(f"   Sources: {metrics['sources']}")
        if metrics.get('errors'):
            print(f"   Errors: {len(metrics['errors'])}")
    
    print(f"\n3. Tool Breakdown by Type:")
    for tool_type in ["mcp", "function", "code_exec"]:
        tools = catalog.get_by_type(tool_type)
        print(f"   {tool_type}: {len(tools)} tools")
    
    print(f"\n4. Tool Catalog:")
    for i, (name, tool) in enumerate(catalog.tools.items(), 1):
        print(f"\n   [{i}] {name}")
        print(f"       Type: {tool.type}")
        print(f"       Description: {tool.description[:80]}...")
        print(f"       Parameters: {len(tool.parameters)}")
        print(f"       Source: {tool.source}")
    
    print(f"\n5. LLM Format Conversion Test:")
    llm_tools = catalog.to_llm_format()
    print(f"   Converted {len(llm_tools)} tools to LLM format")
    
    # Show example
    if llm_tools:
        example_tool = llm_tools[0]
        print(f"\n   Example (first tool):")
        print(f"   Name: {example_tool['name']}")
        print(f"   Description: {example_tool['description'][:60]}...")
        print(f"   Required params: {example_tool['parameters']['required']}")
    
    print(f"\n6. Cache Information:")
    from orchestrator.tools.tool_discovery import ToolDiscoveryOrchestrator
    orchestrator = ToolDiscoveryOrchestrator()
    print(f"   Cache file: {orchestrator.cache_file}")
    print(f"   Cache exists: {orchestrator.cache_file.exists()}")
    if orchestrator.cache_file.exists():
        import os
        size_kb = os.path.getsize(orchestrator.cache_file) / 1024
        print(f"   Cache size: {size_kb:.1f} KB")
    
    print("\n" + "=" * 60)
    
    # Assert some basic expectations
    assert len(catalog.tools) > 0, "Should discover at least some tools"
    assert catalog.discovered_at is not None
    
    # Should have multiple types
    mcp_tools = catalog.get_by_type("mcp")
    function_tools = catalog.get_by_type("function")
    assert len(mcp_tools) > 0 or len(function_tools) > 0, "Should have at least MCP or function tools"


@pytest.mark.asyncio
async def test_tool_discovery_caching():
    """Test that tool discovery uses caching"""
    print("\n" + "=" * 60)
    print("Testing Tool Discovery Caching")
    print("=" * 60)
    
    mcp_client = MCPClientShim()
    
    # First discovery (will cache)
    print("\n1. First discovery (fresh)...")
    catalog1 = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    # Second discovery (should use cache)
    print("\n2. Second discovery (should use cache)...")
    catalog2 = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    print(f"\n   Catalog 1: {len(catalog1.tools)} tools")
    print(f"   Catalog 2: {len(catalog2.tools)} tools")
    
    assert len(catalog1.tools) == len(catalog2.tools), "Cached catalog should have same number of tools"


@pytest.mark.asyncio  
async def test_tool_discovery_force_refresh():
    """Test forcing fresh discovery without cache"""
    print("\n" + "=" * 60)
    print("Testing Force Refresh")
    print("=" * 60)
    
    mcp_client = MCPClientShim()
    
    # Force fresh discovery
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=False  # Force refresh
    )
    
    print(f"\n   Fresh catalog: {len(catalog.tools)} tools")
    
    assert len(catalog.tools) > 0


@pytest.mark.asyncio
async def test_tool_discovery_llm_format():
    """Test conversion to LLM format"""
    print("\n" + "=" * 60)
    print("Testing LLM Format Conversion")
    print("=" * 60)
    
    mcp_client = MCPClientShim()
    
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    llm_tools = catalog.to_llm_format()
    
    print(f"\n   Original tools: {len(catalog.tools)}")
    print(f"   LLM format tools: {len(llm_tools)}")
    
    assert len(llm_tools) > 0, "Should convert at least some tools"
    
    # Check format
    if llm_tools:
        tool = llm_tools[0]
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        print(f"\n   Example tool: {tool['name']}")


def test_tool_discovery_orchestrator():
    """Test ToolDiscoveryOrchestrator initialization"""
    orchestrator = ToolDiscoveryOrchestrator()
    
    assert orchestrator.cache_file is not None
    print(f"\n   Cache file: {orchestrator.cache_file}")
    print(f"   Cache exists: {orchestrator.cache_file.exists()}")


@pytest.mark.asyncio
async def test_tool_discovery_by_type():
    """Test filtering tools by type"""
    mcp_client = MCPClientShim()
    
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    # Test getting tools by type
    mcp_tools = catalog.get_by_type("mcp")
    function_tools = catalog.get_by_type("function")
    code_tools = catalog.get_by_type("code_exec")
    
    print(f"\n   MCP tools: {len(mcp_tools)}")
    print(f"   Function tools: {len(function_tools)}")
    print(f"   Code exec tools: {len(code_tools)}")
    
    total = len(mcp_tools) + len(function_tools) + len(code_tools)
    assert total == len(catalog.tools), "All tools should be categorized"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
