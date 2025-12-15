"""
Test the tool discovery system
"""

import asyncio
from orchestrator.mcp_client import MCPClientShim
from orchestrator.tool_discovery import discover_tools
from orchestrator import workers, functions


async def main():
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
    from orchestrator.tool_discovery import ToolDiscoveryOrchestrator
    orchestrator = ToolDiscoveryOrchestrator()
    print(f"   Cache file: {orchestrator.cache_file}")
    print(f"   Cache exists: {orchestrator.cache_file.exists()}")
    if orchestrator.cache_file.exists():
        import os
        size_kb = os.path.getsize(orchestrator.cache_file) / 1024
        print(f"   Cache size: {size_kb:.1f} KB")
    
    print("\n" + "=" * 60)
    print("Discovery test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
