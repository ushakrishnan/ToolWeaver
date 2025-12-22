"""
YAML-based tool loader for ToolWeaver.

Phase 3: Enable config-driven tool registration via YAML files.

Features:
- Load tool definitions from YAML files
- Validate against schema
- Resolve worker functions from import paths
- Integration with discovery API

Example YAML:
    tools:
      - name: get_expenses
        type: mcp
        domain: finance
        description: "Fetch employee expenses"
        worker: myapp.workers.get_expenses
        parameters:
          - name: employee_id
            type: string
            required: true
            description: "Employee identifier"
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from pydantic import ValidationError

from ..shared.models import ToolDefinition, ToolParameter
from ..plugins.registry import get_registry, register_plugin

logger = logging.getLogger(__name__)


class YAMLLoaderError(Exception):
    """Base exception for YAML loader errors."""
    pass


class YAMLValidationError(YAMLLoaderError):
    """YAML schema validation failed."""
    pass


class WorkerResolutionError(YAMLLoaderError):
    """Failed to resolve worker function from import path."""
    pass


class _YAMLToolPlugin:
    """Plugin that loads tools from YAML configuration."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._workers: Dict[str, Callable] = {}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return all loaded tools as dicts."""
        return [td.model_dump() for td in self._tools.values()]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a YAML-loaded tool."""
        worker = self._workers.get(tool_name)
        if worker is None:
            raise ValueError(f"Unknown YAML tool: {tool_name}")
        
        # Call worker with params
        result = worker(**params)
        
        # Handle async workers
        import inspect
        if inspect.isawaitable(result):
            return await result
        
        return result

    def add(self, tool_def: ToolDefinition, worker: Callable) -> None:
        """Add a tool and its worker function."""
        self._tools[tool_def.name] = tool_def
        self._workers[tool_def.name] = worker
        logger.info(f"Registered YAML tool: {tool_def.name}")


_YAML_PLUGIN_NAME = "yaml_tools"


def _ensure_yaml_plugin() -> _YAMLToolPlugin:
    """Get or create the YAML tools plugin."""
    registry = get_registry()
    if not registry.has(_YAML_PLUGIN_NAME):
        plugin = _YAMLToolPlugin()
        register_plugin(_YAML_PLUGIN_NAME, plugin)
        return plugin
    return registry.get(_YAML_PLUGIN_NAME)  # type: ignore[return-value]


def load_tools_from_yaml(file_path: str | Path) -> int:
    """
    Load tool definitions from a YAML file.
    
    Args:
        file_path: Path to YAML file containing tool definitions
        
    Returns:
        Number of tools loaded
        
    Raises:
        YAMLLoaderError: If YAML is invalid or tools cannot be loaded
        
    Example:
        >>> from orchestrator.tools.loaders import load_tools_from_yaml
        >>> count = load_tools_from_yaml("config/tools.yaml")
        >>> print(f"Loaded {count} tools")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise YAMLLoaderError(f"YAML file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise YAMLLoaderError(f"Failed to parse YAML: {e}") from e
    
    if not isinstance(data, dict) or 'tools' not in data:
        raise YAMLValidationError("YAML must contain a 'tools' key with a list of tool definitions")
    
    tools = data['tools']
    if not isinstance(tools, list):
        raise YAMLValidationError("'tools' must be a list")
    
    plugin = _ensure_yaml_plugin()
    loaded = 0
    
    for tool_data in tools:
        try:
            tool_def, worker = _parse_tool_definition(tool_data)
            plugin.add(tool_def, worker)
            loaded += 1
        except Exception as e:
            logger.error(f"Failed to load tool '{tool_data.get('name', 'unknown')}': {e}")
            # Continue loading other tools
    
    logger.info(f"Loaded {loaded} tools from {file_path}")
    return loaded


def _parse_tool_definition(tool_data: Dict[str, Any]) -> tuple[ToolDefinition, Callable]:
    """
    Parse a single tool definition from YAML data.
    
    Args:
        tool_data: Dictionary containing tool definition
        
    Returns:
        Tuple of (ToolDefinition, worker_function)
        
    Raises:
        YAMLValidationError: If tool definition is invalid
        WorkerResolutionError: If worker function cannot be resolved
    """
    # Validate required fields
    if 'name' not in tool_data:
        raise YAMLValidationError("Tool definition must have a 'name' field")
    
    if 'worker' not in tool_data:
        raise YAMLValidationError(f"Tool '{tool_data['name']}' must have a 'worker' field")
    
    # Extract and validate parameters
    params = []
    if 'parameters' in tool_data:
        for param_data in tool_data['parameters']:
            try:
                param = ToolParameter(
                    name=param_data['name'],
                    type=param_data.get('type', 'string'),
                    description=param_data.get('description', ''),
                    required=param_data.get('required', False),
                    enum=param_data.get('enum'),
                    properties=param_data.get('properties'),
                    items=param_data.get('items'),
                    default=param_data.get('default'),
                )
                params.append(param)
            except (KeyError, ValidationError) as e:
                raise YAMLValidationError(
                    f"Invalid parameter definition in tool '{tool_data['name']}': {e}"
                ) from e
    
    # Create ToolDefinition
    try:
        tool_def = ToolDefinition(
            name=tool_data['name'],
            type=tool_data.get('type', 'function'),
            description=tool_data.get('description', ''),
            provider=tool_data.get('provider'),
            parameters=params,
            input_schema=tool_data.get('input_schema'),
            output_schema=tool_data.get('output_schema'),
            metadata=tool_data.get('metadata', {}),
            source='yaml',
            domain=tool_data.get('domain', 'general'),
        )
    except ValidationError as e:
        raise YAMLValidationError(f"Invalid tool definition for '{tool_data['name']}': {e}") from e
    
    # Resolve worker function
    worker = _resolve_worker(tool_data['worker'])
    
    return tool_def, worker


def _resolve_worker(import_path: str) -> Callable:
    """
    Resolve a worker function from an import path.
    
    Args:
        import_path: Import path like "myapp.workers.get_expenses"
        
    Returns:
        Callable worker function
        
    Raises:
        WorkerResolutionError: If function cannot be imported
        
    Example:
        >>> worker = _resolve_worker("myapp.workers.get_expenses")
    """
    if ':' in import_path:
        # Support "module:function" syntax
        module_path, func_name = import_path.split(':', 1)
    elif '.' in import_path:
        # Support "module.function" syntax
        parts = import_path.rsplit('.', 1)
        if len(parts) == 2:
            module_path, func_name = parts
        else:
            raise WorkerResolutionError(
                f"Invalid import path: {import_path}. "
                "Use 'module.function' or 'module:function' format"
            )
    else:
        raise WorkerResolutionError(
            f"Invalid import path: {import_path}. "
            "Use 'module.function' or 'module:function' format"
        )
    
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise WorkerResolutionError(
            f"Failed to import module '{module_path}': {e}"
        ) from e
    
    try:
        worker = getattr(module, func_name)
    except AttributeError as e:
        raise WorkerResolutionError(
            f"Module '{module_path}' has no function '{func_name}'"
        ) from e
    
    if not callable(worker):
        raise WorkerResolutionError(
            f"'{import_path}' is not callable"
        )
    
    return worker


def load_tools_from_directory(directory: str | Path, pattern: str = "*.yaml") -> int:
    """
    Load all YAML tool definitions from a directory.
    
    Args:
        directory: Path to directory containing YAML files
        pattern: File pattern to match (default: *.yaml)
        
    Returns:
        Total number of tools loaded
        
    Example:
        >>> count = load_tools_from_directory("config/tools/")
        >>> print(f"Loaded {count} tools from directory")
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise YAMLLoaderError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise YAMLLoaderError(f"Not a directory: {directory}")
    
    total_loaded = 0
    
    for yaml_file in directory.glob(pattern):
        try:
            count = load_tools_from_yaml(yaml_file)
            total_loaded += count
        except YAMLLoaderError as e:
            logger.error(f"Failed to load {yaml_file}: {e}")
            # Continue with other files
    
    return total_loaded
