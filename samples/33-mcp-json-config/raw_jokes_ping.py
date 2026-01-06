"""Manual JSON-RPC over HTTP (SSE) ping to the jokes MCP server without ToolWeaver."""
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


def parse_first_json(text: str) -> dict[str, Any] | None:
    """Parse the first JSON object either from SSE data lines or plain body."""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            candidate = line[5:].strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return None
    return None


async def main() -> None:
    if not URL:
        print("❌ JOKES_MCP_URL not set (see .env.example)")
        return
    payload = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=payload, headers=HEADERS) as resp:
            body = await resp.text()
            print(f"Status: {resp.status}")
            print("Raw body:")
            print(body)
            parsed = parse_first_json(body)
            if parsed:
                print("\nParsed JSON:")
                print(json.dumps(parsed, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
