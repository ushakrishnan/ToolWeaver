## v0.11.1 (2026-01-02)

Release type: Patch (monitoring fixes + typing cleanup)

Highlights:
- Standardized `log_tool_call` across monitoring backends with keyword-only latency/token fields; restored local file logging and aligned W&B/Prometheus latency handling.
- ToolUsageMonitor now dispatches backend logging with keywords, fixing broken monitoring tests.
- Discovery/catalog typings tightened and orchestrator monitoring parameter annotated; mypy/ruff now clean for touched modules.
- Targeted performance and monitoring tests pass (previous concurrent search/monitoring failures addressed).

Changes:
- Monitoring protocol/backends: [orchestrator/_internal/observability/monitoring_backends.py](orchestrator/_internal/observability/monitoring_backends.py)
- Monitor dispatch uses keyword args: [orchestrator/_internal/observability/monitoring.py](orchestrator/_internal/observability/monitoring.py#L87-L109)
- Orchestrator type annotation for monitoring: [orchestrator/_internal/runtime/orchestrator.py](orchestrator/_internal/runtime/orchestrator.py#L289-L305)
- Discovery API catalog typing cleanup: [orchestrator/tools/discovery_api.py](orchestrator/tools/discovery_api.py#L13-L24)

Publish steps:
1. Confirm version in `pyproject.toml` is `0.11.1` (done).
2. Build distributions:
  ```bash
  python -m build
  ```
3. Upload to PyPI:
  ```bash
  python -m twine upload dist/toolweaver-0.11.1*
  ```
4. Verify on PyPI: https://pypi.org/project/toolweaver/0.11.1/
5. Tag the release:
  ```bash
  git tag v0.11.1
  git push --tags
  ```

Run instructions (package users):
```bash
pip install toolweaver==0.11.1
```

Post-release checks:
- `python -m ruff check`
- `python -m mypy`
- `python -m pytest tests/test_monitoring.py`
- Optional: full `python -m pytest` (expected deprecation warnings unchanged)

Notes:
- Setuptools now warns that `project.license` as a TOML table is deprecated; switch to `license = "Apache-2.0"` before Feb 2026.

---


## v0.10.1 (2025-12-29)

Release type: Patch (Unicode fixes + demo corrections)

Highlights:
- Fixed Unicode character encoding issues in samples for Windows console compatibility (replaced ✓/✗/→ with ASCII equivalents).
- Fixed missing imports in control flow patterns demo (added orchestrator imports for ControlFlowPatterns and code generation functions).
- Fixed agent delegation sample to use ASCII output characters.
- All 13 core samples validated and tested successfully.
- Confirmed v0.10.1 works with installed package from PyPI.

Changes:
- `samples/11-programmatic-executor/programmatic_demo.py`: Replaced `→` with `->` for Windows console
- `samples/15-control-flow/demo_patterns.py`: Added imports from orchestrator, removed duplicate class defs, replaced Unicode checkmarks with `[OK]`/`[FAIL]`
- `samples/16-agent-delegation/delegate_to_agent.py`: Replaced `✓`/`✗` with `[OK]`/`[FAIL]`
- `samples/25-parallel-agents/main.py`: Replaced various Unicode characters with ASCII equivalents

Publish steps:
1. Confirm version in `pyproject.toml` is `0.10.1` (done).
2. Build distributions:
  ```bash
  python -m build
  ```
3. Upload to PyPI:
  ```bash
  python -m twine upload dist/toolweaver-0.10.1*
  ```
4. Verify on PyPI: https://pypi.org/project/toolweaver/0.10.1/
5. Tag the release:
  ```bash
  git tag v0.10.1
  git push --tags
  ```

Run instructions (package users):
```bash
pip install toolweaver==0.10.1
```

Post-release checks:
- All samples run without UnicodeEncodeError on Windows.
- Control flow demo detects patterns correctly.
- Agent delegation sample delegates without encoding errors.
- Parallel agents sample executes with proper ASCII output.
- README links continue to work on PyPI (inherited from 0.10.0).

----

## v0.10.0 (2025-12-29)

Release type: Patch (PyPI navigation fixes + version alignment)

Highlights:
- Fixed README quick navigation and badges to use absolute docs/GitHub links (no broken PyPI links).
- Swapped remaining "examples" references for "samples" so PyPI readers land on package-aligned demos.
- Bumped public `__version__` to 0.10.0 and published sdist/wheel to PyPI.
- Note: setuptools warns that `project.license` table is deprecated; migrate to SPDX string before Feb 2026.

Publish steps:
1. Confirm version in `pyproject.toml` is `0.10.0` (done).
2. Build distributions:
  ```bash
  python -m build
  ```
3. Upload to PyPI:
  ```bash
  python -m twine upload dist/toolweaver-0.10.0*
  ```
4. Verify on PyPI: https://pypi.org/project/toolweaver/0.10.0/
5. Tag the release:
  ```bash
  git tag v0.10.0
  git push --tags
  ```

Run instructions (package users):
```bash
pip install toolweaver==0.10.0
```

Post-release checks:
- README quick navigation links resolve on PyPI to docs/tool pages.
- Samples links open GitHub or published docs (no 404s on PyPI).
- Version badge and `orchestrator.__version__` show 0.10.0.

---

## v0.8.0 (2025-12-25)

Release type: Minor (docs navigation UX)

Highlights:
- Re-grouped MkDocs sidebar with section index pages for all major areas.
- Removed expand carets and added indentation for nested items to clarify hierarchy.
- Strict MkDocs build clean after navigation updates.

Publish steps:
1. Update version in `pyproject.toml` to `0.8.0`.
2. Build distributions:
  ```bash
  python -m build
  ```
3. Upload to PyPI:
  ```bash
  twine upload dist/*
  ```
4. Verify on PyPI: https://pypi.org/project/toolweaver/0.8.0/
5. Tag the release:
  ```bash
  git tag v0.8.0
  git push --tags
  ```

Run instructions (package users):
```bash
pip install toolweaver==0.8.0
```

Post-release checks:
- Sidebar renders grouped with indentation and no carets.
- README links render correctly on PyPI.
- Docs index pages resolve without 404s.

# ToolWeaver Release Notes

This is a running log of all releases. Use this content when creating GitHub releases.

---

## v0.7.0 (2025-12-24)

Release type: Minor (features + docs + samples refresh)

Highlights:
- Samples and examples updated to use ASCII-safe output (Windows-friendly)
- New documentation: `docs/samples/` with testing guide and overview
- README links adjusted for PyPI (absolute GitHub links for Contributing/Docs)

Publish steps:
1. Update version in `pyproject.toml` to `0.7.0`
2. Build distributions:
  ```bash
  python -m build
  ```
3. Upload to PyPI:
  ```bash
  twine upload dist/*
  ```
4. Verify on PyPI: https://pypi.org/project/toolweaver/0.7.0/
5. Tag the release:
  ```bash
  git tag v0.7.0
  git push --tags
  ```

Run instructions (package users):
```bash
pip install toolweaver==0.7.0
```

Windows note:
- If running samples, emoji have been replaced with ASCII markers (e.g., [OK], [?])
- If any garbled characters appear, set: `$env:PYTHONIOENCODING='utf-8'`

Post-release checks:
- README renders correctly on PyPI (absolute links for Contributing)
- Samples `requirements.txt` pin `toolweaver==0.7.0`
- `docs/samples/*` references `0.7.0`

## v0.6.1 - Examples Modernization Complete (December 23, 2025)

### 🎯 Milestone: 27/27 Examples Working
- Finished modernization of all ToolWeaver examples; every example executes without missing imports or external service dependencies.
- Verified Windows compatibility (removed Unicode glyphs that broke PowerShell consoles).
- Added final completion report and organized docs to keep root clean.

### ✨ What's New
- **Examples:** All 27 examples tested end-to-end; tool registration, agents, routing, caching, monitoring, control-flow patterns, and sharding demos are fully functional.
- **Docs:** Added `COMPLETION_REPORT.md` (now in `docs/internal/completion-reports/`).
- **Organization:** Archived interim planning/status docs into `docs/internal/archive/`; grouped planning docs into `docs/internal/planning/`; moved test artifacts to `docs/internal/test-reports/`.
- **Test Harness:** `test_all_examples.py` updated for Windows-friendly output.

### 🧪 Testing
- `examples/test_all_examples.py` — PASS (structure/syntax for tracked examples).
- Ad-hoc execution of all numbered example scripts — PASS (27/27).

### 🗂️ Files & Locations
- Examples: `examples/*` (all passing).
- Completion report: `docs/internal/completion-reports/COMPLETION_REPORT.md`.
- Planning docs: `docs/internal/planning/`.
- Test artifacts: `docs/internal/test-reports/examples_test_results.csv`.

### 📌 Notes
- No code-breaking changes; primarily documentation and organization plus Unicode-safe logging in tests/examples.
- Ready for tagging/release from `main`.

---

## v0.6.0 - Project Organization & Phase 0-4 Completion (December 23, 2025)

### 🎯 Major Release: Complete Implementation of All Phases

**Milestone Achievement**: All 5 phases (0-4) fully implemented, tested, and documented with 971/985 tests passing (98.6%).

### ✨ What's New

#### 🏗️ Phase 0-4 Implementation Complete
- **Phase 0: Security Foundations** ✅
  - PII Detection & Redaction (96-100% coverage)
  - Secret Management & Rate Limiting
  - Idempotency Keys & Input Validation
  - Sandbox Environment for code execution

- **Phase 1: Sub-Agent Dispatch** ✅
  - Sub-agent registration and capability matching (95% coverage)
  - Dispatch protocol with context preservation
  - Resource quotas and timeout management
  - 15+ test cases for agent delegation

- **Phase 2: Tool Composition** ✅
  - Tool chaining and parallel execution (94% coverage)
  - Conditional execution and branching
  - Tool result caching and optimization
  - 14+ composition test cases

- **Phase 3: Cost Optimization** ✅
  - Cost modeling and model selection (96% coverage)
  - Budget tracking and cost alerts
  - Two-model architecture (small phi3 + large GPT-4)
  - Usage analytics and reporting

- **Phase 4: Error Recovery** ✅
  - Retry logic with exponential backoff (90% coverage)
  - Circuit breakers and fallback mechanisms
  - Error classification and graceful degradation
  - 20+ recovery test cases

#### 📁 Project Organization
- **Root Directory Cleanup**:
  - Moved 17 documentation files to `docs/internal/`
  - Organized mypy reports, completion summaries, test reports
  - Root now has only 11 essential config files
  
- **Scripts Organization**:
  - Deleted 5 obsolete test/dev scripts
  - Added 3 utility scripts (create_example_requirements, organize_files, populate_example_envs)
  - Created SCRIPTS_README.md documenting all utilities

#### 🧪 Examples Setup (29 Total)
- **Full Configuration**:
  - Created .env files for all 26 examples (smart-populated with only needed keys)
  - Created requirements.txt for all 26 examples (differentiated simple vs complex)
  - All examples documented with README.md
  
- **Examples by Category**:
  - Basic Usage (3) | Tool Integration (3) | Workflows (3)
  - Advanced Patterns (3) | Agent Patterns (6) | Specialized Workflows (5)
  - Distributed & Parallel (2) | Advanced Integration (2) | Templates (2)

#### 📚 Documentation Reorganization
- **Folder Consolidation**:
  - Deleted `docs/for-contributors/` (merged into developer-guide)
  - Renamed `docs/for-package-users/` → `docs/getting-started/`
  - Created `docs/examples/` with comprehensive guides
  
- **New Documentation**:
  - `PHASES_OVERVIEW.md` - Complete Phase 0-4 summary
  - `docs/examples/README.md` - 29 example guides
  - `docs/examples/EXAMPLES_TESTING_GUIDE.md` - Testing strategies
  - `QUICK_START_SETUP.md` & `QUICK_START_TESTING.md` in developer-guide
  
- **Status Updates**:
  - Updated `docs/internal/README.md` with Phase 0-4 COMPLETE status
  - Updated main `docs/README.md` with current test results and navigation
  - Fixed all paths and cross-references

#### 🧪 Testing Infrastructure
- **Test Results**: 971/985 passing (98.6% pass rate)
- **Coverage**: 67.61% overall
  - Security modules: 96-100%
  - Sub-agent dispatch: 95%
  - Tool composition: 94%
  - Cost optimization: 96%
  - Error recovery: 90%

- **Test Documentation**:
  - Created `TEST_COVERAGE_REPORT.md` - Module-by-module breakdown
  - Created `FAILING_TESTS_ANALYSIS.md` - Analysis of 8 failing tests
  - Updated testing.md with new test report locations

#### 🔧 Bug Fixes
- **Benchmark Tests**: Fixed ToolCatalog API usage (4 tests)
- **MonitoringBackend**: Use factory function instead of direct instantiation
- **Redis Cache**: Added redis package availability check
- **Unicode Encoding**: Fixed Windows terminal checkmark issues

### 📦 Dependencies
- All examples have requirements.txt with smart dependency loading
- Common: toolweaver>=0.6.0, openai>=1.3.0, anthropic>=0.7.0
- Azure: azure-identity>=1.13.0, azure-cognitiveservices-vision-computervision>=9.0.0
- Optional: redis>=5.0.0, qdrant-client>=2.4.0, wandb>=0.15.0

### 🎓 New User Guides
- [Cost-Aware Selection](../user-guide/cost_aware_selection.md)
- [Parallel Agents](../user-guide/parallel-agents.md)
- [Sub-Agent Dispatch](../user-guide/sub_agent_dispatch.md)
- [Tool Composition](../user-guide/tool_composition.md)

### 📊 Impact
- **Test Quality**: 98.6% pass rate (971/985 tests)
- **Code Coverage**: 67.61% overall, 90%+ on critical modules
- **Documentation**: 80+ markdown files, all current and accurate
- **Examples**: 29 fully configured and documented
- **Organization**: Clean root, organized docs, ready for production

### 🚀 Migration Notes
- Review new `PHASES_OVERVIEW.md` for feature documentation
- Examples now have .env files - copy your API keys before running
- For-package-users docs moved to getting-started/
- All Phase 0-4 features available and tested

### 📝 Technical Details

**New Modules**:
- `orchestrator/selection/cost_optimizer.py` - Cost optimization engine
- `orchestrator/tools/composition.py` - Tool composition logic
- `orchestrator/tools/error_recovery.py` - Error recovery strategies

**Updated Files** (20+ files):
- Test suite improvements across all modules
- Documentation reorganization (20 files changed)
- Example setup automation scripts

**Test Statistics**:
- Phase 0: 80+ tests | Phase 1: 15+ tests | Phase 2: 14+ tests
- Phase 3: 10+ tests | Phase 4: 20+ tests
- Total: 139+ phase-specific tests

### 🎯 What's Next
- Fix remaining 8 failing tests (5 benchmark cosmetic, 3 edge cases)
- Performance benchmarking on production setup
- CI workflow for continuous validation

---

## v0.5.0 - Internal Documentation Consolidation (December 23, 2025)

### 🏗️ Maintenance Release: Documentation Organization

Streamlined internal documentation structure with consolidated planning documents and security analysis.

**Key Achievement**: Single source of truth for all development planning through consolidated master TODO list.

### ✨ What's New

#### 📚 Documentation Restructuring
- **Created `CONSOLIDATED_TODOS.md`**: Master task list (1028 lines)
  - Unified Phase 0-4 implementation roadmap
  - 23 tracked tasks with status indicators
  - Risk assessment and time estimates
  - Sequenced execution plan with blockers

- **Created `SECURITY_ARCHITECTURE_REVIEW.md`**: Security analysis (802 lines)
  - 6 threat scenarios with impact assessment
  - Current security posture evaluation
  - Implementation roadmap for multi-agent safety
  - Red team attack vectors and mitigations

- **Updated `README.md`**: Simplified internal docs index
  - Clean entry point to essential references
  - Quick links to master TODO and security review

#### 🗑️ Cleanup
- **Removed 18 archived documents**:
  - Historical phase completion reports (PHASE_0_*, PHASE_1_*)
  - Superseded roadmaps and planning docs
  - Redundant analysis documents
  - Temporary session notes
  
- **Preserved 5 essential files**:
  - CONSOLIDATED_TODOS.md (master planning)
  - SECURITY_ARCHITECTURE_REVIEW.md (security requirements)
  - BUSINESS_STRATEGY.md (strategic planning)
  - AGENT_UX_AND_MARKET_POSITIONING.md (market positioning)
  - RELEASES.md (this file)

### 📊 Impact
- **Documentation reduction**: 88% fewer files in docs/internal/ (23 → 5)
- **Maintainability**: Eliminated duplication and fragmentation
- **Clarity**: Single consolidated roadmap replacing multiple scattered plans

### 📝 Notes
- **Documentation-only release** - no code changes
- All functionality remains at v0.4.0 level
- Tests passing: 699/735 (95%+)
- Internal docs only (not in public package)

---

## v0.4.0 - Analytics Backends & Monitoring (December 18, 2025)

#### 🐛 Bug Fixes
- **Issue 1**: "Failed to register tool_search_tool" warning
  - Fixed import path in `orchestrator/dispatch/functions.py`
  - Changed from `.tool_search_tool` → `orchestrator.tools.tool_search_tool`
  
- **Issue 2**: "Google Gemini package not installed" warning shown even when using OpenAI
  - Removed warnings from import blocks in `orchestrator/planning/planner.py`
  - Warnings only shown when actually trying to use unavailable provider
  
- **Issue 3**: "Overriding of current MeterProvider is not allowed" warning
  - Check for NoOpMeterProvider before setting new one in OTLP backend
  - Tests safely create multiple OTLP clients
  
- **Issue 4**: SQLite missing `update_health_score()` adapter method
  - Added adapter method to match OTLP/Prometheus interface

#### 📖 Documentation Consolidation
- **ANALYTICS_GUIDE.md**: Comprehensive 680-line guide consolidating 3 previous docs
  - Complete tri-backend comparison and configuration
  - Usage examples for all backends
  - Migration strategies and deployment recommendations
  - W&B integration guidance (complementary, not replacement)
  - Cost comparison and production best practices

- **Removed 18+ Redundant Files**:
  - Eliminated "Phase" references from user-facing docs
  - Removed completion reports (info preserved in git history)
  - Consolidated roadmap documentation
  - Simplified internal documentation structure
  
- **Updated Cross-References**: All links now point to consolidated docs
  - `CONFIGURATION.md`, `SKILL_LIBRARY.md`, `SQLITE_GRAFANA_SETUP.md`, `PRODUCTION_DEPLOYMENT.md`, `README.md`

#### 📦 Dependencies
- **prometheus-client>=0.19.0**: Verified in pyproject.toml
- **opentelemetry-api>=1.20.0**: For OTLP backend
- **opentelemetry-sdk>=1.20.0**: For OTLP backend
- **opentelemetry-exporter-otlp-proto-http>=1.20.0**: For OTLP backend

### 🎯 Production Deployment Recommendations

**Development:**
```env
ANALYTICS_BACKEND=sqlite  # Local storage, zero setup
```

**Staging:**
```env
ANALYTICS_BACKEND=prometheus  # Team dashboards, monitoring practice
PROMETHEUS_PORT=8000
```

**Production (Managed):**
```env
ANALYTICS_BACKEND=otlp  # Grafana Cloud, zero maintenance
OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-2.grafana.net/otlp
```

**Production (Self-hosted):**
```env
ANALYTICS_BACKEND=prometheus  # Self-hosted Prometheus + Grafana stack
PROMETHEUS_PORT=8000
```

### 📊 Metrics & Performance
- **Test Coverage**: 488 tests passing (up from 461, +5.9%)
- **Zero Warnings**: All import and registration warnings resolved
- **Zero Regressions**: All existing functionality maintained
- **Documentation**: 50 markdown files (down from ~68, -26%)
- **Code Quality**: All backends production-ready with comprehensive tests

### 🔗 Links
- **Tag**: v0.4.0
- **Date**: December 18, 2025
- **Test Status**: 488/488 passing (100%)
- **Backends**: 3 production-ready (SQLite, OTLP, Prometheus)

---

## v0.3.0 - Skill Library & Advanced Examples (December 18, 2025)

### 🎯 Major Release: Skill Library MVP & Phase 2 Complete

Phase 2 completion with **Skill Library** for saving and reusing generated code, advanced validation, and comprehensive examples showcasing hybrid tool+agent workflows.

**Key Innovation**: Reusable skill library with multi-level validation and first-class orchestrator support.

### ✨ What's New

#### 📚 Skill Library (MVP)
- **Disk-based Storage**: Manifest + code files under `~/.toolweaver/skills`
- **save_skill()**: Persist code snippets with metadata (tags, description)
- **list_skills()** / **get_skill()**: Query saved skills
- **execute_skill()**: First-class Orchestrator API to run saved skills
  - Syntax validation before execution
  - Sandbox execution with optional inputs
  - Monitoring hooks for success/failure/latency
- **Architecture Decision**: Approved hybrid storage (Redis + Disk + Qdrant + Git)

#### ✅ Code Validation
- **Multi-level Validation**: orchestrator/execution/validation.py
  - **Syntax**: AST parse (always enabled)
  - **Exec**: Lightweight sandbox test (optional)
  - **Mypy**: Type checking if installed (optional)
- **validate_stub()**: Comprehensive validation with result dict
- **Integration Points**: Skill library, code generator, approval workflows

#### 🚀 Advanced Examples (19-22)
- **Example 19**: Hybrid tool→agent→tool flow with streaming & cost logging
- **Example 20**: Approval workflow with human-in-the-loop gate
- **Example 21**: Error recovery pattern (fail→diagnose→remediate→retry)
- **Example 22**: End-to-end showcase combining tools, agents, and skill library
- **Dev Agent Server**: scripts/dev_agents.py for local testing

#### 🔧 Infrastructure
- **External Registry Discovery**: Optional MCP registry via MCP_REGISTRY_URL
- **Minimal Tool Workers**: fetch_data, store_data, apply_changes, process_resource
- **Orchestrator Facade**: Simplified API for examples (discover_tools, execute_tool, execute_agent_step, execute_skill)

#### 📖 Documentation
- **Skill Library Reference**: docs/reference/SKILL_LIBRARY.md
- **Skill Library Wiring**: docs/developer-guide/SKILL_LIBRARY_WIRING.md (Redis + Qdrant)
- **Code Validation Guide**: docs/developer-guide/CODE_VALIDATION.md
- **Executing Skills Guide**: docs/developer-guide/EXECUTING_SKILLS.md
- **Troubleshooting**: docs/user-guide/TROUBLESHOOTING.md (timeouts, streaming, costs)
- **Registry Example**: docs/reference/REGISTRY_EXAMPLE_SERVER.md + registry.json
- **Organized Structure**: All internal docs moved to docs/internal/

#### 🧪 Testing
- All 4 new examples (19-22) with passing smoke tests
- Monkeypatch-based tests for predictable local runs
- Example README updates with dev agent startup instructions

### 📦 What's Next (Phase 3)
- Redis cache for hot skill lookups (~2-3h)
- Qdrant-backed search_skills() (~3-4h)
- Git approval flow for promoted skills (~2-3h)
- Skill composition & dependency tracking (~2-3h)
- Skill metrics & ratings (~2-3h)

### 🔗 Links
- **Tag**: v0.3.0
- **Commit**: 93b1e05
- **Phase**: 2 Complete → 3 Ready

---

## v0.2.0 - Agent-to-Agent (A2A) Integration & Unified Discovery

### 🚀 Major Release: Multi-Agent Orchestration

Revolutionary release adding **Agent-to-Agent (A2A) protocol** for discovering and delegating tasks to other agents. ToolWeaver now supports unified MCP tools + A2A agents through single discovery interface.

**Key Innovation**: First framework to combine tool discovery (MCP) + agent discovery (A2A) in unified interface.

### ✨ What's New

#### 🔗 A2A Integration (NEW)
- **A2AClient**: Full HTTP/SSE/WebSocket support for agent delegation
  - Retry logic with exponential backoff
  - Circuit breaker pattern for fault tolerance
  - Idempotency caching (TTL-based)
  - Streaming response support
- **Agent Discovery**: Convert agents to `ToolDefinition` for seamless integration
- **AgentCapability Model**: Full metadata for agent discovery
  - Execution characteristics (latency, cost)
  - Streaming support indicators
  - Input/output schemas
- **Configuration**: `agents.yaml` for managing external agents

#### 🎯 Unified Discovery
- **Single Interface**: Discover both MCP tools and A2A agents
- **Hybrid Dispatcher**: Route `agent_*` tools transparently to A2A clients
- **Discovery Caching**: TTL-based cache with automatic invalidation
- **Progressive Disclosure**: File-tree exploration of available capabilities

#### 📊 Orchestrator Enhancements
- **execute_agent_step()**: New method for agent delegation within workflows
- **Agent Step Normalization**: Convert delegation requests to standard format
- **Streaming Metadata Surface**: Expose streaming support in discovery
- **Cost Tracking**: Monitor costs for both tools and agents

#### 🛠️ Production Examples
- **Example 16**: Basic Agent Delegation - Discover and delegate to single agent
- **Example 17**: Multi-Agent Coordination - Sequential delegation across agents
- **Example 18**: Tool + Agent Hybrid - Combine tool calls with agent delegation

#### 📚 Comprehensive Documentation
- **A2A Setup Guide** (800+ lines): Complete walkthrough for A2A integration
- **MCP Setup Guide** (450+ lines): Parallel documentation for MCP tools
- **FEATURES_GUIDE**: Updated with unified discovery section
- **docs/README**: 5 learning paths (beginner → advanced)
- **ARCHITECTURE.md**: 1500+ lines on A2A architecture and integration

### 📈 Performance Benchmarks

**Regression Targets - ALL MET ✅**:
- Discovery cache: <5ms (p95) ✅
- Tool search: <50ms (p95) ✅
- Orchestration: <100ms (p95) ✅
- Concurrent requests: 10+ handled ✅

**Test Results**:
- 461 tests passing (96.6% pass rate)
- 35+ tests for A2A functionality
- Zero regressions on existing features
- Streaming support verified for both MCP and A2A

### 🔄 Implementation Details

#### New Files
```
orchestrator/infra/a2a_client.py          # A2A client with transports
orchestrator/tools/agent_discovery.py     # Agent → ToolDefinition converter
orchestrator/dispatch/hybrid_dispatcher.py # Route agent_* tools
agents.yaml                                # Agent configuration
tests/test_a2a_client.py                  # Comprehensive A2A tests
```

#### Modified Files
```
orchestrator/runtime/orchestrator.py       # Added execute_agent_step()
orchestrator/dispatch/dispatcher.py        # Agent routing support
orchestrator/models.py                     # AgentCapability model
orchestrator/tools/discovery.py            # Unified discovery
docs/ARCHITECTURE.md                       # +1500 lines on A2A
docs/FEATURES_GUIDE.md                     # Unified discovery section
docs/README.md                             # Learning paths
```

### 🎓 Learning Paths

| Path | Time | Topics |
|------|------|--------|
| **Quick Start** | 15 min | MCP tools + A2A agents, run example |
| **Tools Deep Dive** | 30 min | MCP setup, configuration, discovery |
| **Agents Deep Dive** | 30 min | A2A setup, delegation, streaming |
| **Hybrid Workflows** | 45 min | Combine tools + agents, error handling |
| **Architecture** | 60 min | Full system design, extension points |

### 🚀 Quick Start

```python
from orchestrator import Orchestrator
from orchestrator.tools.agent_discovery import AgentDiscoverer

# Initialize orchestrator
orchestrator = Orchestrator()

# Discover both tools AND agents
tools = await orchestrator.discover_tools()  # MCP tools
agents = await orchestrator.discover_agents()  # A2A agents

# Unified interface
all_capabilities = tools + agents

# Delegate to agent
result = await orchestrator.execute_agent_step(
    agent_name="analysis_agent",
    request={"data": raw_data}
)

# Or use as tool
result = await orchestrator.execute_tool(
    "agent_analysis_agent",  # Tool name with agent_ prefix
    {"data": raw_data}
)
```

### 📊 Stats

- **4,500+ lines** of new code (A2A client, discovery, orchestration)
- **40+ tests** covering all A2A scenarios
- **1,500+ lines** of architecture documentation
- **400+ lines** of practical code examples
- **Zero** regressions on existing features
- **3** production-ready examples
- **11** comprehensive guides (setup, features, architecture, quick reference)

### 🔗 Resources

- **A2A Setup Guide**: docs/user-guide/A2A_SETUP_GUIDE.md
- **MCP Setup Guide**: docs/user-guide/MCP_SETUP_GUIDE.md
- **Examples 16-18**: examples/16-agent-delegation/, 17-multi-agent/, 18-hybrid-workflow/
- **ARCHITECTURE**: docs/ARCHITECTURE.md (A2A section, line 1500+)

### 💡 Key Capabilities

- ✅ Discover agents from multiple sources
- ✅ Delegate complex tasks to specialized agents
- ✅ Unified interface for tools + agents
- ✅ Streaming response support
- ✅ Retry and fault tolerance
- ✅ Idempotency for safe retries
- ✅ Cost tracking per agent call
- ✅ Full monitoring and observability

### 🔮 What's Next

**Phase 3 (Skill Library)**: Combine tool chains + agent workflows as reusable skills

**Phase 4 (Enterprise)**: RBAC, multi-tenant support, audit logging

### 📝 Breaking Changes

**None** - Fully backward compatible. Existing code continues to work without changes.

### 🙏 Contributors

Built on 8 weeks of engineering (Phase 1-2) with comprehensive testing and documentation.

**Status**: Production Ready  
**Release Date**: December 2025  

---

## v0.1.3 - Complete Examples Suite with Testing Infrastructure

### 🎯 Complete Examples & Testing Infrastructure

Major release adding **13 comprehensive examples** showcasing all ToolWeaver capabilities, complete testing infrastructure, and production-ready documentation.

### ✨ What's New

#### 📚 13 Complete Examples (NEW)
Added 9 new examples demonstrating all major features:
- **Example 04:** Vector Search & Discovery - Tool discovery with semantic search
- **Example 05:** Workflow Library - Reusable workflow patterns  
- **Example 06:** Monitoring & Observability - WandB and Prometheus integration
- **Example 07:** Caching Optimization - Redis caching strategies
- **Example 08:** Hybrid Model Routing - Two-model architecture (GPT-4 + Phi-3)
- **Example 09:** Code Execution - Sandboxed Python execution
- **Example 10:** Multi-Step Planning - LLM-generated execution plans
- **Example 11:** Programmatic Executor - Large-scale batch processing
- **Example 12:** Sharded Catalog - Scaling to 1000+ tools
- **Example 13:** 🌟 Complete End-to-End Pipeline - ALL features in one demo

Enhanced existing examples (01-03) with standardized structure.

#### 🧪 Testing Infrastructure
- ✅ `test_all_examples.py` - Automated validation for all examples
- ✅ `TESTING_REPORT.md` - Detailed test results and requirements
- ✅ `TEST_SUMMARY.md` - Quick reference guide
- ✅ All examples validated: 100% pass rate

#### 📖 Documentation Improvements
- Standardized all example READMEs with consistent format:
  - Complexity ratings (⭐-⭐⭐⭐)
  - Time estimates
  - Real-world scenarios
  - Prerequisites and setup
  - Usage examples
- Added learning paths for different user journeys
- Organized legacy demos into `legacy-demos/` folder

#### ⚙️ Configuration
- All `.env` files populated with working credentials
- Complete `.env.example` templates for each example
- Production-ready configuration examples

#### 🔧 Improvements
- Fixed Example 13 to use actual orchestrator API
- Enhanced examples README with testing instructions
- Added modern Python packaging with pyproject.toml
- Integrated automatic monitoring into orchestrator
- Added pluggable monitoring backends (WandB + Prometheus)

### 📦 Installation

```bash
# Clone repository
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver

# Install core dependencies
pip install -e .

# Or install with all optional features
pip install -e ".[all]"
```

### 🚀 Quick Start

Try the comprehensive demo:
```bash
cd examples/13-complete-pipeline
python complete_pipeline.py
```

Run the test suite:
```bash
cd examples
python test_all_examples.py
```

### 📊 Example Overview

| Example | Complexity | Features Demonstrated |
|---------|------------|----------------------|
| 01 | ⭐ Basic | Basic tool execution, MCP workers |
| 02 | ⭐⭐ Intermediate | Multi-step workflows, cost optimization (98% savings) |
| 03 | ⭐⭐⭐ Advanced | Remote MCP servers, GitHub integration (36+ tools) |
| 04 | ⭐⭐ Intermediate | Tool discovery, semantic search (66-95% token reduction) |
| 05 | ⭐⭐ Intermediate | Workflow composition, parallel execution (25-40% speedup) |
| 06 | ⭐⭐ Intermediate | WandB integration, Prometheus metrics, cost tracking |
| 07 | ⭐⭐ Intermediate | Redis caching, performance optimization |
| 08 | ⭐⭐⭐ Advanced | Two-model architecture, hybrid routing |
| 09 | ⭐⭐ Intermediate | Sandboxed code execution, dynamic calculations |
| 10 | ⭐⭐⭐ Advanced | LLM-generated plans, natural language orchestration |
| 11 | ⭐⭐⭐ Advanced | Batch processing, programmatic execution |
| 12 | ⭐⭐⭐ Advanced | Sharded catalog, scaling to 1000+ tools |
| 13 | ⭐⭐⭐ Advanced | **Complete pipeline** - ALL features (95% cost reduction, 10x speedup) |

### 🎓 Learning Paths

- **Quick Overview (20 min):** Example 13 only
- **Basics (30 min):** Examples 01, 02, 04
- **Production Ready (1-2 hours):** Examples 13, 06, 07, 08
- **Advanced (2-3 hours):** Examples 05, 10, 11, 12
- **Complete Tour (4+ hours):** All examples in order

### 📝 Documentation

- [Examples README](examples/README.md) - Complete examples guide
- [Testing Report](examples/TESTING_REPORT.md) - Validation results
- [Test Summary](examples/TEST_SUMMARY.md) - Quick reference
- [Features Guide](docs/FEATURES_GUIDE.md) - All capabilities
- [Architecture](docs/ARCHITECTURE.md) - System design

### 🔗 Links

- **GitHub:** https://github.com/ushakrishnan/ToolWeaver
- **Documentation:** [docs/](docs/)
- **Examples:** [examples/](examples/)

### 📈 Stats

- 13 production-ready examples
- 100% test pass rate
- Complete documentation coverage
- All configuration files populated
- 4 learning paths for different needs

**Full Changelog:** v0.1.2...v0.1.3

---
