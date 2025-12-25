# REST API Overview

Expose ToolWeaver tools over HTTP using the FastAPI adapter.

- Base URL: `/api/v1` (configurable)
- Endpoints: list tools, get tool details, execute tool
- Why: let any service (browser, server, CLI) call your tools safely

## Start the server

Create a FastAPI app exposing your current tool catalog.

```python
from orchestrator import get_available_tools
from orchestrator.adapters import FastAPIAdapter

# Discover tools (decorators, YAML, templates)
tools = get_available_tools()

# Create REST API
adapter = FastAPIAdapter(tools, base_url="/api/v1")
app = adapter.create_app()

# Run with uvicorn:
# uvicorn main:app --reload --port 8000
```

- Tools are read-only endpoints except execution.
- Requests/Responses are simple JSON where parameters map to tool schemas.

## Endpoints

- List tools: GET `/api/v1/tools` — browse available tools
- Tool details: GET `/api/v1/tools/{tool_name}` — full schema & metadata
- Execute tool: POST `/api/v1/tools/{tool_name}/execute` — run with params

Continue to:
- [List Tools](list-tools.md)
- [Get Tool](get-tool.md)
- [Execute Tool](execute-tool.md)
- [MCP Adapter Endpoints](mcp-adapter.md)
