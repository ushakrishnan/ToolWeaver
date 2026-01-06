"""Test script for the jokes MCP server with JSON-RPC over HTTP with streaming."""
import asyncio
import json
import aiohttp


async def test_jokes_server():
    """Test the jokes MCP server using JSON-RPC over HTTP with SSE."""
    url = "https://jokesmcp-http-typescript.livelysmoke-c2b03354.centralus.azurecontainerapps.io/mcp"
    
    print("Testing jokes MCP server...")
    print(f"URL: {url}\n")
    
    # Test 1: Ping
    print("=== Test 1: Ping ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as resp:
            print(f"Status: {resp.status}")
            content = await resp.text()
            print(f"Response: {content}\n")
    
    # Test 2: List tools
    print("=== Test 2: List Tools (tools/list) ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as resp:
            print(f"Status: {resp.status}")
            content = await resp.text()
            print(f"Response:\n{content}\n")
            
            # Try to parse JSON-RPC response
            try:
                # Handle SSE format
                if "event:" in content or "data:" in content:
                    # Parse SSE
                    lines = content.strip().split("\n")
                    for line in lines:
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            data = json.loads(data_str)
                            print(f"Parsed: {json.dumps(data, indent=2)}")
                            if "result" in data and "tools" in data["result"]:
                                tools = data["result"]["tools"]
                                print(f"\n✓ Found {len(tools)} tools:")
                                for tool in tools:
                                    print(f"  - {tool['name']}: {tool['description']}")
                else:
                    data = json.loads(content)
                    print(f"Parsed: {json.dumps(data, indent=2)}")
            except Exception as e:
                print(f"Parse error: {e}")


if __name__ == "__main__":
    asyncio.run(test_jokes_server())
