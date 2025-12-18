"""
Demo: Auto-discover tools and generate a plan

This demonstrates Phase 2 functionality:
- Automatic tool discovery from MCP, functions, and code execution
- No need to manually register tools
- Cached for fast repeat usage
"""

import asyncio
from orchestrator.planner import LargePlanner


async def main():
    print("=" * 70)
    print("ToolWeaver - Auto-Discovery Demo")
    print("=" * 70)
    
    # Step 1: Discover tools first
    print("\n1. Discovering tools...")
    print("   (Finding MCP, functions, and code execution capabilities)")
    
    from orchestrator.mcp_client import MCPClientShim
    from orchestrator.dispatch import functions
    from orchestrator.tool_discovery import discover_tools
    
    mcp_client = MCPClientShim()
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    
    print(f"   ✓ Discovered {len(catalog.tools)} tools")
    
    # Step 2: Initialize planner with discovered catalog
    print("\n2. Initializing LargePlanner with discovered catalog...")
    async with LargePlanner(tool_catalog=catalog) as planner:
        # Generate a plan that uses multiple discovered tools
        user_request = """
        I have a receipt at https://raw.githubusercontent.com/microsoft/Orb/main/samples/receipt.jpg
        
        Please:
        1. Extract text from the receipt
        2. Parse the line items
        3. Calculate the total
        4. Apply a 10% discount
        5. Categorize the items
        """
        
        print(f"\n3. User Request:")
        print(f"   {user_request.strip()}")
        
        print(f"\n4. Generating plan...")
        plan = await planner.generate_plan(user_request)
        
        print(f"\n5. Generated Plan:")
        print(f"   Total steps: {len(plan.get('steps', []))}")
        
        for i, step in enumerate(plan.get("steps", []), 1):
            print(f"\n   Step {i}:")
            print(f"     Type: {step.get('type')}")
            print(f"     Tool: {step.get('tool_name', 'N/A')}")
            if step.get('description'):
                print(f"     Description: {step['description'][:60]}...")
            if step.get('depends_on'):
                print(f"     Depends on: {step['depends_on']}")
        
        print(f"\n6. Plan Summary:")
        tool_types = {}
        for step in plan.get("steps", []):
            step_type = step.get("type", "unknown")
            tool_types[step_type] = tool_types.get(step_type, 0) + 1
        
        for tool_type, count in tool_types.items():
            print(f"   {tool_type}: {count} steps")
        
        print("\n" + "=" * 70)
        print("Success! Auto-discovery enabled seamless planning")
        print("=" * 70)
        print("\nNOTE: Tool discovery used cache from test_discovery.py")
        print("      Run again with cache invalidation to re-discover")


if __name__ == "__main__":
    asyncio.run(main())
