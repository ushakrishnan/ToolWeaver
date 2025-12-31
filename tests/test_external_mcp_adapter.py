# Load the example adapter module directly from file so it remains an example artifact
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from aiohttp import web

EXAMPLE_DIR = Path(__file__).parent.parent / "examples" / "24-external-mcp-adapter"
ADAPTER_PATH = EXAMPLE_DIR / "external_mcp_adapter.py"

spec = importlib.util.spec_from_file_location("external_mcp_adapter", ADAPTER_PATH.as_posix())
assert spec is not None and spec.loader is not None
adapter_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter_module
spec.loader.exec_module(adapter_module)

AdapterConfig = adapter_module.AdapterConfig
ExternalMCPAdapter = adapter_module.ExternalMCPAdapter


@pytest.mark.asyncio
async def test_external_mcp_adapter_http_mode(unused_tcp_port_factory):
    # Minimal in-process HTTP server implementing /tools and /execute
    tools: list[dict[str, Any]] = [
        {"name": "ping", "description": "Ping tool"},
    ]

    async def tools_handler(request: web.Request) -> web.Response:
        return web.json_response({"tools": tools})

    async def execute_handler(request: web.Request) -> web.Response:
        payload = await request.json()
        return web.json_response({"echo": payload})

    app = web.Application()
    app.router.add_get("/tools", tools_handler)
    app.router.add_post("/execute", execute_handler)

    port = unused_tcp_port_factory()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()

    try:
        endpoint = f"http://127.0.0.1:{port}"
        cfg = AdapterConfig(endpoint=endpoint, timeout=5.0)
        adapter = ExternalMCPAdapter(cfg)

        discovered = await adapter.discover_tools()
        assert isinstance(discovered, list) and discovered and discovered[0]["name"] == "ping"

        result = await adapter.execute("ping", {"msg": "hi"})
        assert result.get("echo", {}).get("name") == "ping"
        assert result.get("echo", {}).get("params", {}).get("msg") == "hi"
    finally:
        await runner.cleanup()
