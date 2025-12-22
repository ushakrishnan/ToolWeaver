"""
Internal implementation details.

WARNING: This module is NOT part of the public API.
Do NOT import from here in your code.

Contents of _internal may change without warning between versions.
If you need something from here, please file an issue on GitHub.

Public API is in orchestrator/__init__.py
"""

# Internal modules (not for public use):
# - logger.py - Structured logging
# - errors.py - Custom exceptions
# - validation.py - Runtime validation
# - runtime_validation.py - Type/parameter validation
# - public_legacy.py - Legacy compatibility shims
# - assessment/ - Evaluation framework
# - dispatch/ - Tool/agent dispatching
# - execution/ - Code execution, sandboxing, workspace
# - infra/ - MCP/A2A clients, Redis cache
# - observability/ - Monitoring, tracing
# - planning/ - Multi-step planning
# - runtime/ - Orchestrator runtime
# - workflows/ - Workflow engine
