# Programmatic Tool Calling - Visual Flow Diagrams

## 1. High-Level Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                           LLM GENERATION PHASE                          │
│                                                                          │
│  Input: Tool Catalog + User Task                                        │
│  "Analyze expense trends for Q3"                                        │
│                                                                          │
│  ↓                                                                       │
│  LLM generates Python code:                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ from tools.finance import get_expenses                          │   │
│  │ from tools.hr import get_team_members                           │   │
│  │ import asyncio                                                  │   │
│  │                                                                 │   │
│  │ team = await get_team_members(status="active")                 │   │
│  │ expenses = await asyncio.gather(*[                             │   │
│  │     get_expenses(uid) for uid in [m["id"] for m in team]       │   │
│  │ ])                                                              │   │
│  │                                                                 │   │
│  │ trends = analyze_trends([e for exp in expenses for e in exp])  │   │
│  │ print(json.dumps(trends))                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ✓ Only 1 LLM inference!                                                │
│                                                                          │
└─────────────────────────────────────────┬──────────────────────────────┘
                                          │
                                          ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                        SANDBOX EXECUTION PHASE                          │
│                                                                          │
│  1. Code validation (AST check for security)                            │
│  2. Stub injection (from tools.finance import ... resolves)             │
│  3. Async execution with timeout                                        │
│  4. Tool call tracking + routing                                        │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ EXECUTING IMPORTED STUBS:                                       │   │
│  │                                                                 │   │
│  │ get_team_members(status="active")  ──────────────┐            │   │
│  │                                    ↓              │            │   │
│  │                            Route to MCP server    │            │   │
│  │                            (route via tool_map)   │            │   │
│  │                                    ↓              │            │   │
│  │                            Execute + Track       │            │   │
│  │                            ↓ Returns 45 people    │            │   │
│  │                                                   │            │   │
│  │ Then PARALLEL execution:                          │            │   │
│  │   asyncio.gather(*[                              │            │   │
│  │     get_expenses(u["id"]) for u in 45 people     │            │   │
│  │   ])                                             │            │   │
│  │   ↓ (45 concurrent API calls)                    │            │   │
│  │   ↓ Routes each through call_tool proxy          │            │   │
│  │   ↓ All 45 complete in parallel (~1s total)      │            │   │
│  │                                                   │            │   │
│  │ Process results in Python (no LLM loop!):        │            │   │
│  │   trends = analyze_trends(...)                   │            │   │
│  │   print(...)                                     │            │   │
│  │                                                   │            │   │
│  │ ✓ 45 tool calls in 1-2 seconds                   │            │   │
│  │ ✓ No LLM in the loop                             │            │   │
│  │ ✓ Aggregation done in code (not context)        │            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Return: {                                                               │
│      "output": "...",                                                    │
│      "result": {...},                                                    │
│      "tool_calls": [45 tracked calls],                                   │
│      "execution_time": 1.23                                             │
│  }                                                                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tool Call Routing Mechanism

```
USER CODE:
    await get_expenses(user_id="alice", quarter="Q3")
         │
         ↓
GENERATED STUB (tools/finance/get_expenses.py):
    async def get_expenses(user_id, quarter):
        parameters = {"user_id": user_id, "quarter": quarter}
        result = await call_tool(
            server="finance",
            tool_name="get_expenses",
            parameters=parameters
        )
        return result
         │
         ↓
TOOL EXECUTOR ROUTER (orchestrator/tools/tool_executor.py):
    async def call_tool(server, tool_name, parameters, timeout=30):
         │
         ├─ if server == "default" or "function":
         │      → _execute_function(tool_name, parameters)
         │         ├─ Look up in orchestrator.dispatch.functions
         │         ├─ Call with timeout
         │         └─ Return result
         │
         └─ else (MCP server):
                → _execute_mcp_tool(server, tool_name, parameters)
                   │
                   ↓
MCP CLIENT SHIM (orchestrator/infra/mcp_client.py):
    MCPClientShim().call_tool(tool_name, parameters)
         │
         ├─ Check cache (idempotency)
         ├─ Check circuit breaker
         ├─ Look up in tool_map:
         │  {
         │    "receipt_ocr": receipt_ocr_worker,
         │    "line_item_parser": line_item_parser_worker,
         │    "get_expenses": get_expenses_worker,  ← FOUND
         │    ...
         │  }
         │
         ├─ Execute with retry + timeout:
         │  result = await tool_map["get_expenses"]({
         │      "user_id": "alice",
         │      "quarter": "Q3"
         │  })
         │
         └─ Return result
              │
              ↓
ACTUAL WORKER (orchestrator/dispatch/workers.py):
    async def get_expenses_worker(payload):
        user_id = payload["user_id"]
        quarter = payload["quarter"]
        
        # Call real API / database
        db_result = await database.query(
            f"SELECT * FROM expenses WHERE user_id=? AND quarter=?",
            (user_id, quarter)
        )
        
        return {
            "user_id": user_id,
            "quarter": quarter,
            "expenses": db_result,
            "total": sum(e["amount"] for e in db_result)
        }
              │
              ↓
BACK TO CODE (with result):
    expenses_data = {
        "user_id": "alice",
        "quarter": "Q3",
        "expenses": [...],
        "total": 15000.00
    }
    
    # Continue code execution
    if expenses_data["total"] > 10000:
        print(f"Alice exceeded budget!")
```

---

## 3. New MCP Registration Flow

```
STEP 1: Create Worker Implementation
┌─────────────────────────────────────────────────────────────┐
│ File: orchestrator/dispatch/workers.py                      │
│                                                             │
│ async def my_new_tool_worker(payload):                      │
│     """MCP worker implementation"""                         │
│     param1 = payload["param1"]                              │
│     param2 = payload.get("param2")                          │
│                                                             │
│     # Implementation (API call, DB query, etc.)             │
│     result = await some_external_service(param1, param2)    │
│                                                             │
│     return {"status": "success", "data": result}            │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 2: Register in Tool Map
┌─────────────────────────────────────────────────────────────┐
│ File: orchestrator/infra/mcp_client.py                      │
│                                                             │
│ from ..dispatch.workers import my_new_tool_worker           │
│                                                             │
│ _tool_map = {                                               │
│     "receipt_ocr": receipt_ocr_worker,                      │
│     "existing_tool": existing_tool_worker,                  │
│     "my_new_tool": my_new_tool_worker,  ← ADD HERE         │
│ }                                                           │
│                                                             │
│ # Now MCPClientShim can find it:                            │
│ # self.tool_map[tool_name] → executes automatically        │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 3: Create Tool Definition
┌─────────────────────────────────────────────────────────────┐
│ In your application code:                                  │
│                                                             │
│ from orchestrator.shared.models import (                    │
│     ToolCatalog, ToolDefinition, ToolParameter              │
│ )                                                           │
│                                                             │
│ catalog = ToolCatalog(source="myapp", version="1.0")        │
│                                                             │
│ catalog.add_tool(ToolDefinition(                            │
│     name="my_new_tool",                                     │
│     type="mcp",                                             │
│     description="Does something useful",                    │
│     domain="my_domain",  ← Unique server domain             │
│     parameters=[                                            │
│         ToolParameter(                                      │
│             name="param1",                                  │
│             type="string",                                  │
│             description="First parameter",                  │
│             required=True                                   │
│         ),                                                  │
│         ToolParameter(                                      │
│             name="param2",                                  │
│             type="string",                                  │
│             description="Optional parameter",               │
│             required=False                                  │
│         )                                                   │
│     ]                                                       │
│ ))                                                          │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 4: Generate Stubs (AUTOMATIC)
┌─────────────────────────────────────────────────────────────┐
│ When executor initializes with enable_stubs=True:           │
│                                                             │
│ executor = ProgrammaticToolExecutor(                        │
│     catalog,                                                │
│     enable_stubs=True  ← Triggers stub generation           │
│ )                                                           │
│                                                             │
│ StubGenerator creates:                                      │
│   stubs/                                                    │
│   └── tools/                                                │
│       └── my_domain/                                        │
│           ├── my_new_tool.py  ← AUTO-GENERATED              │
│           └── __init__.py                                   │
│                                                             │
│ Generated stub content:                                     │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ # AUTO-GENERATED - DO NOT EDIT                       │   │
│ │                                                      │   │
│ │ async def my_new_tool(param1, param2=None):          │   │
│ │     """Does something useful"""                      │   │
│ │     from orchestrator.tools.tool_executor import \   │   │
│ │         call_tool                                    │   │
│ │                                                      │   │
│ │     parameters = {                                   │   │
│ │         "param1": param1,                            │   │
│ │         "param2": param2                             │   │
│ │     }                                                │   │
│ │                                                      │   │
│ │     result = await call_tool(                        │   │
│ │         server="my_domain",                          │   │
│ │         tool_name="my_new_tool",                     │   │
│ │         parameters=parameters                        │   │
│ │     )                                                │   │
│ │     return result                                    │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 5: Use in Code (LLM Generated or Manual)
┌─────────────────────────────────────────────────────────────┐
│ User/LLM code:                                              │
│                                                             │
│ from tools.my_domain import my_new_tool                    │
│                                                             │
│ result = await my_new_tool(                                 │
│     param1="value1",                                        │
│     param2="optional_value"                                 │
│ )                                                           │
│                                                             │
│ print(f"Result: {result}")                                  │
│                                                             │
│ ✓ Tool discovered and used!                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Comparison: Traditional vs Programmatic

```
═══════════════════════════════════════════════════════════════════════════
                            TRADITIONAL TOOL CALLING
═══════════════════════════════════════════════════════════════════════════

User: "Get me expense trends for Q3"
      │
      ↓
Inference 1:
┌──────────────────────────────────────────────────────────────────┐
│ LLM Context (50KB):                                              │
│ - Tool definitions (get_team_members, get_expenses, etc.)       │
│ - System prompt                                                  │
│ - User query                                                     │
│                                                                  │
│ LLM Response:                                                    │
│ "I need to get the team members first"                           │
│ Calls: get_team_members()                                        │
└──────────────────────────────────────────────────────────────────┘
      │
      ↓
Tool Execution: get_team_members() → 45 people returned
      │
      ↓
Inference 2:
┌──────────────────────────────────────────────────────────────────┐
│ LLM Context (60KB + previous context):                           │
│ - Tool definitions                                               │
│ - System prompt                                                  │
│ - User query                                                     │
│ - TEAM LIST (15KB added!)                                        │
│                                                                  │
│ LLM Response:                                                    │
│ "Now I'll get expenses for user 1"                               │
│ Calls: get_expenses(user_id="u1")                                │
└──────────────────────────────────────────────────────────────────┘
      │
      ↓
... REPEAT 44 MORE TIMES FOR EACH TEAM MEMBER ...
      │
      ├─ Inference 3: get_expenses(user_2)  [70KB context]
      ├─ Inference 4: get_expenses(user_3)  [75KB context]
      ├─ ...
      └─ Inference 46: get_expenses(user_45) [300KB context]
      │
      ↓
Inference 47:
┌──────────────────────────────────────────────────────────────────┐
│ LLM Context (400KB!):                                            │
│ - All previous tool defs and data                                │
│ - 45 users × ~8KB each = 360KB                                  │
│                                                                  │
│ LLM Response:                                                    │
│ "Based on all this data, here are trends..."                    │
└──────────────────────────────────────────────────────────────────┘

❌ PROBLEMS:
   - 47 LLM inferences (cost multiplier!)
   - 400KB+ cumulative context (token explosion)
   - ~2-3 minutes latency (network round trips)
   - LLM reasoning overhead on data processing
   - Errors compound (one bad call ruins sequence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                      PROGRAMMATIC TOOL CALLING
═══════════════════════════════════════════════════════════════════════════

User: "Get me expense trends for Q3"
      │
      ↓
Inference 1 (ONLY):
┌──────────────────────────────────────────────────────────────────┐
│ LLM Context (40KB):                                              │
│ - Only imported tool stubs shown                                 │
│   (from tools.hr import get_team_members)                        │
│   (from tools.finance import get_expenses)                       │
│ - User query                                                     │
│                                                                  │
│ LLM generates Python code:                                       │
│                                                                  │
│ from tools.hr import get_team_members                            │
│ from tools.finance import get_expenses                           │
│ import asyncio                                                   │
│                                                                  │
│ team = await get_team_members()                                  │
│ expenses = await asyncio.gather(*[                               │
│     get_expenses(u["id"]) for u in team                          │
│ ])                                                               │
│                                                                  │
│ # Process in code (not LLM)                                      │
│ trends = analyze_expenses(expenses)                              │
│ print(json.dumps(trends))                                        │
└──────────────────────────────────────────────────────────────────┘
      │
      ↓
SANDBOX EXECUTION (0.5-2 seconds):
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: await get_team_members()                                 │
│         → Executes immediately in sandbox                        │
│         → Returns: 45 people                                     │
│                                                                  │
│ Step 2: asyncio.gather(*[45 parallel get_expenses calls])        │
│         → All 45 run in parallel                                 │
│         → EACH call ≠ LLM inference!                             │
│         → Returns: 45 expense lists                              │
│                                                                  │
│ Step 3: analyze_expenses(expenses)                               │
│         → Pure Python processing (loops, aggregation)            │
│         → No LLM involved                                        │
│         → Returns: Trends summary                                │
│                                                                  │
│ Step 4: print(trends)                                            │
│         → Output captured                                        │
│                                                                  │
│ Result: {                                                        │
│   "output": "Q3 trends: ...",                                    │
│   "tool_calls": [45 calls tracked],                              │
│   "execution_time": 1.23s                                        │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘

✓ BENEFITS:
   - 1 LLM inference (47x fewer!)
   - 40KB context (10x less tokens!)
   - 1-2 seconds latency (100x faster!)
   - Complex logic in safe Python code
   - Parallel tool execution (45 at once!)
   - Resilient: errors handled in code

═══════════════════════════════════════════════════════════════════════════

METRICS COMPARISON:
┌────────────────────────┬──────────────────┬─────────────────┐
│ Metric                 │ Traditional      │ Programmatic    │
├────────────────────────┼──────────────────┼─────────────────┤
│ LLM Inferences         │ 47               │ 1               │
│ Total Context          │ 400KB            │ 40KB            │
│ Latency                │ 2-3 minutes      │ 1-2 seconds     │
│ Tool Call Parallelism  │ 1 at a time      │ 45 concurrent   │
│ Cost (tokens)          │ ~100K tokens     │ ~3K tokens      │
│ Error Resilience       │ Low              │ High (in code)  │
│ Processing Logic       │ LLM overhead     │ Pure Python     │
└────────────────────────┴──────────────────┴─────────────────┘
```

---

## 5. Code Validation & Security

```
┌────────────────────────────────────────────────────────────────────┐
│                   SECURITY PIPELINE                                │
└────────────────────────────────────────────────────────────────────┘

Input Code (from LLM):
┌────────────────────────────────────────────────────────────────────┐
│ from tools.finance import get_expenses                             │
│ import os                                                          │
│ os.system("rm -rf /")  ← DANGEROUS!                                │
│                                                                    │
│ await get_expenses(user_id="alice")                                │
└────────────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 1: AST PARSE & VALIDATE
┌────────────────────────────────────────────────────────────────────┐
│ ast.parse(code)                                                    │
│                                                                    │
│ Check for dangerous patterns:                                      │
│ - __import__() calls ❌ Blocked                                    │
│ - eval() / exec() ❌ Blocked                                       │
│ - os.system() / subprocess ❌ Blocked                              │
│ - Direct file I/O outside sandbox ❌ Blocked                       │
│ - os module imports ❌ Blocked                                     │
│                                                                    │
│ raise SecurityError("Dangerous import detected: os")               │
└────────────────────────────────────────────────────────────────────┘
         │
         ↓
REJECTED ❌ - Return error to user
         │
         ↓
┌────────────────────────────────────────────────────────────────────┐
│ If code passes AST check:                                          │
│                                                                    │
│ from tools.finance import get_expenses                             │
│ await get_expenses(user_id="alice")                                │
│                                                                    │
│ ✓ Only imports allowed stubs (tools.*)                             │
│ ✓ Only calls tool functions                                        │
│ ✓ Uses safe Python (asyncio, json, etc.)                          │
└────────────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 2: SANDBOX EXECUTION
┌────────────────────────────────────────────────────────────────────┐
│ Sandbox Environment Protections:                                   │
│                                                                    │
│ 1. Process Isolation:                                              │
│    - Code runs in separate process / container                     │
│    - Can't affect main process                                     │
│                                                                    │
│ 2. Resource Limits:                                                │
│    - CPU: max 1 core                                               │
│    - Memory: max 512MB                                             │
│    - Time: max 30s (configurable)                                  │
│    - ∞ loops auto-terminated                                       │
│                                                                    │
│ 3. Network Isolation:                                              │
│    - No external network access (optional)                         │
│    - Tool calls routed through executor                            │
│                                                                    │
│ 4. Restricted Builtins:                                            │
│    - __import__ removed                                            │
│    - open() restricted to temp dir                                 │
│    - exec() / eval() unavailable                                   │
│    - os module unavailable                                         │
│                                                                    │
│ 5. Tool Access Only:                                               │
│    - Tools only callable via stubs                                 │
│    - Stubs route through executor                                  │
│    - Each call tracked & validated                                 │
└────────────────────────────────────────────────────────────────────┘
         │
         ↓
STEP 3: MONITORING & LOGGING
┌────────────────────────────────────────────────────────────────────┐
│ Every execution tracked:                                           │
│                                                                    │
│ {                                                                  │
│   "execution_id": "ptc_a1b2c3d4",                                  │
│   "start_time": 1702518000.123,                                    │
│   "status": "success" | "timeout" | "security_error",              │
│   "tool_calls": [                                                  │
│     {                                                              │
│       "tool": "get_expenses",                                      │
│       "parameters": {"user_id": "alice"},                          │
│       "timestamp": 1702518000.200,                                 │
│       "duration": 0.456,                                           │
│       "error": null                                                │
│     }                                                              │
│   ],                                                               │
│   "execution_time": 0.789,                                         │
│   "output": "...",                                                 │
│   "error": null                                                    │
│ }                                                                  │
│                                                                    │
│ Alerts if:                                                         │
│ - Timeout exceeded                                                 │
│ - Tool calls exceed limit (100 default)                            │
│ - Memory/CPU limits hit                                            │
│ - Security violation detected                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Performance Gains Visualization

```
LATENCY COMPARISON (Example: Process 50 Users)

Traditional Tool Calling:
┌─────────────────────────────────────────────────────────────────┐
│ Inference 1:        |████| 0.5s                                  │
│ Tool 1:             |████| 0.5s                                  │
│ Inference 2:        |████| 0.5s                                  │
│ Tool 2:             |████| 0.5s                                  │
│ Inference 3:        |████| 0.5s                                  │
│ Tool 3:             |████| 0.5s                                  │
│ ...repeat 47 more times...                                       │
│ Inference 50:       |████| 0.5s                                  │
│ Tool 50:            |████| 0.5s                                  │
│ Inference 51:       |████| 0.5s                                  │
│                                                                  │
│ TOTAL: ~25-30 seconds (sequential execution)                     │
│ With network delays: 2-3 MINUTES                                 │
└─────────────────────────────────────────────────────────────────┘

Programmatic Tool Calling:
┌─────────────────────────────────────────────────────────────────┐
│ Inference 1 (generate code): |████| 0.5s                         │
│                                                                  │
│ SANDBOX EXECUTION (parallel):                                    │
│ Get team:           |████| 0.2s                                  │
│ Get expense #1-50   |████████████| 1.0s (all parallel!)         │
│ Process in Python:  |████| 0.1s                                  │
│                                                                  │
│ TOTAL: 1.8 seconds                                               │
│ SPEEDUP: 50-100x faster!                                         │
└─────────────────────────────────────────────────────────────────┘

TOKEN USAGE:

Traditional:
┌─────────────────────────────────────────────────────────────────┐
│ Base (tools + prompt):     |████| 10K tokens                     │
│ Per inference context:     |████████| 2K tokens × 50 = 100K      │
│ Tool responses (cached):   |████████████| 30K tokens             │
│                                                                  │
│ TOTAL: ~140K tokens                                              │
└─────────────────────────────────────────────────────────────────┘

Programmatic:
┌─────────────────────────────────────────────────────────────────┐
│ Stubs shown to LLM:        |████| 5K tokens                      │
│ Single inference:          |████| 3K tokens                      │
│ Tool responses:            |████| 2K tokens (not in context!)    │
│                                                                  │
│ TOTAL: ~10K tokens                                               │
│ SAVINGS: 93%!                                                    │
└─────────────────────────────────────────────────────────────────┘

COST COMPARISON (at $0.01 per 1K tokens input):

Traditional: 140K tokens × $0.01 = $1.40 per execution
Programmatic: 10K tokens × $0.01 = $0.10 per execution

SAVINGS: 92.8% cost reduction! 🎉
```

---

## 7. Tool Call Log Example

```
Execution Result:

{
  "execution_id": "ptc_a1b2c3d4",
  "error": None,
  "execution_time": 1.234,
  "output": "High spenders: [('Alice', 15000), ('Bob', 12000)]\n",
  "result": [...],
  "tool_calls": [
    {
      # Call 1: Get team members
      "tool": "get_team_members",
      "type": "mcp",
      "parameters": {
        "department": "engineering"
      },
      "timestamp": 1702518000.123,
      "caller": {
        "type": "stub_import",
        "execution_id": "ptc_a1b2c3d4",
        "tool_id": "tool_call_1"
      },
      "completed_at": 1702518000.323,
      "duration": 0.2,
      "result_size": 1245,
      "error": None
    },
    {
      # Call 2: Get expenses for user 1
      "tool": "get_expenses",
      "type": "mcp",
      "parameters": {
        "user_id": "alice",
        "quarter": "Q3"
      },
      "timestamp": 1702518000.524,
      "caller": {
        "type": "stub_import",
        "execution_id": "ptc_a1b2c3d4",
        "tool_id": "tool_call_2"
      },
      "completed_at": 1702518000.834,
      "duration": 0.31,
      "result_size": 2048,
      "error": None
    },
    {
      # Call 3: Get expenses for user 2
      "tool": "get_expenses",
      "type": "mcp",
      "parameters": {
        "user_id": "bob",
        "quarter": "Q3"
      },
      "timestamp": 1702518000.524,  ← SAME TIME (parallel!)
      "caller": {
        "type": "stub_import",
        "execution_id": "ptc_a1b2c3d4",
        "tool_id": "tool_call_3"
      },
      "completed_at": 1702518001.124,  ← All completed in ~1s
      "duration": 0.60,
      "result_size": 1856,
      "error": None
    }
    # ... more parallel calls ...
  ]
}
```

This provides comprehensive visibility into:
- ✓ Which tools were called
- ✓ What parameters were used
- ✓ Execution timing (for optimization)
- ✓ Parallel execution detection
- ✓ Error tracking
- ✓ Resource usage (result size)
