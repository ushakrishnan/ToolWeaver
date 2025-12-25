# Public API

This page orients you to all ToolWeaver interfaces.

**Choose your path**
- Python API (how-to guides by topic): [Python Public API Overview](api-python/overview.md)
- Python exports (fast lookup): [API Exports Index](api-python/exports/index.md)
- REST API (HTTP endpoints): [REST API Overview](api-rest/overview.md)
- Runnable examples: [Samples index](../samples/index.md)

**Python exports map (by group)**
- Decorators: `tool`, `mcp_tool`, `a2a_agent`
- Templates: `BaseTemplate`, `FunctionToolTemplate`, `MCPToolTemplate`, `CodeExecToolTemplate`, `AgentTemplate`, `register_template`
- YAML loaders: `load_tools_from_yaml`, `load_tools_from_directory`, `YAMLLoaderError`, `YAMLValidationError`, `WorkerResolutionError`
- Skills: `save_tool_as_skill`, `load_tool_from_skill`, `get_tool_skill`, `sync_tool_with_skill`, `get_skill_backed_tools`
- Discovery: `get_available_tools`, `search_tools`, `get_tool_info`, `list_tools_by_domain`, `semantic_search_tools`, `browse_tools`
- Plugins: `register_plugin`, `unregister_plugin`, `get_plugin`, `list_plugins`, `discover_plugins`
- Configuration: `get_config`, `reset_config`, `validate_config`
- Logging: `get_logger`, `set_log_level`, `enable_debug_mode`
- Agent-to-agent client: `AgentCapability`, `AgentDelegationRequest`, `AgentDelegationResponse`, `A2AClient`
