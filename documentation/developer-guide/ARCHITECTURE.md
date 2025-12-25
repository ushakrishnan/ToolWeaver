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

## Agent-to-Agent (A2A) Protocol Architecture

### Overview

**A2A** extends ToolWeaver's unified discovery paradigm to include **external agents** alongside MCP tools and functions. While MCP tools are deterministic and fast, A2A agents enable **flexible reasoning, multi-step problem solving, and specialized expertise**.

### A2A Component Design

```
┌─────────────────────────────────────────────────────────┐
│              UNIFIED DISCOVERY LAYER                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   MCP Tools  │  │  A2A Agents  │  │   Functions  │  │
│  │   (Fast)     │  │  (Flexible)  │  │   (Typed)    │  │
│  └────────┬─────┘  └────────┬─────┘  └────────┬─────┘  │
│           │                 │                 │          │
│           └─────────────────┴─────────────────┘          │
│                              ▼                           │
│                    ┌──────────────────┐                  │
│                    │  Tool Catalog    │                  │
│                    │  (Unified Index) │                  │
│                    └──────────────────┘                  │
└─────────────────────────────────────────────────────────┘
                              ▲
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
         ┌──────────────┬───────────┬──────────────┐
         │ Orchestrator │ Hybrid    │   Execution  │
         │              │ Dispatcher│   Engine     │
         └──────────────┴───────────┴──────────────┘
                 │            │            │
         ┌───────┴──┐  ┌──────┴──┐  ┌──────┴──┐
         ▼          ▼  ▼         ▼  ▼         ▼
    [MCP Call]  [Fn Call]  [Agent Step]  [Code-Exec]
```

### A2A Client Architecture (`orchestrator/infra/a2a_client.py`)

#### Core Classes

**AgentCapability**
```python
@dataclass
class AgentCapability:
    agent_id: str              # Unique identifier
    name: str                  # Display name
    description: str           # What the agent does
    input_schema: Dict         # JSON-Schema for inputs
    output_schema: Dict        # JSON-Schema for outputs
    capabilities: List[str]    # e.g., ["text_analysis", "reasoning"]
    endpoint: str              # HTTP(S) endpoint
    protocol: str              # "http", "sse", "websocket"
    cost_estimate: Optional[float]  # Cost per call
    latency_estimate: Optional[int] # Est. execution time (ms)
    metadata: Dict             # Extended metadata (streaming info, etc.)
```

**AgentDelegationRequest/Response**
```python
class AgentDelegationRequest:
    agent_id: str
    input: Dict[str, Any]
    context: Optional[Dict]          # Workflow context
    idempotency_key: Optional[str]   # For deduplication
    timeout_s: int = 30
    stream: bool = False

class AgentDelegationResponse:
    agent_id: str
    success: bool
    result: Optional[Dict]
    error: Optional[str]
    latency_ms: float
    cost: float
    metadata: Dict
```

#### A2AClient Methods

**discover_agents()**
- Loads agents from YAML config or agent registry
- Caches agents in-memory with TTL (300s default)
- Filters by capability or tags
- Returns: `List[AgentCapability]`

**delegate_to_agent(request: AgentDelegationRequest)**
- Routes to appropriate protocol handler (HTTP, SSE, WebSocket)
- Implements retry logic (exponential backoff, max 2 retries default)
- Tracks idempotency via in-memory cache
- Returns: `AgentDelegationResponse`

**delegate_stream(request, on_chunk_fn)**
- Streaming version for long-running agents
- Supports HTTP chunked encoding, SSE, WebSocket
- Calls `on_chunk_fn` for each response chunk
- Per-chunk timeout with automatic retry

#### Resilience Patterns

**Idempotency Caching**
```python
# Same request returns cached response within TTL
cache_key = f"{agent_id}:{hash(input)}"
if cache_key in idempotency_store:
    return cached_response
```

**Retry Logic**
```python
for attempt in range(max_retries + 1):
    try:
        return await delegate_to_agent(request)
    except (TimeoutError, ConnectionError) as e:
        if attempt < max_retries:
            await asyncio.sleep(backoff_ms * (2 ** attempt))
        else:
            raise
```

**Circuit Breaker**
```python
if failed_attempts[agent_id] > threshold:
    if time.time() - last_reset[agent_id] < reset_window_s:
        raise CircuitBreakerOpen(agent_id)
    else:
        reset_circuit(agent_id)
```

### Agent Discovery Integration (`orchestrator/tools/agent_discovery.py`)

**AgentDiscoverer** class extends `ToolDiscoveryService`:

```python
class AgentDiscoverer:
    async def discover(self) -> Dict[str, ToolDefinition]:
        agents = await self.a2a_client.discover_agents()
        for agent in agents:
            tool_def = self._agent_to_tool_definition(agent)
            discovered[tool_def.name] = tool_def
        return discovered
    
    def _agent_to_tool_definition(self, agent):
        # Converts AgentCapability to ToolDefinition
        # Sets type="agent" to distinguish from "tool"
        # Surfaces streaming metadata
        return ToolDefinition(
            name=f"agent_{agent.agent_id}",
            type="agent",  # Key differentiator
            input_schema=agent.input_schema,
            output_schema=agent.output_schema,
            metadata={
                "supports_streaming": agent.metadata.get("supports_streaming"),
                "supports_http_streaming": agent.metadata.get("supports_http_streaming"),
                "supports_sse": agent.metadata.get("supports_sse"),
                "supports_websocket": agent.metadata.get("supports_websocket"),
                "execution_time_ms": agent.latency_estimate,
                "cost_per_call_usd": agent.cost_estimate,
            }
        )
```

### Unified Discovery (`orchestrator/tools/tool_discovery.py`)

```python
async def discover_tools(
    mcp_client: Optional[MCPClient] = None,
    a2a_client: Optional[A2AClient] = None,
    use_cache: bool = True
) -> Dict[str, ToolDefinition]:
    """Discover all capabilities from all sources."""
    catalog = {}
    
    if mcp_client:
        # Existing MCP discovery
        mcp_tools = await mcp_discoverer.discover()
        catalog.update(mcp_tools)
    
    if a2a_client:
        # New: A2A agent discovery
        agent_discoverer = AgentDiscoverer(a2a_client)
        agents = await agent_discoverer.discover()
        catalog.update(agents)
    
    return catalog
```

### Agent Execution (`orchestrator/runtime/orchestrator.py`)

**execute_agent_step()**
```python
async def execute_agent_step(step, context):
    """Execute an agent-typed step."""
    # 1. Build agent request with context
    agent_input = {
        **step.get("inputs", {}),
        **step.get("context", {})  # Inline context from workflow
    }
    
    request = AgentDelegationRequest(
        agent_id=step["agent_id"],
        input=agent_input,
        context=context,  # Full workflow context
        idempotency_key=step.get("idempotency_key"),
        stream=step.get("stream", False)
    )
    
    # 2. Delegate to agent
    if step.get("stream"):
        return await a2a_client.delegate_stream(request, on_chunk_fn)
    else:
        response = await a2a_client.delegate_to_agent(request)
    
    # 3. Monitor and return
    monitor.log_tool_call(
        tool_name=step["agent_id"],
        success=response.success,
        latency_ms=response.latency_ms,
        cost=response.cost
    )
    
    return response.result
```

**Agent-Typed Step Routing in run_step()**
```python
async def run_step(step, context):
    if step.get("type") == "agent":
        # Route to agent execution
        return await execute_agent_step(step, context)
    else:
        # Route to tool/function execution
        return await dispatch_step(step, context)
```

### Hybrid Dispatcher Enhancement (`orchestrator/dispatch/hybrid_dispatcher.py`)

```python
async def dispatch_step(step, resolved_input):
    tool_name = step["tool_name"]
    
    # Check if it's an agent tool (type="agent" in discovery)
    if tool_name.startswith("agent_"):
        agent_id = tool_name.replace("agent_", "")
        request = AgentDelegationRequest(
            agent_id=agent_id,
            input=resolved_input,
            stream=step.get("stream", False)
        )
        
        if step.get("stream"):
            return await a2a_client.delegate_stream(request, on_chunk_fn)
        else:
            response = await a2a_client.delegate_to_agent(request)
            return response.result
    
    # Existing MCP or function routing
    elif tool_name in mcp_client.tool_map:
        if step.get("stream"):
            return {"chunks": await call_tool_stream(tool_name, resolved_input)}
        else:
            return await call_tool(tool_name, resolved_input)
    
    elif tool_name in function_registry:
        return await call_function(tool_name, resolved_input)
```

### Configuration (`agents.yaml` Schema)

```yaml
agents:
  - agent_id: analyzer
    name: Data Analyzer
    description: Performs complex data analysis
    endpoint: https://agents.example.com/analyzer
    protocol: http              # or sse, websocket
    input_schema:
      type: object
      properties:
        data:
          type: array
          description: Data to analyze
      required: [data]
    output_schema:
      type: object
      properties:
        insights:
          type: string
        confidence:
          type: number
    capabilities:
      - text_analysis
      - reasoning
    cost_estimate: 0.05
    latency_estimate: 3000      # milliseconds
    metadata:
      supports_streaming: true
      supports_http_streaming: true
      supports_sse: true
      tags: [analysis, ml]
```

### Monitoring & Cost Tracking

All agent calls emit identical monitoring events as MCP tools:

```python
monitor.log_tool_call(
    tool_name="analyzer",       # Agent ID
    success=True,
    latency_ms=2500,            # Actual execution time
    input_tokens=150,           # If applicable
    output_tokens=300,          # If applicable
    cost=0.05,                  # Per-call cost
    metadata={
        "agent_id": "analyzer",
        "attempt": 1,
        "stream": False,
        "cached": False
    }
)
```

### A2A vs. MCP Comparison

| Aspect | MCP Tools | A2A Agents |
|--------|-----------|-----------|
| **Execution Model** | Synchronous/async function calls | HTTP/SSE/WebSocket delegation |
| **Speed** | <1s typically | 1-30s (flexible) |
| **Use Case** | Deterministic operations | Complex reasoning, analysis |
| **Streaming** | async-generator | HTTP chunked, SSE, WebSocket |
| **Cost** | Tool-dependent (usually cheap) | Per-delegation (higher variable cost) |
| **Caching** | Native in orchestrator | Idempotency cache in A2AClient |
| **Error Handling** | Exceptions | Error field in response |
| **Discovery** | Via MCP servers | Via agent registry |
| **Integration** | Unified via ToolDefinition type="tool" | Unified via ToolDefinition type="agent" |

### Example: Hybrid Workflow

```
┌─────────────────────────────────────────────────────────┐
│                  Workflow Step 1                         │
│              MCP Tool: fetch_data                        │
│          (Fast deterministic operation)                  │
│                      ↓                                   │
│                 Output: raw_data                         │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  Workflow Step 2                         │
│              A2A Agent: analyzer                         │
│          (Flexible reasoning analysis)                   │
│              Input: raw_data + context                  │
│                      ↓                                   │
│                 Output: insights                         │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  Workflow Step 3                         │
│              MCP Tool: format_report                     │
│          (Fast deterministic formatting)                │
│              Input: insights                            │
│                      ↓                                   │
│                 Output: report                          │
└─────────────────────────────────────────────────────────┘
```

---

## Future Enhancements

1. **Async Function Calls** - Support async functions in registry
2. **Streaming Outputs** - Real-time step result streaming
3. **Conditional Execution** - Enhanced `run_if` logic
4. **Tool Composition** - Chain multiple tools in single step
5. **Remote Workers** - Distribute execution across nodes
6. **Telemetry** - OpenTelemetry integration for tracing
7. **Plan Optimizer** - Automatic parallelization analysis

## Comparison with Other Systems

| Feature | This System | Anthropic MCP | LangChain | CrewAI |
|---------|-------------|---------------|-----------|--------|
| Deterministic Tools | ✅ | ✅ | ✅ | ⚠️ |
| Function Calls | ✅ | ❌ | ✅ | ❌ |
| Agent Coordination | ✅ (A2A) | ❌ | ⚠️ | ✅ |
| Code Execution | ✅ | ❌ | ⚠️ | ❌ |
| Dependency Graph | ✅ | ❌ | ⚠️ | ❌ |
| Parallel Execution | ✅ | ⚠️ | ⚠️ | ❌ |
| Type Safety | ✅ (Pydantic) | ✅ | ⚠️ | ⚠️ |
| Idempotency | ✅ | ✅ | ❌ | ⚠️ |
| Sandboxing | ✅ | N/A | ❌ | ❌ |
| Streaming Support | ✅ (MCP & A2A) | ✅ | ⚠️ | ✅ |
| Unified Discovery | ✅ (MCP + A2A) | MCP only | ⚠️ | Custom |
| Cost Tracking | ✅ | ❌ | ❌ | ⚠️ |

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Anthropic's Agent Design](https://www.anthropic.com/research)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
