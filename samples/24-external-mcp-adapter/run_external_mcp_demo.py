import asyncio
import json
import os
from typing import Any

from external_mcp_adapter import AdapterConfig, ExternalMCPAdapter

# Placeholder demo to show intended usage. The real adapter will be provided
# by MCPToolTemplate in Phase 1.

ENDPOINT = os.getenv("EXTERNAL_MCP_ENDPOINT")

async def main():
    if not ENDPOINT:
        print("Set EXTERNAL_MCP_ENDPOINT to your MCP server endpoint (ws/http)")
        return

    token = os.getenv("EXTERNAL_MCP_AUTH")
    tool_name = os.getenv("EXTERNAL_MCP_TOOL")
    raw_params = os.getenv("EXTERNAL_MCP_PARAMS", "{}")
    try:
        params: dict[str, Any] = json.loads(raw_params)
    except Exception:
        params = {}

    print(f"Connecting to external MCP server at: {ENDPOINT}")
    cfg = AdapterConfig(endpoint=ENDPOINT, timeout=20.0, auth_token=token)
    adapter = ExternalMCPAdapter(cfg)

    tools = await adapter.discover_tools()
    print("Discovered tools (truncated to 5):")
    for t in tools[:5]:
        print(" -", t.get("name") or t)

    if tool_name:
        print(f"\nExecuting tool: {tool_name} with params={params}")
        result = await adapter.execute(tool_name, params)
        print("Result:", result)
    else:
        print("\nSet EXTERNAL_MCP_TOOL to execute a tool, e.g.: get_expenses")

if __name__ == "__main__":
    asyncio.run(main())
