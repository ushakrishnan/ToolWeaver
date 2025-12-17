"""
Example 3a: Test GitHub MCP Connection

Tests connection to GitHub's remote MCP server and lists available tools.
"""

import asyncio
import os
import httpx
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def test_github_connection():
    """Test GitHub MCP server connection."""
    
    # Get credentials
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_OWNER')
    mcp_url = os.getenv('GITHUB_MCP_SERVER_URL', 'https://api.githubcopilot.com/mcp/')
    toolsets = os.getenv('GITHUB_MCP_TOOLSETS', 'repos,issues,pull_requests')
    
    if not token:
        print("❌ GITHUB_TOKEN not set in .env")
        print("   Get token from: https://github.com/settings/tokens")
        return
    
    if not owner:
        print("❌ GITHUB_OWNER not set in .env")
        return
    
    print("=" * 60)
    print("GitHub MCP Connection Test")
    print("=" * 60)
    print()
    print(f"✅ Token: {token[:8]}...{token[-4:]}")
    print(f"✅ Owner: {owner}")
    print(f"✅ Server: {mcp_url}")
    print(f"✅ Toolsets: {toolsets}")
    print()
    
    # Test connection
    print("🔍 Testing connection...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                'Authorization': f'Bearer {token}',
                'X-MCP-Toolsets': toolsets,
                'Content-Type': 'application/json'
            }
            
            response = await client.post(
                mcp_url,
                json={
                    'jsonrpc': '2.0',
                    'method': 'tools/list',
                    'params': {},
                    'id': 1
                },
                headers=headers
            )
            
            if response.status_code == 200:
                # Parse SSE format
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'result' in data:
                            tools = data['result'].get('tools', [])
                            print(f"✅ Connected! Found {len(tools)} tools")
                            print()
                            print("📋 Available Tools (showing first 10):")
                            for tool in tools[:10]:
                                name = tool['name']
                                desc = tool.get('description', 'N/A')[:60]
                                print(f"   - {name}")
                                print(f"     {desc}...")
                            
                            if len(tools) > 10:
                                print(f"   ... and {len(tools) - 10} more")
                            
                            print()
                            print("✅ GitHub MCP connection successful!")
                            return
            else:
                print(f"❌ Connection failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_github_connection())
