# Skill Bridge

Why: Persist and share tools as reusable skills.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `save_tool_as_skill`, `load_tool_from_skill`, `get_tool_skill`, `sync_tool_with_skill`, `get_skill_backed_tools`

## Save a tool as a skill
What: Persist a registered tool into a reusable skill package.
When: Promote a vetted tool for sharing across teams/environments.
```python
from orchestrator import save_tool_as_skill, mcp_tool

@mcp_tool(domain="demo")
async def echo(message: str) -> dict:
    return {"echo": message}

save_tool_as_skill("echo", org="acme")
```

## Load a skill
What: Retrieve a previously saved skill-backed tool.
When: Reuse approved tools without redefining code.
```python
from orchestrator import load_tool_from_skill
tool = load_tool_from_skill("echo", org="acme")
print(tool)
```

Links:
- Concepts: [Overview](../../concepts/overview.md)