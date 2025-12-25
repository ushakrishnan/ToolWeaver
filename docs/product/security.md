# Security & Safety

## Simple Explanation
Run many small steps safely: secrets never leak in logs, dangerous code is blocked, and we enforce time and resource limits.

## Technical Explanation
Security combines template sanitization, secrets/PII redaction, sandboxed code execution (restricted builtins, timeouts, memory/FD limits, workspace path filters), and operational guardrails (cost/concurrency/rate limits, idempotency). See the concise threat model below.

## Built-in protections
- Secrets redaction: prevents credentials in logs (installed automatically)
- PII filtering: sanitize templates to avoid leakage
- Template sanitization: block dangerous tokens/patterns
- Sandboxed execution: restricted builtins/modules, timeouts

## Threat model (concise)
- Trust: code/config from trusted operators; LLM providers trusted; user inputs untrusted; external APIs/vector/cache stores treated as potentially hostile.
- Code execution risks: mitigated by sandbox (no network, restricted builtins, timeouts, memory/FD limits, workspace path filter).
- Resource exhaustion: timeouts, memory/FD limits, rate limits, quotas on workspace/files.
- Information disclosure: env filtering, workspace isolation, redaction in logs/outputs.
- Privilege/supply chain: role checks on sensitive ops, pinned deps; prefer managed secrets (Vault/Key Vault) and signed skills where available.

Operational checklist
- Use Managed Identity/Key Vault (avoid plain API keys in prod).
- Enable metrics/logging with redaction; alert on error/timeout spikes.
- Set cost/concurrency/rate limits for fan-out workloads.
- Rotate secrets regularly; restrict network egress for sandboxes where possible.

## Operational guardrails
- Cost caps and concurrency limits
- Failure-rate thresholds and total duration limits
- Idempotency cache: avoid duplicate execution

See:
- [Logging Helpers](../reference/api-python/logging.md)
- [Sandbox Execution](../tutorials/sandbox-execution.md)
- [Parallel Agents](../tutorials/parallel-agents.md)
