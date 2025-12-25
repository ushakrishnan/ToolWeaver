# External Registry Discovery (MCP)

ToolWeaver can optionally discover tools from an external MCP-style registry. This extends built-in discovery (MCP servers, code-exec, local tools) with a simple JSON registry.

## Enable

Windows PowerShell:

```powershell
$env:MCP_REGISTRY_URL = "http://localhost:8090/registry.json"
```

- When set, discovery loads entries from the URL on startup.
- Not set → registry discovery is skipped.

## Registry Format (minimal)

```json
{
  "tools": [
    {
      "name": "fetch_data",
      "description": "Retrieve data from a source",
      "schema": {
        "type": "object",
        "properties": {
          "url": {"type": "string"}
        },
        "required": ["url"]
      },
      "endpoint": "mcp://local/fetch"
    }
  ]
}
```

- `name`: Unique tool identifier
- `schema`: JSON Schema for inputs
- `endpoint`: Registry-side routing hint (opaque to clients)

## Usage Notes
- Works alongside built-in discovery; no overrides unless names collide
- Favors deterministic, typed tool calls via provided schema
- Ideal for org-curated tool catalogs during development

## Security
- Only use trusted registry URLs
- Validate schemas and sanitize input in tool backends
- Prefer HTTPS for remote registries

## Source
- Discovery hook: orchestrator/tools/tool_discovery.py (MCPRegistryDiscoverer)
- Minimal workers: orchestrator/dispatch/workers.py
- MCP client map: orchestrator/infra/mcp_client.py
