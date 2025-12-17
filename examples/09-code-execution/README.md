# Example 09: Code Execution

**Capability Demonstrated:** Sandboxed Python code execution for dynamic operations

## What This Shows

- Safe code execution with restricted builtins
- Multiprocessing isolation for security
- Dynamic operations without predefined tools
- Use cases: data transformation, calculations, custom logic

## Security Features

- Restricted imports (no os, sys, subprocess)
- Timeout limits (prevent infinite loops)
- Memory limits (prevent resource exhaustion)
- Process isolation (separate process per execution)

## Use Cases

1. **Data Transformation**: Complex pandas operations
2. **Calculations**: Custom algorithms and formulas
3. **Validation**: Business rule checking
4. **Parsing**: Custom data format handling

## Setup

```bash
cp .env.example .env
python code_execution_demo.py
```

## Files

- `code_execution_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file