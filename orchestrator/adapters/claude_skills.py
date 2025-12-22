"""
Claude Custom Skills Adapter

Converts ToolWeaver tools to Claude's custom skills format.

Reference: https://platform.openai.com/docs/guides/function-calling

Example:
    from orchestrator import get_available_tools
    from orchestrator.adapters import ClaudeSkillsAdapter
    
    tools = get_available_tools()
    adapter = ClaudeSkillsAdapter(tools)
    
    manifest = adapter.to_claude_manifest()
    # Use manifest with Claude API or in custom skills UI
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..shared.models import ToolDefinition, ToolParameter


class ClaudeSkillsAdapter:
    """Adapter to convert ToolWeaver tools to Claude custom skills format."""
    
    def __init__(self, tools: List[ToolDefinition]) -> None:
        """
        Initialize adapter with tools.
        
        Args:
            tools: List of ToolDefinition objects to adapt
        """
        self.tools = tools
    
    def to_claude_manifest(self) -> Dict[str, Any]:
        """
        Convert tools to Claude custom skills manifest.
        
        Returns:
            Dict with schema version and tools array
            
        Example:
            >>> adapter = ClaudeSkillsAdapter(tools)
            >>> manifest = adapter.to_claude_manifest()
            >>> json.dumps(manifest, indent=2)
        """
        return {
            "schema_version": "1.0",
            "tools": [self._tool_to_claude_format(tool) for tool in self.tools],
        }
    
    def to_claude_functions(self) -> List[Dict[str, Any]]:
        """
        Convert tools to Claude function_tools format for API calls.
        
        Returns:
            List of tool dicts compatible with Claude API
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": self._build_properties(tool.parameters),
                    "required": [p.name for p in tool.parameters if p.required],
                },
            }
            for tool in self.tools
        ]
    
    def _tool_to_claude_format(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Convert a single tool to Claude format."""
        return {
            "id": tool.name,
            "name": tool.name,
            "description": tool.description or f"Tool: {tool.name}",
            "input_schema": {
                "type": "object",
                "properties": self._build_properties(tool.parameters),
                "required": [p.name for p in tool.parameters if p.required],
            },
            "metadata": {
                "source": tool.source or "toolweaver",
                "type": tool.type,
                "provider": tool.provider,
                **(tool.metadata or {}),
            },
        }
    
    def _build_properties(self, parameters: List[ToolParameter]) -> Dict[str, Any]:
        """Build JSON schema properties from parameters."""
        properties = {}
        for param in parameters:
            properties[param.name] = {
                "type": self._map_type(param.type),
                "description": param.description or f"Parameter: {param.name}",
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
        return properties
    
    def _map_type(self, toolweaver_type: str) -> str:
        """Map ToolWeaver parameter type to JSON Schema type."""
        type_map = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "object": "object",
            "array": "array",
        }
        return type_map.get(toolweaver_type, "string")
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Serialize manifest to JSON string.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string
        """
        manifest = self.to_claude_manifest()
        indent = 2 if pretty else None
        return json.dumps(manifest, indent=indent)
