"""
ToolFileSystem: File-tree interface for progressive tool discovery.

Enables AI models to explore available tools without loading full definitions.
Key features:
- List servers/domains (google_drive, jira, slack, etc.)
- List tools within a server
- Get stub path for importing
- Search tools by name or description
- Minimal token usage for exploration

Example usage:
    fs = ToolFileSystem(stub_dir)
    
    # Explore servers (minimal tokens)
    servers = fs.list_servers()  # ['google_drive', 'jira', 'slack']
    
    # Explore tools in a server
    tools = fs.list_tools('google_drive')  # ['get_document', 'create_document']
    
    # Get tool info
    info = fs.get_tool_info('get_document')  # ToolInfo with description, params, etc.
    
    # Get import statement
    stmt = fs.get_import_statement('get_document')
    # "from tools.google_drive import get_document, GetDocumentInput"
"""

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a tool extracted from its stub"""
    name: str
    server: str
    description: str
    file_path: Path
    input_class: str
    output_class: str
    parameters: list[dict[str, Any]]  # Extracted from docstring or model


class ToolFileSystem:
    """
    File-tree interface for progressive tool discovery.
    
    Provides lightweight exploration of generated tool stubs:
    - Directory structure navigation
    - Tool metadata extraction
    - Import statement generation
    
    Token usage:
    - list_servers(): ~20 tokens
    - list_tools(server): ~50 tokens
    - get_tool_info(name): ~200 tokens
    vs. full catalog in context: ~800+ tokens
    """

    def __init__(self, stub_dir: Path):
        """
        Initialize filesystem interface.
        
        Args:
            stub_dir: Root directory containing generated stubs
        """
        self.stub_dir = Path(stub_dir)
        self.tools_dir = self.stub_dir / "tools"

        if not self.tools_dir.exists():
            raise ValueError(f"Tools directory not found: {self.tools_dir}")

        # Cache for tool info to avoid re-parsing
        self._tool_cache: dict[str, ToolInfo] = {}

        logger.info(f"Initialized ToolFileSystem at {stub_dir}")

    def list_servers(self) -> list[str]:
        """
        List all available servers/domains.
        
        Returns list of server names (e.g., ['google_drive', 'jira', 'slack'])
        
        Token usage: ~20 tokens
        """
        servers = [
            d.name
            for d in self.tools_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]

        logger.debug(f"Found {len(servers)} servers: {servers}")
        return sorted(servers)

    def list_tools(self, server: str | None = None) -> list[str]:
        """
        List tools in a specific server, or all tools.
        
        Args:
            server: Server name (e.g., 'google_drive'). If None, lists all tools.
        
        Returns:
            List of tool names
        
        Token usage: ~50 tokens per server
        """
        if server:
            server_dir = self.tools_dir / server
            if not server_dir.exists():
                logger.warning(f"Server not found: {server}")
                return []

            tools = [
                f.stem
                for f in server_dir.iterdir()
                if f.suffix == ".py" and not f.name.startswith("_")
            ]
        else:
            # List all tools from all servers
            tools = []
            for server_name in self.list_servers():
                tools.extend(self.list_tools(server_name))

        logger.debug(f"Found {len(tools)} tools in {server or 'all servers'}")
        return sorted(tools)

    def get_tool_info(self, tool_name: str) -> ToolInfo | None:
        """
        Get detailed information about a tool.
        
        Extracts from stub file:
        - Description (from module docstring)
        - Parameters (from docstring or input model)
        - Input/output class names
        - File path for importing
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            ToolInfo object, or None if tool not found
        
        Token usage: ~200 tokens (lazy loaded only when needed)
        """
        # Check cache first
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]

        # Find the tool file
        tool_file = self._find_tool_file(tool_name)
        if not tool_file:
            logger.warning(f"Tool not found: {tool_name}")
            return None

        # Extract server from path
        server = tool_file.parent.name

        # Parse the file
        try:
            content = tool_file.read_text()
            tree = ast.parse(content)

            # Extract description from module docstring
            description = ast.get_docstring(tree) or "No description"
            if "\n\n" in description:
                description = description.split("\n\n")[0]  # First paragraph

            # Extract class names
            input_class = None
            output_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if "Input" in node.name:
                        input_class = node.name
                    elif "Output" in node.name:
                        output_class = node.name

            # Extract parameters from function docstring
            parameters = []
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef) and node.name == tool_name:
                    func_doc = ast.get_docstring(node)
                    if func_doc:
                        parameters = self._extract_parameters(func_doc)
                    break

            # Create ToolInfo
            info = ToolInfo(
                name=tool_name,
                server=server,
                description=description,
                file_path=tool_file,
                input_class=input_class or f"{tool_name}Input",
                output_class=output_class or f"{tool_name}Output",
                parameters=parameters
            )

            # Cache it
            self._tool_cache[tool_name] = info

            logger.debug(f"Extracted info for tool: {tool_name}")
            return info

        except Exception as e:
            logger.error(f"Failed to parse tool file {tool_file}: {e}")
            return None

    def get_import_statement(self, tool_name: str) -> str | None:
        """
        Generate import statement for a tool.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Python import statement, or None if tool not found
        
        Example:
            "from tools.google_drive import get_document, GetDocumentInput"
        """
        info = self.get_tool_info(tool_name)
        if not info:
            return None

        return f"from tools.{info.server} import {tool_name}, {info.input_class}"

    def search_tools(self, query: str) -> list[str]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query (case-insensitive)
        
        Returns:
            List of matching tool names
        
        Token usage: Depends on number of matches (typically <100 tokens)
        """
        query = query.lower()
        matches = []

        for tool_name in self.list_tools():
            # Check name
            if query in tool_name.lower():
                matches.append(tool_name)
                continue

            # Check description
            info = self.get_tool_info(tool_name)
            if info and query in info.description.lower():
                matches.append(tool_name)

        logger.debug(f"Found {len(matches)} tools matching '{query}'")
        return matches

    def get_directory_tree(self) -> str:
        """
        Get a visual representation of the tool directory structure.
        
        Returns:
            String representation of directory tree
        
        Token usage: ~100 tokens for typical catalog
        """
        lines = ["tools/"]

        for server in self.list_servers():
            lines.append(f"  {server}/")
            for tool in self.list_tools(server):
                lines.append(f"    {tool}.py")

        return "\n".join(lines)

    def _find_tool_file(self, tool_name: str) -> Path | None:
        """Find the file for a tool by searching all servers"""
        for server in self.list_servers():
            tool_file = self.tools_dir / server / f"{tool_name}.py"
            if tool_file.exists():
                return tool_file
        return None

    def _extract_parameters(self, docstring: str) -> list[dict[str, Any]]:
        """
        Extract parameter information from docstring.
        
        Looks for Args section with format:
            param_name (type, required/optional): description
        """
        parameters: list[dict[str, Any]] = []

        # Find Args section
        args_match = re.search(r'Args:(.*?)(?:Returns:|$)', docstring, re.DOTALL)
        if not args_match:
            return parameters

        args_section = args_match.group(1)

        # Parse each parameter line
        # Format: param_name (type, required/optional): description
        param_pattern = r'(\w+)\s*\(([\w\s,]+)\):\s*(.+)'

        for line in args_section.split('\n'):
            line = line.strip()
            match = re.match(param_pattern, line)
            if match:
                name = match.group(1)
                type_info = match.group(2)
                description = match.group(3)

                # Parse type and required
                type_parts = [p.strip() for p in type_info.split(',')]
                param_type = type_parts[0] if type_parts else "any"
                required = "required" in type_info.lower()

                parameters.append({
                    "name": name,
                    "type": param_type,
                    "description": description,
                    "required": required
                })

        return parameters
