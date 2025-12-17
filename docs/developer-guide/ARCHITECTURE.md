# Architecture Documentation - Hybrid Orchestrator

## Overview

The Hybrid Orchestrator is a flexible execution engine that supports three distinct tool types while maintaining a unified interface. It's designed to mirror Anthropic's Model Context Protocol (MCP) approach but extends it with structured function calls and dynamic code execution capabilities.

## Core Design Principles

1. **Tool Type Agnostic** - All tools treated as interchangeable via unified dispatcher
2. **Type Safety First** - Pydantic validation for all inputs/outputs
3. **Async by Default** - Non-blocking execution with parallel step support
4. **Idempotent Operations** - Built-in caching and retry mechanisms
5. **Sandboxed Execution** - Isolated environments for untrusted code

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Planner LLM                           │
│                  (Generates Execution Plan)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Execution Plan │
                   │     (JSON)     │
                   └────────┬───────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Execution Engine                          │    │
│  │  • Dependency Resolution                            │    │
│  │  • Parallel Execution                               │    │
│  │  • Retry Logic                                      │    │
│  │  • Context Management                               │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Hybrid Dispatcher                          │    │
│  │  • Input Resolution (step: references)             │    │
│  │  • Tool Type Detection                              │    │
│  │  • Worker Routing                                   │    │
│  └──────┬────────────────┬───────────────────┬────────┘    │
│         │                │                   │              │
│         ▼                ▼                   ▼              │
│  ┌───────────┐  ┌────────────────┐  ┌──────────────┐      │
│  │    MCP    │  │    Function    │  │   Code-Exec  │      │
│  │  Workers  │  │     Calls      │  │    Worker    │      │
│  └───────────┘  └────────────────┘  └──────────────┘      │
│         │                │                   │              │
│         ▼                ▼                   ▼              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Output Context Store                   │    │
│  │         (All step results indexed by ID)            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Final Synthesis  │
                    │   (LLM Output)   │
                    └──────────────────┘
```

## Component Details

### 1. Execution Engine (`runtime/orchestrator.py`)

**Responsibilities:**
- Validate execution plans against Pydantic schema
- Resolve step dependencies (`depends_on` field)
- Execute ready steps in parallel when possible
- Maintain execution context with all step outputs
- Handle retry policies with exponential backoff
- Generate final synthesis from context

**Key Functions:**
- `execute_plan(plan)` - Main entry point
- `run_step(step, step_outputs, mcp_client)` - Execute single step
- `final_synthesis(plan, context)` - Generate summary

**Execution Flow:**
```python
1. Validate plan schema
2. Build dependency graph
3. While steps remain:
   a. Identify ready steps (all deps satisfied)
   b. Execute ready steps in parallel
   c. Store results in context
   d. Mark steps complete
4. Generate final synthesis
```

### 2. Hybrid Dispatcher (`dispatch/hybrid_dispatcher.py`)

**Responsibilities:**
- Resolve `step:` references in inputs
- Route to appropriate worker based on tool type
- Maintain function registry for structured calls
- Handle nested reference resolution

**Tool Type Detection:**
```python
if tool_type in mcp_client.tool_map:
    # Route to MCP worker
elif tool_type == "function_call":
    # Route to function registry
elif tool_type == "code_exec":
    # Route to code execution worker
else:
    # Error: unknown tool
```

**Reference Resolution:**
- `step:step-1` → Fetch output from step-1
- Supports nested objects and arrays
- Recursive resolution for complex structures

### 3. Tool Types

#### A. MCP Workers (`dispatch/workers.py`, `infra/mcp_client.py`)

**Characteristics:**
- Deterministic and predictable
- Fast execution (async with minimal delays)
- Idempotency supported
- Input/output Pydantic validated

**Examples:**
```python
receipt_ocr_worker(payload) → ReceiptOCROut
line_item_parser_worker(payload) → LineItemParserOut
expense_categorizer_worker(payload) → CategorizerOut
```

**Tool Map:**
```python
_tool_map = {
    "receipt_ocr": receipt_ocr_worker,
    "line_item_parser": line_item_parser_worker,
    "expense_categorizer": expense_categorizer_worker,
}
```

#### B. Function Calls (`dispatch/functions.py`)

**Characteristics:**
- Structured APIs with argument schemas
- Type-safe with runtime validation
- Registered via decorator
- Reusable across plans

**Registration Pattern:**
```python
@register_function("compute_tax")
def compute_tax(amount: float, tax_rate: float = 0.07) -> float:
    return round(amount * tax_rate, 2)
```

**Available Functions:**
- `compute_tax` - Tax calculations
- `merge_items` - Item aggregation
- `apply_discount` - Discount application
- `filter_items_by_category` - Category filtering
- `compute_item_statistics` - Statistical analysis

#### C. Code Execution Worker (`execution/code_exec_worker.py`)

**Characteristics:**
- Sandboxed Python execution
- Isolated process (multiprocessing)
- No unsafe globals (`__builtins__: {}`)
- Timeout protection (5 seconds default)
- Input/output Pydantic validated

**Execution Model:**
```python
1. Create isolated process
2. Pass input_data to code
3. Execute with empty globals
4. Extract output from local_vars
5. Terminate if timeout exceeded
6. Validate output with Pydantic
```

**Security Constraints:**
- No import statements allowed
- No file I/O access
- No network access
- Limited execution time
- Process isolation

## Data Flow

### Step Reference Resolution

```
Plan Input:
{
  "id": "step-2",
  "input": {"data": "step:step-1"}
}

Resolution:
1. Detect "step:" prefix
2. Extract reference: "step-1"
3. Lookup step-1 output in context
4. Replace with actual value
5. Pass to worker
```

### Example Flow

```
step-1 (MCP: receipt_ocr)
   │
   ├─> Output: {"text": "Receipt text..."}
   │
   ├─> step-2 (MCP: line_item_parser)
   │      Input: {"ocr_text": "step:step-1"}
   │      Resolved: {"ocr_text": {"text": "Receipt text..."}}
   │      Output: {"items": [...]}
   │
   ├─> step-3 (Function: merge_items)
   │      Input: {"items": "step:step-2"}
   │      Output: {"result": {"total_sum": 8.5, "count": 2}}
   │
   └─> step-4 (Code-Exec: custom logic)
          Input: {"code": "...", "input_data": {"step2": "step:step-2"}}
          Output: {"output": {...}}
```

## Models & Validation (`models.py`)

### Plan Schema
```python
PlanModel
├── request_id: str
├── steps: List[StepModel]
│   ├── id: str
│   ├── tool: str
│   ├── input: Dict[str, Any]
│   ├── depends_on: List[str]
│   ├── idempotency_key: Optional[str]
│   └── retry_policy: Optional[RetryPolicy]
└── final_synthesis: FinalSynthesisModel
```

### Tool-Specific Models
- `ReceiptOCRIn/Out`
- `LineItemParserIn/Out`
- `CategorizerIn/Out`
- `FunctionCallInput/Output`
- `CodeExecInput/Output`

## Error Handling

### Retry Logic
```python
- Configurable per-step
- Exponential backoff
- Maximum attempts limit
- Last exception propagated
```

### Failure Modes
- Step execution failure → Halt plan, raise exception
- Circular dependencies → Detected, raise RuntimeError
- Unknown tool → List available tools, raise error
- Timeout → Process terminated, TimeoutError raised
- Validation failure → Pydantic ValidationError

## Performance Characteristics

### Parallel Execution
- Steps with satisfied dependencies run concurrently
- `asyncio.gather()` for non-blocking I/O
- Multiprocessing for code-exec (CPU-bound)

### Idempotency
- Key-based caching in `_idempotency_store`
- Cache check before execution
- Deterministic results for repeated calls

### Timeouts
- Default: 30 seconds for MCP tools
- Configurable per-step via `timeout_s`
- Code-exec: 5 seconds hardcoded (safety)

## Extension Points

### Adding New MCP Worker
```python
# 1. Define in dispatch/workers.py
async def my_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    # ... implementation
    return MyOutput(**result).model_dump()

# 2. Register in infra/mcp_client.py
_tool_map["my_tool"] = my_worker
```

### Adding New Function
```python
# In dispatch/functions.py
@register_function("my_function")
def my_function(arg1: str) -> dict:
    return {"result": ...}
```

### Custom Dispatcher Logic
```python
# Extend dispatch_step() in dispatch/hybrid_dispatcher.py
elif tool_type == "my_custom_type":
    return await my_custom_worker(resolved_input)
```

**Note:** Backward-compatible imports (`from orchestrator.workers import ...`) remain available via top-level shims. See [PACKAGE_STRUCTURE.md](PACKAGE_STRUCTURE.md) for full module layout.

## Security Considerations

### Code-Exec Sandboxing
- **Process Isolation**: Separate OS process per execution
- **No Builtins**: Empty `__builtins__` dictionary
- **Timeout**: 5-second hard limit
- **No Network**: Subprocess has no network access
- **No File I/O**: No file operations allowed
- **Read-Only Input**: Input data copied, not shared

### Best Practices
1. Never trust user-provided code without review
2. Use function calls for known operations
3. Reserve code-exec for trusted admin use cases
4. Monitor execution times and resource usage
5. Log all code-exec operations for audit

## Testing Strategy

### Unit Tests
- Individual worker validation
- Model schema validation
- Reference resolution logic
- Error handling paths

### Integration Tests
- End-to-end plan execution
- Multi-tool workflows
- Dependency resolution
- Retry and timeout scenarios

### Demo Plans
- `example_plan.json` - Original MCP + code-exec
- `example_plan_hybrid.json` - All three tool types

## Future Enhancements

1. **Async Function Calls** - Support async functions in registry
2. **Streaming Outputs** - Real-time step result streaming
3. **Conditional Execution** - Enhanced `run_if` logic
4. **Tool Composition** - Chain multiple tools in single step
5. **Remote Workers** - Distribute execution across nodes
6. **Telemetry** - OpenTelemetry integration for tracing
7. **Plan Optimizer** - Automatic parallelization analysis

## Comparison with Other Systems

| Feature | This System | Anthropic MCP | LangChain |
|---------|-------------|---------------|-----------|
| Deterministic Tools | ✅ | ✅ | ✅ |
| Function Calls | ✅ | ❌ | ✅ |
| Code Execution | ✅ | ❌ | ⚠️ |
| Dependency Graph | ✅ | ❌ | ⚠️ |
| Parallel Execution | ✅ | ⚠️ | ⚠️ |
| Type Safety | ✅ (Pydantic) | ✅ | ⚠️ |
| Idempotency | ✅ | ✅ | ❌ |
| Sandboxing | ✅ | N/A | ❌ |

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Anthropic's Agent Design](https://www.anthropic.com/research)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
