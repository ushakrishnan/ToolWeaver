# Implementation Plan: Tool Template System

**Status**: In Progress  
**Last Updated**: December 22, 2025  
**Approach**: Library-First with UI-Ready Interfaces  

---

## 📌 Status Summary

 - Active Phase: 4 ⭐ COMPLETE (Enhanced Examples)
- Live Progress: See Phase 0 status in [docs/internal/PHASE_0_PROGRESS.md](../internal/PHASE_0_PROGRESS.md)
- Phase 4 Progress (Dec 22): Example 23 refreshed with three-ways demo; all registration methods working end-to-end
- Recently Completed (Dec 19, 2025): 
  - **Phase 1 Deliverables**: `@tool` decorator with nested JSON schemas; template base classes (Function/MCP/CodeExec/Agent); discovery API (list/search/info/domain filtering); external MCP HTTP adapter with streaming (HTTP/SSE/WebSocket); CLI commands (list, search, info)
  - **Phase 1.5 Deliverables**: Skill bridge integration - bidirectional tool↔skill conversion with versioning; save_tool_as_skill, load_tool_from_skill, sync_tool_with_skill functions; template methods for skill integration
  - **Phase 1.7 Deliverables**: Semantic search via `semantic_search_tools()` and `search_tools(use_semantic=True)` with vector backend; CLI `--semantic` flag; documentation; 12 semantic-search tests
  - **Phase 1.8 Deliverables**: Progressive tool loading with `browse_tools()` API; detail levels (name/summary/full); pagination (offset/limit); CLI `browse` command with `--detail` flags; 20 comprehensive tests
  - **Phase 1.9 Deliverables**: Sandbox data filtering and PII tokenization - DataFilter, PIITokenizer, filter_and_tokenize() convenience function; 60-90% token reduction on database queries; comprehensive documentation; 26 tests
  - **Phase 1.10 Deliverables**: Workspace skill persistence - WorkspaceManager with session isolation, SKILL.md format, quota management, versioning; save/load skills and intermediates; multi-agent workspaces; 26 tests
  - **Tests**: 677+ tests passing (52 new tests for Phase 1.9 & 1.10); 80%+ coverage maintained
  - **Documentation**: Updated quickstart, registering-tools, discovering-tools, external-mcp, skill-bridge guides; added sandbox-data-filtering guide
 - Coverage Policy: pytest gate `--cov-fail-under=80` and Codecov patch target 85%
- Next: Phase 3 (YAML loader) after Phase 2 completes

## 🎯 Overview

Formalize the tool registration system into a reusable template framework that allows:
1. **Package users** to easily define and register tools via decorators/base classes
2. **Contributors** to extend the core library with new template types
3. **Any UI** to adapt library-format tools to their needs (Claude, Cline, web, etc.)
**Philosophy**: Package-First, Clean, No Legacy Baggage
- Users: `pip install toolweaver` then use decorators/base classes
- Contributors: Modify source via PR (package > everyone modifying source)
- No backward compatibility concerns (clean break now = clean codebase forever)

---

## 📦 Phase 0: Package Infrastructure ⭐ FOUNDATION
**Goal**: Build clean package boundaries and ecosystem patterns  
**Effort**: Medium  
**User Impact**: Sets up the entire ecosystem correctly from day 1

#### Tasks:

**0a: Clean Dependencies & Extras**
**0k: Type Hints & mypy Gate (In Progress)**
- Widen strict mypy overrides to `orchestrator/tools/*`
- Annotate `infra/a2a_client.py`, `tools/agent_discovery.py`, and shared models
- Fix any findings while preserving public API
- Maintain ≥80% coverage with 2–3 targeted edge-case tests

- [x] Update `pyproject.toml`
  - [x] Core dependencies minimal: pydantic, aiohttp, python-dotenv (env helper)
  - [x] Optional extras: `[monitoring]` for wandb, prometheus
  - [x] Optional extras: `[dev]` for pytest, black, mypy
  - [x] No optional deps in core install

**0b: Clear Public API**
- [x] Create clean `orchestrator/__init__.py`
  - [x] Export stubs for: decorators, templates, discovery, skill bridge
  - [x] `__all__` list (explicit public API)
  - [~] Legacy surfaces routed via `_internal.public_legacy` shim (compat kept)
  - [ ] Everything else in `orchestrator._internal`
  - [ ] Users know exactly what's safe to use

- [x] Create `orchestrator/_internal/` package
  - [ ] Move all implementation details here
  - [ ] Users don't import from `_internal`

**0c: Configuration via Environment**
- [x] Create `orchestrator/config.py`
  - [x] TOOLWEAVER_SKILL_PATH → skill storage location
  - [x] TOOLWEAVER_LOG_LEVEL → logging (INFO, DEBUG, etc.)
  - [x] TOOLWEAVER_REDIS_URL → optional caching (no error if missing)
  - [x] TOOLWEAVER_WANDB_PROJECT → optional W&B (no error if missing)
  - [x] No source code config files

**0d: User-Friendly Import Errors**
- [x] Create error helpers in `orchestrator/_internal/errors.py`
  - [x] `MissingOptionalDependency` exception
  - [x] Clear message: "W&B not available. Install: pip install toolweaver[monitoring]"
  - [x] Used when wandb/prometheus/etc imported but not installed

**0e: Plugin Registry (for 3rd-party packages)**
- [x] Create `orchestrator/plugins/registry.py`
  - [x] `register_plugin(name, plugin_class)`
  - [x] `get_plugin(name)` - safely get registered plugins
  - [x] Users' packages can extend without touching ToolWeaver source
  - [x] Example: My package calls `register_plugin("my_tool", MyTool)` on import

**0f: Clean CONTRIBUTING.md**
- [x] Rewrite for package-first mindset
  - [x] "Package Users: Don't fork, use decorators and publish your own package"
  - [x] "Contributors: PR to add core features"
  - [x] "Plugin Authors: Use plugin registry"
  - [x] Clear: you can't just modify ToolWeaver locally

**0g: Documentation Structure**
- [x] Split docs clearly:
  - [x] `docs/for-package-users/` ← Start here for 80% of users
    - [x] quickstart.md (5 min to first tool)
    - [x] registering-tools.md
    - [x] discovering-tools.md
    - [x] extending.md (create own package)
    - [x] faq.md
  - [x] `docs/for-contributors/` ← Only for PR authors
    - [x] development setup
    - [x] adding core features (architecture)
    - [x] testing strategy
    - [x] security

- [x] Update main README.md
  - [x] "For package users" link → for-package-users/quickstart.md
  - [x] "For contributors" link → for-contributors/development.md

**0h: Version & Changelog Policy (No Legacy)**
- [x] Create `.changelog/template.md`
  - [x] Format: New / Changed / Fixed / Breaking
  - [x] No deprecation cycles (clean breaks only)
  - [x] Semver: MAJOR = breaking, MINOR = feature, PATCH = fix

- [ ] Version check on startup (optional warning if outdated)
  - [ ] Not required, just informational

**0i: CI/CD for Clean Package**
- [x] Test fresh install (no local deps)
  - [x] `pip install -e . --no-deps` in CI (public-api-smoke job)
  - [x] Import `orchestrator` works (version printed)
  - [ ] `from orchestrator import mcp_tool` works (after Phase 2)
  - [x] Validates public API is clean
  
- [x] Test optional deps gracefully missing
  - [x] Config validation runs without wandb/prometheus installed (reports warnings only)
  - [x] Clear error only if user explicitly enables it (guarded by helpers)

- [x] Lint for `_internal` usage
  - [x] CI script warns/fails if public code imports from `_internal` (examples)

 - [x] Static checks
   - [x] ruff lint and mypy type checks run in CI matrix

**0j: Example: Community Plugin Package (Template)**
- [x] Create `examples/community-plugin-template/`
  - [x] Shows how to create separate package using ToolWeaver
  - [x] Shows plugin registry usage
  - [ ] Shows decorators + base classes
  - [ ] Can be forked by users who want to publish tools

**Testing:**
- [ ] Fresh install works (no local deps)
- [ ] Public API is clean
- [ ] Optional deps fail gracefully with good messages
- [ ] Plugin registry works
- [ ] Configuration via env vars works

**Documentation:**
- [ ] Create `docs/for-package-users/quickstart.md`
- [ ] Update `CONTRIBUTING.md` (package-first)
- [ ] Create `.changelog/template.md`
- [ ] Document plugin registry in `docs/for-contributors/plugins.md`
**0k: Type Hints & IDE Support**
- [ ] All code fully type-hinted (Python 3.10+ syntax)
  - [ ] Function signatures with type hints
  - [ ] Return types on all functions
  - [ ] Type hints for class attributes
  - [ ] Generic types (List, Dict, Optional) properly used
- [ ] Enable IDE autocomplete for package users
- [ ] Type checking in CI: `mypy orchestrator/`
- [ ] Type stubs for any compiled modules

**0l: Structured Logging (Built-In)**
- [x] Create `orchestrator/_internal/logger.py`
  - [x] Standard Python logging (no external deps)
  - [x] Configurable via `TOOLWEAVER_LOG_LEVEL` env var
  - [x] Structured logs: timestamp, level, component, message
  - [x] Debug mode for troubleshooting
- [ ] Use throughout codebase for visibility
- [ ] Document logging for package users

**0m: Security & Input Validation**
- [x] Create `orchestrator/_internal/validation.py`
  - [x] Tool parameter validation framework (sanitization, path/url/code checks)
  - [x] Pydantic models for ToolDefinition validation
  - [ ] Document: what trusts what
  - [ ] Threat model: what are we protecting against
  - [ ] Sandboxing approach if running untrusted code
- [ ] Security documentation for contributors
- [ ] Security section in CONTRIBUTING.md

**0n: Python Version & Platform Support Policy**
- [x] Set minimum: Python 3.10+ only
- [ ] CI/CD tests on Python 3.10, 3.11, 3.12, 3.13
- [ ] CI/CD tests on Windows, Linux, macOS
- [ ] Document in README: supported versions
- [ ] Document any platform-specific limitations
- [x] Add `python_requires=">=3.10"` in pyproject.toml
---

## � Skill Library Integration

**Context**: ToolWeaver has an existing Skill Library (`~/.toolweaver/skills/`) with versioning, dependency tracking, and optional semantic search. Tools and skills are complementary:
- **Tools** = Callable functions with input/output schemas registered in `_tool_map`
- **Skills** = Reusable code snippets with versions, metadata, dependencies, and persistence

**Bridge Pattern**: 
1. Tools can reference/wrap skills (tool execution calls skill)
2. Skills can be created from tool implementations (tool's code saved as skill for reuse)
3. Tools have optional `skill_reference` metadata pointing to backing skill

**Integration Points** (across all phases):
- **Phase 1**: Tools can optionally reference skills via metadata
- **Phase 2**: Decorators can auto-save tool code as skills (optional `@auto_skill=True`)
- **Phase 3**: YAML can reference skill IDs instead of re-writing code
- **Phase 4**: Example 23 showcases tool ↔ skill bridge patterns
- **Phase 1.5** (NEW): Formalize skill registry integration

---

### Phase 1.5: Skill Bridge Integration ⭐ COMPLETE ✅
**Goal**: Connect tool templates to skill library  
**Effort**: Low  
**User Impact**: Tools can be version-managed like skills

#### Tasks:
- [x] Create `orchestrator/tools/skill_bridge.py`
  - [x] Functions: `save_tool_as_skill()`, `load_tool_from_skill()`, `get_tool_skill()`, `sync_tool_with_skill()`, `get_skill_backed_tools()`
  - [x] Handle skill versioning (patch/minor/major bumps)
  - [x] Decorator stripping and code dedenting for clean skill storage
  - [x] Preserve nested JSON schemas in skill metadata

- [x] Update `orchestrator/tools/templates.py`
  - [x] Add `save_as_skill()` method to BaseTemplate
  - [x] Add `load_from_skill()` class method to BaseTemplate
  - [x] Update FunctionToolTemplate to store function reference
  - [x] Skill reference stored in metadata

- [x] Integration with skill_library.py
  - [x] Tool source code saved as skill with automatic versioning
  - [x] Skills can be loaded as tools with full schema reconstruction
  - [x] Sync tools with latest skill versions

- [x] Update decorator (`orchestrator/tools/decorators.py`)
  - [x] Store `__wrapped__` reference for source extraction
  - [x] Store `__tool_definition__` for easy access

- [x] Export from public API (`orchestrator/__init__.py`)
  - [x] `save_tool_as_skill`, `load_tool_from_skill`, `get_tool_skill`, `sync_tool_with_skill`, `get_skill_backed_tools`

**Testing:**
- [x] Tool can save implementation as skill (test_save_tool_as_skill)
- [x] Tool can load from existing skill (test_load_tool_from_skill)
- [x] Template integration works (test_template_save_as_skill, test_template_load_from_skill)
- [x] Tool versioning syncs with skill versioning (test_skill_versioning)
- [x] Skill-backed tools can be listed (test_get_skill_backed_tools)
- [x] Sync with latest skill version works (test_sync_tool_with_skill)
- [x] Nested schemas preserved (test_nested_schema_preservation)
- [x] Error cases handled (test_error_no_function, test_error_skill_not_found, test_error_invalid_skill_code)
- [x] **12 tests passing, 605 total tests**

**Documentation:**
- [x] Created docs/for-package-users/skill-bridge.md
  - [x] Quick start examples
  - [x] API reference
  - [x] Use cases and best practices
  - [x] Template integration examples

---

### Phase 1.6: Discovery & Querying APIs ⭐ COMPLETE ✅
**Goal**: Enable package users to query available tools  
**Effort**: Low  
**User Impact**: Essential for users to understand their tools

#### Tasks:
- [x] Create `orchestrator/tools/discovery_api.py`
  - [x] `get_available_tools()` - List all tools with filters
  - [x] `search_tools(query, filters)` - Keyword search (semantic later)
  - [x] `get_tool_info(tool_name)` - Full schema, examples, metadata
  - [ ] `get_tool_dependencies(tool_name)` - What skills/tools does it need? (Phase 1.5+)
  - [x] `list_tools_by_domain(domain)` - Filter by domain
  - [ ] `list_tools_by_status(status)` - Active, deprecated, etc. (Phase 1.7+)

- [x] Add CLI commands
  - [x] `toolweaver list` - Show all tools
  - [x] `toolweaver search "expense"` - Search for tools
  - [x] `toolweaver info get_expenses` - Details on one tool
  - [ ] `toolweaver dependencies process_invoice` - Dependency tree (Phase 1.5+)
  - [ ] JSON output format (`--json`) (Phase 1.7+)
  - [ ] Pagination for large lists (Phase 1.7+)

- [x] Add to package exports
  - [x] Make discovery API available from `orchestrator`
  - [x] Python API: `from orchestrator import search_tools`
  - [x] CLI entry point in pyproject.toml: `toolweaver = "orchestrator.cli:main"`

**Example Usage:**
```python
from orchestrator import get_available_tools, search_tools, get_tool_info

# List all tools
all_tools = get_available_tools()

# Search by query
expense_tools = search_tools(query="expense")

# Filter by domain
finance_tools = search_tools(domain="finance")

# Get full details
info = get_tool_info("get_expenses")
```

**CLI Usage:**
```bash
# List all tools
$ toolweaver list

# Search for tools
$ toolweaver search "expense"

# Get detailed info
$ toolweaver info get_expenses
```

**Testing:**
- [x] Discovery API returns correct tools (test_discovery_api.py)
- [x] CLI commands work (test_cli.py: list, search, info)
- [x] Nested JSON schemas preserved in discovery
- [x] Semantic search with vector backend
- [x] Filters (domain) work correctly
- [ ] Dependency tree calculation accurate
- [ ] CLI commands produce formatted output

**Documentation:**
- [x] "Discovering Available Tools" guide
- [ ] Add to docs/how-it-works/
- [ ] API reference docs

---

### Phase 1.7: Semantic Search & Vector Backend ⭐ COMPLETE ✅
**Goal**: Add vector-backed semantic search with graceful fallback and CLI support  
**Effort**: Medium  
**User Impact**: Better discovery at scale; reduced token usage

#### Tasks:
- [x] Add `semantic_search_tools()` with vector fallback to substring search
- [x] Extend `search_tools()` with `use_semantic`, `top_k`, `min_score`
- [x] Build catalog → vector index flow with Qdrant + in-memory fallback
- [x] CLI: `toolweaver search ... --semantic --top-k N`
- [x] Export new API from `orchestrator/__init__.py`

**Testing:**
- [x] 12 semantic search tests (domain filters, top_k, min_score, fallback)
- [x] CLI regression tests still passing

**Documentation:**
- [x] Added docs/for-package-users/semantic-search.md (setup, usage, performance)

**Notes:**
- Auto-fallback to substring when Qdrant/deps unavailable
- In-memory vector search path for offline/dev usage

**Example Usage:**
```python
from orchestrator import search_tools

# Semantic search
tools = search_tools(query="create pull request", use_semantic=True, top_k=3)
```

---

### Phase 1: Template Base System ⭐ COMPLETE ✅
**Goal**: Create foundational abstractions  
**Effort**: Medium  
**User Impact**: Foundation for all other phases

#### Tasks:
- [x] Create `orchestrator/tools/templates.py`
  - [x] Define `BaseTemplate` ABC with core methods
  - [x] Define `build_definition()` and `execute()` lifecycle
  - [x] Add validation framework via Pydantic
  - [x] Add metadata/tracking support

- [x] Create template subclasses in `orchestrator/tools/templates.py`
  - [x] Implement `FunctionToolTemplate` base class (simple callable wrapper)
  - [x] Implement `MCPToolTemplate` base class (MCP client wrapper)
  - [x] Implement `CodeExecToolTemplate` base class (code execution wrapper)
  - [x] Implement `AgentTemplate` base class (A2A agent wrapper)
  - [x] Auto-generate `ToolDefinition` from template
  - [x] Handle parameter validation via Pydantic
  - [x] Built-in retry/timeout logic via template patterns
  - [x] External MCP adapter capability (connect to remote MCP servers)
    - [x] HTTP adapter plugin implemented (`orchestrator/tools/mcp_adapter.py`)
    - [x] Tool discovery (GET /tools) with schema normalization
    - [x] Execute (POST /execute) with JSON payload
    - [x] Streaming support: HTTP chunked, SSE, WebSocket
    - [ ] Connection config via env + params for ws/http endpoints (basic HTTP done, WS/SSE variants optional)
    - [x] Error mapping and retries (basic error handling)
    - [x] Optional plugin wrapper for third-party servers (MCPHttpAdapterPlugin)
    - [x] Nested JSON support via `input_schema` / `output_schema` on templates and decorators

- [x] Create `orchestrator/tools/__init__.py` exports
  - [x] Export templates for package users
  - [x] Organize public API

**1a: Tool Metadata Standardization**
- [x] Standard tool metadata fields defined in `ToolDefinition`
    - [x] name, description, type, provider, parameters
    - [x] metadata dict for extensibility
  - [x] Validation schema via Pydantic models
  - [ ] Standard categories/tags list (recommended) (Phase 1.7+)
  - [ ] Tool health/status enum (Phase 1.7+)

**1b: Error & Exception Hierarchy**
- [ ] Create `orchestrator/_internal/exceptions.py` (Phase 1.7+)
  - [ ] Base `ToolError` exception (inherit from Exception)
  - [ ] `ToolNotFoundError` - tool doesn't exist
  - [ ] `InvalidParametersError` - bad params
  - [ ] `ToolTimeoutError` - execution timeout
  - [ ] `ToolExecutionError` - general execution failure
  - [ ] `ToolDependencyError` - missing dependencies
  - [ ] Each with clear, actionable error message
- [ ] Use throughout codebase
- [ ] Document exception hierarchy for users

**1c: Built-in Diagnostics (No External Tools Needed)**
- [ ] Create `orchestrator/diagnostics.py` (Phase 1.7+)
  - [ ] `get_tool_health(tool_name)` - is tool working?
  - [ ] `get_execution_stats(tool_name)` - call count, success rate, avg duration
  - [ ] `get_all_stats()` - stats for all tools
  - [ ] `get_debug_info()` - what's happening now
  - [ ] `check_dependencies()` - are all deps satisfied
- [ ] Tracked automatically (no external dependencies)
- [ ] Users can diagnose issues without W&B/Prometheus

**Testing:**
- [x] Unit tests for template base classes (test_templates.py)
- [x] Parameter validation tests
- [x] Integration with plugin system
- [ ] Test error types are raised correctly (Phase 1.7+)
- [ ] Test diagnostics collection (Phase 1.7+)
 - [x] External MCP server smoke test (mock server with HTTP adapter in test_mcp_adapter.py)
 - [x] Nested JSON round-trip tests for decorators/templates (plugin `get_tools()` returns serialized dicts)

**Documentation:**
- [x] Update examples/24 (external MCP adapter example)
- [x] Create docs/for-package-users/external-mcp.md
- [x] Update docs/for-package-users/registering-tools.md with templates
- [ ] Document tool metadata standards (Phase 1.7+)
- [ ] Document error handling (Phase 1.7+)
- [ ] Document diagnostics API (Phase 1.7+)

---

### Phase 1.8: Progressive Tool Loading ⭐ COMPLETE ✅
**Goal**: Enable efficient token management by loading tool definitions incrementally  
**Effort**: Medium  
**User Impact**: HIGH - Reduces context size for large tool catalogs

#### Tasks:
- [x] Implement `browse_tools()` API
  - [x] Support detail levels: `name` (minimal), `summary` (moderate), `full` (complete)
  - [x] Pagination support with `offset` and `limit` parameters
  - [x] Domain, type, and plugin filtering
  - [x] Returns lightweight projections to minimize token usage

- [x] Update `search_tools()` for progressive loading
  - [x] Add optional `detail_level` parameter
  - [x] Support `name`, `summary`, `full` detail levels
  - [x] Backward compatible (defaults to full ToolDefinition)

- [x] Update `get_tool_info()` for progressive loading
  - [x] Add `detail_level` parameter (default: `full`)
  - [x] Add `include_examples` parameter
  - [x] Support lightweight projections

- [x] Add `_format_tool_view()` helper
  - [x] Projects ToolDefinition to lightweight views
  - [x] Validates detail_level parameter
  - [x] Handles examples inclusion

- [x] Update CLI with progressive loading
  - [x] New `browse` command with `--detail`, `--offset`, `--limit` flags
  - [x] Add `--detail` flag to `search` command
  - [x] Add `--detail` flag to `info` command
  - [x] Support all three detail levels in output formatting

**Testing:**
- [x] 20 comprehensive progressive loading tests (test_progressive_loading.py)
- [x] Test all detail levels (name, summary, full)
- [x] Test pagination (offset/limit)
- [x] Test filters (domain, type, plugin)
- [x] Test error handling (invalid detail level, negative offset/limit)
- [x] Test token reduction verification
- [x] CLI regression tests still passing

**Documentation:**
- [x] Code comments and docstrings for new APIs
- [ ] Update docs/for-package-users/discovering-tools.md with progressive loading examples

**Example Usage:**
```python
from orchestrator import browse_tools, search_tools, get_tool_info

# Browse names only (minimal tokens)
names = browse_tools(detail_level="name", limit=20)

# Search with summary for quick overview
summaries = search_tools(query="github", detail_level="summary")

# Get full details only for selected tool
full_info = get_tool_info("create_pr", detail_level="full")
```

---

### Phase 1.9: Sandbox Data Filtering & PII Tokenization ⭐ COMPLETE ✅
**Goal**: Reduce token costs and protect sensitive information by filtering large outputs and tokenizing PII  
**Effort**: Medium  
**User Impact**: HIGH - Significant token savings (60-90% on database queries) + privacy protection

#### Tasks:
- [x] Create `sandbox_filters.py` module
  - [x] `DataFilter` class with configurable limits (max_bytes, max_rows, max_string_length)
  - [x] Intelligent truncation that preserves data structure
  - [x] Human-readable truncation summaries
  - [x] `PIITokenizer` class with deterministic token generation (SHA-256)
  - [x] PII detection patterns: email, phone, SSN, credit cards, IP addresses
  - [x] Reversible tokenization for secure contexts
  - [x] `filter_and_tokenize()` convenience function

- [x] Implement filtering strategies
  - [x] Output size limiting with configurable thresholds
  - [x] Row/item truncation for tabular data
  - [x] String truncation with summary
  - [x] Structure preservation during truncation
  - [x] Statistics tracking (bytes saved, rows truncated)

- [x] Implement PII tokenization
  - [x] Regex patterns for common PII types
  - [x] Configurable PII types (enable/disable selectively)
  - [x] Token map for detokenization
  - [x] Nested structure support (dict, list recursion)

- [x] Export from execution module
  - [x] Add to `orchestrator/execution/__init__.py`
  - [x] Export DataFilter, PIITokenizer, FilterConfig, TokenizationConfig, PIIType

**Testing:**
- [x] 26 comprehensive tests (test_sandbox_filters.py)
- [x] Test email, phone, SSN, credit card, IP address tokenization
- [x] Test nested structure handling
- [x] Test detokenization correctness
- [x] Test filtering with various limits
- [x] Test combined filter + tokenize workflow
- [x] Test edge cases (empty data, None values, unicode)

**Documentation:**
- [x] Created docs/user-guide/sandbox-data-filtering.md
- [x] Usage examples for filtering only, tokenization only, and combined
- [x] Realistic scenarios (database queries, API responses, log files)
- [x] Configuration reference
- [x] Security considerations
- [x] Performance characteristics

**Token Reduction Results:**
- Database queries: 60-90% reduction
- API responses: 50-80% reduction
- Log files: 70-95% reduction
- Large JSON: 40-70% reduction

**Example Usage:**
```python
from orchestrator.execution import filter_and_tokenize, FilterConfig

# Process large database query result
result = filter_and_tokenize(
    data=query_result,
    filter_config=FilterConfig(max_rows=100, max_bytes=50000),
    tokenize_pii=True
)

# Access filtered data (PII tokenized, size reduced)
processed = result["data"]
stats = result["stats"]  # Token savings
token_map = result["token_map"]  # For detokenization if needed
```

---

### Phase 1.10: Workspace Skill Persistence ⭐ COMPLETE ✅
**Goal**: Enable agents to persist reusable code and intermediate outputs across sessions  
**Effort**: Medium  
**User Impact**: HIGH - Enables agent learning, skill reuse, and work resumability

#### Tasks:
- [x] Create `workspace.py` module
  - [x] `WorkspaceManager` class for session-isolated workspaces
  - [x] `WorkspaceSkill` dataclass with versioning and metadata
  - [x] `WorkspaceQuota` for resource limits
  - [x] Custom exceptions: `WorkspaceQuotaExceeded`, `SkillNotFound`

- [x] Implement skill management
  - [x] `save_skill()` with auto-versioning on updates
  - [x] `load_skill()` by name
  - [x] `list_skills()` with tag filtering
  - [x] `delete_skill()` with metadata cleanup
  - [x] Skill metadata: dependencies, tags, examples, hash

- [x] Implement SKILL.md format
  - [x] `to_markdown()` for human-readable skill docs
  - [x] `from_markdown()` parser for skill import
  - [x] Markdown includes: code, dependencies, examples, metadata
  - [x] Automatic generation on skill save

- [x] Implement intermediate output storage
  - [x] `save_intermediate()` for JSON-serializable data
  - [x] `load_intermediate()` by name
  - [x] `list_intermediates()` for discovery
  - [x] Size tracking and quota enforcement

- [x] Implement quota management
  - [x] Max workspace size (default: 100MB)
  - [x] Max files (default: 1000)
  - [x] Max skill size (default: 1MB)
  - [x] Max intermediate size (default: 10MB)
  - [x] Quota checking before writes

- [x] Workspace utilities
  - [x] `get_workspace_stats()` for monitoring
  - [x] `clear_workspace()` for cleanup
  - [x] Session isolation (separate dirs per session_id)
  - [x] Metadata tracking (skill count, size, timestamps)

- [x] Export from execution module
  - [x] Add to `orchestrator/execution/__init__.py`
  - [x] Export WorkspaceManager, WorkspaceSkill, WorkspaceQuota, exceptions

**Testing:**
- [x] 26 comprehensive tests (test_workspace.py)
- [x] Test skill save/load/update/delete
- [x] Test skill versioning (auto-increment)
- [x] Test SKILL.md format (to_markdown, from_markdown)
- [x] Test intermediate save/load
- [x] Test quota enforcement (all limits)
- [x] Test multi-agent isolation
- [x] Test realistic agent workflows
- [x] Test skill evolution over time

**Documentation:**
- [x] Comprehensive docstrings in workspace.py
- [x] Usage examples in docstrings
- [ ] User guide for workspace management (future)

**Example Usage:**
```python
from orchestrator.execution import WorkspaceManager

# Create workspace for agent session
workspace = WorkspaceManager(session_id="agent-123")

# Agent writes reusable skill
skill = workspace.save_skill(
    name="csv_parser",
    code="def parse_csv(data): ...",
    description="Parse CSV into list of dicts",
    tags=["parsing", "csv"]
)

# Save intermediate result
workspace.save_intermediate("parsed_users", parsed_data)

# Later: Resume session and load skill
skill = workspace.load_skill("csv_parser")
data = workspace.load_intermediate("parsed_users")

# Check workspace usage
stats = workspace.get_workspace_stats()
print(f"Skills: {stats['skills']}, Size: {stats['total_size_mb']}MB")
```

---

### Code-Mode & Sandbox Roadmap (Backlog)
**Goal**: Reduce context/token load and improve safety by executing agent-written code against typed MCP APIs in a secure sandbox.

- [x] Design code-mode sandbox pathway (typed MCP APIs, no outbound network, bindings only; monitoring + limits) → See docs/internal/code_mode_sandbox.md
- [x] Implement progressive tool loading (search/browse with detail levels: name/summary/full schema) → Phase 1.8 COMPLETE
- [x] Filter/tokenize large or sensitive data in sandbox before returning to model → Phase 1.9 COMPLETE
- [x] Enable workspace skill persistence (persist reusable code + SKILL.md; scoped FS) → Phase 1.10 COMPLETE

---

### Phase 2: Decorators & Easy Registration ⭐ ACTIVE — NOT COMPLETE
**Goal**: Make it dead simple for package users  
**Effort**: Low  
**User Impact**: HIGH - Fastest way to add tools

**Status check (Dec 22, 2025):** Specialized decorators `@mcp_tool` and `@a2a_agent` implemented with auto parameter extraction; 4 tests passing; registry validation still pending.

#### Completed (Phase 1):
- [x] Create `orchestrator/tools/decorators.py`
  - [x] `@tool()` generic decorator for all tool types
  - [x] Accepts `input_schema`/`output_schema` for nested JSON
  - [x] Auto-register with plugin system (`decorators` plugin)
  - [x] Exported from `orchestrator` package

- [x] Package exports
  - [x] Make `@tool` decorator available from `orchestrator` package
  - [x] Works with function wrapper pattern

#### Remaining (Phase 2):
- [x] Create specialized decorators
  - [x] `@mcp_tool()` decorator for MCP tools (sugar over `@tool`)
  - [x] `@a2a_agent()` decorator for agents (sugar over `@tool`)
  - [x] Auto-extract parameters from type hints
  - [x] 4 tests passing (test_decorators.py)

- [ ] Create `orchestrator/tools/registry.py` (formalize tool registry)
  - [x] Plugin system already provides centralized registration
  - [ ] Add validation on registration (beyond Pydantic)
  - [ ] Add deduplication checks
  - [ ] Add domain detection

**Example of Phase 1 decorator usage:**
```python
from orchestrator import tool

@tool(
    name="get_expenses",
    description="Fetch employee expenses",
    type="function",
    parameters=[
        {"name": "employee_id", "type": "string", "required": True}
    ]
)
def get_expenses(employee_id: str) -> dict:
    # ... implementation
    return {...}
```

**Example of Phase 2 decorator usage (now working):**
```python
from orchestrator import mcp_tool

@mcp_tool(domain="finance")  # Auto-extracts params from type hints
async def get_expenses(employee_id: str) -> dict:
    """Fetch employee expenses"""
    # ... implementation
    return {...}
```
    """Fetch employee expenses"""
    # ... implementation
    return {...}
```

**2a: Decorator Validation & Type Checking**
- [ ] When decorator runs, validate function signature
  - [ ] Check for missing docstrings → warn
  - [ ] Check for missing type hints → warn
  - [ ] Check for non-async without reason → warn
  - [ ] Validate parameter names (no spaces, special chars)
  - [ ] Check return type is defined
- [ ] Warn users at registration time of issues
- [ ] Document what makes a "good" tool function

**Testing:**
- [x] Test decorator extraction of parameters (test_decorators.py)
- [x] Test auto-registration flow
- [ ] Test domain detection
- [ ] Test validation warnings (missing docstring, type hints, etc.)
- [ ] Test error messages are helpful

**Documentation:**
- [x] Update docs/for-package-users/quickstart.md with decorator usage
- [x] Update docs/for-package-users/registering-tools.md with decorator examples
- [ ] "Quickest Way: Decorators" guide in how-it-works (Phase 2)
- [ ] Add to examples/ (Phase 2)
- [ ] Document decorator best practices (Phase 2)
- [ ] Document what validation checks are performed (Phase 2)

---

### Phase 3: YAML Loader ⭐ COMPLETE ✅
**Goal**: Config-driven tool registration  
**Effort**: Medium  
**User Impact**: DevOps/config-first teams

**Status (Dec 22, 2025):** YAML loader fully implemented with 16 tests passing.

#### Completed Tasks:
- [x] Create `orchestrator/tools/loaders.py`
  - [x] YAML schema validator (pydantic integration)
  - [x] Load tools from YAML files
  - [x] Resolve worker functions from import paths
  - [x] Integration with discovery (yaml_tools plugin)
  - [x] Batch loading from directories

- [x] Create schema file `orchestrator/tools/tool-schema.yaml`
  - [x] Full JSON schema for YAML tools
  - [x] Examples and defaults
  - [x] Support for nested object/array parameters

- [x] Integration with discovery
  - [x] `load_tools_from_yaml()` registers via yaml_tools plugin
  - [x] `load_tools_from_directory()` batch loads
  - [x] Discovered tools accessible via same APIs as decorator/template tools

**Testing (16/16 passing):**
- [x] Load simple tool with parameters
- [x] Execute sync and async workers
- [x] Load multiple tools per file
- [x] Error cases (missing fields, invalid YAML, import failures)
- [x] Worker path resolution (colon and dot separators)
- [x] Metadata preservation
- [x] Optional field defaults
- [x] Batch directory loading

---

### Phase 4: Enhanced Example 23 ⭐ COMPLETE ✅
**Goal**: Showcase all registration methods  
**Effort**: Low  
**User Impact**: Clear examples for different styles

**Status (Dec 22, 2025):** Example 23 updated with comprehensive three-ways demo.

#### Completed Tasks:
- [x] Create `examples/23-adding-new-tools/three_ways.py`
  - [x] Method 1: Template class approach (FunctionToolTemplate)
  - [x] Method 2: Decorator approach (@mcp_tool, @a2a_agent)
  - [x] Method 3: YAML approach (load_tools_from_yaml)
  - [x] All three produce identical tools
  - [x] End-to-end demo runs successfully

- [x] Create corresponding tests (`test_three_ways.py`)
  - [x] Template tool registration and execution
  - [x] Decorator registration verification
  - [x] YAML worker function execution

**Example Output:**
All three methods successfully register tools with:
- Automatic parameter extraction from type hints
- Proper integration with discovery API
- Mixed usage in single application
- Clear comparison of use cases

---

### Phase 5: Optional Extensions (Community-Driven)
**Goal**: Extend package with monitoring, UI integrations, and plugins  
**Effort**: Medium (per extension)  
**User Impact**: Only if users explicitly enable  
**Important**: Extensions are **opt-in**. Core package works great standalone.

#### 5a: UI Adapters
**Goal**: Connect library to any UI  

- [ ] Create `orchestrator/sdk/adapters/` folder structure
  - [ ] `claude_adapter.py` - Convert to Claude custom skills format
  - [ ] `cline_adapter.py` - Convert to Cline tool format
  - [ ] `fastapi_adapter.py` - REST API wrapper

- [ ] Adapter interface
  - [ ] Define `UIAdapter` base class
  - [ ] Standardize conversion methods

- [ ] Each adapter converts ToolDefinition → UI format, handles dispatch

**Example:**
```python
from orchestrator.sdk.adapters import ClaudeAdapter

adapter = ClaudeAdapter(catalog)
claude_skills = adapter.to_custom_skills_format()
```

#### 5b: Monitoring & Observability (Optional Plugins)
**Goal**: Add observability without forcing dependencies  

- [ ] Create `orchestrator/monitoring/plugins/` structure
  - [ ] `wandb_plugin.py` - W&B integration (requires `pip install wandb`)
  - [ ] `prometheus_plugin.py` - Prometheus metrics (requires `pip install prometheus-client`)
  - [ ] `grafana_plugin.py` - Grafana dashboard template

- [ ] Plugin system
  - [ ] Define `MonitoringPlugin` base class
  - [ ] Plugin discovery and auto-loading

- [ ] Each plugin:
  - [ ] Tracks tool execution metrics
  - [ ] Tool registration events
  - [ ] Skill save/load operations
  - [ ] Optional: performance traces, error rates

**Example - Users explicitly opt-in:**
```python
# Only if user installs: pip install toolweaver[wandb]
from orchestrator.monitoring import enable_wandb

enable_wandb(project="my_tools")
# Now all tool calls are logged to W&B

# Or with Prometheus:
from orchestrator.monitoring import enable_prometheus

enable_prometheus(port=8000)
# Metrics available at http://localhost:8000/metrics
```

**Key Design**:
- Monitoring is OPTIONAL
- No W&B/Prometheus in core dependencies
- Graceful degradation if plugins not installed
- Users must explicitly enable monitoring

**Documentation:**
- [ ] "Optional: Adding Monitoring" guide
- [ ] Examples for each plugin
- [ ] Note: Not required for core functionality

---

**Note**: Phases 5a and 5b are COMMUNITY-DRIVEN and independent. Users/contributors create adapters and plugins as needed. Core package (Phases 1-4) never depends on these.

---

## 🎯 Success Criteria

### By End of Phase 0:
- ✅ Package has clean public API (`orchestrator.*`)
- ✅ All internal code hidden in `_internal`
- ✅ Optional dependencies don't break core install
- ✅ Configuration via environment variables (no source files)
- ✅ Fresh install passes tests (`pip install --no-deps`)
- ✅ CONTRIBUTING.md guides package users to use decorators/plugins
- ✅ Documentation split: package-users vs contributors
- ✅ Plugin registry works for 3rd-party packages
- ✅ Clear import errors if optional deps missing
- ✅ All code fully type-hinted (Python 3.10+)
- ✅ Structured logging built-in (no external deps)
- ✅ Security & validation framework defined
- ✅ Python 3.10+ only, tested on 3.10/3.11/3.12/3.13
- ✅ Windows/Linux/macOS CI tests pass
- ✅ 80%+ test coverage
- ✅ Testing/documentation/contributor standards documented

### By End of Phase 1.5:
- ✅ Tools and skills can be bridged/linked
- ✅ Tool code can be saved as reusable skills
- ✅ Skills can be wrapped by tools
- ✅ Versioning works across tool/skill boundary
- ✅ Example 23 shows both patterns

### By End of Phase 1.6:
- ✅ Package users can query available tools
- ✅ Search works (semantic + keyword + filter)
- ✅ Dependency tree is accessible
- ✅ CLI commands work for discovery
- ✅ Python API is intuitive and complete

### By End of Phase 1:
- ✅ Templates are the foundational abstraction
- ✅ All existing tools can be re-registered using templates
- ✅ Example 23 uses templates instead of raw code
- ✅ Tool metadata standards defined and validated
- ✅ Error hierarchy implemented and used throughout
- ✅ Built-in diagnostics API works (no external tools)
- ✅ All error types have clear, actionable messages

### By End of Phase 2:
- ✅ Decorators are the fastest way to add tools
- ✅ Package users can `@mcp_tool` without knowing templates
- ✅ Auto-discovery still works
- ✅ Registry is single source of truth
- ✅ Decorator validation catches common mistakes
- ✅ Missing type hints/docstrings warned at registration time

### By End of Phase 3:
- ✅ Teams can manage tools via YAML
- ✅ Config can be in version control
- ✅ Both Python and YAML approaches coexist

### By End of Phase 4:
- ✅ All three approaches work identically
- ✅ Documentation covers all paths
- ✅ Example 23 is a complete reference
- ✅ All examples have passing tests
- ✅ All examples demonstrate error cases
- ✅ Examples use only public API

---

## 📊 Implementation Matrix

| Phase | Scope | Effort | User Impact | Risk | Priority |
|-------|-------|--------|-------------|------|----------|
| **0** | **Package Infrastructure** | **Medium** | **Very High** | **Very Low** | 🔴 **CRITICAL** |
| 1 | Templates ABC | Medium | High | Low | 🔴 CRITICAL |
| 1.5 | Skill Bridge | Low | High | Very Low | 🔴 CRITICAL |
| 1.6 | Discovery APIs | Low | Very High | Very Low | 🔴 CRITICAL |
| 2 | Decorators | Low | Very High | Very Low | 🔴 CRITICAL |
| 3 | YAML Loader | Medium | Medium | Low | 🟡 HIGH |
| 4 | Example 23 | Low | High | Very Low | 🟡 HIGH |
| 5a | UI Adapters | Medium | Medium | Very Low | 🟢 OPTIONAL |
| 5b | Monitoring Plugins | Low | Medium | Very Low | 🟢 OPTIONAL |

---

## 🏗️ File Structure After Implementation

```
orchestrator/
├── __init__.py                     ← CLEAN (Phase 0): Public API only
├── config.py                       ← NEW (Phase 0): Env var config
├── plugins/                        ← NEW (Phase 0): Plugin registry
│   └── registry.py
├── _internal/                      ← NEW (Phase 0): All internals hidden
│   ├── errors.py                   ← User-friendly error messages
│   └── ... (move existing internals here)
│
├── tools/
│   ├── templates/                  ← NEW (Phase 1)
│   │   ├── __init__.py
│   │   ├── base.py                 ← ToolTemplate ABC
│   │   ├── mcp.py                  ← MCPToolTemplate
│   │   ├── agent.py                ← A2AAgentTemplate
│   │   ├── decorators.py           ← @mcp_tool, @a2a_agent (Phase 2)
│   │   └── skill_mixin.py          ← ToolWithSkill mixin (Phase 1.5)
│   ├── skill_bridge.py             ← NEW (Phase 1.5): tool ↔ skill
│   ├── discovery_api.py            ← NEW (Phase 1.6): query & search
│   ├── loaders.py                  ← NEW (Phase 3): YAML loader
│   ├── registry.py                 ← NEW (Phase 2): Registry
│   ├── tool_discovery.py           ← ENHANCE (Phase 1.6): add search
│   ├── tool_schema.yaml            ← NEW (Phase 3): YAML schema
│   └── ...
│
├── sdk/                            ← NEW (Phase 5a - Optional)
│   ├── adapters/
│   │   ├── claude_adapter.py
│   │   ├── cline_adapter.py
│   │   └── fastapi_adapter.py
│   └── ...
│
└── monitoring/                     ← NEW (Phase 5b - Optional)
    ├── plugins/
    │   ├── __init__.py
    │   ├── wandb_plugin.py         ← Opt-in W&B
    │   ├── prometheus_plugin.py    ← Opt-in Prometheus
    │   └── grafana_plugin.py       ← Opt-in Grafana
    ├── base.py
    └── ...

ROOT FILES (Phase 0):
├── pyproject.toml                  ← CLEAN: only core deps
├── CONTRIBUTING.md                 ← REWRITTEN: package-first
└── .changelog/
    └── template.md

docs/ (Phase 0):
├── for-package-users/              ← NEW
│   ├── quickstart.md
│   ├── registering-tools.md
│   ├── discovering-tools.md
│   ├── extending.md
│   └── faq.md
├── for-contributors/               ← NEW
│   ├── development.md
│   ├── architecture.md
│   ├── plugins.md
│   └── testing.md
└── how-it-works/                   ← Existing (phases 1+)
    └── ...

examples/ (Phase 0+):
├── 23-adding-new-tools/            ← Existing (Phase 4)
└── community-plugin-template/      ← NEW (Phase 0)
    ├── README.md
    ├── setup.py
    └── example_plugin/
        ├── __init__.py
        └── tools.py
```

examples/
├── 23-adding-new-tools/            ← ENHANCED
│   ├── add_new_tools.py            ← Show all 3 approaches
│   ├── tools.yaml                  ← NEW: YAML examples
│   ├── README.md                   ← "Three Ways" section
│   └── ...

docs/
├── how-it-works/
│   ├── tool-templates/             ← NEW
│   │   ├── README.md
│   │   ├── TEMPLATES.md
│   │   ├── DECORATORS.md
│   │   └── YAML.md
│   └── ...
└── ...
```

---

## 📅 Timeline Estimate

- **Phase 0**: 1-2 days (package foundation, sets up everything else)
- **Phase 1**: 1-2 days (templates, builds on Phase 0)
- **Phase 1.5**: 0.5 day (skill bridge integration)
- **Phase 1.6**: 0.5 day (discovery & querying APIs)
- **Phase 2**: 1 day (decorators, builds on Phase 1)
- **Phase 3**: 1-2 days (YAML + integration)
- **Phase 4**: 0.5 day (update examples with all approaches)
- **Phase 5**: As-needed (community-driven, optional)
  - 5a (UI Adapters): 1-2 days per adapter
  - 5b (Monitoring Plugins): 1 day per plugin

**With Package Foundation (Phases 0-4): 6-8 days**
**With Examples & Documentation: 6.5-9 days**
**With Optional Plugins: Add 1-2 days per plugin**

---

## 🚀 Next Steps

1. Review this plan with team
2. Decide if all phases or subset
3. Start Phase 1 when ready
4. Update this doc as we progress

---

## 📝 Tracking Updates

### Completed
- [x] Created implementation plan
- [x] Added Phase 0 detailed tasks
- [x] Created PACKAGE_VS_FRAMEWORK_DECISION.md
- [x] Defined quality standards (testing, docs, contributor guidelines)
- [x] Phase 0.a: pyproject cleaned with minimal core deps and structured extras
- [x] Phase 0.c: Environment-based configuration module (`orchestrator/config.py`)
- [x] Phase 0.d: Optional dependency error helpers (`orchestrator/_internal/errors.py`)
- [x] Phase 0.e: Plugin registry scaffold (`orchestrator/plugins/registry.py`)
- [x] Phase 0.l: Structured logging module (`orchestrator/_internal/logger.py`)
- [x] Phase 0.m: Validation module scaffold (`orchestrator/_internal/validation.py`)
- [x] Phase 0.f: CONTRIBUTING rewritten for package-first model
- [x] Phase 0.g: Docs split (package users vs contributors) and README links
- [x] Phase 0.h: Changelog template created
- [x] Phase 0.j: Community plugin template scaffolded
- [x] Added ToolDefinition/ToolParameter pydantic schemas
- [x] Phase 0.b: Legacy public surfaces moved behind `_internal` shim
- [x] Phase 0.i: CI workflow (matrix + public API smoke + lint/typecheck)
- [x] Code coverage upload (Codecov) and base config
- [x] Release workflow for tagged releases (PyPI)
- [x] External MCP adapter demo (Example 24) scaffolded and runnable
- [x] Runtime validation hooks for registration/calls

### In Progress - Phase 0 (Foundation)
- [x] **0.b**: Finalize public API exports and migrate remaining internals
  - [x] Removed placeholder stubs that were raising NotImplementedError
  - [x] Consolidated imports from all submodules (decorators, loaders, templates, skill_bridge, discovery, plugins)
  - [x] Cleaned up __all__ export list - now only exports implemented features
  - [x] Removed duplicates and legacy error classes placeholders
  - [x] Public API now mirrors actual implementation (Phase 1-3 complete)
- [ ] **0.i**: CI smoke for clean install + optional deps missing + `_internal` lint
- [x] **0.k.1-0.k.2**: Type hints foundation complete - Critical APIs done (decorators, loaders, templates, skill_bridge)
  - [x] Installed types-PyYAML and created mypy.ini with phase-based strictness
  - [x] Fixed Literal types in decorators.py, loaders.py, templates.py, skill_bridge.py
  - [x] Parametrized Callable types (Callable[..., Any]) across Phase 2-1.5 APIs
  - [x] All 20 decorator + loader tests passing with type hints
  - [x] mypy.ini configured for progressive typing approach
  - [ ] **0.k.3-0.k.5**: Complete remaining modules and add mypy gating to CI
- [ ] **0.m**: Threat model doc + sandboxing guidance + security section updates
- [ ] **0.n**: CI matrix + README support statements

### In Progress - Phase 2 (Decorators)
- [x] Implement `mcp_tool` and `a2a_agent` decorators with auto parameter extraction
- [x] Wire specialized decorators into public exports and tests (4 tests passing)
- [ ] Add registry validation/deduplication/domain detection (registry.py)
- [ ] Decorator validation warnings (missing docstrings, type hints)

### Completed - Phase 3 (YAML Loader)
- [x] Implement YAML tool loader with schema validation (loaders.py)
- [x] Create tool-schema.yaml with full specification
- [x] Support worker function resolution (colon/dot separators)
- [x] Batch loading from directories
- [x] 16 comprehensive tests passing

### Completed - Phase 4 (Enhanced Examples)
- [x] Create three-ways example showing all registration methods
- [x] Template class approach (verbose, full control)
- [x] Decorator approach (fast, auto param extraction)
- [x] YAML approach (config-driven, DevOps-friendly)
- [x] All methods work together seamlessly

---

## 💭 Notes

### Phase 0: Foundation First
- **No legacy baggage**: Clean break now = clean codebase forever
- **Public vs Internal**: Clear `orchestrator.*` for users, `_internal` for impl
- **Package-first from day 1**: Users install & use, never modify source
- **Clean dependency story**: Core has zero optional deps, everything graceful
- **Plugin ecosystem ready**: 3rd parties can extend without touching source

### Phases 1-4: Core Capabilities
- **No feature bloat**: Core never depends on W&B, Prometheus, Grafana, UIs
- **Opt-in philosophy**: Everything is explicit enable, not implicit
- **UI-agnostic**: Library works standalone; adapters optional (Phase 5a)
- **Extensible**: Contributors add via PR, not via modifying source
- **Skill integration**: Tools ↔ skills bridge (Phase 1.5)
- **Discovery built-in**: Phase 1.6 gives full introspection
- **Multiple registration paths**: Templates (Phase 1), decorators (Phase 2), YAML (Phase 3)

### Phases 5a/5b: Extensions (Not Core)
- **Completely optional**: Core works perfectly without them
- **Community-driven**: Users/contributors add as needed
- **Plugin registry pattern**: 3rd-party packages register without modifying ToolWeaver

### Breaking Changes (OK)
- Not public yet → clean break now is better than tech debt later
- No deprecation cycles needed
- No migration guides required
- Just document in changelog what changed

### Success = Clean Package
- ✅ Users understand: `pip install toolweaver` + use decorators
- ✅ Contributors understand: PR to add core features
- ✅ Plugin authors understand: Register via plugin system
- ✅ No source code modification expected by anyone
- ✅ Public API is small, clear, stable
- ✅ Internal stuff is hidden and can change freely

---

## 🚀 Phase 0: Implementation Readiness

### Before Starting Phase 1, Ensure Phase 0 Complete:

1. **Can fresh install work?**
   - [ ] `pip install -e . --no-deps` succeeds
   - [ ] `from orchestrator import mcp_tool` works
   - [ ] No import errors for core features

2. **Is public API clear?**
   - [ ] `orchestrator.__all__` lists everything users need
   - [ ] Try `from orchestrator import *` → only safe things imported
   - [ ] Run: `grep -r "from orchestrator._internal" examples/` → zero results

3. **Are optional deps optional?**
   - [ ] Uninstall wandb/prometheus → code still runs (or clear error if explicitly used)
   - [ ] Decorators work without optional deps
   - [ ] Error message helps user know what to install

4. **Is configuration clear?**
   - [ ] No config files committed to repo
   - [ ] All config via env vars (documented in README)
   - [ ] Example: `TOOLWEAVER_SKILL_PATH=~/.my-skills` works

5. **Does plugin registry work?**
   - [ ] Example plugin package can register tools
   - [ ] No source code modification needed
   - [ ] Plugin loads on import automatically

6. **Is documentation split?**
   - [ ] docs/for-package-users/ exists and is standalone
   - [ ] README.md points package users here
   - [ ] docs/for-contributors/ exists
   - [ ] CONTRIBUTING.md rewritten for package-first mindset

### Why Phase 0 First?
All phases 1-5 assume Phase 0 is done. If Phase 0 is incomplete:
- Users get confused about where to put code
- Contributors modify source instead of using decorators
- Optional dependencies cause mysterious breakage
- Documentation sends users in circles

**Phase 0 unblocks everything else.**

---

## 🧪 Testing Standards (Across All Phases)

**Coverage & Quality**:
- [ ] Minimum test coverage: 80% of code
- [ ] All public APIs have tests
- [ ] Edge cases and error paths tested
- [ ] Integration tests for tool execution

**Platform & Version Testing**:
- [ ] CI tests on Python 3.10, 3.11, 3.12, 3.13
- [ ] CI tests on Windows, Linux, macOS
- [ ] Test optional dependencies gracefully missing
- [ ] Test with multiple versions of key dependencies

**Test Organization**:
- [ ] Unit tests in `tests/` parallel to `orchestrator/`
- [ ] Integration tests in `tests/integration/`
- [ ] Example tests in each `examples/` folder
- [ ] Performance regression tests for critical paths

**Test Maintenance**:
- [ ] Tests pass on every commit
- [ ] No flaky tests (all deterministic)
- [ ] Tests are fast (suite runs in < 2 minutes)
- [ ] Clear test names indicating what's tested

---

## 📚 Documentation Standards (Across All Phases)

**Code Documentation**:
- [ ] All functions/classes have docstrings
- [ ] Docstring format: Google style or NumPy style (pick one)
- [ ] Include examples in docstrings for public APIs
- [ ] Type hints in all function signatures

**User Documentation**:
- [ ] `docs/for-package-users/` guides
  - [ ] quickstart.md - 5 minutes to first tool
  - [ ] registering-tools.md - all 3 registration methods
  - [ ] discovering-tools.md - querying available tools
  - [ ] extending.md - creating your own package with ToolWeaver
  - [ ] faq.md - common questions
  - [ ] troubleshooting.md - debugging issues

**Developer Documentation**:
- [ ] `docs/for-contributors/` guides
  - [ ] development.md - setup & local testing
  - [ ] architecture.md - system design
  - [ ] plugins.md - plugin registry system
  - [ ] testing.md - testing strategy
  - [ ] security.md - security considerations

**API Documentation**:
- [ ] Auto-generate from docstrings (e.g., with Sphinx)
- [ ] Link examples to API docs
- [ ] Document error codes/exceptions
- [ ] Deprecation notices in API docs (if any)

**README Standards**:
- [ ] Main README.md has section links
- [ ] Links to for-package-users/ for most people
- [ ] Links to for-contributors/ for developers
- [ ] Installation instructions
- [ ] Link to examples

---

## 📦 Release & Versioning Strategy

**Semantic Versioning**:
- [ ] MAJOR.MINOR.PATCH version numbers
- [ ] MAJOR: Breaking changes (rare)
- [ ] MINOR: New features (backward compatible)
- [ ] PATCH: Bug fixes (backward compatible)

**Release Frequency**:
- [ ] Aim for quarterly releases (or as-needed)
- [ ] Security fixes released ASAP
- [ ] Document release process

**Version Compatibility Matrix**:
- [ ] Document: which tool versions work with which package versions
- [ ] Example: "ToolWeaver 1.5 works with tool schema v2"

**Breaking Change Policy** (Since we're early):
- [ ] Can break anything now (not public yet)
- [ ] Document breaking changes clearly in CHANGELOG
- [ ] No deprecation cycles needed until 1.0+
- [ ] After 1.0: use semver strictly

**Changelog Format**:
- [ ] Template in `.changelog/template.md`
- [ ] Sections: New / Changed / Fixed / Breaking
- [ ] Link to issues/PRs
- [ ] Link to migration guides if breaking

---

## 📢 Communication & Contributor Guide

**CONTRIBUTING.md Standards**:
- [ ] Welcome message (this is a package, not a framework to modify)
- [ ] How to report issues (GitHub issues template)
- [ ] How to request features (GitHub discussions or issues)
- [ ] Development setup (how to clone and set up venv)
- [ ] Testing requirements (coverage, linting)
- [ ] Code style (black, isort, mypy)
- [ ] PR process (link to CODEOWNERS, review process)
- [ ] Commit message format
- [ ] Link to security.md for security issues

**Development Setup Documentation**:
- [ ] `git clone` repo
- [ ] Create venv: `python -m venv .venv`
- [ ] Install dev: `pip install -e '.[dev]'`
- [ ] Run tests: `pytest`
- [ ] Run type check: `mypy orchestrator/`
- [ ] Format code: `black orchestrator/`

**Code Style Standards**:
- [ ] Use Black for formatting
- [ ] Use isort for import sorting
- [ ] Use mypy for type checking (strict mode)
- [ ] Use pylint or flake8 for linting
- [ ] Pre-commit hooks configured

**Issue & PR Templates**:
- [ ] GitHub issue template for bug reports
- [ ] GitHub issue template for feature requests
- [ ] GitHub PR template with checklist
  - [ ] Tests pass
  - [ ] Documentation updated
  - [ ] CHANGELOG entry added
  - [ ] Backward compatible (or breaking change noted)

---

## ✅ Phase Readiness Checklist

| Item | Phase 0 | Phase 1+ |
|------|---------|---------|
| Type hints | ✅ Required | ✅ Required |
| Logging | ✅ Built-in | ✅ Used |
| Error types | ⚠️ Framework | ✅ Used |
| Diagnostics | ⚠️ Framework | ✅ Used |
| Tests 80%+ | ✅ Required | ✅ Required |
| Docstrings | ✅ Required | ✅ Required |
| Examples pass | ⚠️ Phase 4 | ✅ Phase 4+ |
| Docs complete | ✅ Required | ✅ Required |
| CONTRIBUTING updated | ✅ Required | ⚠️ As needed |
| CHANGELOG entry | ⚠️ Phase 0 | ✅ Every phase |

