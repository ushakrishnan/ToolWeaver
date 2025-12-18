# Quick Reference

One-page cheat sheet for running ToolWeaver. For explanations and architecture, see [FEATURES_GUIDE](FEATURES_GUIDE.md) and [WORKFLOW_USAGE_GUIDE](WORKFLOW_USAGE_GUIDE.md).

## Core Toggles

### Planner (large model)

| Provider | Variable | Use When |
|----------|----------|----------|
| Azure OpenAI | `PLANNER_PROVIDER=azure-openai` | Enterprise / Azure defaults |
| OpenAI | `PLANNER_PROVIDER=openai` | Fast start, latest models |
| Anthropic | `PLANNER_PROVIDER=anthropic` | Prefer Claude |
| Gemini | `PLANNER_PROVIDER=gemini` | Google stack |

### Small Model (execution)

| Backend | Variable | Use When |
|---------|----------|----------|
| Ollama | `SMALL_MODEL_BACKEND=ollama` | Local / free / dev |
| Azure AI Foundry | `SMALL_MODEL_BACKEND=azure` | Managed small model |
| Transformers | `SMALL_MODEL_BACKEND=transformers` | Custom models |
| None | `USE_SMALL_MODEL=false` | Basic prototyping |

## Minimal Commands

- **No LLM**: `pip install -r requirements.txt` → `python examples/run_demo.py`
- **Planner**: set `PLANNER_PROVIDER` + keys → `python examples/run_planner_demo.py "<request>"`
- **Hybrid (planner + small model)**: set planner vars + `USE_SMALL_MODEL=true`, `WORKER_MODEL=phi3`, run `python examples/run_planner_demo.py "<request>"`

## Env Vars (essentials)

```
PLANNER_PROVIDER=azure-openai|openai|anthropic|gemini
PLANNER_MODEL=gpt-4o

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# OpenAI / Anthropic / Gemini
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Small model
USE_SMALL_MODEL=true|false
SMALL_MODEL_BACKEND=ollama|azure|transformers
WORKER_MODEL=phi3
OLLAMA_API_URL=http://localhost:11434
AZURE_SMALL_MODEL_ENDPOINT=...
AZURE_SMALL_MODEL_KEY=...
```

## Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Planner fails to start | Check `PLANNER_PROVIDER` matches your keys; enable DEBUG to see provider init logs |
| API key missing | Ensure env vars align with provider (Azure vs OpenAI vs Anthropic vs Gemini) |
| Small model not responding | Verify Ollama is running (`ollama list`) or Azure endpoint/key are set |
| Slow runs / timeouts | Reduce concurrent steps, enable streaming, set `max_retries`/`retry_delay` on steps |
| Tool not found | Refresh discovery and confirm tool name matches registry entry |

## Pointers

- Setup & install: [GETTING_STARTED](GETTING_STARTED.md)
- Configuration flags: [CONFIGURATION](CONFIGURATION.md)
- Feature explanations: [FEATURES_GUIDE](FEATURES_GUIDE.md)
- Building workflows: [WORKFLOW_USAGE_GUIDE](WORKFLOW_USAGE_GUIDE.md)
- Examples catalog: [../examples/README.md](../examples/README.md)

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
