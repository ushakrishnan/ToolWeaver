# Security & Threat Model (Foundations)

This document outlines the initial threat model and defensive measures for ToolWeaver’s package-first architecture. It will evolve alongside Phases 1–3 as templates, decorators, and loaders come online.

## Trust Boundaries
- User input (requests, CLI args, env): Untrusted
- Model output (LLM plans, parameters): Untrusted
- External services (MCP servers, APIs, DBs): Untrusted
- Internal code paths under `orchestrator._internal`: Trusted implementation details, not public surface

## Attack Classes Considered
- Injection (shell, SQL, prompt-mediated); Path traversal; RCE in code execution; SSRF; Exfiltration
- Deserialization/unsafe eval; Dependency confusion; Supply-chain/plugin abuse
- Resource abuse (DoS via unbounded inputs, runaway loops)

## Baseline Defenses (Phase 0)
- Validation & Sanitization: use `orchestrator._internal.validation`:
	- `sanitize_string`, `sanitize_dict` prevent common injection patterns
	- `validate_file_path` prevents path traversal outside allowed roots
	- `validate_url` restricts unsafe protocols and loopback unless allowed
	- `validate_code` blocks dangerous AST nodes/functions by default
	- `validate_tool_input` composes sanitization + Pydantic schema checks
- Structured Tool Schemas: `ToolParameter`, `ToolDefinition` (Pydantic) enforce typed, documented parameters
- Optional Dependencies: gate with `_internal.errors` helpers (`require_package`, `MissingDependencyError`)
- Logging: `_internal.logger` for visibility without leaking secrets (avoid logging raw secrets/keys)

## Code Execution Safeguards (Foundational)
- Treat code execution as high risk; default to disabled in public APIs
- When enabled, ensure:
	- Strict timeouts (overall and per-chunk for streams)
	- Memory/CPU guardrails (process limits, where applicable)
	- No file/network access unless explicitly allowed
	- AST validation via `validate_code` and constrained builtins

## External MCP Servers
- Consider remote MCP endpoints untrusted. Adapter must:
	- Validate tool schemas and normalize parameters using Pydantic
	- Enforce timeouts/retries and map errors to typed exceptions
	- Apply allowlists for endpoints and require explicit configuration
	- Avoid proxying arbitrary file/URL inputs without validation

## Plugins & Supply Chain
- Plugins register via `orchestrator.plugins` and should be isolated packages
- Do not auto-install plugin dependencies; keep them in extras
- Prefer runtime checks to fail gracefully when optional deps are missing
- Encourage plugin authors to validate inputs and document trust assumptions

## Operational Guidance
- Secrets: pass via env vars; do not commit to repo/logs
- Least privilege: restrict tokens/keys to the minimum scopes required
- Observability: log errors, timeouts, and retries with enough context (no PII)
- CI: run linting, types, tests on all supported Python versions/OS matrix

## Future Work (Phases 1–3)
- Templates/Decorators: integrate schema validation + sanitization at registration and call-time
- YAML Loader: strict schema and safe import resolution
- Sandboxing: document recommended OS/container policies; optional seccomp/AppArmor guidance
- Diagnostics: surface health and error rates without leaking sensitive data

## Reviewer Checklist (PRs)
- Are inputs sanitized/validated before execution?
- Are optional deps gated and error messages helpful?
- Are secrets kept out of logs and docs?
- Are public APIs free of `_internal` imports?
- Are new external surfaces documented with trust boundaries?
