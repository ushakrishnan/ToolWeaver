# 33 – MCP JSON Config Loader

Claude Desktop-compatible JSON configuration loader for registering and discovering MCP servers. This sample demonstrates how to load server definitions and fetch tool definitions from running MCP servers.

## Features

- **Claude-compatible format**: Uses the same `mcpServers` array structure as Claude Desktop
- **Multi-format support**: Works with array, map, and legacy list formats
- **Protocol auto-detection**: Automatically selects HTTP or WebSocket based on URL scheme
- **Environment variables**: Reference env vars in config via `${VAR_NAME}`
- **Flexible server discovery**: Get tool definitions from any MCP server endpoint

## Quick Start

This sample showcases **MCP with authentication** using Sample 34's GitHub MCP server:

```powershell
# 0. Install ToolWeaver
#   Option A: pip install toolweaver
#   Option B: python -m pip install -e .

# 1. Activate the virtual env
cd C:\ushak-projects\ToolWeaver
.\.venv\Scripts\Activate.ps1

# 2. Ensure .env has your GitHub token (samples/34-github-mcp-server/.env)
# Token is used by Sample 34 (server). Sample 33 just connects.

# 3. Terminal 1: Start the GitHub MCP server (Sample 34)
cd samples/34-github-mcp-server
python server.py
# Output: [OK] Starting GitHub MCP Server on http://localhost:9877

# 4. Terminal 2: Discover tools via JSON config (Sample 33)
cd samples/33-mcp-json-config
python run_mcp_json_demo.py --fetch
```

You should see:
```
Registered MCP servers:
  - github

Fetching tool definitions from servers...
  * github: 5 tools discovered

Total tools discovered: 5
```

## Prerequisites (Package-first)

Install the package first:

```powershell
# Option A: pip install toolweaver
pip install toolweaver

# Option B: local dev (editable)
python -m pip install -e .
```

## GitHub Token Setup

Create a Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens):

1. Click **Generate new token (classic)**
2. Add scopes: `repo`, `read:org`, `read:user`
3. Copy the token (starts with `ghp_`)
4. Set it in your environment:
   ```powershell
   $env:GITHUB_TOKEN="ghp_your_token_here"
   ```

## Integration with Sample 34 (Building Custom MCP Servers)

Sample 34 shows how to **build your own MCP server** when:
- You need custom tool logic
- Wrapping proprietary APIs
- Learning MCP server development
- No official integration exists

Use hosted APIs (like GitHub Copilot MCP) when available – simpler and maintained by the provider!

## Config Format

The config uses **Claude Desktop-compatible array format**:

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
      "url": "https://jokesmcp-http-typescript.livelysmoke-c2b03354.centralus.azurecontainerapps.io/mcp",
      "protocol": "json_rpc",
      "timeout_s": 30,
      "verify_ssl": true
    }
  ]
}
```

### Protocol Types

- `http`: REST endpoints (GET /tools, POST /execute)
- `websocket`: WebSocket JSON-RPC (`ws://` or `wss://` URLs)
- `json_rpc`: JSON-RPC over HTTP with SSE responses (e.g., streamable MCP servers)

The jokes server demonstrates a **no-auth streamable MCP server** that uses JSON-RPC over HTTP with Server-Sent Events (SSE). It provides 7 tools including Chuck Norris jokes, dad jokes, and weather data.

**Supported formats:**
- **Array** (modern Claude): `"mcpServers": [ { "name": "...", "url": "..." } ]`
- **Map** (legacy Claude): `"mcpServers": { "name": { "url": "..." } }`
- **List** (ToolWeaver): `"servers": [ { "name": "...", "url": "..." } ]`

**Config fields:**
- `name` - Server identifier (required)
- `url` - Server endpoint (http://, https://, ws://, wss://)
- `protocol` - `http`, `sse`, or `websocket` (auto-detected from URL if omitted)
- `env` - Environment variables (for documentation; actual auth via headers)
- `headers` - Custom HTTP headers (supports `${ENV_VAR}` substitution)
- `timeout_s` - Request timeout in seconds (default: 15)
- `verify_ssl` - SSL verification (default: true)

## Usage

### Config Location

Loader checks these paths automatically:
1. Explicit path via `--config` flag
2. `MCP_SERVERS_FILE` environment variable
3. `CLAUDE_SERVERS_FILE` environment variable
4. `~/.claude/config.json` (Claude Desktop config - Windows)
5. `samples/33-mcp-json-config/servers.json` (sample default)

### Dry Run (No Network)

Lists configured servers without calling them:

```powershell
python samples/33-mcp-json-config/run_mcp_json_demo.py
```

Output:
```
Registered MCP servers:
  - github
  - jokes
```

### Fetch Tools

Discovers tools from each server:

```powershell
python samples/33-mcp-json-config/run_mcp_json_demo.py --fetch
```

Output:
```
Fetching tool definitions from servers...
  * jokes: 7 tools discovered

Total tools discovered across servers: 7
```

### Test Jokes Tools

Execute tools from the jokes server:

```powershell
python samples/33-mcp-json-config/test_jokes_tools.py
```

This will call various joke and weather tools demonstrating the JSON-RPC HTTP protocol.

### Custom Config

```powershell
python samples/33-mcp-json-config/run_mcp_json_demo.py --config /path/to/config.json --fetch
```

### Use Your Claude Desktop Config

Windows:
```powershell
# Copy Claude's config to test with ToolWeaver
Copy-Item "$env:USERPROFILE\.claude\config.json" samples/33-mcp-json-config/claude-config.json
python samples/33-mcp-json-config/run_mcp_json_demo.py --config samples/33-mcp-json-config/claude-config.json --fetch
```

### Hosted vs local MCP

Claude often points to hosted MCP servers with tokens in config. Here, GitHub lacks a public MCP endpoint, so Sample 34 runs locally and Sample 33 connects to it. Swap `url` to a hosted MCP server when available; the config loader already supports that pattern.
