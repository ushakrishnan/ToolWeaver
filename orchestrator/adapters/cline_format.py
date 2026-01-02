"""
Cline Tool Format Adapter

Converts ToolWeaver tools to Cline's tool format for integration with Cline MCP.

Reference: https://github.com/cline/cline

Example:
    from orchestrator import get_available_tools
    from orchestrator.adapters import ClineAdapter

    tools = get_available_tools()
    adapter = ClineAdapter(tools)

    cline_config = adapter.to_cline_config()
    # Use with cline_config in Cline MCP setup
"""

from __future__ import annotations

import json
from typing import Any

from ..shared.models import ToolDefinition, ToolParameter


class ClineAdapter:
    """Adapter to convert ToolWeaver tools to Cline format."""

    def __init__(self, tools: list[ToolDefinition]) -> None:
        """
        Initialize adapter with tools.

        Args:
            tools: List of ToolDefinition objects to adapt
        """
        self.tools = tools

    def to_cline_config(self) -> dict[str, Any]:
        """
        Convert tools to Cline MCP tool format.

        Returns:
            Dict with Cline-compatible tool configuration
        """
        return {
            "version": "1.0",
            "tools": [self._tool_to_cline_format(tool) for tool in self.tools],
            "metadata": {
                "source": "toolweaver",
                "tool_count": len(self.tools),
            },
        }

    def to_cline_tools_json(self) -> list[dict[str, Any]]:
        """
        Return tools in Cline's tools.json format.

        Returns:
            List of tool objects for tools.json
        """
        return [self._tool_to_cline_format(tool) for tool in self.tools]

    def _tool_to_cline_format(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert a single tool to Cline format."""
        cline_tool = {
            "id": tool.name,
            "name": tool.name,
            "description": tool.description or f"Tool: {tool.name}",
            "category": getattr(tool, "domain", "general"),
            "input_schema": {
                "type": "object",
                "properties": self._build_properties(tool.parameters),
                "required": [p.name for p in tool.parameters if p.required],
            },
        }

        # Add optional fields if present
        if tool.metadata:
            cline_tool["metadata"] = tool.metadata

        if tool.returns:
            cline_tool["output_schema"] = tool.returns

        return cline_tool

    def _build_properties(self, parameters: list[ToolParameter]) -> dict[str, Any]:
        """Build JSON schema properties from parameters."""
        properties = {}
        for param in parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description or f"Parameter: {param.name}",
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
        return properties

    def to_json(self, pretty: bool = True) -> str:
        """
        Serialize config to JSON string.

        Args:
            pretty: If True, format with indentation

        Returns:
            JSON string
        """
        config = self.to_cline_config()
        indent = 2 if pretty else None
        return json.dumps(config, indent=indent)

    def save_to_file(self, filepath: str, pretty: bool = True) -> None:
        """
        Save Cline config to file.

        Args:
            filepath: Path to write JSON file
            pretty: If True, format with indentation
        """
        with open(filepath, "w") as f:
            f.write(self.to_json(pretty=pretty))
