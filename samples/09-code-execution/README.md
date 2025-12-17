# Sample 09: Code Execution

> Status: PyPI package refresh is in progress. This sample may lag behind the latest source; for the most up-to-date code paths, use [examples/](../../examples/). Samples will be regenerated after the refresh.
> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Feature Demonstrated:** Sandboxed Python code execution for dynamic operations

## Overview

### What This Example Does
Executes Python code safely in a sandboxed environment with security restrictions.

### Key Features Showcased
- **Safe Execution**: Sandboxed environment with restricted imports
- **Security Features**: Timeout limits, memory limits, process isolation
- **Dynamic Operations**: Custom logic without predefined tools
- **Use Cases**: Data transformation, calculations, validation, parsing

### Why This Matters

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