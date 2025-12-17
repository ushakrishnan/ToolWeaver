"""
Code Stub Generator

Generates Python function stubs from tool definitions for code execution.

Features:
- Generate Pydantic models from JSON schemas
- Create async function wrappers
- Organize by server/domain
- Type hints and docstrings

Usage:
    catalog = ToolCatalog()
    generator = StubGenerator(catalog, Path("stubs"))
    stubs = generator.generate_all()
"""

import textwrap
import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.control_flow_patterns import (
    ControlFlowPatterns,
    PatternType,
    create_polling_code,
    create_parallel_code,
    create_conditional_code,
    create_retry_code,
)

logger = logging.getLogger(__name__)


@dataclass
class GeneratedStub:
    """Information about a generated stub"""
    tool_name: str
    file_path: Path
    code: str
    imports: List[str]
    classes: List[str]


class StubGenerator:
    """
    Generate Python function stubs from tool catalog.
    
    Architecture:
    - Groups tools by server/domain
    - Generates Pydantic input models
    - Creates async function wrappers
    - Adds type hints and docstrings
    """
    
    def __init__(self, catalog: ToolCatalog, output_dir: Path):
        """
        Initialize stub generator.
        
        Args:
            catalog: ToolCatalog with tool definitions
            output_dir: Directory to write stubs
        """
        self.catalog = catalog
        self.output_dir = output_dir
        self.generated_stubs: Dict[str, GeneratedStub] = {}
        
    def generate_all(self) -> Dict[str, str]:
        """
        Generate all stubs organized by server.
        
        Returns:
            Dictionary mapping file paths to code
        """
        logger.info(f"Generating stubs for {len(self.catalog.tools)} tools")
        
        # Group tools by server/domain
        by_server = self._group_by_server()
        
        stubs = {}
        
        for server_name, tools in by_server.items():
            server_dir = self.output_dir / "tools" / server_name
            server_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Generating {len(tools)} stubs for server: {server_name}")
            
            for tool in tools:
                try:
                    stub_path = server_dir / f"{tool.name}.py"
                    stub_code = self._generate_stub(tool)
                    
                    # Write to disk
                    stub_path.write_text(stub_code)
                    
                    stubs[str(stub_path)] = stub_code
                    
                    # Track generated stub
                    self.generated_stubs[tool.name] = GeneratedStub(
                        tool_name=tool.name,
                        file_path=stub_path,
                        code=stub_code,
                        imports=self._extract_imports(stub_code),
                        classes=self._extract_classes(stub_code)
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to generate stub for {tool.name}: {e}")
                    continue
            
            # Generate __init__.py for server
            self._generate_server_init(server_dir, tools)
        
        # Generate top-level __init__.py
        self._generate_top_init()
        
        logger.info(f"Generated {len(stubs)} stubs")
        return stubs

    # --- Control Flow Integration (Phase 2) ---
    def list_control_flow_patterns(self) -> List[Dict[str, Any]]:
        """Expose available control flow patterns for code generation prompts."""
        patterns = ControlFlowPatterns.list_patterns()
        return [
            {
                "type": p.type.value,
                "description": p.description,
                "required_params": p.required_params,
                "example": p.example,
            }
            for p in patterns
        ]

    def render_control_flow(self, pattern_type: str, params: Dict[str, Any]) -> str:
        """Render a control flow code snippet by pattern type and parameters."""
        try:
            ptype = PatternType(pattern_type)
        except Exception:
            # best-effort: allow lowercase names
            ptype = PatternType(pattern_type.lower())
        pattern = ControlFlowPatterns.get_pattern(ptype)
        if not pattern:
            raise ValueError(f"Unknown control flow pattern: {pattern_type}")
        return ControlFlowPatterns.generate_code(pattern, params)
        
    def _group_by_server(self) -> Dict[str, List[ToolDefinition]]:
        """Group tools by server/domain"""
        grouped = {}
        
        for tool in self.catalog.tools.values():
            server = tool.domain or tool.type or "default"
            
            if server not in grouped:
                grouped[server] = []
            
            grouped[server].append(tool)
        
        return grouped
        
    def _generate_stub(self, tool: ToolDefinition) -> str:
        """
        Generate single stub from tool definition.
        
        Args:
            tool: ToolDefinition to generate from
            
        Returns:
            Python code as string
        """
        # Generate input/output models
        input_class = self._generate_input_model(tool)
        output_class = self._generate_output_model(tool)
        
        # Generate function
        function = self._generate_function(tool)
        
        # Combine into module
        return textwrap.dedent(f'''
"""
{tool.description or tool.name}

Generated from: {tool.name}
Type: {tool.type}
Server: {tool.domain or "default"}
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

{input_class}

{output_class}

{function}
        ''').strip() + "\n"
        
    def _generate_input_model(self, tool: ToolDefinition) -> str:
        """Generate Pydantic model for input parameters"""
        class_name = self._camel_case(tool.name) + "Input"
        
        if not tool.parameters:
            return f"class {class_name}(BaseModel):\n    \"\"\"Input parameters for {tool.name}\"\"\"\n    pass"
        
        fields = []
        fields.append(f'class {class_name}(BaseModel):')
        fields.append(f'    """Input parameters for {tool.name}"""')
        fields.append("")
        
        for param in tool.parameters:
            field_type = self._python_type(param.type)
            
            # Make optional if not required
            if not param.required:
                field_type = f"Optional[{field_type}]"
            
            # Build field definition
            if param.required:
                default = "..."
            else:
                default = "None"
            
            # Add description
            if param.description:
                field_def = f'Field({default}, description="{param.description}")'
            else:
                field_def = default
            
            fields.append(f"    {param.name}: {field_type} = {field_def}")
        
        return "\n".join(fields)
        
    def _generate_output_model(self, tool: ToolDefinition) -> str:
        """Generate Pydantic model for output"""
        class_name = self._camel_case(tool.name) + "Output"
        
        # For now, use generic output
        # TODO: Parse output schema if available
        return textwrap.dedent(f'''
class {class_name}(BaseModel):
    """Output from {tool.name}"""
    result: Any
    success: bool = True
    error: Optional[str] = None
        ''').strip()
        
    def _generate_function(self, tool: ToolDefinition) -> str:
        """Generate async function wrapper"""
        input_class = self._camel_case(tool.name) + "Input"
        output_class = self._camel_case(tool.name) + "Output"
        
        # Generate docstring
        docstring = self._generate_docstring(tool)
        
        return textwrap.dedent(f'''
async def {tool.name}(input_data: {input_class}) -> {output_class}:
    """
{docstring}
    """
    from orchestrator.tool_executor import call_tool
    
    try:
        result = await call_tool(
            server="{tool.domain or 'default'}",
            tool_name="{tool.name}",
            parameters=input_data.model_dump()
        )
        
        return {output_class}(result=result, success=True)
    
    except Exception as e:
        return {output_class}(
            result=None,
            success=False,
            error=str(e)
        )
        ''').strip()
        
    def _generate_docstring(self, tool: ToolDefinition) -> str:
        """Generate comprehensive docstring"""
        lines = []
        
        # Description
        if tool.description:
            lines.append(f"    {tool.description}")
            lines.append("")
        
        # Parameters
        if tool.parameters:
            lines.append("    Args:")
            for param in tool.parameters:
                req = "required" if param.required else "optional"
                desc = param.description or "No description"
                lines.append(f"        {param.name} ({param.type}, {req}): {desc}")
            lines.append("")
        
        # Returns
        lines.append("    Returns:")
        lines.append(f"        {self._camel_case(tool.name)}Output with result")
        
        return "\n".join(lines)
        
    def _python_type(self, param_type: str) -> str:
        """Convert parameter type to Python type hint"""
        type_map = {
            "string": "str",
            "str": "str",
            "integer": "int",
            "int": "int",
            "number": "float",
            "float": "float",
            "boolean": "bool",
            "bool": "bool",
            "array": "List[Any]",
            "list": "List[Any]",
            "object": "Dict[str, Any]",
            "dict": "Dict[str, Any]",
            "any": "Any"
        }
        
        return type_map.get(param_type.lower(), "Any")
        
    def _camel_case(self, snake_str: str) -> str:
        """Convert snake_case to CamelCase"""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)
        
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code"""
        imports = []
        for line in code.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        return imports
        
    def _extract_classes(self, code: str) -> List[str]:
        """Extract class names from code"""
        classes = []
        for line in code.split('\n'):
            if line.startswith('class '):
                match = re.match(r'class\s+(\w+)', line)
                if match:
                    classes.append(match.group(1))
        return classes
        
    def _generate_server_init(self, server_dir: Path, tools: List[ToolDefinition]):
        """Generate __init__.py for a server directory"""
        init_path = server_dir / "__init__.py"
        
        imports = []
        all_exports = []
        
        for tool in tools:
            # Import function and models
            imports.append(f"from .{tool.name} import {tool.name}")
            all_exports.append(tool.name)
            
            # Also export input/output classes
            input_class = self._camel_case(tool.name) + "Input"
            output_class = self._camel_case(tool.name) + "Output"
            
            imports.append(f"from .{tool.name} import {input_class}, {output_class}")
            all_exports.extend([input_class, output_class])
        
        content = textwrap.dedent(f'''
"""
Generated tool stubs for {server_dir.name}

Auto-generated by StubGenerator
"""

{chr(10).join(imports)}

__all__ = {all_exports}
        ''').strip() + "\n"
        
        init_path.write_text(content)
        logger.debug(f"Generated {init_path}")
        
    def _generate_top_init(self):
        """Generate top-level __init__.py"""
        tools_dir = self.output_dir / "tools"
        init_path = tools_dir / "__init__.py"
        
        # List all server directories
        servers = [d.name for d in tools_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
        
        imports = [f"from . import {server}" for server in servers]
        
        content = textwrap.dedent(f'''
"""
Generated tool stubs

Auto-generated by StubGenerator
"""

{chr(10).join(imports)}

__all__ = {servers}
        ''').strip() + "\n"
        
        init_path.write_text(content)
        logger.debug(f"Generated {init_path}")
        
    def get_stub_info(self, tool_name: str) -> Optional[GeneratedStub]:
        """Get information about a generated stub"""
        return self.generated_stubs.get(tool_name)
        
    def list_generated_stubs(self) -> List[str]:
        """List all generated stub names"""
        return list(self.generated_stubs.keys())
