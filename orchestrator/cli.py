"""CLI for ToolWeaver discovery API."""

import argparse
import sys

from orchestrator import (
    browse_tools,
    get_available_tools,
    get_tool_info,
    search_tools,
)


def format_tool_info(tool_name: str, detail_level: str = "full") -> str:
    """Format a single tool's info for display."""
    tool = get_tool_info(tool_name, detail_level=detail_level)
    if not tool:
        return f"Tool '{tool_name}' not found"

    if detail_level == "name":
        if isinstance(tool, dict):
            return f"Name: {tool['name']}\nType: {tool['type']}\nDomain: {tool.get('domain', 'N/A')}"
        return f"Name: {tool.name}\nType: {tool.type}\nDomain: {tool.domain}"

    if detail_level == "summary":
        if isinstance(tool, dict):
            lines = [
                f"Name: {tool['name']}",
                f"Type: {tool['type']}",
                f"Domain: {tool.get('domain', 'N/A')}",
                f"Description: {tool['description']}",
                f"Parameters: {tool.get('parameter_count', 0)}",
            ]
            return "\n".join(lines)

    # Full detail level
    if isinstance(tool, dict):
        tool_name_val = tool['name']
    else:
        tool_name_val = tool.name

    lines = [
        f"Name: {tool_name_val if isinstance(tool, dict) else tool.name}",
        f"Type: {tool['type'] if isinstance(tool, dict) else tool.type}",
        f"Provider: {tool.get('provider', 'N/A') if isinstance(tool, dict) else (tool.provider or 'N/A')}",
        f"Domain: {tool.get('domain', 'N/A') if isinstance(tool, dict) else tool.domain}",
        f"Description: {tool['description'] if isinstance(tool, dict) else tool.description}",
    ]

    if hasattr(tool, "parameters"):
        if tool.parameters:
            lines.append("Parameters:")
            for param in tool.parameters:
                req = " (required)" if param.required else ""
                lines.append(f"  - {param.name}: {param.type}{req}")

    return "\n".join(lines)


def browse_cmd(args) -> int:
    """Browse tools with progressive detail levels."""
    detail_level = getattr(args, 'detail', 'summary')
    offset = getattr(args, 'offset', 0)
    limit = getattr(args, 'limit', 50)

    results = browse_tools(
        plugin=args.plugin if hasattr(args, 'plugin') else None,
        type_filter=args.type if hasattr(args, 'type') else None,
        domain=args.domain if hasattr(args, 'domain') else None,
        detail_level=detail_level,
        offset=offset,
        limit=limit,
    )

    if not results:
        print("No tools found.")
        return 0

    print(f"Found {len(results)} tool(s) (showing {offset}-{offset+len(results)}):\n")

    for item in results:
        if detail_level == "name":
            if isinstance(item, dict):
                print(f"  {item['name']:30} | {item['type']:12}")
            else:
                print(f"  {item.name:30} | {item.type:12}")
        elif detail_level == "summary":
            if isinstance(item, dict):
                print(f"  {item['name']:30} | {item.get('description', '')[:50]}")
            else:
                print(f"  {item.name:30} | {item.description[:50]}")
        else:  # full
            if isinstance(item, dict):
                print(f"  {item['name']:30} | {item['type']:12} | {item.get('description', '')[:50]}")
            else:
                print(f"  {item.name:30} | {item.type:12} | {item.description[:50]}")

    return 0


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

    # Get search parameters
    use_semantic = getattr(args, 'semantic', False)
    top_k = getattr(args, 'top_k', 10)
    detail_level = getattr(args, 'detail', None)

    results = search_tools(
        query=args.query,
        domain=args.domain if hasattr(args, 'domain') else None,
        type_filter=args.type if hasattr(args, 'type') else None,
        use_semantic=use_semantic,
        top_k=top_k,
        detail_level=detail_level,
    )

    if not results:
        print(f"No tools found matching '{args.query}'")
        return 0

    search_mode = "semantic" if use_semantic else "keyword"
    print(f"Found {len(results)} tool(s) using {search_mode} search:\n")

    for item in results:
        if detail_level == "name":
            if isinstance(item, dict):
                print(f"  {item['name']:30}")
            else:
                print(f"  {item.name:30}")
        elif detail_level == "summary":
            if isinstance(item, dict):
                print(f"  {item['name']:30} | {item.get('description', '')}")
            else:
                print(f"  {item.name:30} | {item.description}")
        else:  # full or None (returns ToolDefinition)
            if isinstance(item, dict):
                print(f"  {item['name']:30} | {item.get('description', '')}")
            else:
                print(f"  {item.name:30} | {item.description}")

    return 0


def info_cmd(args) -> int:
    """Get detailed info on a tool."""
    if not args.name:
        print("Error: tool name is required")
        return 1

    detail_level = getattr(args, 'detail', 'full')
    info = format_tool_info(args.name, detail_level=detail_level)
    print(info)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="toolweaver",
        description="ToolWeaver CLI - Tool discovery and management",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Browse command (new)
    browse_parser = subparsers.add_parser("browse", help="Browse tools with progressive detail levels")
    browse_parser.add_argument("--plugin", help="Filter by plugin name")
    browse_parser.add_argument("--type", help="Filter by tool type (function, mcp, agent, etc.)")
    browse_parser.add_argument("--domain", help="Filter by domain")
    browse_parser.add_argument("--detail", choices=["name", "summary", "full"], default="summary",
                               help="Detail level: name (minimal), summary (moderate), full (complete schema)")
    browse_parser.add_argument("--offset", type=int, default=0, help="Pagination offset (default: 0)")
    browse_parser.add_argument("--limit", type=int, default=50, help="Pagination limit (default: 50)")
    browse_parser.set_defaults(func=browse_cmd)

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
    search_parser.add_argument("--semantic", action="store_true", help="Use semantic search with vector embeddings (requires Qdrant)")
    search_parser.add_argument("--top-k", type=int, default=10, help="Number of results to return (default: 10)")
    search_parser.add_argument("--detail", choices=["name", "summary", "full"],
                               help="Detail level: name (minimal), summary (moderate), full (complete schema)")
    search_parser.set_defaults(func=search_cmd)

    # Info command
    info_parser = subparsers.add_parser("info", help="Get tool details")
    info_parser.add_argument("name", nargs="?", help="Tool name")
    info_parser.add_argument("--detail", choices=["name", "summary", "full"], default="full",
                             help="Detail level: name (minimal), summary (moderate), full (complete schema)")
    info_parser.set_defaults(func=info_cmd)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    result = args.func(args)
    return int(result)


if __name__ == "__main__":
    sys.exit(main())
