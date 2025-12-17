# ToolWeaver Package Structure

## Overview

ToolWeaver 1.0 refactored the orchestrator package into thematic subpackages for clarity and maintainability. All top-level imports remain backward-compatible via thin shims.

## Subpackage Organization

```
orchestrator/
├── __init__.py                    # Main exports
├── models.py                      # Core data models (unchanged)
│
├── workflows/                     # Workflow orchestration
│   ├── __init__.py               # Exports: WorkflowTemplate, WorkflowExecutor, etc.
│   ├── workflow.py               # Workflow templates and execution
│   ├── workflow_library.py       # Pattern detection and library
│   └── control_flow_patterns.py  # Control-flow patterns (loops, retries, etc.)
│
├── execution/                     # Code execution layer
│   ├── __init__.py               # Exports: SandboxEnvironment, ProgrammaticToolExecutor, etc.
│   ├── sandbox.py                # Secure sandbox with resource limits
│   ├── programmatic_executor.py  # Tool calling via code gen
│   ├── code_generator.py         # Stub/code generation
│   ├── small_model_worker.py     # Small model integration
│   └── code_exec_worker.py       # Code execution worker
│
├── tools/                         # Tool discovery and search
│   ├── __init__.py               # Exports: ToolDiscoveryService, ToolSearchEngine, etc.
│   ├── tool_discovery.py         # Tool discovery orchestration
│   ├── tool_executor.py          # Tool execution (call_tool)
│   ├── tool_filesystem.py        # Tool filesystem abstraction
│   ├── tool_search.py            # Hybrid BM25 + embedding search
│   ├── tool_search_tool.py       # Dynamic tool search tool
│   ├── vector_search.py          # Qdrant vector search
│   └── sharded_catalog.py        # Domain-based catalog sharding
│
├── infra/                         # Infrastructure utilities
│   ├── __init__.py               # Exports: RedisCache, MCPClientShim
│   ├── redis_cache.py            # Distributed Redis cache
│   └── mcp_client.py             # Model Context Protocol client
│
├── observability/                 # Monitoring and context tracking
│   ├── __init__.py               # Exports: ToolUsageMonitor, create_monitor, etc.
│   ├── monitoring.py             # Tool usage monitoring
│   ├── monitoring_backends.py    # Backends (Local, Wandb, Prometheus)
│   └── context_tracker.py        # Context tracking
│
├── assessment/                    # Evaluation framework
│   ├── __init__.py               # Exports: AgentEvaluator, TaskResult, BenchmarkResults
│   └── evaluation.py             # Agent evaluation
│
├── dispatch/                      # Central dispatcher
│   ├── __init__.py               # Exports: register_function, dispatch_step, workers
│   ├── hybrid_dispatcher.py      # Hybrid dispatcher (function calling + MCP)
│   ├── functions.py              # Registered functions
│   └── workers.py                # Worker callables (OCR, parser, categorizer)
│
├── planning/                      # Task planning
│   ├── __init__.py               # Exports: LargePlanner
│   └── planner.py                # Large model planner
│
└── runtime/                       # Orchestration runtime
    ├── __init__.py               # Exports: execute_plan, final_synthesis, get_monitor, retry
    └── orchestrator.py           # Plan execution and synthesis
```

## Backward Compatibility

All existing imports from the top-level `orchestrator` package continue to work via thin re-export shims:

```python
# These imports still work (via shims):
from orchestrator.workflow import WorkflowTemplate
from orchestrator.sandbox import SandboxEnvironment
from orchestrator.planner import LargePlanner
from orchestrator.monitoring import create_monitor
# ... etc.
```

## Recommended Import Patterns

### For New Code
Use the subpackage imports for clarity:

```python
# Workflows
from orchestrator.workflows import WorkflowTemplate, WorkflowExecutor
from orchestrator.workflows.control_flow_patterns import create_loop_code

# Execution
from orchestrator.execution import SandboxEnvironment, ProgrammaticToolExecutor
from orchestrator.execution import create_sandbox

# Tools
from orchestrator.tools import ToolDiscoveryService, ToolSearchEngine
from orchestrator.tools import discover_tools, search_tools

# Monitoring
from orchestrator.observability import ToolUsageMonitor, create_monitor
from orchestrator.observability import print_metrics_report

# Planning & Runtime
from orchestrator.planning import LargePlanner
from orchestrator.runtime import execute_plan, final_synthesis
```

### For Existing Code
No changes needed! Top-level imports remain supported:

```python
from orchestrator.workflow import WorkflowTemplate
from orchestrator.sandbox import SandboxEnvironment
# ... these continue to work
```

## Optional Dependencies

Some subpackages have optional dependencies that fall back gracefully when unavailable:

- **tools.tool_search**: Requires `numpy`, `sentence-transformers`, `rank_bm25` for full hybrid search; falls back to lightweight token-based scoring.
- **tools.vector_search**: Requires `qdrant-client` for Qdrant integration; falls back to in-memory token similarity.
- **infra.redis_cache**: Requires `redis` package; falls back to file cache.
- **observability.monitoring_backends**: Requires `wandb`, `prometheus_client` for specific backends; gracefully skips unavailable backends.

When optional deps are missing, shims provide lightweight fallback implementations that satisfy the API contract and allow tests/code to run.

## Migration Notes

- All file moves preserve the public API; internal module paths updated but exports unchanged.
- Tests validated: 394 passing after refactor (core suites green; optional-dep tests skip or stub when deps unavailable).
- Commits structured: each layer moved with validation and commit (workflows → execution → tools → infra → observability → assessment → dispatch → planning/runtime).

## Further Reading

- [IMPLEMENTATION.md](developer-guide/IMPLEMENTATION.md) - Code structure and patterns
- [ARCHITECTURE.md](developer-guide/ARCHITECTURE.md) - System design
- [MIGRATION_GUIDE.md](reference/MIGRATION_GUIDE.md) - Upgrading between versions
