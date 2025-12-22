# Code-Mode Sandbox Pathway (Design Draft)

Goal: Execute agent-written code against typed MCP/ToolWeaver APIs inside an isolated sandbox, minimizing context/token load while enforcing security and data controls.

## Objectives
- Reduce context bloat by generating typed APIs from MCP/tool schemas and letting the agent write code.
- Enforce isolation: no outbound network; only explicit bindings to MCP endpoints/tool adapters.
- Enable progressive disclosure: load tool definitions on demand (search/browse/detail levels).
- Support data hygiene: local filtering/aggregation; optional PII tokenization before returning to the model.
- Allow stateful reuse: persisted skills/code in a scoped workspace with metadata (SKILL.md).

## Architecture (proposed)
- API generation: emit typed client stubs (TypeScript/Python) from ToolDefinition/MCP schemas; include doc comments.
- Sandbox runtime: per-request ephemeral VM/wasm/isolated process; deny default outbound network; provide bindings for approved MCP/tool calls.
- Bindings layer: wraps credentials/tokens; prevents key leakage; enforces allowlist (method+params) and rate limits; logs audited calls.
- FS workspace: scoped directory for persisted skills and intermediate artifacts; size/time quotas; optional clean-on-complete.
- Telemetry: structured logs for tool calls, sandbox stdout/stderr, resource usage, and policy violations.

## Progressive Tool Loading
- Discovery service exposes search/browse:
  - List servers/domains/tools (names only)
  - Fetch summaries (name+description)
  - Fetch full schema (parameters, IO schemas)
- Agent flow: search → fetch needed schemas → generate imports → execute code.

## Data Handling & PII
- In-sandbox transforms: filter/aggregate large datasets before returning.
- Tokenization option: replace sensitive fields (email/phone/name) before model sees outputs; detokenize only when sending to downstream tools.
- Caps: max rows/bytes returned to model; logs truncated with notice.

## Security Controls
- Network: default deny; only binding calls allowed; no generic fetch/connect.
- Resources: CPU/mem/runtime limits per execution; kill on exceed.
- I/O: FS sandbox with allowlist paths; no device/exec access.
- Policy enforcement: schema-level validation of tool calls; audit log of all invocations; optional approval gates for high-risk tools.

## Rollout Plan (staged)
1) Design/Scaffolding
   - Generate typed stubs from ToolDefinition (Phase: current)
   - Define sandbox interface (bindings, FS contract, limits)
2) Progressive Loading
   - Implement search/browse/detail APIs and client helpers
   - CLI flag or API param to fetch summaries/full schemas on demand
3) Sandbox Prototype
   - Local sandbox runner (no network); bindings shim to call existing tool adapters
   - Logging/limits; minimal PII redaction (configurable)
4) Data Hygiene
   - Add tokenization/redaction utilities; max-output guards; truncated logging
5) Skill Persistence
   - Scoped workspace; SKILL.md metadata; list/load saved skills; quota enforcement
6) Hardening
   - Policy engine (allow/deny), rate limits, audit sinks; optional approvals for sensitive domains

## Open Questions
- Target runtime (Node/V8 isolate vs. Python subprocess vs. wasm)?
- How to surface binding schemas to the agent for autocomplete/docgen?
- Do we need multi-tenant isolation inside the same host process?
- Credential handling for third-party MCP servers (per-binding token vault)?

## Success Criteria
- 50%+ token reduction for workflows with many tools or large outputs.
- No outbound network except whitelisted bindings; zero key leakage by design.
- Progressive loading yields <10% of previous context size for large catalogs.
- Sandbox executions capped within defined CPU/mem/time limits.
- Skills can be persisted and reused safely within workspace constraints.
