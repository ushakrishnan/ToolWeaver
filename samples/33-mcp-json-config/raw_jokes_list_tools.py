"""Manually list tools from the jokes MCP server via JSON-RPC over HTTP (SSE)."""
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
URL = os.getenv("JOKES_MCP_URL")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def parse_sse_tools(text: str) -> list[dict[str, Any]]:
    """Extract tools list from an SSE or plain JSON response."""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            payload = line[5:].strip()
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and "result" in data and isinstance(data.get("result"), dict):
                tools = data["result"].get("tools")
                if isinstance(tools, list):
                    return [t for t in tools if isinstance(t, dict)]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "result" in data and isinstance(data.get("result"), dict):
        tools = data["result"].get("tools")
        if isinstance(tools, list):
            return [t for t in tools if isinstance(t, dict)]
    return []


async def main() -> None:
    if not URL:
        print("❌ JOKES_MCP_URL not set (see .env.example)")
        return
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=payload, headers=HEADERS) as resp:
            body = await resp.text()
            print(f"Status: {resp.status}")
            print("Raw body:\n" + body)
            tools = parse_sse_tools(body)
            if tools:
                print(f"\nParsed {len(tools)} tools:")
                for tool in tools:
                    print(f"- {tool.get('name')}: {tool.get('description')}")
            else:
                print("\nNo tools parsed.")


if __name__ == "__main__":
    asyncio.run(main())
