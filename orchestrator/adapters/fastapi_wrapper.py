"""
FastAPI REST Wrapper Adapter

Exposes ToolWeaver tools as a REST API using FastAPI.

Example:
    from orchestrator import get_available_tools
    from orchestrator.adapters import FastAPIAdapter

    tools = get_available_tools()
    adapter = FastAPIAdapter(tools)
    app = adapter.create_app()

    # Run: uvicorn main:app --reload --port 8000

    # API Endpoints:
    # GET  /tools - List all available tools
    # GET  /tools/{tool_name} - Get tool details
    # POST /tools/{tool_name}/execute - Execute a tool
"""

from __future__ import annotations

from typing import Any

from ..shared.models import ToolDefinition


class FastAPIAdapter:
    """Adapter to expose ToolWeaver tools as FastAPI REST endpoints."""

    def __init__(self, tools: list[ToolDefinition], base_url: str = "/api/v1") -> None:
        """
        Initialize adapter with tools.

        Args:
            tools: List of ToolDefinition objects to expose
            base_url: Base path for API routes (default: /api/v1)
        """
        self.tools = tools
        self.base_url = base_url
        self._tool_map = {tool.name: tool for tool in tools}

    def create_app(self) -> Any:
        """
        Create a FastAPI application with tool endpoints.

        Returns:
            FastAPI app instance

        Requires:
            pip install fastapi uvicorn

        Example:
            >>> app = adapter.create_app()
            >>> # Run with: uvicorn app:app --port 8000
        """
        try:
            import json  # noqa: F401

            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "FastAPI and uvicorn required for REST wrapper. "
                "Install with: pip install toolweaver[fastapi]"
            ) from e

        app = FastAPI(
            title="ToolWeaver REST API",
            description="REST API for executing ToolWeaver tools",
            version="1.0.0",
        )

        @app.get(f"{self.base_url}/tools")
        async def list_tools() -> dict[str, Any]:
            """List all available tools."""
            return {
                "count": len(self.tools),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "type": tool.type,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                            }
                            for p in tool.parameters
                        ],
                    }
                    for tool in self.tools
                ],
            }

        @app.get(f"{self.base_url}/tools/{{tool_name}}")
        async def get_tool(tool_name: str) -> dict[str, Any]:
            """Get details for a specific tool."""
            tool = self._tool_map.get(tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

            return {
                "name": tool.name,
                "description": tool.description,
                "type": tool.type,
                "provider": tool.provider,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                        "enum": p.enum,
                    }
                    for p in tool.parameters
                ],
                "metadata": tool.metadata or {},
            }

        @app.post(f"{self.base_url}/tools/{{tool_name}}/execute")
        async def execute_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            """Execute a tool with given parameters."""
            tool = self._tool_map.get(tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

            # Validate required parameters
            required_params = {p.name for p in tool.parameters if p.required}
            provided_params = set(params.keys())
            missing = required_params - provided_params
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameters: {', '.join(missing)}",
                )

            try:
                # Execute tool - assumes tools are registered in plugin registry
                from ..plugins.registry import get_registry

                registry = get_registry()
                # Find plugin containing this tool
                for plugin_name in registry.list():
                    plugin = registry.get(plugin_name)
                    tools_dict = {t.get("name"): t for t in plugin.get_tools()}
                    if tool_name in tools_dict:
                        result = await plugin.execute(tool_name, params)
                        return {
                            "success": True,
                            "tool": tool_name,
                            "result": result,
                        }

                raise HTTPException(
                    status_code=404,
                    detail=f"Tool '{tool_name}' not registered in any plugin",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Tool execution failed: {str(e)}",
                  ) from e
