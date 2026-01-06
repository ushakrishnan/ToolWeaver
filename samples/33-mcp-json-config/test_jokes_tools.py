"""Test calling tools from the jokes MCP server."""
import asyncio
from orchestrator.tools.mcp_config_loader import load_mcp_servers_from_json
from pathlib import Path


async def main():
    """Load config and test calling a joke tool."""
    config_path = Path(__file__).parent / "servers.json"
    
    print("Loading MCP servers from config...")
    adapters = load_mcp_servers_from_json(str(config_path))
    
    if "jokes" not in adapters:
        print("❌ jokes server not registered")
        return
    
    jokes_adapter = adapters["jokes"]
    print(f"✓ jokes adapter registered\n")
    
    # Discover tools
    print("Discovering tools...")
    tools = await jokes_adapter.discover()
    print(f"✓ Discovered {len(tools)} tools:")
    for name in tools.keys():
        print(f"  - {name}")
    
    # Test 1: Get a Chuck Norris joke (no params)
    print("\n=== Test 1: get-chuck-joke (no params) ===")
    try:
        result = await jokes_adapter.execute("get-chuck-joke", {})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get Chuck categories
    print("\n=== Test 2: get-chuck-categories ===")
    try:
        result = await jokes_adapter.execute("get-chuck-categories", {})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get a dad joke
    print("\n=== Test 3: get-dad-joke ===")
    try:
        result = await jokes_adapter.execute("get-dad-joke", {})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get weather for a location
    print("\n=== Test 4: get-current-weather (with params) ===")
    try:
        result = await jokes_adapter.execute("get-current-weather", {"location": "Seattle"})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
