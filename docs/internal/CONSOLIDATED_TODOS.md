# ToolWeaver: Master TODO List

**Last Updated:** December 23, 2025  
**Status:** Phase 0 (Security) → Phase 1-4 (Agent Orchestration) → Backlog  
**Current Phase:** Phase 0 (Security Foundations) - NOT STARTED  
**Next Task:** 0.1 - Sub-Agent Resource Quotas

---

## 📊 OVERALL PROGRESS

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        TOOLWEAVER ROADMAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 0: Security      ⬜⬜⬜⬜⬜⬜⬜  0/7   🔒 BLOCKER
Phase 1: Dispatch      ⏸️⏸️⏸️⏸️  0/4   ⏸️ BLOCKED by Phase 0
Phase 2: Composition   ⏸️⏸️⏸️    0/3   ⏸️ BLOCKED by Phase 1
Phase 3: Cost Select   ⏸️⏸️⏸️    0/3   ⏸️ BLOCKED by Phase 2
Phase 4: Recovery      ⏸️⏸️⏸️    0/3   ⏸️ BLOCKED by Phase 3

Quick Wins             ⬜⬜⬜      0/3   ✅ Can do anytime

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 0/23 tasks complete (0%)
Estimated Time Remaining: ~5 weeks (Phase 0: 5-7 hours blocking)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 EXECUTION ROADMAP

```
Phase 0 (Security)  →  Phase 1 (Dispatch)  →  Phase 2 (Composition)  →  Phase 3 (Cost)  →  Phase 4 (Recovery)
     5-7 hours              1 week               1.5 weeks              1 week            1 week
   🔒 BLOCKER            ⏸️ BLOCKED           ⏸️ BLOCKED            ⏸️ BLOCKED        ⏸️ BLOCKED
```

**⚠️ CRITICAL: Phase 0 MUST be completed before Phase 1 can begin**

---

## 📊 CURRENT STATE

### ✅ Foundation Complete
- **Infrastructure:** 699/735 tests passing (95%+), mypy=0 errors
- **Package:** Public API (37 exports), plugin system, decorators
- **Tools:** Template system, YAML loader, MCP adapter
- **Execution:** Sandbox, code execution, workflow DAGs
- **A2A:** Sequential delegation (A2AClient working)
- **Monitoring:** Local/wandb/prometheus backends
- **Security (Single-Op):** Sandbox isolation, input validation, audit logs

### ❌ Critical Gaps (Multi-Agent)
- **No aggregate resource limits** (cost, concurrency, time)
- **No rate limiting** for parallel API calls
- **No PII detection** in agent responses
- **No secrets redaction** in logs
- **No prompt injection** protection for templates
- **No recursion depth** limits for nested dispatch

---

## 🔒 PHASE 0: SECURITY FOUNDATIONS (5-7 hours)

**Status:** NOT STARTED  
**Blocker for:** Phase 1  
**Risk if skipped:** CRITICAL - $1000s financial loss + security breach

### 🎯 Goals
- Prevent cost exhaustion attacks
- Prevent data exfiltration
- Prevent credential leakage
- Prevent prompt injection at scale
- Enable safe parallel dispatch

### 📋 Task Breakdown

#### 0.1: Sub-Agent Resource Quotas (2-3 hours) ⚠️ CRITICAL
**File:** `orchestrator/tools/sub_agent_limits.py` (NEW)

**What to Build:**
- [x] Create `DispatchResourceLimits` dataclass
  - Cost controls: `max_total_cost_usd`, `cost_per_agent_estimate`
  - Concurrency: `max_concurrent`, `max_total_agents`
  - Time: `max_agent_duration_s`, `max_total_duration_s`
  - Rate limiting: `requests_per_second`
  - Failure: `max_failure_rate`, `min_success_count`
  - Recursion: `max_dispatch_depth`, `current_depth`
- [x] Create `DispatchQuotaExceeded` exception
- [x] Create `DispatchLimitTracker` class
  - `check_pre_dispatch()` - Validate BEFORE dispatch starts
  - `record_agent_completion()` - Track cost/failures during execution
  - Enforce all limits in real-time
- [x] Write unit tests (13 test cases)
  - Cost limit enforcement
  - Agent count limits
  - Recursion depth prevention
  - Failure rate fail-fast
  - Wall-clock timeout

**Threats Mitigated:**
- AS-1: Cost Bomb ($1000s+ in one dispatch)
- AS-2: Recursive Agent Spawn (exponential DoS)

**Acceptance Criteria:**
- [x] Dispatch fails if estimated cost > budget
- [x] Dispatch fails if depth > max_dispatch_depth
- [x] Dispatch fails fast if failure_rate > threshold
- [x] All tests pass

---

#### 0.2: Rate Limiter (1-2 hours) ⚠️ HIGH
**File:** `orchestrator/_internal/infra/rate_limiter.py` (NEW)

**What to Build:**
- [x] Create `RateLimiter` class (token bucket algorithm)
  - Constructor: `requests_per_second`, `burst_size`
  - Method: `async acquire()` - Block until token available
  - Context manager support (`async with rate_limiter:`)
- [x] Token refill logic (elapsed × rate)
- [x] Thread-safe with asyncio.Lock
- [x] Write unit tests (17 test cases)
  - Correct rate enforcement (10 RPS test)
  - Burst handling
  - Concurrent usage (thread safety)

**Threats Mitigated:**
- API rate limit errors from upstream services
- Overwhelming external APIs with parallel requests

**Acceptance Criteria:**
- [x] 10 RPS limit allows exactly 10 requests in 1 second
- [x] Burst allows temporary spike
- [x] Thread-safe under concurrent load

---

#### 0.3: Auth Structure (30 min) ⚠️ MEDIUM
**File:** `orchestrator/_internal/infra/a2a_auth.py` (NEW)

**What to Build:**
- [x] Create `AuthConfig` dataclass
  - Fields: `type` ("bearer", "api_key", "none"), `token_env`, `header_name`
- [x] Create `AuthManager` class
  - Method: `get_headers(config)` - Returns dict with auth headers
  - Handle bearer token formatting
  - Validate token exists in env
- [x] Write unit tests (19 test cases)

**Threats Mitigated:**
- Missing auth tokens causing silent failures
- Foundation for OAuth2/mTLS later

**Acceptance Criteria:**
- [x] Bearer token formatted correctly
- [x] Raises error if token missing

---

#### 0.4: PII Detection & Response Filtering (2 hours) ⚠️ HIGH
**File:** `orchestrator/_internal/security/pii_detector.py` (NEW)

**What to Build:**
- [x] Create `PIIDetector` class
  - Regex patterns: SSN, email, credit card, phone, API key
  - Method: `scan(text)` - Returns list of (type, match) findings
  - Method: `redact(text)` - Replace PII with `[REDACTED_TYPE]`
- [x] Create `ResponseFilter` class
  - Method: `filter_response(response_dict)` - Remove sensitive keys, redact PII
  - Add `_field_pii_detected` metadata for audit
- [x] Write unit tests (28 test cases)
  - Detect SSN, email, credit card, phone
  - Redaction accuracy
  - Nested dict handling

**Threats Mitigated:**
- AS-4: PII Exfiltration (GDPR/CCPA violation)
- Data breach via compromised agents

**Acceptance Criteria:**
- [x] SSN "123-45-6789" redacted to "[REDACTED_SSN]"
- [x] API keys removed from responses
- [x] Metadata tracks what was redacted

---

#### 0.5: Secrets Redaction in Logs (1 hour) ⚠️ CRITICAL
**File:** `orchestrator/_internal/security/secrets_redactor.py` (NEW)

**What to Build:**
- [x] Create `SecretsRedactor(logging.Filter)`
  - Regex patterns: api_key, bearer token, password, OpenAI key, GitHub token
  - Method: `filter(record)` - Redact secrets from log messages
- [x] Create `install_secrets_redactor()` - Install on root logger
- [ ] Integrate in `orchestrator/__init__.py` (called at import)
- [x] Write unit tests (24 test cases)
  - OpenAI key "sk-abc..." → "[REDACTED_OPENAI_KEY]"
  - Bearer tokens redacted
  - Passwords redacted

**Threats Mitigated:**
- AS-3: Credential Harvesting (API keys in logs × 100 agents)
- Security breach via log files

**Acceptance Criteria:**
- [x] "sk-abc123" never appears in logs
- [x] Bearer tokens redacted
- [ ] Works across all logger instances

---

#### 0.6: Template Sanitization (1 hour) ⚠️ HIGH
**File:** `orchestrator/_internal/security/template_sanitizer.py` (NEW)

**What to Build:**
- [x] Add `LLM_INJECTION_PATTERNS` regex list
  - "ignore previous instructions"
  - "disregard prior"
  - "you are now"
  - "system:"
- [x] Add `sanitize_template(template)` function
  - Check LLM injection patterns
  - Check existing DANGEROUS_PATTERNS
  - Raise `UnsafeInputError` if found
- [x] Write unit tests (40 test cases)
  - Detect common prompt injections
  - Allow safe templates

**Threats Mitigated:**
- AS-5: Mass Prompt Injection (malicious template × 100 agents)
- LLM jailbreak at scale

**Acceptance Criteria:**
- [x] "Ignore previous instructions" blocked
- [x] "system: you are now" blocked
- [x] Safe templates pass validation

---

#### 0.7: Idempotency Keys (1 hour) ⚠️ MEDIUM
**File:** `orchestrator/_internal/infra/idempotency.py` (NEW)

**What to Build:**
- [x] Add `idempotency_key` field to `SubAgentTask`
- [x] Create `generate_idempotency_key(task)` function
  - Hash: template + arguments + agent_name
  - Return 16-char hex string
- [x] Add idempotency check in `dispatch_agents()`
  - Check cache before dispatch
  - Store result with key after completion
- [x] Write unit tests (4+ test cases)

**Threats Mitigated:**
- AS-6: Race Conditions (duplicate operations on retry)
- Data corruption from concurrent access

**Acceptance Criteria:**
- [x] Same task generates same key
- [x] Cached results returned immediately
- [x] No duplicate operations

---

### ✅ Phase 0 Completion Checklist

**Before proceeding to Phase 1:**
- [x] All 7 components implemented
- [x] All unit tests passing (35+ tests total)
- [ ] Security tests added to CI
- [ ] Code review completed
- [x] Documentation updated

**Estimated Time:** 6.5-7.5 hours (mandatory: 5-6 hours)

---

## 🚀 PHASE 1: PARALLEL SUB-AGENT DISPATCH (v0.4)

**Status:** 🚧 IN PROGRESS (Phase 1 started)  
**Timeline:** 1 week (6-8 hours)  
**Depends on:** Phase 0 complete

### 🎯 Goals
Enable agents to dispatch 100+ sub-agents in parallel for divide-and-conquer tasks.

### 📋 Task Breakdown

#### 1.1: Define Dispatch API (1 hour)
**File:** `orchestrator/tools/sub_agent.py` (NEW)

**What to Build:**
- [x] Create `SubAgentTask` dataclass
  - Fields: `prompt_template`, `arguments`, `agent_name`, `model`, `timeout_sec`, `idempotency_key`
- [x] Create `SubAgentResult` dataclass
  - Fields: `task_args`, `output`, `error`, `duration_ms`, `success`, `cost`
- [x] Define `dispatch_agents()` function signature
  ```python
  async def dispatch_agents(
      template: str,
      arguments: List[Dict[str, Any]],
      agent_name: str = "default",
      model: str = "haiku",
      max_parallel: int = 10,
      timeout_per_agent: int = 30,
      limits: Optional[DispatchResourceLimits] = None,
      **kwargs
  ) -> List[SubAgentResult]
  ```
- [x] Add comprehensive docstrings with examples
- [ ] Write API design doc

**Acceptance Criteria:**
- [ ] Clean, intuitive API design
- [x] Type hints on all functions
- [x] Docstrings with usage examples

---

#### 1.2: Implement Parallel Execution (2-3 hours)
**File:** `orchestrator/tools/sub_agent.py`

**What to Build:**
- [x] Template filling logic (format strings with arguments)
- [x] Create agent tasks from template + arguments
- [x] Implement parallel dispatch with `asyncio.gather()`
- [x] Add semaphore for `max_parallel` concurrency control
- [x] Integrate `DispatchResourceLimits` from Phase 0
- [x] Integrate `RateLimiter` from Phase 0 (if configured)
- [x] Per-agent timeout handling (don't fail all if one times out)
- [x] Per-agent error capture (store in `SubAgentResult.error`)
- [x] Track cost per agent (use `A2AClient` cost tracking)
- [x] Apply `ResponseFilter` from Phase 0 to all results
- [x] Template sanitization via Phase 0 `sanitize_template()`

**Integration Points:**
```python
# Uses Phase 0 components:
limits = limits or DispatchResourceLimits()
tracker = DispatchLimitTracker(limits)
tracker.check_pre_dispatch(len(arguments))

template = sanitize_template(template)  # Phase 0.6
rate_limiter = RateLimiter(limits.requests_per_second) if limits.requests_per_second else None

for result in results:
    filtered = ResponseFilter.filter_response(result)  # Phase 0.4
    tracker.record_agent_completion(result.cost, result.success)  # Phase 0.1
```

**Acceptance Criteria:**
- [x] 100 agents execute in parallel
- [x] Respects max_parallel limit
- [x] One failure doesn't stop others
- [x] All Phase 0 integrations working

---

#### 1.3: Add Aggregation & Ranking (1-2 hours)
**File:** `orchestrator/tools/sub_agent.py`

**What to Build:**
- [x] Result collection from parallel execution
- [x] Success rate calculation
- [x] Check `min_success_count` threshold (raise if not met)
- [x] Built-in aggregation functions:
  - `collect_all()` - Return all results as-is
  - `rank_by_metric(field)` - Sort results by a field
  - `majority_vote(field)` - Find most common value
  - `best_result(score_fn)` - Return highest scored result
- [x] Optional custom aggregation function parameter

**Acceptance Criteria:**
- [x] All aggregation patterns work
- [x] Thresholds enforced
- [x] Custom functions supported

---

#### 1.4: Integration & Testing (2-3 hours)
**File:** `tests/test_sub_agent_dispatch.py` (NEW)

**What to Build:**
- [ ] Unit tests (15+ test cases):
  - Basic dispatch (10 agents)
  - Large dispatch (100 agents)
  - Max parallel enforcement
  - Timeout handling
  - Error handling (partial failures)
  - Cost tracking
  - Success rate threshold
  - Template filling accuracy
  - Idempotency (same task = same result)
  - **Integration with Phase 0:**
    - Cost limit enforcement
    - Rate limiting
    - PII redaction
    - Secrets redaction
    - Template sanitization
    - Recursion depth limits
- [ ] Integration test with real A2AClient
- [ ] Example: `examples/25-parallel-agents/`
  - Quicksort comparison (100 implementations)
  - Unit test ranking (parallel test execution)
- [ ] Documentation: `docs/user-guide/sub_agent_dispatch.md`

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] >90% code coverage
- [ ] Examples run successfully
- [ ] Documentation complete

---

### ✅ Phase 1 Completion Checklist
- [ ] All 4 sub-tasks complete
- [ ] All tests passing (15+ new tests)
- [ ] Integration with Phase 0 validated
- [ ] Examples working
- [ ] Documentation published
- [ ] Ready for v0.4 release

---

## 🧩 PHASE 2: TOOL COMPOSITION (v0.5)

**Status:** ⏸️ BLOCKED (waiting for Phase 1)  
**Timeline:** 1.5 weeks (10-12 hours)  
**Depends on:** Phase 1 complete

### 🎯 Goals
Chain tools where output of one becomes input to next.

### 📋 Task Breakdown

#### 2.1: Define Composition API (2 hours)
**What to Build:**
- [ ] Create `CompositionStep` dataclass
- [ ] Define `@composite_tool` decorator
- [ ] Parameter mapping syntax

#### 2.2: Implement Chain Execution (4 hours)
**What to Build:**
- [ ] Extend HybridDispatcher for chains
- [ ] Auto-wire outputs to inputs
- [ ] Error propagation logic

#### 2.3: Testing & Examples (4-6 hours)
**What to Build:**
- [ ] 15+ unit tests
- [ ] Integration test
- [ ] Example: Fetch → Parse → Extract pipeline
- [ ] Documentation

**Effort:** 10-12 hours

---

## 💰 PHASE 3: COST-BENEFIT SELECTION (v0.5.5)

**Status:** ⏸️ BLOCKED (waiting for Phase 2)  
**Timeline:** 1 week (6-8 hours)  
**Depends on:** Phase 2 complete

### 🎯 Goals
Let planners choose tools based on cost/latency constraints.

### 📋 Task Breakdown

#### 3.1: Add Metadata Fields (2 hours)
**What to Build:**
- [ ] Extend `ToolDefinition` with cost/latency fields
- [ ] Update @tool decorator
- [ ] Database migration

#### 3.2: Implement Selection Logic (3 hours)
**What to Build:**
- [ ] Efficiency scoring algorithm
- [ ] `registry.get_best_tool()` method
- [ ] Budget constraint checking

#### 3.3: Testing & Examples (2-3 hours)
**What to Build:**
- [ ] 10+ unit tests
- [ ] Example: Cost optimization
- [ ] Documentation

**Effort:** 6-8 hours

---

## 🛡️ PHASE 4: ERROR RECOVERY AT SCALE (v0.6)

**Status:** ⏸️ BLOCKED (waiting for Phase 3)  
**Timeline:** 1 week (6-8 hours)  
**Depends on:** Phase 3 complete

### 🎯 Goals
Graceful degradation when partial failures occur.

### 📋 Task Breakdown

#### 4.1: Define Policy Model (2 hours)
**What to Build:**
- [ ] Create `ErrorRecoveryPolicy` dataclass
- [ ] Policy types: retry, fallback, partial_success

#### 4.2: Implement Recovery (3-4 hours)
**What to Build:**
- [ ] Integrate with dispatch_agents()
- [ ] Retry with exponential backoff
- [ ] Fallback tool selection
- [ ] Partial result handling

#### 4.3: Testing & Examples (2-3 hours)
**What to Build:**
- [ ] 12+ unit tests
- [ ] Example: Resilient dispatch
- [ ] Documentation

**Effort:** 6-8 hours

---

## ⚡ QUICK WINS (Can Do Anytime)

These provide immediate value without waiting for full phases.

### QW1: Export A2A Classes to Public API (1 hour)
- [ ] Add to `orchestrator/__init__.py`:
  - `AgentDelegationRequest`
  - `AgentDelegationResponse`
  - `A2AClient`
- [ ] Update `__all__` list
- [ ] Add to documentation

### QW2: Multi-Agent Quicksort Example (2 hours)
- [ ] Create `examples/quicksort-orchestration/`
- [ ] Show A2AClient usage for parallel patterns
- [ ] Document cost calculation
- [ ] Performance results

### QW3: Parallel Patterns Documentation (1 hour)
- [ ] Create `docs/user-guide/parallel-agents.md`
- [ ] Document A2AClient patterns
- [ ] Cost calculation examples
- [ ] Error handling best practices

---

## 🔧 TECHNICAL DEBT & IMPROVEMENTS (Backlog)

### Low Priority

**Type Safety:**
- [ ] Complete type hints in optional modules
- [ ] Add type hints to tests

**Logging:**
- [ ] Expand structured logging to more paths
- [ ] Standardize log levels

**Documentation:**
- [ ] Update ANTHROPIC_MCP_COMPARISON.md
- [ ] Update RELEASES.md with v0.2.0+
- [ ] Create 2-3 advanced workflow examples
- [ ] Create getting-started video
- [ ] Expand troubleshooting guide

**Performance:**
- [ ] Benchmark streaming chunk sizes
- [ ] Cost analytics improvements
- [ ] Caching layer optimization

---

## ⏭️ DEFERRED (Post-Launch)

**Phase 5b: Monitoring Plugins** (community-driven)
- W&B integration adapter
- Prometheus metrics exporter
- Grafana dashboard template

**Infrastructure:**
- Version check on startup
- Additional platform docs

---

## 📈 SUCCESS METRICS

### Code Quality
- ✅ mypy = 0 errors
- ✅ 95%+ test pass rate (699/735)
- 🎯 >90% code coverage per phase
- 🎯 No regressions

### Timeline
- 🎯 Phase 0: 5-7 hours
- 🎯 Phase 1: 1 week
- 🎯 Phase 2: 1.5 weeks
- 🎯 Phase 3: 1 week
- 🎯 Phase 4: 1 week
- **Total: ~5 weeks**

### User Impact
- 🎯 100+ parallel agent dispatch
- 🎯 Tool composition <100ms overhead
- 🎯 Cost predictions within 10%
- 🎯 95%+ success with error recovery

---

## 📚 REFERENCE DOCUMENTS

### Primary Planning
- **CONSOLIDATED_TODOS.md** (THIS FILE) - Master TODO list
- **SECURITY_ARCHITECTURE_REVIEW.md** - Complete security analysis & threat model
- **AGENT_ORCHESTRATION_ROADMAP.md** - Detailed 4-phase plan (973 lines)
- **INTEGRATION_ASSESSMENT.md** - What exists vs. gaps (510 lines)
- **TOMORROW_PLAN.md** - CI stabilization status

### Reference & History
- **A2A_INTEGRATION_PLAN.md** - Phase 2 A2A completion (🟢 COMPLETE)
- **NOT_YET_COMPLETED.md** - Phase 0-5a status tracking
- **CODE_EXECUTION_IMPLEMENTATION_PLAN.md** - Phase 0-1 reference

### Strategic
- **BUSINESS_STRATEGY.md** - Business model, licensing
- **AGENT_UX_AND_MARKET_POSITIONING.md** - Market positioning

---

## 🎯 CURRENT FOCUS

**Next Action:** Begin Phase 0 (Security Foundations)  
**Current Task:** 0.1 - Sub-Agent Resource Quotas  
**ETA:** 2-3 hours

**Progress Tracking:**
- Phase 0: ⬜⬜⬜⬜⬜⬜⬜ 0/7 complete
- Phase 1: ⏸️ BLOCKED
- Phase 2: ⏸️ BLOCKED
- Phase 3: ⏸️ BLOCKED
- Phase 4: ⏸️ BLOCKED

---

**Document Version:** 2.0 (MASTER)  
**Last Updated:** December 23, 2025  
**Next Review:** After Phase 0 completion

*This is the single source of truth for all ToolWeaver development tasks.*

---

## 📋 PROGRESS TRACKING LOG

Update this section after completing each task:

### Phase 0: Security Foundations
- [ ] 0.1 Sub-Agent Resource Quotas (2-3h) - Status: NOT STARTED
- [ ] 0.2 Rate Limiter (1-2h) - Status: NOT STARTED
- [ ] 0.3 Auth Structure (30m) - Status: NOT STARTED
- [ ] 0.4 PII Detection (2h) - Status: NOT STARTED
- [ ] 0.5 Secrets Redaction (1h) - Status: NOT STARTED
- [ ] 0.6 Template Sanitization (1h) - Status: NOT STARTED
- [ ] 0.7 Idempotency Keys (1h) - Status: NOT STARTED

**Phase 0 Status:** 0/7 complete (0%)  
**Estimated Time:** 6.5-7.5 hours  
**Actual Time:** TBD  
**Completion Date:** TBD

### Phase 1: Parallel Sub-Agent Dispatch
- [ ] 1.1 Define Dispatch API (1h) - Status: BLOCKED
- [ ] 1.2 Implement Parallel Execution (2-3h) - Status: BLOCKED
- [ ] 1.3 Add Aggregation & Ranking (1-2h) - Status: BLOCKED
- [ ] 1.4 Integration & Testing (2-3h) - Status: BLOCKED

**Phase 1 Status:** 0/4 complete (0%) - BLOCKED BY PHASE 0  
**Estimated Time:** 6-8 hours  
**Actual Time:** TBD  
**Completion Date:** TBD

### Phase 2-4: (To be tracked when unblocked)

### Quick Wins:
- [ ] QW1: Export A2A Classes (1h) - Status: NOT STARTED
- [ ] QW2: Quicksort Example (2h) - Status: NOT STARTED
- [ ] QW3: Parallel Patterns Doc (1h) - Status: NOT STARTED

---

## 🎯 SESSION NOTES

Use this space to track progress during work sessions:

### Session 1 (Date: TBD)
**Goal:** Complete Phase 0.1-0.3  
**Time:** TBD  
**Completed:**
- [ ] Task 1
- [ ] Task 2

**Notes:**
- (Add any issues, blockers, or insights here)

---

### Session 2 (Date: TBD)
**Goal:** Complete Phase 0.4-0.7  
**Time:** TBD  
**Completed:**
- [ ] Task 1

**Notes:**
- (Add notes here)

### Phase 1: Parallel Sub-Agent Dispatch (v0.4) - NEXT
**Timeline:** 1 week  
**Status:** Ready to start  

**Goal:** Enable agents to dispatch 100+ sub-agents in parallel (Claude Opus → 100x Haiku pattern)

#### Implementation Steps (6-8 hours total)

**Step 1.1: Define API** (1 hour)
- [ ] Create `orchestrator/tools/sub_agent.py`
- [ ] Define `SubAgentTask` dataclass
- [ ] Define `SubAgentResult` dataclass  
- [ ] Define `dispatch_agents()` function signature
- [ ] Add docstrings with examples

**Step 1.2: Implement Parallel Execution** (2-3 hours)
- [ ] Implement `dispatch_agents()` with asyncio.gather()
- [ ] Add semaphore for concurrency control (max_parallel)
- [ ] Template filling logic (format strings with arguments)
- [ ] Per-agent timeout handling
- [ ] Per-agent error capture (don't fail all if one fails)

**Step 1.3: Add Aggregation & Ranking** (1-2 hours)
- [ ] Implement result collection
- [ ] Add success rate calculation
- [ ] Raise error if below min_success_rate threshold
- [ ] Add optional aggregation functions:
  - `collect_all()` - Return all results
  - `rank_by_metric()` - Sort by result field
  - `majority_vote()` - Find consensus

**Step 1.4: Integration & Testing** (2-3 hours)
- [ ] Unit tests (mock A2AClient): 10+ test cases
- [ ] Integration test with real sub-agents
- [ ] Add example: `examples/25-parallel-agents/`
  - Quicksort comparison (100 implementations)
  - Unit test ranking (parallel test execution)
- [ ] Documentation: `docs/user-guide/sub_agent_dispatch.md`

#### Acceptance Criteria
- [ ] Dispatch 100+ agents in parallel
- [ ] Execution time <60s for 100 agents
- [ ] Proper timeout handling (no hangs)
- [ ] Success rate tracking accurate
- [ ] Tests >90% code coverage
- [ ] Documentation + 2 examples

---

### Phase 2: Tool Composition (v0.5)
**Timeline:** 1.5 weeks  
**Depends on:** Phase 1  

**Goal:** Chain tools where output of one becomes input to next

#### Implementation Steps (10-12 hours total)

**Step 2.1: Define Composition API** (2 hours)
- [ ] Create `orchestrator/tools/composition.py`
- [ ] Define `CompositionStep` dataclass
- [ ] Define `@composite_tool` decorator
- [ ] Parameter mapping syntax (input → output)

**Step 2.2: Implement Chain Execution** (4 hours)
- [ ] Extend HybridDispatcher for chains
- [ ] Auto-wire outputs to inputs
- [ ] Error propagation logic
- [ ] Intermediate result caching

**Step 2.3: Testing & Examples** (4-6 hours)
- [ ] Unit tests: 15+ test cases
- [ ] Integration test: multi-step workflow
- [ ] Add example: `examples/26-tool-composition/`
  - Fetch → Parse → Extract pipeline
  - Receipt → OCR → Categorize → Notify
- [ ] Documentation: `docs/user-guide/tool_composition.md`

#### Acceptance Criteria
- [ ] Chain 5+ tools seamlessly
- [ ] Execution overhead <100ms
- [ ] Error handling and retry works
- [ ] Auto-wiring is bulletproof
- [ ] Tests >90% code coverage

---

### Phase 3: Cost-Benefit Tool Selection (v0.5.5)
**Timeline:** 1 week  
**Depends on:** Phase 2  

**Goal:** Planners choose tools based on cost/latency constraints

#### Implementation Steps (6-8 hours total)

**Step 3.1: Add Metadata Fields** (2 hours)
- [ ] Extend `ToolDefinition` with:
  - `cost_per_call: float`
  - `expected_latency_ms: int`
  - `capabilities: List[str]`
- [ ] Update @tool decorator to accept metadata
- [ ] Database migration (if needed)

**Step 3.2: Implement Selection Logic** (3 hours)
- [ ] Create `orchestrator/selection/cost_optimizer.py`
- [ ] Implement efficiency scoring algorithm
- [ ] Add `registry.get_best_tool()` method
- [ ] Budget constraint checking

**Step 3.3: Testing & Examples** (2-3 hours)
- [ ] Unit tests: 10+ test cases
- [ ] Add example: `examples/27-cost-optimization/`
- [ ] Documentation: `docs/user-guide/cost_aware_selection.md`

#### Acceptance Criteria
- [ ] Tools ranked by efficiency
- [ ] Planner respects cost constraints
- [ ] Cost predictions within 10%
- [ ] Tests >90% code coverage

---

### Phase 4: Error Recovery at Scale (v0.6)
**Timeline:** 1 week  
**Depends on:** Phase 3  

**Goal:** Graceful degradation when partial failures occur

#### Implementation Steps (6-8 hours total)

**Step 4.1: Define Policy Model** (2 hours)
- [ ] Create `orchestrator/resilience/policies.py`
- [ ] Define `ErrorRecoveryPolicy` dataclass
- [ ] Policy types: retry, fallback, partial_success

**Step 4.2: Implement Recovery** (3-4 hours)
- [ ] Integrate with dispatch_agents()
- [ ] Retry with exponential backoff
- [ ] Fallback tool selection
- [ ] Partial result handling

**Step 4.3: Testing & Examples** (2-3 hours)
- [ ] Unit tests: 12+ test cases
- [ ] Add example: `examples/28-resilient-dispatch/`
- [ ] Documentation: `docs/user-guide/error_recovery.md`

#### Acceptance Criteria
- [ ] Retry logic with exponential backoff
- [ ] Min success rate enforced
- [ ] Partial results handled gracefully
- [ ] Tests >90% code coverage
- [ ] v0.6 release ready

---

## ✅ QUICK WINS (Can Do Anytime)

These provide immediate value without waiting for full phases:

### QW1: Export A2A Classes to Public API (1 hour)
- [ ] Add to `orchestrator/__init__.py`:
  - `AgentDelegationRequest`
  - `AgentDelegationResponse`
  - `A2AClient`
- [ ] Update `__all__` list
- [ ] Add to documentation

### QW2: Multi-Agent Quicksort Example (2 hours)
- [ ] Create `examples/quicksort-orchestration/`
- [ ] Show how to use existing A2AClient for parallel patterns
- [ ] Demonstrate cost calculation
- [ ] Document performance results

### QW3: Parallel Patterns Documentation (1 hour)
- [ ] Create `docs/user-guide/parallel-agents.md`
- [ ] Document A2AClient usage patterns
- [ ] Cost calculation examples
- [ ] Error handling best practices

---

## 🔧 TECHNICAL DEBT & IMPROVEMENTS

### Low Priority (Backlog)

**Type Safety** (already at mypy=0, but can enhance):
- [ ] Complete remaining type hints in optional modules
- [ ] Add type hints to tests

**Logging** (framework exists, expand usage):
- [ ] Add structured logging to more execution paths
- [ ] Standardize log levels across modules

**Documentation**:
- [ ] Update ANTHROPIC_MCP_COMPARISON.md with current capabilities
- [ ] Update RELEASES.md with v0.2.0+ releases
- [ ] Create 2-3 advanced workflow examples
- [ ] Create 1 getting-started video
- [ ] Expand troubleshooting guide

**Performance** (future optimization):
- [ ] Benchmark streaming chunk sizes
- [ ] Cost analytics improvements
- [ ] Caching layer optimization

---

## ⏭️ DEFERRED (Post-Launch)

**Phase 5b: Monitoring Plugins** (community-driven)
- W&B integration adapter
- Prometheus metrics exporter
- Grafana dashboard template

**Infrastructure**:
- Version check on startup (informational only)
- Additional platform-specific documentation

---

## 📈 SUCCESS METRICS

### Code Quality
- ✅ mypy = 0 errors
- ✅ 95%+ test pass rate (699/735)
- 🎯 >90% code coverage per phase
- 🎯 No regressions in test suite

### Feature Delivery
- 🎯 Phase 1: 1 week
- 🎯 Phase 2: 1.5 weeks
- 🎯 Phase 3: 1 week
- 🎯 Phase 4: 1 week
- **Total: ~4.5 weeks** (original estimate: 12 weeks, 62% reduction)

### User Impact
- 🎯 Enable 100+ parallel agent dispatch
- 🎯 Tool composition with <100ms overhead
- 🎯 Cost predictions within 10% accuracy
- 🎯 95%+ success rate with error recovery

---

## 📚 REFERENCE DOCUMENTS

### Primary Planning
- **NEXT_STEPS_SUMMARY.md** - This document (consolidated view)
- **AGENT_ORCHESTRATION_ROADMAP.md** - Detailed 4-phase plan (973 lines)
- **INTEGRATION_ASSESSMENT.md** - What exists vs. gaps (510 lines)
- **TOMORROW_PLAN.md** - CI stabilization status

### Reference & History
- **A2A_INTEGRATION_PLAN.md** - Phase 2 A2A completion (🟢 COMPLETE)
- **NOT_YET_COMPLETED.md** - Phase 0-5a status tracking
- **CODE_EXECUTION_IMPLEMENTATION_PLAN.md** - Phase 0-1 reference

### Strategic
- **BUSINESS_STRATEGY.md** - Business model, licensing
- **AGENT_UX_AND_MARKET_POSITIONING.md** - Market positioning
- **ANTHROPIC_MCP_COMPARISON.md** - Gap analysis (⚠️ needs update)

---

## 🎯 DECISION SUMMARY

### Technical Decisions Made
1. ✅ Build on A2AClient, don't replace
2. ✅ Reuse Workflow DAGs for composition
3. ✅ Metadata-driven tool selection
4. ✅ Policy-based error recovery
5. ✅ Keep public API minimal

### Effort Revised
- Original estimate: 12 weeks
- Revised estimate: 4.5 weeks (62% reduction)
- Reason: Extensive reuse of existing infrastructure

### Prioritization
1. **Phase 1** (Sub-Agent Dispatch) - Highest user impact
2. **Phase 2** (Tool Composition) - Core workflow enhancement
3. **Phase 3** (Cost Selection) - Optimization layer
4. **Phase 4** (Error Recovery) - Production hardening

---

## 🚀 READY TO START

**Next Action:** Begin Phase 1 implementation
- Codebase is stable (mypy=0, 95%+ tests)
- Infrastructure is production-ready
- Roadmap is detailed and realistic
- Team approval obtained

**Estimated Timeline:**
- Week 1: Phase 1 (Sub-Agent Dispatch)
- Week 2-3: Phase 2 (Tool Composition)
- Week 4: Phase 3 (Cost Selection)
- Week 5: Phase 4 (Error Recovery)

**Status: APPROVED FOR IMPLEMENTATION** ✅

---

*This document consolidates all TODOs from: NEXT_STEPS_SUMMARY.md, TOMORROW_PLAN.md, NOT_YET_COMPLETED.md, README.md, and AGENT_ORCHESTRATION_ROADMAP.md*
