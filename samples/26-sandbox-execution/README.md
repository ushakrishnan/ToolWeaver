# Sample 26: Sandbox Execution Environments

## What This Does

Demonstrates how ToolWeaver creates independent execution environments for secure code execution. This sample shows:
- Creating isolated sandbox instances
- Namespace isolation between sandboxes
- Security restrictions and validation
- Resource limits and timeout enforcement
- How ProgrammaticToolExecutor uses sandboxes

**Complexity:** ⭐⭐ Intermediate  
**Concepts:** Sandboxing, code isolation, security, resource limits  
**Time:** 10 minutes

## What You'll Learn

- How `SandboxEnvironment` creates independent execution contexts
- Where and when sandboxes are instantiated
- How namespace isolation prevents variable leakage
- Security mechanisms (AST validation, restricted builtins)
- Resource limit enforcement (timeouts, memory limits)
- Integration with `ProgrammaticToolExecutor`

## Prerequisites

- Python 3.10+
- ToolWeaver installed
- Basic understanding of Python execution model

## Key Concepts

### 1. Independent Execution Environments

Each `SandboxEnvironment` instance creates a completely isolated namespace:

```python
from orchestrator._internal.execution.sandbox import SandboxEnvironment, ResourceLimits

# Create independent sandboxes
sandbox1 = SandboxEnvironment(limits=ResourceLimits(max_duration=10.0))
sandbox2 = SandboxEnvironment(limits=ResourceLimits(max_duration=5.0))

# Variables in sandbox1 are NOT accessible in sandbox2
```

### 2. Where Sandboxes Are Created

**Location**: `orchestrator/_internal/execution/sandbox.py`

**Creation Points**:
1. **Direct instantiation**: `SandboxEnvironment(limits=...)`
2. **Factory function**: `create_sandbox(use_docker=False, limits=...)`
3. **Automatic in ProgrammaticToolExecutor**: Line 107 of `programmatic_executor.py`

```python
# In ProgrammaticToolExecutor.__init__()
self.sandbox = create_sandbox(use_docker=False, limits=sandbox_limits)
```

### 3. Independence Mechanisms

#### Namespace Isolation
Each execution gets:
- Empty `__builtins__`: `{'__builtins__': {}}`
- Only whitelisted safe builtins added
- Fresh `local_vars: {}` dictionary
- User context injected separately

```python
# Internal mechanism (simplified)
safe_globals = {'__builtins__': {}}  # Empty!
for name in SAFE_BUILTINS:
    safe_globals['__builtins__'][name] = getattr(builtins, name)

safe_globals.update(user_context)  # Add user variables
local_vars = {}  # Fresh namespace

exec(compiled_code, safe_globals, local_vars)
```

#### Security Restrictions
- **Forbidden builtins**: `eval`, `exec`, `open`, `__import__`, `compile`
- **Forbidden modules**: `os`, `sys`, `subprocess`, `socket`, `pickle`
- **AST validation**: Code analyzed before execution
- **Timeout enforcement**: `asyncio.wait_for()` with configurable limits

#### I/O Isolation
- stdout/stderr redirected to `StringIO` per execution
- Output captured separately for each sandbox
- Original streams restored after execution

## Setup

No additional setup required beyond ToolWeaver installation.

## Run the Sample

```bash
cd samples/26-sandbox-execution
python sandbox_demo.py
```

## Expected Output

```
================================================================================
SAMPLE 26: Independent Execution Environments
================================================================================

1. Creating Multiple Independent Sandboxes
--------------------------------------------------------------------------------
✓ Sandbox 1 created with 256MB memory limit
✓ Sandbox 2 created with 512MB memory limit
✓ Sandbox 3 created via factory function

2. Demonstrating Namespace Isolation
--------------------------------------------------------------------------------
Sandbox 1 execution: True
  Output: executed in sandbox 1

Sandbox 2 execution: True
  Output: Cannot access sandbox1 variable: name 'secret_var' is not defined

3. Context Injection (Controlled Sharing)
--------------------------------------------------------------------------------
Execution with context: True
  Output: Sum of 5 numbers = 15

4. I/O Stream Isolation
--------------------------------------------------------------------------------
Sandbox 1 captured stdout:
  Message from Sandbox 1
  Line 2 from Sandbox 1

Sandbox 2 captured stdout:
  Message from Sandbox 2
  Line 2 from Sandbox 2

5. Security Restrictions
--------------------------------------------------------------------------------
Dangerous code execution: False
  Error: Forbidden module: os
  Error Type: SecurityError

6. Timeout Enforcement (Resource Limits)
--------------------------------------------------------------------------------
Slow code execution: False
  Error: Execution timeout after 0.5s
  Duration: 0.500s

7. How Isolation Works: Safe Globals Dictionary
--------------------------------------------------------------------------------
...

SUMMARY: How Independent Execution Environments Are Created
================================================================================
...
```

## Code Structure

```
samples/26-sandbox-execution/
├── README.md           # This file
├── sandbox_demo.py     # Main demonstration script
├── requirements.txt    # Dependencies
└── .env.example        # Environment template
```

## Key Files Reference

| File | Description |
|------|-------------|
| `orchestrator/_internal/execution/sandbox.py` | SandboxEnvironment implementation |
| `orchestrator/_internal/execution/programmatic_executor.py` | Uses sandbox for code execution |
| `tests/test_sandbox.py` | Comprehensive sandbox tests |

## What Happens Under the Hood

### Step 1: Sandbox Creation
```python
sandbox = SandboxEnvironment(limits=ResourceLimits(...))
```

### Step 2: Code Validation (AST Analysis)
```python
sandbox.validate_code(code)  # Checks for forbidden operations
```

### Step 3: Safe Globals Creation
```python
safe_globals = sandbox._create_safe_globals(context)
# Returns: {'__builtins__': {...safe_builtins...}, **context}
```

### Step 4: Execution with Timeout
```python
async def execute_with_timeout():
    compiled = compile(code, '<sandbox>', 'exec')
    exec(compiled, safe_globals, local_vars)
    return local_vars.get('result', None)

output = await asyncio.wait_for(
    execute_with_timeout(),
    timeout=limits.max_duration
)
```

## Security Model

### Current Implementation (In-Process)
- ✅ Namespace isolation (logical separation)
- ✅ Restricted builtins (whitelist approach)
- ✅ AST validation (pre-execution checks)
- ✅ Timeout enforcement
- ✅ I/O stream capture
- ⚠️ Same Python process (not OS-level isolation)

### Future Enhancement (Phase 5)
- 🔜 Docker-based sandboxing
- 🔜 True process isolation
- 🔜 Container resource limits (cgroups)
- 🔜 Network isolation

## Common Use Cases

1. **Programmatic tool orchestration** - Execute LLM-generated code safely
2. **Batch processing** - Run same code against multiple data sets
3. **User-submitted code** - Execute untrusted code with restrictions
4. **Multi-tenant execution** - Isolate executions from different users
5. **Testing and validation** - Run code in controlled environments

## Related Samples

- **Sample 11**: Programmatic Executor - Uses sandbox for tool orchestration
- **Sample 14**: Programmatic Execution - Full pipeline with sandbox
- **Sample 09**: Code Execution - Basic code execution patterns

## Troubleshooting

**Q: Code execution times out**
- Increase `max_duration` in ResourceLimits
- Check for infinite loops or blocking operations

**Q: ImportError for allowed module**
- Add module to `allowed_modules` parameter
- Verify module is in SAFE_BUILTINS list

**Q: SecurityError on valid code**
- Check if code uses forbidden operations
- Review FORBIDDEN_BUILTINS and FORBIDDEN_MODULES lists

## Learn More

- [Architecture Documentation](../../docs/architecture/)
- [Security Policy](../../docs/developer-guide/SECURITY.md)
- [Programmatic Tool Calling](../../docs/how-it-works/programmatic-tool-calling/)
- [Test Suite](../../tests/test_sandbox.py)

---

**Key Takeaway**: Independent execution environments are created through namespace isolation, restricted builtins, and resource limits. Each `SandboxEnvironment` instance provides a fresh, isolated context for code execution.
