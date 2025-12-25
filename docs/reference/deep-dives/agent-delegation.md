# Agent Delegation

## Simple Explanation
Let one agent hand off a task to another specialized agent. Discover available agents, match by capability, and delegate with clear inputs/outputs.

## Technical Explanation
Use an A2A (agent-to-agent) client and registry: discover agents and their tools via metadata or YAML, select candidates by capability tags, and execute remotely with well-defined payloads. Track delegation outcomes for learning.

**When to use**
- Specialized agents (e.g., data extraction vs analysis) working together
- Cross-boundary execution in separate processes or services

**Key Primitives**
- Agent registry and metadata
- A2A client for remote tool execution
- Capability-based selection and scoring
- Audit logs and feedback loops

**Try it**
- Discover agents: [samples/16-agent-delegation/discover_agents.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/16-agent-delegation/discover_agents.py)
- Delegate tasks: [samples/16-agent-delegation/delegate_to_agent.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/16-agent-delegation/delegate_to_agent.py)
- See the README: [samples/16-agent-delegation/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/16-agent-delegation/README.md)

**Gotchas**
- Validate payload schemas across agents to avoid decoding issues
- Prevent circular delegation; enforce max hops and tracing
- Handle auth/permissions if agents run in different domains
