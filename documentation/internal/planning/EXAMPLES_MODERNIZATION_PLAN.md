# Examples Modernization Plan

**Goal:** Update all 29 examples to use current public API and ensure they work

**Current Status:** Most examples use old/deprecated APIs (`execute_plan`, `orchestrator.orchestrator`, etc.)

---

## Current Public API (from orchestrator/__init__.py)

### Core Tool Registration
- `@tool` - Register function tools
- `@mcp_tool` - Register MCP tools
- `@a2a_agent` - Register agent tools
- `search_tools()`, `get_available_tools()`, `list_tools_by_domain()`

### Configuration
- `get_config()`, `validate_config()`

### Agent-to-Agent
- `A2AClient`, `AgentCapability`, `AgentDelegationRequest`

### Workflows & Skills
- `load_tools_from_yaml()`, `save_tool_as_skill()`

### Plugins
- `register_plugin()`, `get_plugin()`

---

## Example Categories & Status

### ✅ Working (New API)
- 25-parallel-agents (uses sub_agent dispatch)
- 27-cost-optimization (uses selection API)
- 28-quicksort-orchestration (uses A2A client)

### ❌ Needs Update (Old API)
- 01-basic-receipt-processing (execute_plan)
- 02-receipt-with-categorization (execute_plan)
- 03-github-operations (old MCP API)
- 04-09 (various old APIs)
- 10-24 (legacy demos, old patterns)

---

## Modernization Strategy

### Approach 1: Rewrite to Use Tool Registration
**Best for:** Simple examples showing tool usage
**Pattern:**
```python
from orchestrator import mcp_tool, search_tools

@mcp_tool(domain="receipts")
async def process_receipt(image_url: str) -> dict:
    # ... implementation

# Use the tool
tools = search_tools("receipt")
result = await tools[0].execute({"image_url": "..."})
```

### Approach 2: Use Sub-Agent Dispatch
**Best for:** Examples showing agent coordination
**Pattern:**
```python
from orchestrator.tools.sub_agent import dispatch_agents

results = await dispatch_agents(
    template="Process {item}",
    arguments=[{"item": x} for x in data],
    executor=my_exec_fn
)
```

### Approach 3: Use A2A Client
**Best for:** Agent delegation examples
**Pattern:**
```python
from orchestrator._internal.infra.a2a_client import A2AClient

client = A2AClient()
response = await client.delegate_task(capability, request)
```

---

## Priority Order

### Phase 1: Critical Examples (Users start here)
1. **01-basic-receipt-processing** - Simplest entry point
2. **02-receipt-with-categorization** - Basic workflow
3. **03-github-operations** - External tool integration

### Phase 2: Feature Examples
4. **04-vector-search-discovery** - Tool discovery
5. **05-workflow-library** - Tool composition
6. **06-monitoring-observability** - Observability
7. **07-caching-optimization** - Performance
8. **08-hybrid-model-routing** - Model selection

### Phase 3: Advanced Examples
9-18. Agent patterns, pipelines, workflows

### Phase 4: Specialized
19-24. Specialized workflows

### Phase 5: Already Working
25, 27, 28 - Verify only

---

## Action Items

For each example:
1. ✅ Read current code
2. ✅ Identify what it's trying to demonstrate
3. ✅ Rewrite using current public API
4. ✅ Test execution
5. ✅ Update README with:
   - Clear "What This Does"
   - "What You'll Learn"
   - Prerequisites
   - Setup instructions
   - Expected output
6. ✅ Verify .env has correct keys
7. ✅ Update requirements.txt if needed

---

## Decision: Simplify or Keep Complex?

**Option A: Simplify All**
- Make examples ultra-simple, focused on one feature
- 50-100 lines max per example
- Easy for beginners

**Option B: Keep Realistic**
- Show real-world usage patterns
- More code but more useful
- Better for production learning

**Recommendation: HYBRID**
- Examples 01-08: Simple, focused (Option A)
- Examples 09-24: Realistic workflows (Option B)
- Examples 25-28: Already good (keep as-is)

