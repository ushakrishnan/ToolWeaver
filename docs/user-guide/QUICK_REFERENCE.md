# Quick Reference - Two-Model Orchestrator

## Architecture Overview

```
Natural Language → Large Model → JSON Plan → Orchestrator → Workers
                   (Planning)                              ↓
                                                    Small Model
                                                    (Execution)
```

## When Small Models Are Used

| Worker | Without Small Model | With Small Model |
|--------|---------------------|------------------|
| `receipt_ocr` | Azure Computer Vision | Azure Computer Vision *(no change)* |
| `line_item_parser` | Keyword matching (coffee, bagel) | **Phi-3 intelligently parses ANY receipt** |
| `expense_categorizer` | Simple rules (coffee→beverage) | **Phi-3 intelligently categorizes** |

**Enable:** `USE_SMALL_MODEL=true` in `.env`

## Configuration Matrix

### Large Model (Planning)

| Provider | Variable | When to Use |
|----------|----------|-------------|
| **Azure OpenAI** ⭐ | `PLANNER_PROVIDER=azure-openai` | Enterprise, existing Azure |
| OpenAI | `PLANNER_PROVIDER=openai` | Quick start, latest models |
| Anthropic | `PLANNER_PROVIDER=anthropic` | Claude preference |
| Gemini | `PLANNER_PROVIDER=gemini` | Google ecosystem |

### Small Model (Execution)

| Backend | Variable | When to Use |
|---------|----------|-------------|
| **Ollama** ⭐ | `SMALL_MODEL_BACKEND=ollama` | Local, free, development |
| Azure AI Foundry | `SMALL_MODEL_BACKEND=azure` | Enterprise, managed |
| Transformers | `SMALL_MODEL_BACKEND=transformers` | Custom models, full control |
| **None** | `USE_SMALL_MODEL=false` | Simple testing, prototyping |

## Quick Setup

### Minimal (No LLM)
```bash
pip install -r requirements.txt
python run_demo.py  # Uses pre-defined plans
```

### With Azure OpenAI Planner
```bash
# .env
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

python run_planner_demo.py "Your request"
```

### With Ollama Small Model
```bash
ollama pull phi3

# .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3

python run_demo.py
```

### Full Stack (Azure + Ollama)
```bash
# .env
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3

python run_planner_demo.py "Process receipt and categorize"
```

## Cost Comparison (1000 receipts)

| Configuration | Cost | Speed |
|---------------|------|-------|
| GPT-4o only | **$15.00** | 5-10s each |
| GPT-4o + Phi-3 (Ollama) | **$0.002** | 2-4s each |
| GPT-4o + Phi-3 (Azure) | **$0.50** | 2-4s each |

**Savings: 96-99%**

## File Structure

```
orchestrator/
├── planning/planner.py              # Large model → generates plans
├── execution/small_model_worker.py  # Small model → parses/categorizes
├── dispatch/
│   ├── workers.py                   # MCP workers with small model integration
│   ├── hybrid_dispatcher.py         # Routes to correct tool type
│   └── functions.py                 # Registered functions
├── execution/code_exec_worker.py    # Sandboxed Python execution
└── runtime/orchestrator.py          # Main execution engine
```

**Note:** Top-level imports (`from orchestrator.planner import ...`) remain backward-compatible via shims. See [PACKAGE_STRUCTURE.md](../developer-guide/PACKAGE_STRUCTURE.md) for full subpackage layout.

## Environment Variables Cheatsheet

### Required for Planning
```bash
PLANNER_PROVIDER=azure-openai|openai|anthropic|gemini
PLANNER_MODEL=gpt-4o

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Or OpenAI
OPENAI_API_KEY=sk-...

# Or Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Or Gemini
GOOGLE_API_KEY=AIza...
```

### Optional for Small Models
```bash
USE_SMALL_MODEL=true|false
SMALL_MODEL_BACKEND=ollama|azure|transformers
WORKER_MODEL=phi3

# Ollama
OLLAMA_API_URL=http://localhost:11434

# Azure AI Foundry
AZURE_SMALL_MODEL_ENDPOINT=...
AZURE_SMALL_MODEL_KEY=...
```

## Common Commands

```bash
# Test planner (generates plan from natural language)
python run_planner_demo.py "Your request here"

# Run predefined plans
python run_demo.py

# Run specific plan
python run_demo.py example_plan_hybrid.json

# Test cost calculation examples
python usage_examples.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to initialize planner" | Check `PLANNER_PROVIDER` matches: `azure-openai`, `openai`, `anthropic`, or `gemini` |
| "OPENAI_API_KEY not set" | Wrong provider? Set `PLANNER_PROVIDER=azure-openai` and use `AZURE_OPENAI_*` variables |
| Small model not responding | Check Ollama is running: `ollama list` |
| "No text detected" from Azure CV | Check OCR_MODE=azure and credentials are correct |
| Items not parsed | Enable small model: `USE_SMALL_MODEL=true` |

## Example Workflow

```
1. User Request:
   "Process this Walmart receipt and tell me food vs beverage spending"

2. GPT-4o (Large Model):
   Generates 4-step plan:
   - receipt_ocr → Azure CV
   - line_item_parser → Phi-3
   - expense_categorizer → Phi-3
   - compute_statistics → function

3. Orchestrator:
   Executes plan with dependency resolution

4. Phi-3 (Small Model):
   - Parses 15 items from Walmart receipt
   - Categorizes: 10 food, 5 beverage

5. Function Call:
   Computes totals: Food $42, Beverage $18

6. Result:
   Structured JSON with categories and totals
   Cost: $0.002 (99.98% cheaper than GPT-4o only)
```

## Tool & Agent Discovery Examples

### Discover MCP Tools

```python
from orchestrator.tool_search import discover_tools
from orchestrator.mcp_client import MCPClient

# Initialize MCP client
mcp = MCPClient(env_file=".env")

# Discover all available MCP tools
tools = await discover_tools(mcp_client=mcp, use_cache=True)

# Browse tools
for tool_name, tool_def in tools.items():
    print(f"{tool_name}: {tool_def.description}")
    print(f"  Input: {tool_def.input_schema}")
    print(f"  Streaming: {tool_def.metadata.get('supports_streaming')}")
```

### Discover A2A Agents

```python
from orchestrator.tool_search import discover_tools
from orchestrator.infra.a2a_client import A2AClient

# Initialize A2A client
a2a = A2AClient(registry_url="https://agents.example.com")

# Discover agents
tools = await discover_tools(a2a_client=a2a, use_cache=True)

# Filter for agents only
agents = [t for t in tools.values() if t.type == "agent"]
for agent in agents:
    print(f"{agent.name}: {agent.description}")
    print(f"  Cost: ${agent.metadata.get('cost_per_call_usd')}")
    print(f"  Latency: {agent.metadata.get('execution_time_ms')}ms")
```

### Unified Discovery (MCP + A2A)

```python
# Single call discovers both tools and agents
tools_and_agents = await discover_tools(
    mcp_client=mcp,
    a2a_client=a2a,
    use_cache=True
)

# Semantic search across both
from orchestrator.tool_search import find_relevant_tools

results = await find_relevant_tools(
    query="analyze customer data",
    catalog=tools_and_agents,
    limit=5
)

for tool in results:
    tool_type = "Agent" if tool.type == "agent" else "Tool"
    print(f"[{tool_type}] {tool.name}: {tool.description}")
```

### Call MCP Tools

```python
from orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator(tools_and_agents)

# Call a tool
result = await orchestrator.run_step({
    "tool_name": "extract_text",
    "inputs": {"image_url": "https://example.com/receipt.jpg"}
})

print(result)  # {"text": "Extracted content..."}
```

### Delegate to A2A Agents

```python
# Delegate to an agent
result = await orchestrator.run_step({
    "type": "agent",
    "agent_id": "analyzer",
    "inputs": {"data": extracted_text},
    "stream": False  # Set True for streaming response
})

print(result)  # {"insights": "Analysis result..."}
```

### Hybrid Workflow (Tool → Agent → Tool)

```python
# Step 1: MCP Tool - Fast extraction
step1 = await orchestrator.run_step({
    "tool_name": "fetch_api_data",
    "inputs": {"endpoint": "/api/users"}
})

# Step 2: A2A Agent - Complex analysis
step2 = await orchestrator.run_step({
    "type": "agent",
    "agent_id": "analyzer",
    "inputs": {"data": step1["users"]},
    "stream": True  # Stream analysis results
})

# Step 3: MCP Tool - Fast formatting
step3 = await orchestrator.run_step({
    "tool_name": "format_report",
    "inputs": {"analysis": step2}
})

print(step3)  # Final formatted report
```

### Cost Tracking for Agents

```python
from orchestrator.monitoring import MonitoringBackend

monitor = MonitoringBackend(backend="wandb")
orchestrator = Orchestrator(tools_and_agents, monitoring=monitor)

# Call agent (cost is tracked)
result = await orchestrator.run_step({
    "type": "agent",
    "agent_id": "analyzer",
    "inputs": {...}
})

# Later: retrieve cost metrics
total_cost = sum(
    call['cost'] for call in monitor.get_calls()
    if call['success']
)
print(f"Total cost: ${total_cost:.4f}")
```

## Next Steps

1. ✅ Fill in `.env` with your provider credentials
2. ✅ Test planner: `python run_planner_demo.py "test"`
3. ✅ Optional: Install Ollama and enable small models
4. ✅ Run full demo: `python run_demo.py`
5. ✅ Read [Configuration Guide](docs/CONFIGURATION.md) for advanced setup

## Links

- [Full Configuration Guide](docs/CONFIGURATION.md)
- [Two-Model Architecture Deep Dive](docs/TWO_MODEL_ARCHITECTURE.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Azure CV Setup](docs/AZURE_SETUP.md)
