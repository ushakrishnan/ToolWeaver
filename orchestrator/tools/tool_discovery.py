"""
Tool Discovery System for ToolWeaver

Automatically discovers tools from:
- MCP servers (via MCPClientShim)
- Python functions (via introspection)
- Code execution capabilities (sandboxed Python)

Phase 2 Implementation
"""

import asyncio
import inspect
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel

from ..shared.models import ToolDefinition, ToolParameter, ToolCatalog
import os
import aiohttp


class DiscoveryMetrics(BaseModel):
    """Metrics for tool discovery operations"""
    total_tools_found: int = 0
    discovery_duration_ms: float = 0
    sources: Dict[str, int] = {}  # source_name -> tool_count
    errors: List[str] = []


class ToolDiscoveryService(ABC):
    """Base class for tool discovery implementations"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.discovered_tools: Dict[str, ToolDefinition] = {}
    
    @abstractmethod
    async def discover(self) -> Dict[str, ToolDefinition]:
        """
        Discover tools from this source.
        Returns dict of tool_name -> ToolDefinition
        """
        pass
    
    def _parse_python_type(self, annotation: Any) -> str:
        """Convert Python type annotation to JSON Schema type"""
        type_map = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'dict': 'object',
            'list': 'array',
            'Dict': 'object',
            'List': 'array',
            'Any': 'string',
        }
        
        type_str = str(annotation).replace('typing.', '').replace('<class ', '').replace('>', '').replace("'", "")
        
        for py_type, json_type in type_map.items():
            if py_type in type_str:
                return json_type
        
        return 'string'  # Default fallback


class MCPToolDiscoverer(ToolDiscoveryService):
    """Discovers tools from MCP servers via MCPClientShim"""
    
    def __init__(self, mcp_client):
        super().__init__("mcp")
        self.mcp_client = mcp_client
    
    async def discover(self) -> Dict[str, ToolDefinition]:
        """
        Discover tools from MCP client's tool_map.
        
        Since MCPClientShim has a tool_map dict, we can introspect
        the registered workers to build ToolDefinitions.
        """
        discovered = {}
        
        if not hasattr(self.mcp_client, 'tool_map'):
            return discovered
        
        for tool_name, worker_func in self.mcp_client.tool_map.items():
            try:
                tool_def = await self._introspect_worker(tool_name, worker_func)
                discovered[tool_name] = tool_def
            except Exception as e:
                # Log but don't fail entire discovery
                print(f"Warning: Failed to discover MCP tool '{tool_name}': {e}")
        
        return discovered
    
    async def _introspect_worker(self, tool_name: str, worker_func) -> ToolDefinition:
        """Extract tool definition from worker function"""
        sig = inspect.signature(worker_func)
        doc = inspect.getdoc(worker_func) or f"MCP tool: {tool_name}"
        is_streaming = inspect.isasyncgenfunction(worker_func)
        
        # Extract parameters
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == 'payload':
                # Special case: payload is a Dict[str, Any], we need to document expected keys
                parameters.append(ToolParameter(
                    name="payload",
                    type="object",
                    description=f"Parameters for {tool_name}",
                    required=True
                ))
            else:
                param_type = self._parse_python_type(param.annotation)
                is_required = param.default == inspect.Parameter.empty
                
                parameters.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter: {param_name}",
                    required=is_required
                ))
        
        # Build ToolDefinition
        return ToolDefinition(
            name=tool_name,
            type="mcp",
            description=doc.split('\n')[0][:200],  # First line, max 200 chars
            parameters=parameters,
            source=self.source_name,
            metadata={
                "module": worker_func.__module__,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "supports_streaming": is_streaming,
            }
        )


class FunctionToolDiscoverer(ToolDiscoveryService):
    """Discovers tools from Python functions in a module"""
    
    def __init__(self, module, function_names: Optional[List[str]] = None):
        """
        Args:
            module: Python module to scan
            function_names: If provided, only discover these functions.
                           If None, discover all public functions.
        """
        super().__init__(f"functions:{module.__name__}")
        self.module = module
        self.function_names = function_names
    
    async def discover(self) -> Dict[str, ToolDefinition]:
        """Discover callable functions in the module"""
        discovered = {}
        
        # Get all public functions or specified subset
        if self.function_names:
            functions = {name: getattr(self.module, name) 
                        for name in self.function_names 
                        if hasattr(self.module, name)}
        else:
            functions = {name: obj for name, obj in inspect.getmembers(self.module) 
                        if inspect.isfunction(obj) and not name.startswith('_')}
        
        for func_name, func in functions.items():
            try:
                tool_def = self._function_to_tool(func_name, func)
                discovered[func_name] = tool_def
            except Exception as e:
                print(f"Warning: Failed to discover function '{func_name}': {e}")
        
        return discovered
    
    def _function_to_tool(self, func_name: str, func) -> ToolDefinition:
        """Convert Python function to ToolDefinition"""
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or f"Function: {func_name}"
        is_streaming = inspect.isasyncgenfunction(func)
        
        # Extract parameters with type hints
        parameters = []
        for param_name, param in sig.parameters.items():
            param_type = self._parse_python_type(param.annotation)
            is_required = param.default == inspect.Parameter.empty
            
            # Try to extract description from docstring
            param_desc = self._extract_param_description(doc, param_name)
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=param_desc or f"Parameter: {param_name}",
                required=is_required
            ))
        
        # Extract return type
        return_annotation = sig.return_annotation
        returns = None
        if return_annotation != inspect.Signature.empty:
            returns = {
                "type": self._parse_python_type(return_annotation),
                "description": "Function return value"
            }
        
        return ToolDefinition(
            name=func_name,
            type="function",
            description=doc.split('\n')[0][:200],
            parameters=parameters,
            returns=returns,
            source=self.source_name,
            metadata={
                "module": func.__module__,
                "file": inspect.getfile(func),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "supports_streaming": is_streaming,
            }
        )
    
    def _extract_param_description(self, docstring: str, param_name: str) -> Optional[str]:
        """Extract parameter description from docstring (basic implementation)"""
        if not docstring:
            return None
        
        # Look for common docstring patterns: Args:, Parameters:, :param name:
        lines = docstring.split('\n')
        in_params = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if we're entering parameters section
            if stripped.lower() in ['args:', 'arguments:', 'parameters:']:
                in_params = True
                continue
            
            # Check if we're leaving parameters section
            if in_params and stripped.lower() in ['returns:', 'raises:', 'examples:']:
                break
            
            # Look for parameter description
            if in_params and param_name in line:
                # Extract description after parameter name
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return None


class CodeExecToolDiscoverer(ToolDiscoveryService):
    """Discovers code execution capabilities"""
    
    def __init__(self):
        super().__init__("code_exec")
    
    async def discover(self) -> Dict[str, ToolDefinition]:
        """
        Register code execution as a special tool.
        This is a synthetic tool definition for sandboxed Python execution.
        """
        code_exec_tool = ToolDefinition(
            name="code_exec",
            type="code_exec",
            description="Execute Python code in a sandboxed environment. Supports data analysis, calculations, and transformations.",
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="Python code to execute. Can use variables from context.",
                    required=True
                ),
                ToolParameter(
                    name="context",
                    type="object",
                    description="Variables to make available in the execution context",
                    required=False
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Execution timeout in seconds (default: 30)",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "Execution result with stdout, return value, and any errors"
            },
            source=self.source_name,
            metadata={
                "capabilities": ["data_analysis", "calculations", "transformations"],
                "sandbox": "restricted_builtins",
                "discovered_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {"code_exec": code_exec_tool}


class MCPRegistryDiscoverer(ToolDiscoveryService):
    """Discovers MCP servers and tools from an external registry endpoint.

    The registry returns servers and (optionally) tool metadata. This discoverer
    advertises tools as suggestions requiring install/enablement, enabling
    progressive disclosure with user approval.
    """

    def __init__(self, registry_url: str):
        super().__init__("mcp_registry")
        self.registry_url = registry_url

    async def discover(self) -> Dict[str, ToolDefinition]:
        discovered: Dict[str, ToolDefinition] = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.registry_url, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except Exception:
            return discovered

        servers = data.get("servers", []) if isinstance(data, dict) else []
        for srv in servers:
            server_name = srv.get("name") or srv.get("id") or "server"
            domain = srv.get("domain") or server_name
            for tool in srv.get("tools", []):
                tname = tool.get("name") or f"{server_name}_tool"
                desc = tool.get("description", f"Tool from {server_name} (registry)")
                params = []
                for p in tool.get("parameters", []):
                    params.append(ToolParameter(
                        name=p.get("name", "arg"),
                        type=p.get("type", "string"),
                        description=p.get("description", ""),
                        required=bool(p.get("required", False)),
                    ))
                td = ToolDefinition(
                    name=tname,
                    type="mcp",
                    description=desc,
                    parameters=params,
                    source=self.source_name,
                    metadata={
                        "server": server_name,
                        "requires_install": True,
                        "registry_url": self.registry_url,
                    },
                    domain=domain,
                )
                discovered[td.name] = td
        return discovered


class ToolDiscoveryOrchestrator:
    """
    Orchestrates multiple discovery services and manages caching.
    
    This is the main entry point for tool discovery in the system.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_hours: int = 24):
        """
        Args:
            cache_dir: Directory to cache discovered tools. 
                      Defaults to ~/.toolweaver/
        """
        self.discoverers: List[ToolDiscoveryService] = []
        self.cache_dir = cache_dir or Path.home() / ".toolweaver"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "discovered_tools.json"
        self.cache_ttl_hours = cache_ttl_hours
    
    def register_discoverer(self, discoverer: ToolDiscoveryService):
        """Register a discovery service"""
        self.discoverers.append(discoverer)
    
    async def discover_all(self, use_cache: bool = True, cache_ttl_hours: Optional[int] = None) -> ToolCatalog:
        """
        Run all registered discoverers and build a unified ToolCatalog.
        
        Args:
            use_cache: Whether to use cached results if available
            cache_ttl_hours: Cache time-to-live in hours
        
        Returns:
            ToolCatalog with all discovered tools
        """
        # Try to load from cache
        ttl = cache_ttl_hours if cache_ttl_hours is not None else self.cache_ttl_hours
        if use_cache and self.cache_file.exists():
            cached_catalog = self._load_cache()
            if cached_catalog and self._is_cache_valid(cached_catalog, ttl):
                print(f"Using cached tools: {len(cached_catalog.tools)} tools from cache")
                return cached_catalog
        
        # Run discovery
        start_time = datetime.now(timezone.utc)
        print(f"Starting tool discovery with {len(self.discoverers)} discoverers...")
        
        # Run all discoverers in parallel
        discovery_tasks = [d.discover() for d in self.discoverers]
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Build unified catalog
        catalog = ToolCatalog(
            discovered_at=start_time,
            source="orchestrator",
            version="1.0"
        )
        
        metrics = DiscoveryMetrics()
        
        for discoverer, result in zip(self.discoverers, results):
            if isinstance(result, Exception):
                error_msg = f"Discoverer '{discoverer.source_name}' failed: {result}"
                print(f"Warning: {error_msg}")
                metrics.errors.append(error_msg)
                continue
            
            # Add tools to catalog
            for tool_name, tool_def in result.items():
                catalog.add_tool(tool_def)
                metrics.total_tools_found += 1
                metrics.sources[discoverer.source_name] = \
                    metrics.sources.get(discoverer.source_name, 0) + 1
        
        # Record metrics
        end_time = datetime.now(timezone.utc)
        metrics.discovery_duration_ms = (end_time - start_time).total_seconds() * 1000
        catalog.metadata["discovery_metrics"] = metrics.model_dump()
        
        # Phase 6: Always add tool_search_tool
        try:
            from .tool_search_tool import get_tool_search_definition
            tool_search_def = get_tool_search_definition()
            catalog.add_tool(tool_search_def)
            metrics.total_tools_found += 1
            metrics.sources["built-in"] = metrics.sources.get("built-in", 0) + 1
            print(f"Added tool_search_tool to catalog")
        except Exception as e:
            print(f"Warning: Failed to add tool_search_tool: {e}")
        
        # Cache results
        if use_cache:
            self._save_cache(catalog)
        
        print(f"Discovery complete: {metrics.total_tools_found} tools found in {metrics.discovery_duration_ms:.0f}ms")
        print(f"  Sources: {metrics.sources}")
        
        return catalog
    
    def _load_cache(self) -> Optional[ToolCatalog]:
        """Load cached tool catalog"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            return ToolCatalog(**data)
        except Exception as e:
            print(f"Failed to load cache: {e}")
            return None
    
    def _save_cache(self, catalog: ToolCatalog):
        """Save tool catalog to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                # Use model_dump() to convert to dict
                json.dump(catalog.model_dump(), f, indent=2, default=str)
            print(f"Cached {len(catalog.tools)} tools to {self.cache_file}")
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def _is_cache_valid(self, catalog: ToolCatalog, ttl_hours: int) -> bool:
        """Check if cached catalog is still valid"""
        age = datetime.now(timezone.utc) - catalog.discovered_at
        return age.total_seconds() < (ttl_hours * 3600)
    
    def invalidate_cache(self):
        """Delete the cache file to force re-discovery"""
        if self.cache_file.exists():
            self.cache_file.unlink()
            print(f"Cache invalidated: {self.cache_file}")


# Convenience function for quick discovery
async def discover_tools(
    mcp_client=None,
    function_modules: Optional[List[Any]] = None,
    include_code_exec: bool = True,
    use_cache: bool = True,
    a2a_client=None,
    registry_url: Optional[str] = None,
) -> ToolCatalog:
    """
    Convenience function to discover tools from common sources.
    
    Args:
        mcp_client: MCPClientShim instance to discover MCP tools
        function_modules: List of Python modules to scan for functions
        include_code_exec: Whether to include code execution capability
        use_cache: Whether to use cached discovery results
    
    Returns:
        ToolCatalog with all discovered tools
    
    Example:
        from orchestrator._internal.dispatch import workers
        from orchestrator._internal.dispatch import functions
        catalog = await discover_tools(
            mcp_client=mcp_client,
            function_modules=[workers, functions],
            include_code_exec=True
        )
    """
    orchestrator = ToolDiscoveryOrchestrator()
    
    # Register MCP discoverer
    if mcp_client:
        orchestrator.register_discoverer(MCPToolDiscoverer(mcp_client))

    # Register A2A agent discoverer
    if a2a_client:
        from .agent_discovery import AgentDiscoverer  # Lazy import to avoid circular dependency

        orchestrator.register_discoverer(AgentDiscoverer(a2a_client))

    # Register external MCP registry discoverer
    reg = registry_url or os.getenv("MCP_REGISTRY_URL")
    if reg:
        orchestrator.register_discoverer(MCPRegistryDiscoverer(reg))
    
    # Register function discoverers
    if function_modules:
        for module in function_modules:
            orchestrator.register_discoverer(FunctionToolDiscoverer(module))
    
    # Register code execution
    if include_code_exec:
        orchestrator.register_discoverer(CodeExecToolDiscoverer())
    
    return await orchestrator.discover_all(use_cache=use_cache)
