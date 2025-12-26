# Decorators

Why: Fastest way to convert Python functions into ToolWeaver tools. Decorators infer parameter schemas from type hints and register callable endpoints for planners, APIs, and CLI.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `tool`, `mcp_tool`, `a2a_agent`

---

## `mcp_tool()`

- What: Register a tool following MCP-style semantics with structured parameters and async execution.
- When: Use for tools you want discoverable and callable across adapters (FastAPI, CLI, planners).
- How: Decorate an `async` function with type hints; provide metadata like `domain`, `description`.

Parameters (common):
- `domain`: short namespace grouping (e.g., "github", "finance")
- `description`: human-friendly description
- Optional metadata via keyword args depending on implementation

Returns: A callable tool object; the decorated function is registered in the catalog.

Example:
```python
from orchestrator import mcp_tool, search_tools

@mcp_tool(domain="github", description="List repositories")
async def list_repositories(org: str, limit: int = 10) -> dict:
    """List repositories for a GitHub organization.
    
    Args:
        org: Organization name (e.g., 'openai')
        limit: Maximum repositories to return (default: 10)
    
    Returns:
        Dictionary with list of repository names
    """
    return {"repositories": ["repo-a", "repo-b"]}

print([t.name for t in search_tools(domain="github")])
```

Pitfalls:
- Ensure function is `async` for non-blocking execution.
- Use precise type hints for reliable schema extraction.

---

## `tool()`

- What: Generic decorator for simple tool registration without MCP extras.
- When: Use for lightweight utilities or internal helpers; still discoverable.
- How: Decorate a function and provide minimal metadata.

Example:
```python
from orchestrator import tool

@tool(domain="demo", description="Echo a message")
async def echo(message: str) -> dict:
    """Echo back the provided message.
    
    Args:
        message: The message to echo back
    
    Returns:
        Dictionary with the echoed message
    """
    return {"echo": message}
```

---

## `a2a_agent()`

- What: Wrap an agent function to be delegatable via the A2A client.
- When: Use for higher-level evaluators/classifiers that other agents call.
- Ho"""Classify text into predefined categories.
    
    Args:
        text: The text to classify
    
    Returns:
        Dictionary with classification label
    """
    w: Decorate an async function; give it a stable `name` and optional version.

Example:
```python
from orchestrator import a2a_agent

@a2a_agent(name="classifier", version="1.0")
async def classify(text: str) -> dict:
    return {"label": "electronics"}
```

---

Related:
- Samples: [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)
- Concepts: [Overview](../../concepts/overview.md)