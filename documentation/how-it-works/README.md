# How It Works - Architecture & Implementation Guides

This folder contains in-depth documentation about how ToolWeaver's core systems work.

## 📚 Available Topics

### Programmatic Tool Calling

Complete documentation on how programmatic tool calling works in ToolWeaver - a pattern where the LLM generates Python orchestration code that runs in a sandbox, enabling 50-100x latency improvements and 97% token savings.

**Location**: [`programmatic-tool-calling/`](programmatic-tool-calling/)

**Choose your format**:

- **[README.md](programmatic-tool-calling/README.md)** - Navigation hub & learning guide (5 min read)
- **[EXPLAINED.md](programmatic-tool-calling/EXPLAINED.md)** - Comprehensive deep dive (15 min read)  
- **[DIAGRAMS.md](programmatic-tool-calling/DIAGRAMS.md)** - Visual flow diagrams (10 min read)
- **[WALKTHROUGH.md](programmatic-tool-calling/WALKTHROUGH.md)** - Code trace with line-by-line execution (20 min read)
- **[REFERENCE.md](programmatic-tool-calling/REFERENCE.md)** - Quick reference tables & checklists (5 min quick ref)

**Key Topics Covered**:
- High-level overview & comparison to traditional tool calling
- Architecture: Tool definition → Stub generation → Execution
- How new MCPs are integrated (5-step process)
- Tool call routing mechanism & execution flow
- Security model: Code validation & sandboxing
- Performance benefits: 50-100x latency, 97% token savings
- Complete code walkthrough of a real tool call
- Debugging tips & common patterns

---

## Getting Started

### Quick Start (5 minutes)
1. Read [programmatic-tool-calling/README.md](programmatic-tool-calling/README.md)
2. Look at [programmatic-tool-calling/DIAGRAMS.md](programmatic-tool-calling/DIAGRAMS.md) - "Tool Call Routing Mechanism"

### Medium Dive (15 minutes)
1. [programmatic-tool-calling/EXPLAINED.md](programmatic-tool-calling/EXPLAINED.md) - High-level overview
2. [programmatic-tool-calling/DIAGRAMS.md](programmatic-tool-calling/DIAGRAMS.md) - Visual understanding
3. [programmatic-tool-calling/REFERENCE.md](programmatic-tool-calling/REFERENCE.md) - "Adding a New MCP" checklist

### Deep Understanding (45 minutes)
1. Read all of [EXPLAINED.md](programmatic-tool-calling/EXPLAINED.md)
2. Study [WALKTHROUGH.md](programmatic-tool-calling/WALKTHROUGH.md) - "Execution Flow - Detailed Trace"
3. Reference [DIAGRAMS.md](programmatic-tool-calling/DIAGRAMS.md) for visual understanding
4. Use [REFERENCE.md](programmatic-tool-calling/REFERENCE.md) for implementation details

### Implementing New Tools (10 minutes)
1. Go to [REFERENCE.md](programmatic-tool-calling/REFERENCE.md) - "Adding a New MCP Tool: Checklist"
2. Look at [WALKTHROUGH.md](programmatic-tool-calling/WALKTHROUGH.md) - "Step 1A: Create the Worker Function"
3. Follow the checklist step-by-step

---

## Future Topics

Additional "How It Works" topics coming soon:

- [ ] Orchestrator & Planning
- [ ] Hybrid Model Dispatch
- [ ] Tool Discovery & Indexing
- [ ] Monitoring & Observability
- [ ] Caching & Optimization
- [ ] Multi-Agent Coordination

---

## Need Help?

- **Quick answers**: Check [REFERENCE.md](programmatic-tool-calling/REFERENCE.md) - "FAQ"
- **Visual learner**: Go to [DIAGRAMS.md](programmatic-tool-calling/DIAGRAMS.md)
- **Code trace**: See [WALKTHROUGH.md](programmatic-tool-calling/WALKTHROUGH.md)
- **Implementation**: Follow [REFERENCE.md](programmatic-tool-calling/REFERENCE.md) - "Adding a New MCP Tool: Checklist"
- **Debugging**: Check [REFERENCE.md](programmatic-tool-calling/REFERENCE.md) - "Debugging Tips"
