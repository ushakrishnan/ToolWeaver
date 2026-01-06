"""Adapter-only demo for the jokes MCP server."""
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from orchestrator.tools.mcp_config_loader import load_mcp_servers_from_json


async def main() -> None:
    # Load env (JOKES_MCP_URL used by servers.json via ${...} substitution)
    load_dotenv(Path(__file__).parent / ".env")
    config_path = Path(__file__).parent / "servers.json"
    adapters = load_mcp_servers_from_json(str(config_path))
    jokes = adapters.get("jokes")
    if not jokes:
        print("❌ jokes adapter not found")
        return

    print("=== Adapter: Discover tools ===")
    tools = await jokes.discover()
    print(f"✓ Found {len(tools)} tools: {list(tools.keys())}")

    print("\n=== Adapter: Call get-chuck-joke ===")
    result = await jokes.execute("get-chuck-joke", {})
    print(f"Joke: {result}")


if __name__ == "__main__":
    asyncio.run(main())
