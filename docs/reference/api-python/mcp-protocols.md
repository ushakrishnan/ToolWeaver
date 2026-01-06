# MCP Protocol Support

ToolWeaver supports three MCP (Model Context Protocol) adapter protocols for connecting to external MCP servers.

## Supported Protocols

### 1. HTTP REST (`protocol: "http"`)

Standard REST endpoints with JSON responses.

**Expected Server Endpoints:**
- `GET /tools` → Returns array of tool definitions
- `POST /execute` → Executes a tool with `{name, params}`

**Use Case:** Simple MCP servers with synchronous tool execution.

**Example Config:**
```json
{
  "name": "github",
  "url": "http://localhost:9877",
  "protocol": "http",
  "timeout_s": 30
}
```

**Implementation:** `MCPHttpAdapterPlugin` in [orchestrator/tools/mcp_adapter.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/mcp_adapter.py)

---

### 2. WebSocket JSON-RPC (`protocol: "websocket"`)

JSON-RPC 2.0 over WebSocket connections.

**Expected Server Behavior:**
- Connect to `ws://` or `wss://` URL
- Send `{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}` to discover tools
- Send `{"jsonrpc": "2.0", "id": X, "method": "tools/call", "params": {"name": "...", "arguments": {...}}}` to execute

**Use Case:** Bidirectional communication, persistent connections, real-time updates.

**Example Config:**
```json
{
  "name": "realtime-mcp",
  "url": "wss://example.com/mcp",
  "protocol": "websocket",
  "timeout_s": 30
}
```

**Implementation:** `MCPWebSocketAdapterPlugin` in [orchestrator/tools/mcp_adapter.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/mcp_adapter.py)

---

### 3. JSON-RPC over HTTP with SSE (`protocol: "json_rpc"`)

JSON-RPC 2.0 over HTTP with Server-Sent Events (SSE) streaming responses.

**Expected Server Behavior:**
- POST to server URL with JSON-RPC request
- Requires Accept header: `application/json, text/event-stream`
- Response format:
  ```
  event: message
  data: {"jsonrpc": "2.0", "id": 1, "result": {...}}
  ```

**Use Case:** Streamable MCP servers that support both request-response and streaming patterns.

**Example Config:**
```json
{
  "name": "jokes",
  "url": "https://jokesmcp-http-typescript.livelysmoke-c2b03354.centralus.azurecontainerapps.io/mcp",
  "protocol": "json_rpc",
  "timeout_s": 30
}
```

**Implementation:** `MCPJsonRpcHttpAdapterPlugin` in [orchestrator/tools/mcp_adapter.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/mcp_adapter.py)

**Live Demo:** See [Sample 33](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/33-mcp-json-config) for a working example with a jokes MCP server (7 tools: Chuck Norris jokes, dad jokes, weather data).

---

## Protocol Auto-Detection

The config loader automatically detects protocol from URL:
- URLs starting with `ws://` or `wss://` → `websocket`
- All others default to `http`
- Explicit `protocol` field overrides auto-detection

**Example:**
```json
{
  "name": "auto-ws",
  "url": "wss://example.com/mcp"
  // protocol auto-detected as "websocket"
}
```

---

## Configuration Reference

All protocols support these common fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Server identifier |
| `url` | string | Yes | - | Server endpoint URL |
| `protocol` | string | No | auto | `http`, `websocket`, or `json_rpc` |
| `timeout_s` | int | No | 15 (http/ws)<br>30 (json_rpc) | Request timeout in seconds |
| `verify_ssl` | bool | No | true | Enable SSL certificate verification |
| `headers` | object | No | {} | Custom HTTP headers (supports `${ENV_VAR}`) |

---

## Examples

### Working Samples

1. **Sample 33** - MCP Config Loader
   - Location: [samples/33-mcp-json-config/](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/33-mcp-json-config)
   - Demonstrates: HTTP and JSON-RPC protocols
   - Includes: GitHub MCP server (local) and jokes MCP server (hosted)

2. **Sample 34** - Custom GitHub MCP Server
   - Location: [samples/34-github-mcp-server/](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/34-github-mcp-server)
   - Demonstrates: Building a custom MCP server with HTTP protocol
   - Tools: 5 GitHub API tools (list repos, create issue, etc.)

### Testing Protocol Support

```python
from orchestrator.tools.mcp_config_loader import load_mcp_servers_from_json

# Load servers from config
adapters = load_mcp_servers_from_json("servers.json")

# Discover tools from all servers
for name, adapter in adapters.items():
    tools = await adapter.discover()
    print(f"{name}: {len(tools)} tools")
    
    # Execute a tool
    if tools:
        first_tool = list(tools.keys())[0]
        result = await adapter.execute(first_tool, {})
        print(f"Result: {result}")
```

---

## See Also

- [MCP Config Loader](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/mcp_config_loader.py) - Configuration parser
- [MCP Adapters](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/mcp_adapter.py) - Protocol implementations
- [Sample 33 README](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/33-mcp-json-config/README.md) - Full usage guide
