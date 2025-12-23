# ToolWeaver Release Notes

This is a running log of all releases. Use this content when creating GitHub releases.

---

## v0.3.1 - Documentation Restructuring & Internal Organization (December 23, 2025)

### 🏗️ Maintenance Release: Consolidated Developer Documentation

Streamlined internal documentation with consolidated master TODO list and security analysis framework.

**Key Improvements**: Single source of truth for all development tasks, streamlined internal docs structure, and comprehensive security architecture review for Phase 1 readiness.

### ✨ What's New

#### 📚 Documentation Consolidation
- **`CONSOLIDATED_TODOS.md`**: Master task list combining all phases and roadmaps
  - Phase 0-4 implementation plans
  - Real-time task tracking with status indicators
  - Risk assessment and sequencing
  - ~1000 lines of comprehensive planning

- **`SECURITY_ARCHITECTURE_REVIEW.md`**: Pre-Phase 1 security requirements
  - 6 critical threat scenarios with impact analysis
  - Current security posture assessment
  - 8 priority security improvements
  - 802 lines of security analysis

- **`README.md`**: Updated index for internal docs
  - Cleaned up 18 archived documents
  - Single entry point for all development guidance
  - Quick links to essential references

#### 🗑️ Documentation Cleanup
- **Removed 18 archived/redundant documents**:
  - Historical phase documents (PHASE_0_*, PHASE_1_*)
  - Superseded roadmaps and plans
  - Old analysis documents
  - Session notes and temporary files

- **Preserved 5 essential references**:
  - CONSOLIDATED_TODOS.md (master TODO)
  - SECURITY_ARCHITECTURE_REVIEW.md (pre-Phase 1)
  - BUSINESS_STRATEGY.md (strategic planning)
  - AGENT_UX_AND_MARKET_POSITIONING.md (market positioning)
  - RELEASES.md (version history)

### 📊 Impact
- **Documentation cleanliness**: 88% reduction in doc files (23 → 5 in docs/internal)
- **Maintainability**: Single source of truth for all development work
- **Clarity**: Organized roadmap from current state through Phase 4 completion

### 🚀 Development Status
- **Current Version**: v0.3.1 ← **YOU ARE HERE**
- **Tests Passing**: 699/735 (95%+)
- **Phase Status**: Foundation complete, Phase 0 Security pending start
- **Next Release**: v0.4.0 (Phase 0 Security Implementation)

### 📝 Notes
- This is a **documentation-only release** - no code changes
- All functionality remains at v0.3.0 level
- Internal docs moved to `docs/internal/` (not in public package)
- Update `pyproject.toml` version to 0.3.1 ✅

---

## v0.4.0 - Phase 0 Security Implementation (PLANNED - Target: 5-7 hours)

### 🔒 Security Foundations for Multi-Agent Orchestration

**Status**: NOT STARTED (blocker for Phase 1)

**Goals**: Enable safe parallel agent dispatch with cost controls, data protection, and attack prevention.

**Implementation Roadmap**:
1. Sub-agent resource quotas (cost, concurrency, depth limits)
2. PII detection in agent responses  
3. Request rate limiting for parallel API calls
4. Secrets redaction in logs and errors
5. Prompt injection protection for templates
6. Dispatch depth limits for recursion prevention
7. Template sanitization for LLM safety
8. Distributed lock support for shared state

See `docs/internal/SECURITY_ARCHITECTURE_REVIEW.md` for complete threat analysis and detailed implementation plan.

---

## v0.5.0 - Analytics Backends & Monitoring (December 18, 2025)

### ✨ What's New

#### 📊 Tri-Backend Analytics System
- **SQLite Backend**: Local file storage for development and self-hosted deployments
  - Location: `orchestrator/execution/analytics/skill_analytics.py` (861 lines)
  - Full SQL query access with unlimited retention
  - Methods: `record_skill_usage()`, `rate_skill()`, `update_health_score()`, `compute_health_score()`, `get_leaderboard()`
  - 14/14 dedicated tests passing

- **OTLP Backend**: Grafana Cloud push-based metrics for managed monitoring
  - Location: `orchestrator/execution/analytics/otlp_metrics.py` (380 lines)
  - OpenTelemetry Protocol with automatic 60-second export
  - Base64 authentication, NoOpMeterProvider check (prevents override warnings)
  - Successfully pushing to production Grafana Cloud (verified)

- **Prometheus Backend**: HTTP /metrics endpoint for scraping and standard monitoring stacks
  - Location: `orchestrator/execution/analytics/prometheus_metrics.py` (300+ lines)
  - HTTP endpoint at :8000/metrics for Prometheus scraping
  - Singleton pattern for metric registration (test-safe)
  - Counter/Histogram/Gauge metrics with labels

#### 🏭 Factory Pattern & Configuration
- **Backend Selection**: Single `ANALYTICS_BACKEND` env var (`sqlite` | `otlp` | `prometheus`)
- **Factory Function**: `create_analytics_client(backend=None)` auto-detects from env
- **Zero Code Changes**: Switch backends without modifying application code
- **Unified Interface**: All backends support standard operations
  - `record_skill_execution()` / `record_skill_usage()`
  - `record_skill_rating()`
  - `update_health_score()`
  - `health_check()`

#### 🧪 Comprehensive Testing
- **Test Suite**: `tests/test_all_backends.py`
- **Results**: 4/4 backend categories passing (100%)
  - SQLite: 4/4 subtests ✓
  - OTLP: 4/4 subtests ✓ (Grafana Cloud verified)
  - Prometheus: 4/4 subtests ✓ (HTTP endpoint operational)
  - Factory: 3/3 subtests ✓
- **Total Test Count**: 488 tests passing (up from 461)
- **Zero Warnings**: Fixed Gemini import, tool_search_tool registration, MeterProvider override

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
