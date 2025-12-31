"""Unit tests for the CLI discovery commands."""

import argparse
from typing import Any
from unittest.mock import Mock

from orchestrator import tool
from orchestrator.cli import info_cmd, list_tools, search_cmd
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


def test_cli_list_tools(capsys):
    registry = get_registry()
    registry.clear()

    @tool(description="Echo text")
    def echo(params: dict[str, Any]) -> dict[str, Any]:
        return {"text": params["text"]}

    args = Mock(plugin=None, type=None, domain=None)
    result = list_tools(args)

    captured = capsys.readouterr()
    assert "Found 1 tool" in captured.out
    assert "echo" in captured.out
    assert result == 0


def test_cli_search_tools(capsys):
    registry = get_registry()
    registry.clear()

    @tool(description="Process order")
    def process_order(params: dict[str, Any]) -> dict[str, Any]:
        return params

    # Explicitly set all attributes for Mock to avoid auto-creation
    args = Mock(query="order", domain=None, type=None, spec=['query', 'domain', 'type'])
    result = search_cmd(args)

    captured = capsys.readouterr()
    assert "Found 1 tool" in captured.out or "process_order" in captured.out
    assert result == 0


def test_cli_info_tool(capsys):
    registry = get_registry()
    registry.clear()

    @tool(
        description="Echo text",
        parameters=[ToolParameter(name="text", type="string", description="Text to echo", required=True)],
    )
    def echo(params: dict[str, Any]) -> dict[str, Any]:
        return {"text": params["text"]}

    # Create a real args object with name attribute set correctly
    args = argparse.Namespace(name="echo")
    result = info_cmd(args)

    captured = capsys.readouterr()
    assert "echo" in captured.out
    assert "Parameters:" in captured.out
    assert result == 0
