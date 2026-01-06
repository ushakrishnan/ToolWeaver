"""Direct test of JSON-RPC adapter to debug tool discovery."""
import asyncio
from orchestrator.tools.mcp_adapter import MCPJsonRpcHttpAdapterPlugin


async def test_jokes_adapter():
    """Test the JSON-RPC HTTP adapter with jokes server."""
    url = "https://jokesmcp-http-typescript.livelysmoke-c2b03354.centralus.azurecontainerapps.io/mcp"
    
    adapter = MCPJsonRpcHttpAdapterPlugin(url, timeout_s=30)
    
    print("Testing JSON-RPC HTTP Adapter...")
    print(f"URL: {url}\n")
    
    # Test raw request first
    print("=== Raw test ===")
    import aiohttp
    import json
    async with aiohttp.ClientSession() as session:
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        async with session.post(
            url,
            json=req,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as resp:
            content = await resp.text()
            print(f"Status: {resp.status}")
            print(f"Raw response: {content[:500]}")
            
            # Parse it
            for line in content.strip().split("\n"):
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    data = json.loads(data_str)
                    print(f"Parsed data: {json.dumps(data, indent=2)[:500]}")
    
    # Test discovery
    print("\n=== Discovering tools via adapter ===")
    try:
        # Manually test discovery logic
        import aiohttp
        connector = aiohttp.TCPConnector(ssl=True)
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            async with session.post(url, json=req, headers=headers) as resp:
                content = await resp.text()
                print(f"Response status: {resp.status}")
                
                # Parse SSE
                for line in content.strip().split("\n"):
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        data = json.loads(data_str)
                        print(f"Parsed JSON-RPC response has 'result': {'result' in data}")
                        
                        if "result" in data:
                            result = data["result"]
                            tools_list = result.get("tools", [])
                            print(f"Found {len(tools_list)} tools in result")
                            
                            from orchestrator.shared.models import ToolDefinition
                            
                            for i, tool_data in enumerate(tools_list[:2]):  # Just first 2
                                print(f"\nTool {i+1}: {tool_data['name']}")
                                print(f"  Description: {tool_data.get('description', '')}")
                                print(f"  InputSchema: {tool_data.get('inputSchema', {})}")
                                
                                try:
                                    td = ToolDefinition(
                                        name=tool_data["name"],
                                        description=tool_data.get("description", ""),
                                        params=tool_data.get("inputSchema", {"type": "object", "properties": {}}),
                                    )
                                    print(f"  ✓ Successfully created ToolDefinition")
                                except Exception as e:
                                    print(f"  ✗ Error creating ToolDefinition: {e}")
                                    import traceback
                                    traceback.print_exc()
        
        print("\n=== Now using adapter.discover() ===")
        tools = await adapter.discover()
        print(f"Discovered {len(tools)} tools:")
        for name, td in tools.items():
            print(f"  - {name}: {td.description}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test execution if we found tools
    if tools:
        first_tool = list(tools.keys())[0]
        print(f"\n=== Testing execution of '{first_tool}' ===")
        try:
            result = await adapter.execute(first_tool, {})
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_jokes_adapter())
