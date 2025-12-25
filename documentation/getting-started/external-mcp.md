# Using External MCP Servers

ToolWeaver can integrate with external MCP servers (e.g., sap-bdc-mcp-server) via an HTTP adapter or future WS adapter.

## HTTP Adapter (Available)
Use `register_mcp_http_adapter()` to register a plugin backed by a remote server:
```python
from orchestrator.tools.mcp_adapter import register_mcp_http_adapter
import asyncio

plugin = register_mcp_http_adapter("external_mcp_http", "http://localhost:9876")

async def demo():
	tools = await plugin.discover()  # Dict[str, ToolDefinition]
	result = await plugin.execute("process_user", {"user": {"id": "u1"}})
	print(result)

asyncio.run(demo())
```

Server contract:
- `GET /tools` → returns list of ToolDefinition-like dicts (supports nested `input_schema`/`output_schema`)
- `POST /execute` with JSON `{ name: str, params: dict }` → returns result JSON

See the mock example: `examples/24-external-mcp-adapter/server.py`.

## Roadmap
- WS/SSE adapter variants
- Template-based MCP integration (`MCPToolTemplate`)
- Error mapping and retry policies
