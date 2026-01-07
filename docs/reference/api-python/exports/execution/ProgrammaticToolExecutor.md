# ProgrammaticToolExecutor

## Simple Explanation
Execute LLM-generated Python code that orchestrates tools, enabling parallel execution and complex workflows without multi-round tool calling.

## Technical Explanation
`ProgrammaticToolExecutor` creates a sandboxed Python environment where LLMs can generate orchestration code that calls tools directly. This eliminates the context bloat and latency of traditional multi-round tool calling by letting the LLM write code once and execute it completely.

**Import Path**
```python
from orchestrator import ProgrammaticToolExecutor
```

**Signature**
```python
class ProgrammaticToolExecutor:
    def __init__(
        self,
        catalog: ToolCatalog,
        limits: ResourceLimits | None = None,
        enable_stubs: bool = False,
        mcp_client: MCPClient | None = None
    ):
        ...
    
    async def execute(
        self,
        code: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        ...
```

## When to Use
- **Complex Workflows**: LLM orchestrates multiple tools with conditional logic
- **Parallel Execution**: Generate code that calls tools in parallel with `asyncio.gather`
- **Local Aggregation**: Combine tool results without round-tripping through LLM
- **Reduce Latency**: One LLM call to generate code + fast local execution

## Key Methods
- `execute(code, context)`: Execute Python code in sandbox with tool access
- `get_available_tools()`: Return list of tools accessible in sandbox
- `validate_code(code)`: Check code for safety before execution

## Examples

### Basic Execution
```python
from orchestrator import ProgrammaticToolExecutor, ResourceLimits

# Create executor with tool catalog
executor = ProgrammaticToolExecutor(
    catalog=tool_catalog,
    limits=ResourceLimits(timeout_seconds=30, max_tool_calls=50)
)

# LLM generates this code
code = """
# Extract data from receipt
data = await extract_receipt_fields(receipt_text)

# Categorize based on merchant
category = await categorize_merchant(data['merchant'])

# Return structured result
return {
    'total': data['total'],
    'merchant': data['merchant'],
    'category': category
}
"""

# Execute in sandbox
result = await executor.execute(code, context={"receipt_text": text})
print(result)
```

### Parallel Tool Calls
```python
from orchestrator import ProgrammaticToolExecutor

executor = ProgrammaticToolExecutor(catalog=tool_catalog)

# LLM generates parallel orchestration code
code = """
import asyncio

# Call multiple tools in parallel
results = await asyncio.gather(
    extract_receipt_fields(receipt_1),
    extract_receipt_fields(receipt_2),
    extract_receipt_fields(receipt_3)
)

# Aggregate locally
totals = [r['total'] for r in results]
return {'sum': sum(totals), 'count': len(totals)}
"""

result = await executor.execute(code, context={
    "receipt_1": text1,
    "receipt_2": text2,
    "receipt_3": text3
})
# Returns: {'sum': 287.43, 'count': 3}
```

### Conditional Logic
```python
from orchestrator import ProgrammaticToolExecutor

executor = ProgrammaticToolExecutor(catalog=tool_catalog)

# LLM generates conditional workflow
code = """
# Extract receipt data
data = await extract_receipt_fields(receipt_text)

# Conditional processing based on amount
if data['total'] > 100:
    # High-value: get detailed categorization
    category = await categorize_detailed(data['merchant'])
else:
    # Low-value: simple categorization
    category = await categorize_simple(data['merchant'])

return {'total': data['total'], 'category': category}
"""

result = await executor.execute(code, context={"receipt_text": text})
```

### With Stubs for Testing
```python
from orchestrator import ProgrammaticToolExecutor

# Enable stubs for testing without real API calls
executor = ProgrammaticToolExecutor(
    catalog=tool_catalog,
    enable_stubs=True  # Tools return mock data
)

code = """
# This won't make real API calls
data = await extract_receipt_fields(receipt_text)
return data
"""

result = await executor.execute(code, context={"receipt_text": "..."})
# Returns mock data for testing
```

## Architecture Pattern

### Traditional Multi-Round (Slow)
```
User → LLM → Tool1 → LLM → Tool2 → LLM → Tool3 → Result
Latency: ~15-20 seconds for 3 tools
Context: Grows with each round
```

### Programmatic Execution (Fast)
```
User → LLM (generates code) → Sandbox executes all tools → Result
Latency: ~3-5 seconds for 3 tools
Context: Single LLM call
```

## Security

The executor runs code in a sandboxed environment with:
- **Import restrictions**: Only whitelisted modules allowed
- **Resource limits**: Memory, CPU, and timeout constraints
- **Network isolation**: No external network access by default
- **Filesystem restrictions**: Limited read/write access

## See Also
- [ResourceLimits](ResourceLimits.md) — Configure sandbox constraints
- [SandboxEnvironment](SandboxEnvironment.md) — Isolated execution environment
- [Sample 02: Receipt Categorization](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/02-receipt-with-categorization) — End-to-end orchestration example
- [How to Orchestrate with Code](../../../how-to/orchestrate-with-code.md) — Comprehensive guide

## Notes
- Code must be async (use `await` for tool calls)
- Available tools are injected as async functions in the sandbox
- Return value must be JSON-serializable
- Use `enable_stubs=True` for testing without API calls
- Typical execution: 100-500ms for local orchestration after code generation
