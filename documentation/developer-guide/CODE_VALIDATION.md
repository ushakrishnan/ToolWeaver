# Code Validation (Optional)

Advanced validation for generated stubs and skills to catch errors early.

## Levels

### Level 1: Syntax (Always)
✅ **Enabled by default**  
Catches parse errors via `ast.parse()`.

```python
from orchestrator.execution.validation import validate_stub

result = validate_stub("def add(x int y: int")
# {"valid": False, "syntax": {"pass": False, "error": "..."}}
```

### Level 2: Execution (Optional)
⚠️ **Slower; use for high-stakes code**  
Runs code in sandboxed environment with safe builtins.

Catches:
- Import errors (missing modules)
- Name errors (unbound variables)
- Type errors (callable mismatch)

```python
result = validate_stub(
    "def add(x, y): return x + y\nadd(1)",
    check_exec=True
)
# Detects: missing arg error
```

**Trade-off**: ~100-200ms per check; good for approval workflows.

### Level 3: Type Checking (Optional)
⚠️⚠️ **Slowest; use for critical code**  
Runs mypy if installed (skips silently if not).

Catches:
- Type mismatches
- Missing annotations
- Inconsistent returns

```python
result = validate_stub(
    code,
    check_mypy=True  # Requires mypy in environment
)
```

**Trade-off**: ~500ms-1s per check; best for library code.

## Integration Points

### In Skill Library
```python
from orchestrator.execution import skill_library as sl
from orchestrator.execution.validation import validate_stub

code = """
def process(items: list) -> int:
    return len(items)
"""

result = validate_stub(code, check_syntax=True, check_exec=True)
if result["valid"]:
    sl.save_skill(name="process", code=code, metadata=result)
```

### In Code Generator
```python
from orchestrator.execution.code_generator import generate_stub
from orchestrator.execution.validation import validate_stub

stub = generate_stub(tool_schema)
validation = validate_stub(stub, check_syntax=True, check_exec=True)

if validation["valid"]:
    execute(stub)
else:
    log_error(validation)
```

## Best Practices

- **Development**: Use `check_syntax=True, check_exec=True` for fast feedback
- **CI/CD**: Add all levels (`check_mypy=True`) before merge
- **Runtime**: Keep to syntax only to minimize latency
- **Skill Approval**: Use exec+mypy for high-confidence

## When to Skip

- Real-time code execution (latency-critical)
- Trusted internal code
- Prototyping phase

## When to Use Each Level

| Phase | Syntax | Exec | Mypy |
|-------|--------|------|------|
| Generate | ✅ | — | — |
| Approve | ✅ | ✅ | ✅ |
| Save | ✅ | — | — |
| Runtime | ✅ | — | — |

## Environment

No new dependencies; mypy is optional:

```bash
# Optional
pip install mypy>=1.0
```

If mypy is not installed, `check_mypy=True` silently succeeds.
