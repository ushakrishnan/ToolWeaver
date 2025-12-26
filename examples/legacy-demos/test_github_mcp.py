"""
Test GitHub MCP Server Connection
Tests the GitHub MCP server integration using the remote hosted server.
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_github_mcp():
    """Test GitHub MCP server connection and basic operations"""
    
    # Get configuration from .env
    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    mcp_url = os.getenv("GITHUB_MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/")
    toolsets = os.getenv("GITHUB_MCP_TOOLSETS", "repos,issues,pull_requests")
    
    if not github_token:
        print("[X] GITHUB_TOKEN not found in .env file")
        print("Get token from: https://github.com/settings/tokens")
        return False
    
    if not github_owner:
        print("[X] GITHUB_OWNER not found in .env file")
        return False
    
    print(f"[OK] GitHub Token: {github_token[:8]}...{github_token[-4:]}")
    print(f"[OK] GitHub Owner: {github_owner}")
    print(f"[OK] MCP Server URL: {mcp_url}")
    print(f"[OK] Toolsets: {toolsets}")
    print()
    
    # Test 1: List available tools
    print("🔍 Test 1: Listing available MCP tools...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {github_token}",
                "X-MCP-Toolsets": toolsets,
                "Content-Type": "application/json"
            }
            
            # MCP protocol: tools/list request
            response = await client.post(
                f"{mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 1
                },
                headers=headers
            )
            
            if response.status_code == 200:
                # Parse Server-Sent Events (SSE) format
                import json
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        if 'result' in data:
                            tools = data['result'].get('tools', [])
                            print(f"[OK] Found {len(tools)} tools")
                            print(f"📋 Sample tools:")
                            for tool in tools[:5]:
                                print(f"   - {tool['name']}: {tool.get('description', 'N/A')[:80]}")
                            break
            else:
                print(f"[X] Failed to list tools: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test 2: Get user info
    print("🔍 Test 2: Getting GitHub user info...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {github_token}",
                "X-MCP-Toolsets": "users",
                "Content-Type": "application/json"
            }
            
            # Call get_user tool
            response = await client.post(
                f"{mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_user",
                        "arguments": {"username": github_owner}
                    },
                    "id": 2
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                print(f"[OK] User info retrieved successfully")
                print(f"📋 User: {result.get('content', [{}])[0].get('text', 'N/A')[:200]}...")
            else:
                print(f"⚠️  User info call: {response.status_code}")
                print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"⚠️  User info error: {e}")
    
    print()
    print("[OK] GitHub MCP Server connection test complete!")
    return True

if __name__ == "__main__":
    asyncio.run(test_github_mcp())
