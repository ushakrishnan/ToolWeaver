"""
ToolWeaver UI/Format Adapters (Phase 5a)

Adapters for integrating ToolWeaver tools with external environments:
- Claude custom skills
- Cline tool format
- FastAPI REST wrapper

Example:
    from orchestrator.adapters import ClaudeSkillsAdapter, ClineAdapter, FastAPIAdapter

    # Adapt tools for Claude
    adapter = ClaudeSkillsAdapter(tools)
    claude_manifest = adapter.to_claude_manifest()

    # Adapt tools for Cline
    adapter = ClineAdapter(tools)
    cline_config = adapter.to_cline_format()

    # Expose as REST API
    adapter = FastAPIAdapter(tools)
    app = adapter.create_app()
    # uvicorn run app --port 8000
"""

from .claude_skills import ClaudeSkillsAdapter
from .cline_format import ClineAdapter
from .fastapi_wrapper import FastAPIAdapter

__all__ = [
    "ClaudeSkillsAdapter",
    "ClineAdapter",
    "FastAPIAdapter",
]
