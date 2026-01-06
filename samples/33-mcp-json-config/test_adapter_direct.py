"""Adapter-only direct test for JSON-RPC over HTTP with SSE."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from orchestrator.tools.mcp_adapter import MCPJsonRpcHttpAdapterPlugin


async def main() -> None:
    # Load env from this sample folder
    load_dotenv(Path(__file__).parent / ".env")
    url = os.getenv("JOKES_MCP_URL")
    if not url:
        print("❌ JOKES_MCP_URL not set (see .env.example)")
        return
    adapter = MCPJsonRpcHttpAdapterPlugin(url, timeout_s=30)

    print("Testing JSON-RPC HTTP Adapter...")
    print(f"URL: {url}\n")

    print("=== Discovering tools via adapter ===")
    tools = await adapter.discover()
    print(f"Discovered {len(tools)} tools:")
    for name, td in tools.items():
        print(f"  - {name}: {td.description}")

    if tools:
        first_tool = list(tools.keys())[0]
        print(f"\n=== Testing execution of '{first_tool}' ===")
        result = await adapter.execute(first_tool, {})
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
