"""
Skill Bridge - Connect tools to skill library for versioning and reuse.

Provides:
- save_tool_as_skill(): Save a tool's implementation as a skill
- load_tool_from_skill(): Create a tool from an existing skill
- get_tool_skill(): Get the skill backing a tool (if any)
- sync_tool_with_skill(): Update tool to match latest skill version
"""

import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from .._internal.execution.skill_library import Skill, get_skill, save_skill, update_skill
from ..shared.models import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)


def save_tool_as_skill(
    tool_def: ToolDefinition,
    function: Callable[..., Any],
    *,
    tags: list[str] | None = None,
    bump_type: str = "patch"
) -> Skill:
    """
    Save a tool's implementation as a skill in the skill library.
    
    Args:
        tool_def: Tool definition to save
        function: The actual function implementation
        tags: Optional tags for skill categorization
        bump_type: Version bump type ("major", "minor", "patch") if updating
    
    Returns:
        Skill object representing the saved skill
    
    Example:
        >>> @tool(name="process_data", description="Process data")
        >>> def process_data(data: dict) -> dict:
        >>>     return {"processed": True}
        >>> 
        >>> tool_def = get_tool_info("process_data")
        >>> skill = save_tool_as_skill(tool_def, process_data, tags=["data"])
    """
    # Extract function source code
    # Unwrap decorated functions if needed
    source_func = function
    if hasattr(function, '__wrapped__'):
        source_func = function.__wrapped__

    try:
        source_code = inspect.getsource(source_func)

        # Remove decorators from source code (they can't be executed in skill context)
        lines = source_code.split('\n')
        # Find first line that starts with 'def' or 'async def'
        def_line_idx = None
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                def_line_idx = i
                break

        if def_line_idx is not None:
            # Keep only from def line onwards
            lines = lines[def_line_idx:]
            # Dedent the code to start at column 0
            import textwrap
            source_code = textwrap.dedent('\n'.join(lines))

    except (TypeError, OSError) as e:
        logger.error(f"Cannot extract source for {tool_def.name}: {e}")
        raise ValueError("Cannot save tool as skill: unable to extract source code")

    # Prepare skill metadata
    skill_tags = tags or []
    if tool_def.type:
        skill_tags.append(f"type:{tool_def.type}")
    if tool_def.provider:
        skill_tags.append(f"provider:{tool_def.provider}")

    skill_metadata = {
        "tool_name": tool_def.name,
        "tool_type": tool_def.type,
        "tool_provider": tool_def.provider,
        "parameters": [p.model_dump() for p in tool_def.parameters] if tool_def.parameters else [],
        "input_schema": tool_def.input_schema,
        "output_schema": tool_def.output_schema,
    }
    if tool_def.metadata:
        skill_metadata["tool_metadata"] = tool_def.metadata

    # Check if skill already exists (update vs create)
    existing_skill = get_skill(tool_def.name)

    if existing_skill:
        # Update existing skill
        logger.info(
            f"Updating skill '{tool_def.name}' with bump_type={bump_type}",
            extra={
                "skill_name": tool_def.name,
                "action": "update",
                "bump_type": bump_type,
                "tool_type": tool_def.type,
                "provider": tool_def.provider,
            }
        )
        skill = update_skill(
            tool_def.name,
            source_code,
            description=tool_def.description,
            tags=skill_tags,
            bump_type=bump_type
        )
    else:
        # Create new skill
        logger.info(
            f"Creating new skill '{tool_def.name}'",
            extra={
                "skill_name": tool_def.name,
                "action": "create",
                "tool_type": tool_def.type,
                "provider": tool_def.provider,
                "tags": skill_tags,
            }
        )
        skill = save_skill(
            tool_def.name,
            source_code,
            description=tool_def.description,
            tags=skill_tags,
            metadata=skill_metadata
        )

    logger.debug(
        f"Skill saved: {skill.name}",
        extra={
            "skill_name": skill.name,
            "skill_version": skill.version,
            "code_path": skill.code_path,
        }
    )
    return skill


def load_tool_from_skill(
    skill_name: str,
    *,
    version: str | None = None,
    tool_type: Literal["mcp", "function", "code_exec", "agent", "tool"] = "function",
    provider: str = "skill"
) -> tuple[ToolDefinition, Callable[..., Any]]:
    """
    Load a tool from a skill in the skill library.
    
    Args:
        skill_name: Name of the skill to load
        version: Optional specific version (defaults to latest)
        tool_type: Type of tool to create (default: "function")
        provider: Provider name (default: "skill")
    
    Returns:
        Tuple of (ToolDefinition, callable function)
    
    Raises:
        KeyError: If skill not found
        ValueError: If skill code cannot be executed
    
    Example:
        >>> tool_def, func = load_tool_from_skill("process_data")
        >>> result = func({"input": "test"})
    """
    logger.debug(f"Loading tool from skill '{skill_name}' (version={version})")

    # Get skill (specific version or latest)
    if version:
        from .._internal.execution.skill_library import get_skill_version
        skill = get_skill_version(skill_name, version)
        if not skill:
            raise KeyError(f"Skill '{skill_name}' version {version} not found")
    else:
        skill = get_skill(skill_name)
        if not skill:
            raise KeyError(f"Skill '{skill_name}' not found")

    logger.debug(
        f"Skill loaded: {skill_name}",
        extra={
            "skill_name": skill_name,
            "skill_version": skill.version,
            "code_path": skill.code_path,
        }
    )

    # Load skill code
    skill_path = Path(skill.code_path)
    if not skill_path.exists():
        raise ValueError(f"Skill code file not found: {skill.code_path}")

    code = skill_path.read_text()

    # Execute skill code to get function
    namespace: dict[str, Any] = {}
    try:
        exec(code, namespace)
    except Exception as e:
        logger.error(f"Failed to execute skill code for '{skill_name}': {e}")
        raise ValueError(f"Cannot execute skill code: {e}")

    # Find the main function (same name as skill or first callable)
    func = namespace.get(skill_name)
    if func is None or not callable(func):
        # Try to find first callable that's not a builtin
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('_') and name not in ('print', 'len', 'str', 'int'):
                func = obj
                break

    if func is None or not callable(func):
        raise ValueError(f"No callable function found in skill '{skill_name}'")

    # Extract parameters from skill metadata
    parameters = []
    if skill.metadata and "parameters" in skill.metadata:
        parameters = [ToolParameter(**p) for p in skill.metadata["parameters"]]
    else:
        # Fall back to inspecting function signature
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            param_type = "string"  # Default
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else "string"

            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                required=param.default == inspect.Parameter.empty,
                description=f"Parameter {param_name}"
            ))

    # Build tool definition
    tool_def = ToolDefinition(
        name=skill.name,
        type=tool_type,
        provider=provider,
        description=skill.description or f"Tool loaded from skill '{skill.name}'",
        parameters=parameters,
        input_schema=skill.metadata.get("input_schema") if skill.metadata else None,
        output_schema=skill.metadata.get("output_schema") if skill.metadata else None,
        metadata={
            "skill_reference": skill.name,
            "skill_version": skill.version,
            "skill_tags": skill.tags,
            "loaded_from_skill": True
        }
    )

    return tool_def, func


def get_tool_skill(tool_name: str) -> Skill | None:
    """
    Get the skill backing a tool (if any).
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Skill object if tool has a skill reference, None otherwise
    """
    return get_skill(tool_name)


def sync_tool_with_skill(tool_name: str) -> tuple[ToolDefinition, Callable[..., Any]] | None:
    """
    Sync a tool with the latest version of its backing skill.
    
    Args:
        tool_name: Name of the tool to sync
    
    Returns:
        Updated (ToolDefinition, callable) tuple, or None if no skill reference
    
    Example:
        >>> # Tool is outdated, skill was updated
        >>> tool_def, func = sync_tool_with_skill("process_data")
        >>> # Now using latest skill version
    """
    skill = get_skill(tool_name)
    if not skill:
        logger.warning(f"No skill found for tool '{tool_name}'")
        return None

    # Reload tool from latest skill version (don't specify version to get current)
    logger.info(f"Syncing tool '{tool_name}' to skill version {skill.version}")
    return load_tool_from_skill(tool_name)


def get_skill_backed_tools() -> list[str]:
    """
    Get list of all tools that are backed by skills.
    
    Returns:
        List of tool names that have corresponding skills
    """
    from .._internal.execution.skill_library import list_skills

    skills = list_skills()
    return [s.name for s in skills if s.metadata and s.metadata.get("tool_name")]
