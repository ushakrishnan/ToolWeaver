# External MCP Adapter Example

This example shows how to connect to a third-party MCP server (e.g., sap-bdc-mcp-server). It includes a minimal adapter that supports WebSocket JSON-RPC and simple HTTP routes.

Prerequisites:
- A running MCP server endpoint (WebSocket or HTTP)
	- WebSocket JSON-RPC: `ws://host:port/path`
	- HTTP endpoints: `<base>/tools` (GET) and `<base>/execute` (POST)

What this example does now:
- Connects to the endpoint
- Discovers tools
- Optionally executes a tool (if provided via env)

Run (placeholder):
```bash
# Windows PowerShell
$env:EXTERNAL_MCP_ENDPOINT = "ws://localhost:3000/ws"
# Optional auth
$env:EXTERNAL_MCP_AUTH = "<token>"
# Optional execute
$env:EXTERNAL_MCP_TOOL = "get_expenses"
$env:EXTERNAL_MCP_PARAMS = '{"employee_id":"E123"}'
python examples/24-external-mcp-adapter/run_external_mcp_demo.py

# Linux/macOS
export EXTERNAL_MCP_ENDPOINT=ws://localhost:3000/ws
export EXTERNAL_MCP_AUTH=<token>
export EXTERNAL_MCP_TOOL=get_expenses
export EXTERNAL_MCP_PARAMS='{"employee_id":"E123"}'
python examples/24-external-mcp-adapter/run_external_mcp_demo.py
```

Notes:
- This adapter aims to be compatible with common MCP-style servers using either JSON-RPC over WebSocket, or simple REST endpoints.
- For packaging third-party servers as ToolWeaver plugins, see the community plugin template example.
