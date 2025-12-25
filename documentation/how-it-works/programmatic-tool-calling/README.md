# Programmatic Tool Calling - Complete Documentation

A comprehensive 5-part documentation set explaining how programmatic tool calling works in ToolWeaver.

## 📚 Documentation Files in This Folder

### 1. **[EXPLAINED.md](EXPLAINED.md)** - Main Deep Dive (15 min read)
**Purpose**: Comprehensive explanation of the entire architecture and how it works

**Contents**:
- High-level overview comparing traditional vs programmatic approaches
- 7-phase architecture walkthrough with code references
- Step-by-step: how a new MCP gets integrated
- Tool call tracking & logging details
- Security model (sandboxing & limits)
- Performance benefits with concrete examples
- Complete architecture diagram
- Key files reference table

**Best for**: Understanding the overall system, architecture decisions, security model

---

### 2. **[DIAGRAMS.md](DIAGRAMS.md)** - Visual Flows (10 min read)
**Purpose**: Visual representations of how tool calling happens

**Contents**:
- High-level execution flow diagram
- Tool call routing mechanism (detailed flow)
- New MCP registration flow (5 steps)
- Traditional vs programmatic comparison (side-by-side)
- Code validation & security pipeline
- Performance gains visualization (latency & token usage)
- Tool call log example

**Best for**: Visual learners, understanding workflows, performance comparisons

---

### 3. **[WALKTHROUGH.md](WALKTHROUGH.md)** - Code Trace (20 min read)
**Purpose**: Line-by-line execution trace of a real tool call

**Contents**:
- Complete implementation example: adding `get_team_budget` MCP
- Step 1: Worker implementation in `orchestrator/dispatch/workers.py`
- Step 2: Registration in `orchestrator/infra/mcp_client.py`
- Step 3: Tool definition in catalog
- Step 4: Stub generation (shows auto-generated code)
- Step 5: User/LLM code generation
- Detailed time-stamped execution trace (T+0.100s through T+0.353s)
- Full execution result with tool call tracking
- Extensibility example

**Best for**: Understanding the complete flow, debugging, learning the call path

---

### 4. **[REFERENCE.md](REFERENCE.md)** - Quick Reference (5 min quick ref)
**Purpose**: Condensed reference guide for quick lookup

**Contents**:
- Core components table (8 key components)
- The 5-step flow (quick summary)
- Tool call routing map
- File organization
- Adding a new MCP: checklist
- Performance metrics comparison table
- Key concepts explained
- Common patterns (parallelism, error handling, filtering, conditionals)
- Security model summary
- Debugging tips & tools
- FAQ (10 common questions)
- Full end-to-end example
- Links to key files

**Best for**: Quick reference, checklists, common patterns, troubleshooting

---

## 🎯 Quick Navigation

### I want to understand...

| Goal | Read This |
|------|-----------|
| **How the system works overall** | [EXPLAINED.md](EXPLAINED.md) - "Architecture: Step-by-Step" |
| **What happens when code runs** | [WALKTHROUGH.md](WALKTHROUGH.md) - "Execution Flow - Detailed Trace" |
| **How to add a new MCP tool** | [REFERENCE.md](REFERENCE.md) - "Adding a New MCP Tool: Checklist" |
| **Performance improvements** | [EXPLAINED.md](EXPLAINED.md) or [DIAGRAMS.md](DIAGRAMS.md) - "Performance Benefits" |
| **The code flow visually** | [DIAGRAMS.md](DIAGRAMS.md) - "Tool Call Routing Mechanism" |
| **Where to find code** | [REFERENCE.md](REFERENCE.md) - "File Organization" |
| **Security model** | [EXPLAINED.md](EXPLAINED.md) - "Security" or [DIAGRAMS.md](DIAGRAMS.md) - "Code Validation" |
| **Real code walkthrough** | [WALKTHROUGH.md](WALKTHROUGH.md) - Entire document |
| **Common patterns to use** | [REFERENCE.md](REFERENCE.md) - "Common Patterns" |
| **Troubleshooting issues** | [REFERENCE.md](REFERENCE.md) - "Debugging Tips" or "FAQ" |

---

## 📖 Reading Recommendations

### For Quick Understanding (5 minutes)
1. Read [REFERENCE.md](REFERENCE.md): "Core Components" table
2. Read [REFERENCE.md](REFERENCE.md): "The 5-Step Flow"
3. Look at [DIAGRAMS.md](DIAGRAMS.md): "Tool Call Routing Mechanism"

### For Medium Understanding (15 minutes)
1. Read [EXPLAINED.md](EXPLAINED.md): "High-Level Overview"
2. Read [DIAGRAMS.md](DIAGRAMS.md): "High-Level Execution Flow"
3. Read [DIAGRAMS.md](DIAGRAMS.md): "New MCP Registration Flow"
4. Read [REFERENCE.md](REFERENCE.md): "Adding a New MCP Tool: Checklist"

### For Deep Understanding (45 minutes)
1. Read all of [EXPLAINED.md](EXPLAINED.md) (comprehensive architecture)
2. Study [WALKTHROUGH.md](WALKTHROUGH.md): "Execution Flow - Detailed Trace"
3. Reference [DIAGRAMS.md](DIAGRAMS.md) for visual understanding
4. Use [REFERENCE.md](REFERENCE.md) for quick lookups

### For Implementing New Tools (10 minutes)
1. Go to [REFERENCE.md](REFERENCE.md): "Adding a New MCP Tool: Checklist"
2. Look at [WALKTHROUGH.md](WALKTHROUGH.md): "Step 1A: Create the Worker Function" (example code)
3. **NEW**: See **[Example 23: Adding New Tools](../../../examples/23-adding-new-tools/)** for complete end-to-end implementation (MCP + A2A)
4. Follow the checklist step-by-step

### For Troubleshooting (5-10 minutes)
1. Check [REFERENCE.md](REFERENCE.md): "Debugging Tips"
2. Check [REFERENCE.md](REFERENCE.md): "FAQ"
3. Look at [REFERENCE.md](REFERENCE.md): "Common Patterns" if implementing
4. Read [EXPLAINED.md](EXPLAINED.md): "Security" section if security concern

---

## 🚀 Key Concepts At a Glance

### The Problem Solved
```
TRADITIONAL LOOP:
LLM → Call Tool A → LLM → Call Tool B → LLM → Call Tool C
(20+ inferences, 2-3 minutes, ~100K tokens)

PROGRAMMATIC CALLING:
LLM → Generate Code → Sandbox: Tool A → Tool B → Tool C
(1 inference, 2-3 seconds, ~3K tokens)
```

### The 5-Step Process
1. **Tool Definition**: Define tool in `ToolCatalog` with parameters
2. **Worker Registration**: Create worker function, register in `tool_map`
3. **Stub Generation**: Executor auto-generates importable Python stubs
4. **Code Execution**: User/LLM code imports and calls stubs
5. **Result Collection**: Tool calls tracked, results aggregated, returned

### The Routing Path
```
User Code (await get_expenses(...))
  ↓
Stub Function (auto-generated)
  ↓
call_tool() Router
  ↓
MCP Executor → MCPClientShim
  ↓
tool_map Lookup
  ↓
Worker Function (actual implementation)
  ↓
Back through stack to User Code (result)
```

### Key Performance Metrics
- **50-100x faster**: 2-3 minutes → 2-3 seconds latency
- **97% token savings**: 100K tokens → 3K tokens per execution
- **20x fewer inferences**: 20+ LLM calls → 1 LLM call
- **Parallel execution**: N tools in ~1 API latency instead of N × latency

---

## 💡 How It Works: The Essence

### When a New MCP is Added

```
1. Create worker:
   async def my_tool_worker(payload): return result
   
2. Register:
   _tool_map["my_tool"] = my_tool_worker
   
3. Define:
   catalog.add_tool(ToolDefinition(name="my_tool", ...))
   
4. Stubs auto-generated:
   stubs/tools/mydomain/my_tool.py
   
5. Use in code:
   from tools.mydomain import my_tool
   result = await my_tool(...)
   
   ✓ All routing, retry, tracking automatic!
```

### How Programmatic Calling Happens

```
When user code: await get_expenses(user_id="alice", quarter="Q3")

1. Calls stub function (auto-generated)
2. Stub packs parameters
3. Calls: await call_tool("finance", "get_expenses", {...})
4. Router checks if MCP or function → routes to MCP executor
5. MCP executor creates MCPClientShim
6. MCPClientShim looks up tool_map["get_expenses"] → finds worker
7. Executes worker with retry + timeout
8. Worker calls API/database
9. Result bubbles back through entire stack
10. User code continues with result

All in ~200-300ms for a real API call!
```

---

## ✅ What You Can Do After Reading

✅ Explain how programmatic tool calling works  
✅ Add a new MCP tool in 5 minutes  
✅ Understand the complete execution flow  
✅ Read and understand the actual codebase  
✅ Debug tool call issues  
✅ Optimize performance (parallel execution)  
✅ Implement complex orchestration workflows  
✅ Explain performance benefits to stakeholders  

---

## 📋 Navigation

- **Up one level**: [../README.md](../README.md)
- **Main docs**: [../../README.md](../../README.md)
