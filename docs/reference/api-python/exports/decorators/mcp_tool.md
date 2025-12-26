# `mcp_tool`

- What: Register an MCP-style tool with structured parameters.
- When: Tools discoverable across adapters and planners.
- How:
```python
from orchestrator import mcp_tool

@mcp_tool(domain="github", description="List repositories")
async def list_repositories(org: str, limit: int = 10) -> dict:
    """List repositories for a GitHub organization.
    
    Args:
        org: Organization name
        limit: Maximum repositories to return
    
    Returns:
        Dictionary with list of repository names
    """
    return {"repositories": ["repo-a", "repo-b"]}
```
- Returns: Registered tool callable.
- Pitfalls: Function must be `async`; use precise type hints.
- Links: [Decorators](../../decorators.md), [REST API](../../../api-rest/overview.md)
