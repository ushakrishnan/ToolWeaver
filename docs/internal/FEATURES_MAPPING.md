# ToolWeaver Features Mapping

## Available in Public API (orchestrator.__init__)

### Core Tool Registration
- `@tool` - Generic tool decorator
- `@mcp_tool` - MCP tool decorator
- `@a2a_agent` - Agent tool decorator

### Tool Discovery
- `get_available_tools()` - Get all registered tools
- `search_tools(*, query, domain, type_filter, use_semantic, ...)` - Search tools (keyword-only args!)
- `get_tool_info(name)` - Get specific tool info
- `list_tools_by_domain(domain)` - List tools by domain
- `semantic_search_tools(query, ...)` - Semantic search
- `browse_tools()` - Browse all tools

### YAML Workflows
- `load_tools_from_yaml(yaml_path)` - Load tools from YAML
- `load_tools_from_directory(dir_path)` - Load all YAML in directory

### Skill Bridge
- `save_tool_as_skill(tool_name, skill_path)` - Export tool as skill
- `load_tool_from_skill(skill_path)` - Import tool from skill
- `get_tool_skill(tool_name)` - Get associated skill
- `sync_tool_with_skill(tool_name)` - Sync with skill library

### Configuration
- `get_config()` - Get current config
- `reset_config()` - Reset to defaults
- `validate_config()` - Validate current config

### Logging
- `get_logger(name)` - Get logger instance
- `set_log_level(level)` - Set log level
- `enable_debug_mode()` - Enable debug logging

### Agent-to-Agent (A2A)
- `A2AClient` - Client for agent delegation
- `AgentCapability` - Agent capability definition
- `AgentDelegationRequest` - Delegation request model
- `AgentDelegationResponse` - Delegation response model

## Available in Internal Modules (Not Exported But Usable)

### Sub-Agent Dispatch (orchestrator.tools.sub_agent)
- `dispatch_agents(template, arguments, limits, executor, ...)` - Parallel agent dispatch
- `rank_by_metric(results, metric)` - Rank results by metric
- `DispatchResourceLimits` - Resource limits config
- `SubAgentTask` - Task definition
- `SubAgentResult` - Result container

### Tool Registry & Selection (orchestrator.selection.registry)
- `ToolRegistry` - Registry with cost-aware selection
- `SelectionConfig` - Cost/latency/reliability weights
- `ErrorRecoveryPolicy` - Error handling policy
- `ErrorStrategy` - RAISE/CONTINUE/FALLBACK/PARTIAL_SUCCESS

### Error Recovery (orchestrator.tools.error_recovery)
- `ErrorRecoveryExecutor` - Execute tools with error handling

### Programmatic Execution (orchestrator._internal.execution.programmatic_executor)
- `ProgrammaticExecutor` - Execute tool chains programmatically
- Allows building and executing tool sequences

### Workflows (orchestrator._internal.workflows)
- `Workflow` - Workflow definition class
- `WorkflowExecutor` - Execute workflows
- `WorkflowLibrary` - Store and retrieve workflows
- `WorkflowStep` - Individual workflow step

## NOT Available (Examples Import These Incorrectly)

❌ `execute_plan` - Old API, removed
❌ `final_synthesis` - Old API, removed  
❌ `orchestrator.orchestrator` module - Old module path, removed
❌ `Orchestrator` class - Old class, removed
❌ `orchestrator.workflow` - Should use `orchestrator._internal.workflows.workflow`
❌ `orchestrator.workflow_library` - Should use `orchestrator._internal.workflows.workflow_library`
❌ `orchestrator.programmatic` - Should use `orchestrator._internal.execution.programmatic_executor`
❌ `orchestrator.caching` - No such module
❌ `orchestrator.monitoring` - No such module (use logging instead)

## Example-to-Feature Mapping

| Example | Should Use | Status |
|---------|-----------|---------|
| 01 | @mcp_tool, search_tools | ✅ Fixed |
| 02 | @mcp_tool + ProgrammaticExecutor | ❌ Needs fix |
| 03 | Standalone MCP test | ✅ OK as-is |
| 04 | semantic_search_tools | ❌ Needs fix |
| 05 | load_tools_from_yaml | ❌ Wrong imports |
| 06 | get_logger, @mcp_tool | ❌ Wrong imports |
| 07 | No caching module exists | ❌ Needs new example |
| 08 | @mcp_tool with model selection | ❌ Wrong imports |
| 09 | ProgrammaticExecutor | ❌ Wrong imports |
| 10 | ProgrammaticExecutor | ❌ Wrong imports |
| 11 | ProgrammaticExecutor | ❌ Wrong imports |
| 12 | ToolRegistry | ❌ Wrong imports |
| 13 | Mock example | ✅ OK as-is |
| 14 | @mcp_tool, ProgrammaticExecutor | ❌ Wrong imports |
| 15 | @mcp_tool, ProgrammaticExecutor | ❌ Wrong imports |
| 16 | A2AClient | ❌ Wrong imports |
| 17 | dispatch_agents, A2AClient | ❌ Wrong imports |
| 18 | @mcp_tool, A2AClient | ❌ Wrong imports |
| 19 | Test file | ✅ Passing |
| 20 | Test file | ✅ Passing |
| 21 | Test file | ✅ Passing |
| 22 | Test file | ✅ Passing |
| 23 | @mcp_tool, templates | ❌ Wrong imports |
| 24 | MCP adapter | ✅ OK as-is |
| 25 | dispatch_agents | ❌ Runtime error |
| 27 | ToolRegistry, SelectionConfig | ❌ Runtime error |
| 28 | dispatch_agents | ❌ Runtime error |

## Implementation Strategy

### Phase 1: Fix Simple Examples (01-04)
1. ✅ Example 01 - Done
2. Example 02 - Rewrite with @mcp_tool + tool chaining
3. Example 03 - Verify or update
4. Example 04 - Use semantic_search_tools

### Phase 2: Fix Feature Examples (05-12)
5. Example 05 - Use load_tools_from_yaml correctly
6. Example 06 - Use get_logger + @mcp_tool
7. Example 07 - Create new example showing tool composition
8. Example 08 - Model selection with @mcp_tool
9-11. Examples 09-11 - ProgrammaticExecutor patterns
12. Example 12 - ToolRegistry usage

### Phase 3: Fix Agent Examples (13-18)
13. Example 13 - Verify mock example
14-15. Examples 14-15 - ProgrammaticExecutor + control flow
16-18. Examples 16-18 - A2AClient + dispatch_agents

### Phase 4: Fix Specialized Examples (19-24)
19-22. Verify test files work as examples
23. Update tool creation guide
24. Verify MCP adapter

### Phase 5: Fix Parallel Examples (25-28)
25. Fix dispatch_agents runtime error
27. Fix ToolRegistry runtime error  
28. Fix quicksort orchestration error

### Phase 6: Testing & Documentation
- Run comprehensive test suite
- Update all READMEs
- Create examples showcase
- Update main README
