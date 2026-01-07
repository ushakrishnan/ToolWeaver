# API Exports Index

Deep links for ultra-granular browsing, with brief descriptions of what, when, and how. For HTTP endpoints, use the [REST API Overview](../../api-rest/overview.md).

## Decorators
- ### Decorators Overview
- Why: Fastest way to convert Python functions into discoverable, callable tools/agents.
- What: Schema inferred from type hints; registered into the catalog for planners, REST, and CLI.
- When: Use `mcp_tool` for public tools, `tool` for lightweight utilities, `a2a_agent` for delegatable agents.
- [tool](decorators/tool.md) — Register a generic tool from a Python function.
- [mcp_tool](decorators/mcp_tool.md) — Register an MCP-style tool with structured parameters for discovery.
- [a2a_agent](decorators/a2a_agent.md) — Wrap an agent function to delegate via the A2A client.

## Templates
- ### Templates Overview
- Why: Maximum control over tool definitions, parameters, validation, and lifecycle.
- What: Class-based tools with explicit schemas and custom behaviors.
- When: Use when decorators are too limiting or for sandbox/code-exec scenarios.
- [BaseTemplate](templates/base_template.md) — Abstract base for custom template behaviors.
- [FunctionToolTemplate](templates/function_tool_template.md) — Define function-style tools with explicit schemas.
- [MCPToolTemplate](templates/mcp_tool_template.md) — MCP-flavored template with richer discovery metadata.
- [CodeExecToolTemplate](templates/code_exec_tool_template.md) — Execute user-provided code with sandbox controls.
- [AgentTemplate](templates/agent_template.md) — Define agent-style tools (evaluators, classifiers).

## YAML Loaders
- ### YAML Loaders Overview
- Why: Configuration-driven registration for repeatable deployments and non-Python authors.
- What: Load single files or directories of YAML; validated schemas with clear error types.
- When: Use in DevOps pipelines or to share tools without Python code changes.
- [load_tools_from_yaml](yaml-loaders/load_tools_from_yaml.md) — Load a single YAML tool definition.
- [load_tools_from_directory](yaml-loaders/load_tools_from_directory.md) — Bulk load YAML tool definitions from a directory.
- [YAMLLoaderError](yaml-loaders/YAMLLoaderError.md) — General loading error (IO/parse).
- [YAMLValidationError](yaml-loaders/YAMLValidationError.md) — Schema validation error.
- [WorkerResolutionError](yaml-loaders/WorkerResolutionError.md) — Referenced backend/worker cannot be resolved.

## Skill Bridge
- ### Skill Bridge Overview
- Why: Persist and share tools as reusable skills across teams/environments.
- What: Save, load, sync skills; list tools backed by skills.
- When: Promote approved tools to a registry for standardized reuse.
- [save_tool_as_skill](skill-bridge/save_tool_as_skill.md) — Persist a tool as a reusable skill package.
- [load_tool_from_skill](skill-bridge/load_tool_from_skill.md) — Load a skill-backed tool for reuse.
- [get_tool_skill](skill-bridge/get_tool_skill.md) — Retrieve a tool’s associated skill metadata.
- [sync_tool_with_skill](skill-bridge/sync_tool_with_skill.md) — Synchronize tool changes to its skill package.
- [get_skill_backed_tools](skill-bridge/get_skill_backed_tools.md) — List tools backed by skills.

## Discovery
- ### Discovery Overview
- Why: Find and browse the right tools for planners, UIs, and workflows.
- What: List all tools, keyword/domain search, semantic matching, and progressive browsing.
- When: Build catalogs, surface tools to users, or feed planners.
- [get_available_tools](discovery/get_available_tools.md) — Return all registered tools.
- [search_tools](discovery/search_tools.md) — Filter tools by domain/keywords.
- [get_tool_info](discovery/get_tool_info.md) — Detailed definition for a tool by name.
- [list_tools_by_domain](discovery/list_tools_by_domain.md) — List tools within a given domain.
- [semantic_search_tools](discovery/semantic_search_tools.md) — Natural language matching against tool descriptions.
- [browse_tools](discovery/browse_tools.md) — Progressive detail browsing suitable for CLI/UX.

## Plugins
- ### Plugins Overview
- Why: Extend ToolWeaver with new discovery sources, integrations, and custom behaviors.
- What: Register, list, get, unregister, and auto-discover plugins.
- When: Add bespoke capabilities without modifying core.
- [register_plugin](plugins/register_plugin.md) — Register a plugin instance.
- [unregister_plugin](plugins/unregister_plugin.md) — Remove a plugin by name.
- [get_plugin](plugins/get_plugin.md) — Retrieve a plugin instance.
- [list_plugins](plugins/list_plugins.md) — List all registered plugins.
- [discover_plugins](plugins/discover_plugins.md) — Scan and auto-register discoverable plugins.

## Configuration
- ### Configuration Overview
- Why: Control runtime behavior via environment variables and defaults.
- What: Read, reset, and validate configuration; typical fields include cache path, Redis URL, skill path, and logging.
- When: Setup environment, troubleshoot issues, and standardize deployments.
- [get_config](configuration/get_config.md) — Read current runtime configuration.
- [reset_config](configuration/reset_config.md) — Reset cached configuration state.
- [validate_config](configuration/validate_config.md) — Validate configuration and return warnings/errors.

## Logging
- ### Logging Overview
- Why: Provide observability with safety (secrets never leak into logs).
- What: Module-specific loggers, global log level, and a secrets redactor installed via debug mode.
- When: Standardize logging across apps and CI while protecting credentials.
- [get_logger](logging/get_logger.md) — Get a module-specific logger with safe defaults.
- [set_log_level](logging/set_log_level.md) — Set global log level.
- [enable_debug_mode](logging/enable_debug_mode.md) — Install secrets redactor and enable safe logging.

## A2A Client
- ### A2A Client Overview
- Why: Delegate work to other agents and compose agent networks.
- What: Capabilities, delegation requests/responses, and `A2AClient` for execution.
- When: Orchestrate multi-agent workflows and federated capabilities.
- [AgentCapability](a2a-client/AgentCapability.md) — Describe a capability an agent provides.
- [AgentDelegationRequest](a2a-client/AgentDelegationRequest.md) — Request payload to delegate to an agent.
- [AgentDelegationResponse](a2a-client/AgentDelegationResponse.md) — Response payload from delegated agent.
- [A2AClient](a2a-client/A2AClient.md) — Client to delegate requests to agents.

## Sandbox Execution
- ### Sandbox Execution Overview
- Why: Execute code and tools with resource limits and isolation for safety.
- What: Sandbox environment, resource limits, small model workers, and programmatic tool execution.
- When: LLM-generated code execution, tool orchestration, or multi-step workflows requiring isolation.
- [SandboxEnvironment](execution/SandboxEnvironment.md) — Isolated execution environment for code.
- [ResourceLimits](execution/ResourceLimits.md) — Configure memory, CPU, timeout, and execution limits.
- [SmallModelWorker](execution/SmallModelWorker.md) — Execute tools using small, cost-efficient models.
- [ProgrammaticToolExecutor](execution/ProgrammaticToolExecutor.md) — Execute LLM-generated code that orchestrates tools.

## Planning & Orchestration
- ### Planning & Orchestration Overview
- Why: Build execution plans with large models and execute them efficiently.
- What: LargePlanner for DAG creation and execute_plan for runtime execution.
- When: Complex multi-step workflows requiring upfront planning with large models, then execution with small models.
- [LargePlanner](orchestration/LargePlanner.md) — Create DAG execution plans using large models (GPT-4, etc.).
- [execute_plan](orchestration/execute_plan.md) — Execute planned workflows with configured workers.

## Version & Security
- ### Version & Security Overview
- Why: Track package version and leverage built-in safety features.
- What: `__version__` string and an auto-installed secrets redactor on import.
- When: Display version in UIs/logs and ensure safe logging defaults.
- [__version__](version-security/__version__.md) — Package version string.
- [secrets redactor](version-security/secrets_redactor.md) — Auto-installed redactor to prevent secrets appearing in logs.
