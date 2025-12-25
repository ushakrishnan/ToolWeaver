# Security Threat Model

## Overview

ToolWeaver is a production-ready AI tool orchestration platform that executes arbitrary code and runs LLM workloads. This document outlines the security threat model, assumptions, and mitigations.

**Last Updated**: December 22, 2025  
**Status**: Active (Phase 0 Security Review)

---

## 1. Trust Assumptions

### 1.1 What We Trust

- **LLM Provider Responses**: We trust that responses from configured LLM providers (OpenAI, Anthropic, Gemini, etc.) are legitimate and not poisoned.
- **Tool Definitions**: We trust that tool YAML definitions and decorator-registered tools are authored by trusted administrators.
- **Configuration Files**: We trust that `pyproject.toml`, `.env`, and config files are controlled by trusted operators.
- **Skill Library Sources**: We trust that skill sources (local disk, GitHub, enterprise registries) are controlled by the deployment operator.
- **Monitoring/Audit Infrastructure**: We trust that audit logs, monitoring backends (Prometheus, Wandb, OTLP), and database backends are available and trustworthy.

### 1.2 What We Don't Trust

- **Untrusted Code Execution**: User-provided Python code (from agents, skills, or workflows) is executed in sandboxes with limited capabilities.
- **External APIs**: HTTP endpoints called by tools may be untrusted; responses are validated but not assumed benign.
- **Vector/Cache Databases**: Qdrant, Redis, SQLite may be compromised; we validate data integrity where possible.
- **User Inputs**: Text inputs to LLMs, tool parameters, and workflow definitions are assumed potentially malicious.

---

## 2. Attack Surface & Threat Scenarios

### 2.1 Code Injection Threats

**Threat**: Malicious code execution via skill injection, workflow definition injection, or tool parameter injection.

**Scenarios**:
- Attacker injects `__import__('os').system('rm -rf /')` into a skill code field
- LLM returns tool parameters containing shell escape sequences
- Workflow YAML contains arbitrary Python expressions in field values

**Mitigations**:
- **Sandbox Isolation** (Section 3.1): Code executed in restricted Python environment with:
  - Limited builtins (no `__import__`, `eval`, `exec` by default)
  - Restricted globals: only safe types (list, dict, set, tuple, str, int, float, bool, None)
  - Restricted filesystem: `PathFilter` enforces scoped directory access
  - No network access from within sandbox
- **YAML Parsing Safety** (Section 3.2): YAML deserialized without `Loader=yaml.FullLoader`; uses safe loader by default
- **Tool Parameter Validation**: Pydantic models validate tool parameters before execution
- **Skill Versioning & Signatures**: Skills are versioned; optional cryptographic signatures validate authenticity

### 2.2 Resource Exhaustion Threats

**Threat**: Malicious or buggy code consumes excessive resources, denying service.

**Scenarios**:
- Infinite loop in skill code causes 100% CPU for indefinite time
- Skill allocates unbounded memory (e.g., `[1] * 10_000_000_000`)
- Skill opens thousands of files, exhausting file descriptors
- Skill makes millions of API calls, exhausting rate limits

**Mitigations**:
- **Execution Timeout** (Section 3.3): All user code runs under timeout (default: 60s, configurable). Exceeded timeouts raise `TimeoutError`.
- **Memory Limits** (Section 3.4): Sandbox enforces max heap size via `resource.setrlimit(resource.RLIMIT_AS, ...)`.
- **File Descriptor Limits**: OS-level FD limits restrict number of open files.
- **API Rate Limiting**: Tools validate rate limits; quotas enforced per session.
- **Workspace Quotas** (Section 3.5): Workspace persists intermediate outputs under per-session quota (default: 100MB, 1000 files).

### 2.3 Information Disclosure Threats

**Threat**: Attacker reads sensitive data (secrets, other users' data, system internals).

**Scenarios**:
- Skill code reads `os.environ` to extract API keys
- Skill reads files outside workspace directory
- Skill queries audit logs to find sensitive user actions
- LLM exfiltrates data by embedding it in tool parameters

**Mitigations**:
- **Environment Variable Filtering**: Unsafe env vars filtered before sandbox execution (see `sandbox.py:_filter_environment`).
- **Filesystem Sandboxing** (Section 3.1): PathFilter restricts access to designated workspace only.
- **Audit Trail Separation** (Section 4): Audit logs recorded; access controls prevent unprivileged users from reading logs.
- **Output Encoding**: Responses sanitized before being sent to LLM or returned to user.

### 2.4 Privilege Escalation Threats

**Threat**: Non-admin user gains admin privileges or accesses resources they shouldn't.

**Scenarios**:
- Non-admin user modifies workflow definitions to run arbitrary code
- User reads/modifies other user's workspace data
- User bypasses team approval workflow via API

**Mitigations**:
- **Role-Based Access Control** (RBAC) (Section 4): Workflows, tools, and API endpoints enforce role checks.
- **Team Collaboration Gating** (Section 4): Multi-step approval required for sensitive actions (code execution, skill registration, data export).
- **Workspace Isolation**: Each session has isolated workspace; cross-session access blocked.
- **Audit Logging** (Section 4): All privilege-requiring operations logged with actor, action, resource, timestamp.

### 2.5 Supply Chain Threats

**Threat**: Compromised dependency (PyPI package, skill from registry) contains malicious code.

**Scenarios**:
- Attacker publishes typosquatted package (e.g., `pytorch` instead of `torch`)
- Skill registry account compromised; attacker publishes malicious skill
- GitHub Actions workflow poisoned to inject backdoor

**Mitigations**:
- **Dependency Pinning**: `pyproject.toml` pins all versions; no automatic upgrades.
- **Skill Versioning & Signatures** (Section 3.2): Skills versioned and optionally cryptographically signed.
- **Workspace/Skill Audit**: `WorkspaceManager` tracks skill versions, hashes, and installation source.
- **CI/CD Security**: GitHub Actions workflows use pinned actions; secrets managed via GitHub Secrets.

---

## 3. Technical Mitigations

### 3.1 Code Sandbox Architecture

**Location**: `orchestrator/execution/sandbox.py`

**Design**:
```
User Code
    ↓
Sandbox Container
├─ Restricted Builtins (no __import__, eval, exec, open)
├─ Safe Globals (list, dict, set, tuple, str, int, float, bool, None)
├─ Filesystem Filter (PathFilter: read/write only workspace)
├─ Network Disabled (no socket access)
└─ Resource Limits (timeout, memory, file descriptors)
    ↓
Tool Dispatcher (orchestrator/execution/dispatch/)
    ↓
LLM/External APIs
```

**Key Controls**:
- `SafeExecutor.execute()`: Runs code in restricted namespace
- `PathFilter`: Allows only workspace-scoped paths
- `execute_with_timeout()`: Enforces execution timeout
- `_filter_environment()`: Removes sensitive env vars

**Testing**: `tests/test_sandbox.py`, `tests/test_sandbox_filters.py`

---

### 3.2 Skill Loading & Validation

**Location**: `orchestrator/tools/loaders.py`, `orchestrator/execution/skill_library.py`

**Design**:
```
YAML Skill File / Python Decorator
    ↓
YAML.safe_load() / Pydantic Validation
    ↓
Skill Model (ToolDefinition, SkillDefinition)
    ↓
Hash Calculation (SHA256)
    ↓
Optional Signature Verification (Ed25519)
    ↓
Skill Registry / Workspace
```

**Key Controls**:
- YAML safe loader (no arbitrary object construction)
- Pydantic model validation (type checking, field constraints)
- Hash stored in metadata for integrity checking
- Optional cryptographic signatures (stored in `.signature` file)

**Testing**: `tests/test_loaders.py`, `tests/test_skill_library.py`

---

### 3.3 Execution Timeout

**Location**: `orchestrator/execution/sandbox.py:execute_with_timeout()`

**Design**:
```python
with timeout(seconds=60):
    result = eval(user_code, safe_globals)  # Raises TimeoutError if exceeds 60s
```

**Behavior**:
- Default: 60 seconds
- Configurable: `skill_config.timeout_seconds`
- Exceeded: Raises `TimeoutError` (caught, logged, operation fails gracefully)

**Testing**: `tests/test_sandbox.py`

---

### 3.4 Memory Limits

**Location**: `orchestrator/execution/sandbox.py:SafeExecutor`

**Design**:
```python
resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))  # Address space limit
```

**Behavior**:
- Default: 500MB per execution
- Configurable: `skill_config.max_memory_mb`
- Exceeded: Raises `MemoryError` (caught, operation fails gracefully)

**Testing**: `tests/test_sandbox.py` (mocked due to resource limitations in CI)

---

### 3.5 Workspace Quotas

**Location**: `orchestrator/execution/workspace.py:WorkspaceManager`

**Design**:
```
WorkspaceManager (per session)
├─ Max Size: 100MB (configurable)
├─ Max Files: 1000 (configurable)
├─ Max Skill Size: 1MB per skill
└─ Max Intermediate: 10MB per file

save_skill() / save_intermediate()
├─ Check quota
├─ Check size
└─ Reject if exceeded (raise WorkspaceQuotaExceeded)
```

**Behavior**:
- Enforced at save time (not retroactively)
- Prevents runaway skill accumulation
- Quota metadata tracked in `metadata.json`

**Testing**: `tests/test_workspace.py`

---

## 4. Audit & Compliance

### 4.1 Audit Trail

**Location**: `orchestrator/execution/team_collaboration.py:AuditTrail`

**Events Logged**:
- **Access**: User login, workspace access, skill access
- **Modification**: Skill registration, workflow creation, approval status change
- **Execution**: Tool call, code execution, error occurrence
- **Privilege**: Approval requested, approval granted, privilege escalation

**Fields Per Event**:
```python
{
  "timestamp": "2025-12-22T10:15:30Z",
  "actor_id": "user@example.com",
  "action": "AuditAction.EXECUTE_SKILL",
  "resource_type": "skill",
  "resource_id": "data_parser",
  "details": {"result": "success", "duration_ms": 1234},
  "status": "success" | "failure"
}
```

**Storage**: SQLite (local) or PostgreSQL (enterprise), with optional export to SIEM.

**Retention**: 90 days default (configurable).

**Testing**: `tests/test_team_collaboration.py`

---

### 4.2 Role-Based Access Control (RBAC)

**Location**: `orchestrator/execution/team_collaboration.py:SkillApprovalWorkflow`

**Roles**:
- **User**: Can call approved tools, create workflows
- **Developer**: Can register skills, create tools
- **Approver**: Can approve skill registration and multi-step workflows
- **Admin**: Unrestricted access

**Enforced Checks**:
```python
@require_role('developer')
def register_skill(skill_def: SkillDefinition):
    ...

@require_role('approver')
def approve_workflow_request(request_id: str):
    ...
```

**Testing**: `tests/test_team_collaboration.py`

---

### 4.3 Data Handling

**PII/Secrets**:
- Never logged in audit trails (automated redaction in progress)
- Masked in error messages (e.g., `api_key="****...xyz"`)
- Env vars filtered before sandbox execution
- Workspace data encrypted at rest (optional, via `WorkspaceEncryption` plugin)

**Cross-User Isolation**:
- Each user has isolated workspace directory
- Skill registry validates ownership before modification
- Workflows scoped to team/project

---

## 5. Deployment Security Checklist

### Production Deployment

- [ ] **Environment**: Run on isolated VM/container, not shared cluster
- [ ] **Network**: No outbound internet (if possible); proxy external calls through enterprise gateway
- [ ] **Secrets Management**: Use HashiCorp Vault / AWS Secrets Manager; not `.env` files
- [ ] **Audit Logging**: Forward audit logs to SIEM (Splunk, ELK, Datadog)
- [ ] **Monitoring**: Alert on:
  - Timeout/memory errors (potential attack)
  - Suspicious API calls from sandbox
  - Unauthorized access attempts
  - Large file operations
- [ ] **Backup**: Daily backup of workspace and audit logs
- [ ] **Rotation**: Rotate API keys monthly; rotate database credentials quarterly
- [ ] **Hardening**: Run as non-root user; disable unnecessary OS features

### Development/Testing

- [ ] **Isolation**: Run in isolated VM/container, not developer laptop
- [ ] **No Secrets**: Don't commit API keys; use `.env.example` only
- [ ] **Testing**: Include fuzzing tests for code execution
- [ ] **Dependencies**: Keep pyproject.toml up-to-date; audit dependencies monthly

---

## 6. Known Limitations & Future Work

### Current Limitations

1. **No Cryptographic Signatures** (Phase 1): Skill signatures optional; not enforced
2. **Limited Encryption** (Phase 2): Workspace data not encrypted at rest by default
3. **No Network Isolation** (Phase 2): Tools can call any external API; no proxy/egress filtering
4. **Audit Redaction** (Phase 1): PII redaction not yet automated; manual review required
5. **No Multi-Tenancy** (Phase 2): Single-tenant per deployment; no built-in multi-tenancy isolation

### Future Enhancements

- **Phase 1.5 (Q1 2026)**:
  - Mandatory skill signature verification
  - Automated audit redaction for PII
  - OTLP observability for security events
  
- **Phase 2 (Q2 2026)**:
  - Workspace encryption (AES-256-GCM)
  - Network egress filtering via proxy
  - Multi-tenancy with namespace isolation
  - Hardware security module (HSM) integration for key management

---

## 7. References & Further Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Sandboxing Techniques](https://en.wikipedia.org/wiki/Sandbox_(computer_security))
- [Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling)

---

## 8. Questions & Support

For security questions or to report a vulnerability:
- **GitHub Issues**: [security] tag on public repo
- **Email**: security@example.com (configure in SECURITY.md)
- **Response Time**: Critical (CVSS 9+) within 24h; High (CVSS 7-8) within 7d

---

**Document Version**: 1.0  
**Last Reviewed**: December 22, 2025  
**Next Review**: March 22, 2026
