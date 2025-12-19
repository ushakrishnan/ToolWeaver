# Using External MCP Servers

ToolWeaver can integrate with external MCP servers (e.g., sap-bdc-mcp-server) via an adapter.

Planned options:
- Template-based adapter (Phase 1) in `MCPToolTemplate` that connects to ws/http endpoints
- Plugin wrapper to register third-party MCP servers as ToolWeaver tools

Basic steps:
1) Set endpoint via env (e.g., `EXTERNAL_MCP_ENDPOINT=ws://localhost:3000/ws`).
2) Use the adapter to discover tools (handshake → tool schema normalization).
3) Execute tools via adapter with timeout/retry; map errors to ToolWeaver error types.

See example: `examples/24-external-mcp-adapter/`.
