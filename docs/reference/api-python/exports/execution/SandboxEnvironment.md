# SandboxEnvironment

## Simple Explanation
Isolated Python execution environment with resource limits and security restrictions for running untrusted code safely.

## Technical Explanation
`SandboxEnvironment` creates a restricted Python runtime that prevents malicious or buggy code from affecting the host system. It enforces resource limits, blocks dangerous imports, and isolates filesystem and network access.

**Import Path**
```python
from orchestrator import SandboxEnvironment
```

**Signature**
```python
class SandboxEnvironment:
    def __init__(
        self,
        limits: ResourceLimits | None = None,
        allowed_imports: list[str] | None = None,
        filesystem_access: bool = False
    ):
        ...
    
    async def execute_code(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None
    ) -> Any:
        ...
```

## When to Use
- **LLM-Generated Code**: Execute code from GPT-4, Claude, etc. safely
- **User Scripts**: Run user-provided code without system access
- **Tool Orchestration**: Execute orchestration code with tool access
- **Multi-Tenancy**: Isolate different users' code execution

## Key Methods
- `execute_code(code, globals_dict)`: Execute Python code in sandbox
- `reset()`: Clear sandbox state for new execution
- `get_logs()`: Retrieve stdout/stderr from execution

## Examples

### Basic Sandbox Usage
```python
from orchestrator import SandboxEnvironment, ResourceLimits

# Create sandbox with limits
sandbox = SandboxEnvironment(
    limits=ResourceLimits(
        max_memory_mb=256,
        timeout_seconds=10
    )
)

# Execute untrusted code
code = """
result = sum([i**2 for i in range(100)])
return result
"""

result = await sandbox.execute_code(code)
print(f"Result: {result}")  # Result: 328350
```

### With Custom Globals
```python
from orchestrator import SandboxEnvironment

sandbox = SandboxEnvironment()

# Provide functions/data to sandbox
globals_dict = {
    "data": [1, 2, 3, 4, 5],
    "multiply": lambda x, y: x * y
}

code = """
# Access provided globals
total = sum(data)
doubled = multiply(total, 2)
return doubled
"""

result = await sandbox.execute_code(code, globals_dict=globals_dict)
print(f"Result: {result}")  # Result: 30
```

### Restricted Imports
```python
from orchestrator import SandboxEnvironment

# Only allow safe imports
sandbox = SandboxEnvironment(
    allowed_imports=["json", "math", "datetime"]
)

# This works
code1 = """
import json
return json.dumps({"key": "value"})
"""
result1 = await sandbox.execute_code(code1)  # ✓ Success

# This fails
code2 = """
import os  # Not in allowed_imports
os.system("rm -rf /")
"""
# ✗ Raises ImportError: Import 'os' not allowed
```

### Timeout Protection
```python
from orchestrator import SandboxEnvironment, ResourceLimits

sandbox = SandboxEnvironment(
    limits=ResourceLimits(timeout_seconds=5)
)

# This will timeout
code = """
while True:  # Infinite loop
    pass
"""

try:
    await sandbox.execute_code(code)
except TimeoutError:
    print("Code exceeded 5 second timeout")
```

### Memory Limit
```python
from orchestrator import SandboxEnvironment, ResourceLimits

sandbox = SandboxEnvironment(
    limits=ResourceLimits(max_memory_mb=100)
)

# This will fail due to memory limit
code = """
# Try to allocate 500MB
big_list = [0] * (500 * 1024 * 1024 // 8)
"""

try:
    await sandbox.execute_code(code)
except MemoryError:
    print("Code exceeded 100MB memory limit")
```

## Security Features

### Import Restrictions
Only whitelisted modules are allowed:
- **Safe**: `json`, `math`, `datetime`, `asyncio`, `typing`
- **Blocked**: `os`, `sys`, `subprocess`, `socket`, `requests`

### Filesystem Isolation
```python
sandbox = SandboxEnvironment(filesystem_access=False)

# This fails
code = """
with open("/etc/passwd", "r") as f:
    return f.read()
"""
# ✗ Raises PermissionError
```

### Network Isolation
Network access is blocked by default. External API calls fail.

### Resource Enforcement
- CPU usage capped at configured percentage
- Memory allocation limited
- Execution time bounded
- No subprocess creation

## See Also
- [ResourceLimits](ResourceLimits.md) — Configure sandbox constraints
- [ProgrammaticToolExecutor](ProgrammaticToolExecutor.md) — Execute code with tools
- [How to Orchestrate with Code](../../../how-to/orchestrate-with-code.md) — Orchestration guide

## Notes
- Requires Linux with cgroups for full resource enforcement on Windows/macOS
- Async code supported (use `await` for async operations)
- Sandbox state persists between calls (use `reset()` to clear)
- Logs available via `get_logs()` for debugging
- Consider using Docker for stronger isolation in production
