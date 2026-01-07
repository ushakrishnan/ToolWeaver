# ResourceLimits

## Simple Explanation
Configure resource constraints for sandbox execution: memory limits, CPU usage, execution timeout, and maximum tool calls.

## Technical Explanation
`ResourceLimits` is a dataclass that defines resource boundaries for code execution environments. Use it with `SandboxEnvironment` or `dispatch_agents` to prevent runaway processes, enforce quotas, and protect infrastructure.

**Import Path**
```python
from orchestrator import ResourceLimits
```

**Signature**
```python
@dataclass
class ResourceLimits:
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    timeout_seconds: int = 30
    max_tool_calls: int = 100
    max_concurrent: int = 5
    max_total_cost_usd: float = 10.0
```

## When to Use
- **Sandbox Execution**: Prevent LLM-generated code from consuming excessive resources
- **Parallel Dispatch**: Limit concurrent agent calls and total cost
- **Production Safety**: Enforce quotas to protect infrastructure and budgets
- **Multi-Tenancy**: Isolate user workloads with per-request limits

## Key Properties
- `max_memory_mb`: Maximum memory allocation (default: 512 MB)
- `max_cpu_percent`: CPU usage cap as percentage (default: 50%)
- `timeout_seconds`: Execution timeout (default: 30 seconds)
- `max_tool_calls`: Maximum number of tool invocations (default: 100)
- `max_concurrent`: Maximum parallel executions (default: 5)
- `max_total_cost_usd`: Budget cap for LLM calls (default: $10.00)

## Examples

### Basic Sandbox Limits
```python
from orchestrator import ResourceLimits, SandboxEnvironment

# Create conservative limits for untrusted code
limits = ResourceLimits(
    max_memory_mb=256,
    max_cpu_percent=30.0,
    timeout_seconds=15,
    max_tool_calls=50
)

sandbox = SandboxEnvironment(limits=limits)
result = await sandbox.execute_code(user_code)
```

### Parallel Dispatch with Quotas
```python
from orchestrator import ResourceLimits
from orchestrator.tools.sub_agent import dispatch_agents

# Limit parallel processing and cost
limits = ResourceLimits(
    max_concurrent=10,
    max_total_cost_usd=5.0,
    timeout_seconds=60
)

results = await dispatch_agents(
    template="analyze {{item}}",
    arguments=[{"item": f"receipt_{i}"} for i in range(100)],
    agent_name="analyzer",
    model="gpt-4o-mini",
    limits=limits
)
```

### Production Safety
```python
from orchestrator import ResourceLimits, ProgrammaticToolExecutor

# Strict limits for production workloads
production_limits = ResourceLimits(
    max_memory_mb=1024,
    max_cpu_percent=75.0,
    timeout_seconds=120,
    max_tool_calls=200,
    max_total_cost_usd=25.0
)

executor = ProgrammaticToolExecutor(
    catalog=tool_catalog,
    limits=production_limits
)
```

## See Also
- [SandboxEnvironment](SandboxEnvironment.md) — Isolated execution environment
- [ProgrammaticToolExecutor](ProgrammaticToolExecutor.md) — Execute code with resource limits
- [How to Run Parallel Dispatch](../../../how-to/parallel-dispatch.md) — Parallel execution guide
- [Sample 07: Caching Optimization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/07-caching-optimization) — Resource management patterns

## Notes
- Memory and CPU limits require OS-level enforcement (Linux cgroups or similar)
- Cost tracking requires model pricing configuration
- Timeout applies to total execution time, not individual operations
- Use lower limits for untrusted code, higher for internal workflows
