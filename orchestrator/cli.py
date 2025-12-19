"""CLI for ToolWeaver discovery API."""

import argparse
import sys
import asyncio
from typing import List

from orchestrator import get_available_tools, search_tools, get_tool_info, list_tools_by_domain


def format_tool_info(tool_name: str) -> str:
    """Format a single tool's full info for display."""
    tool = get_tool_info(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found"
    
    lines = [
        f"Name: {tool.name}",
        f"Type: {tool.type}",
        f"Provider: {tool.provider or 'N/A'}",
        f"Domain: {tool.domain}",
        f"Description: {tool.description}",
    ]
    
    if tool.parameters:
        lines.append("Parameters:")
        for param in tool.parameters:
            req = " (required)" if param.required else ""
            lines.append(f"  - {param.name}: {param.type}{req}")
    
    if tool.input_schema:
        lines.append(f"Input Schema: {tool.input_schema}")
    
    if tool.output_schema:
        lines.append(f"Output Schema: {tool.output_schema}")
    
    return "\n".join(lines)


def list_tools(args) -> int:
    """List all available tools."""
    tools = get_available_tools(
        plugin=args.plugin,
        type_filter=args.type,
        domain=args.domain,
    )
    
    if not tools:
        print("No tools found.")
        return 0
    
    print(f"Found {len(tools)} tool(s):\n")
    for tool in tools:
        print(f"  {tool.name:30} | {tool.type:12} | {tool.description[:50]}")
    
    return 0


def search_cmd(args) -> int:
    """Search for tools by query."""
    if not args.query:
        print("Error: query is required for search")
        return 1
    
    results = search_tools(
        query=args.query,
        domain=args.domain,
        type_filter=args.type,
    )
    
    if not results:
        print(f"No tools found matching '{args.query}'")
        return 0
    
    print(f"Found {len(results)} tool(s):\n")
    for tool in results:
        print(f"  {tool.name:30} | {tool.description}")
    
    return 0


def info_cmd(args) -> int:
    """Get detailed info on a tool."""
    if not args.name:
        print("Error: tool name is required")
        return 1
    
    info = format_tool_info(args.name)
    print(info)
    return 0


def main(argv: List[str] = None) -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="toolweaver",
        description="ToolWeaver CLI - Tool discovery and management",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all tools")
    list_parser.add_argument("--plugin", help="Filter by plugin name")
    list_parser.add_argument("--type", help="Filter by tool type (function, mcp, agent, etc.)")
    list_parser.add_argument("--domain", help="Filter by domain")
    list_parser.set_defaults(func=list_tools)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for tools")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--domain", help="Filter by domain")
    search_parser.add_argument("--type", help="Filter by tool type")
    search_parser.set_defaults(func=search_cmd)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get tool details")
    info_parser.add_argument("name", nargs="?", help="Tool name")
    info_parser.set_defaults(func=info_cmd)
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
