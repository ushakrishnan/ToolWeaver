# 33 – MCP JSON Config Loader

This sample provides two paths:
- **Without ToolWeaver (manual)**: raw `aiohttp` + JSON-RPC over HTTP + SSE parsing to talk to the jokes server.
- **With ToolWeaver + adapter (recommended)**: load config, auto-pick protocol, discover tools, and call them via adapters—no HTTP plumbing.

## Quick start (with ToolWeaver + adapter)
```powershell
# Install ToolWeaver
pip install toolweaver
# or local editable: python -m pip install -e .

# Discover and fetch tools from servers.json
python samples/33-mcp-json-config/run_mcp_json_demo.py --fetch

# Call tools from the jokes server via adapter
python samples/33-mcp-json-config/test_jokes_tools.py
```
What happens: the config loader reads `servers.json`, registers adapters, discovers 7 tools from the jokes server, and executes them through the adapter API (`discover()`, `execute()`), without manual HTTP/SSE handling.

## Manual path (without ToolWeaver)
Run the raw scripts to see the underlying protocol exchange:
```powershell
python samples/33-mcp-json-config/raw_jokes_ping.py          # JSON-RPC ping
python samples/33-mcp-json-config/raw_jokes_list_tools.py    # tools/list
python samples/33-mcp-json-config/raw_jokes_call_tool.py     # tools/call get-current-weather
```
These scripts build JSON-RPC payloads, set SSE-friendly headers, and parse SSE/JSON by hand.

## What ToolWeaver handles for you
- Registers MCP servers from Claude-compatible config (`mcpServers` array/map/list)
- Chooses protocol (`http`, `websocket`, `json_rpc`) and wires the right adapter
- Manages JSON-RPC framing, request IDs, headers (incl. SSE `Accept`), timeouts, SSE parsing
- Normalizes tool schemas into `ToolDefinition` objects

## Config format (Claude-compatible)
```json
{
  "mcpServers": [
    {
      "name": "github",
      "url": "http://localhost:9877",
      "protocol": "http",
      "timeout_s": 30,
      "verify_ssl": true
    },
    {
      "name": "jokes",
      "url": "https://xxx.centralus.azurecontainerapps.io/mcp",
      "protocol": "json_rpc",
      "timeout_s": 30,
      "verify_ssl": true
    }
  ]
}
```
Supported forms: array (above), map (`"mcpServers": { "name": { ... } }`), list (`"servers": [ ... ]`).

Protocols: `http` (REST), `websocket` (JSON-RPC over WS), `json_rpc` (JSON-RPC over HTTP with SSE responses).

Key fields: `name`, `url`, `protocol` (auto-detected if omitted), `headers`, `timeout_s`, `verify_ssl`. Env var substitution works in headers.

## Config location search order
1) `--config` CLI flag
2) `MCP_SERVERS_FILE` env var
3) `CLAUDE_SERVERS_FILE` env var
4) `~/.claude/config.json`
5) `samples/33-mcp-json-config/servers.json` (sample default)

## Scripts in this sample
- Manual path: `raw_jokes_ping.py`, `raw_jokes_list_tools.py`, `raw_jokes_call_tool.py`
- Adapter path: `run_mcp_json_demo.py` (list/fetch) and `test_jokes_tools.py` (execute tools)

## When to use what
- Use **ToolWeaver adapters** for real integrations: fewer moving parts, consistent schemas, protocol handled for you.
- Use the **manual path** only for protocol debugging or learning the underlying JSON-RPC over HTTP + SSE exchange.
