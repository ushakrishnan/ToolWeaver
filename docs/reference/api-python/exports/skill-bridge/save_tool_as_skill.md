# `save_tool_as_skill`

- What: Persist a tool as a reusable skill package.
- When: Share tools across environments/teams.
- Example:
```python
from orchestrator import save_tool_as_skill, mcp_tool

@mcp_tool(domain="demo")
async def echo(message: str) -> dict:
    return {"echo": message}

save_tool_as_skill("echo", org="acme")
```
- Links: [Skill Bridge](../../skill-bridge.md)