# Quickstart (Package Users)

1. Install: `pip install toolweaver`
2. Configure env vars if needed: `TOOLWEAVER_SKILL_PATH`, `TOOLWEAVER_LOG_LEVEL`.
3. Define a tool with the upcoming decorator (Phase 2):
```python
from orchestrator import mcp_tool

@mcp_tool(domain="demo")
async def ping(message: str) -> dict:
    return {"echo": message}
```
4. Run your app and import from `orchestrator` only (not `_internal`).

> Decorator and discovery APIs are stubs until Phase 2/1.6; current package focuses on Phase 0 foundations.
