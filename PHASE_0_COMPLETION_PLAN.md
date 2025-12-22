# Phase 0 Completion Plan: Remaining Work

**Status**: December 22, 2025  
**Target**: Complete all Phase 0 critical items  
**Estimated Effort**: 2-3 days

---

## 📋 Work Breakdown

### Task 1: Audit & Plan Internal Migration
**Duration**: 1-2 hours  
**Goal**: Understand what should be public vs internal

**Current Structure Analysis**:
```
Public (exported from orchestrator/__init__.py):
- tools.decorators (mcp_tool, a2a_agent, tool) ✅
- tools.templates (BaseTemplate, FunctionToolTemplate, etc.) ✅
- tools.discovery_api (search_tools, get_available_tools, etc.) ✅
- tools.loaders (load_tools_from_yaml, etc.) ✅
- tools.skill_bridge (save_tool_as_skill, etc.) ✅
- plugins (register_plugin, etc.) ✅
- config (get_config, etc.) ✅
- logging (get_logger, etc.) ✅

Should Remain Internal:
- orchestrator/execution/* (except WorkspaceManager, Skill classes)
- orchestrator/dispatch/* (hybrid_dispatcher, workers, etc.)
- orchestrator/observability/* (monitoring backends)
- orchestrator/infra/* (redis_cache, mcp_client, etc.)
- orchestrator/assessment/* (evaluation)
- orchestrator/planning/* (planner)
- orchestrator/runtime/* (orchestrator)
- orchestrator/workflows/* (workflow engine)
- orchestrator/shared/* (models, validation - except what's public)
```

**Plan**:
- [ ] Create orchestrator/_internal/__init__.py if not exists
- [ ] Move internal modules: execution, dispatch, observability, infra, assessment, planning, runtime, workflows
- [ ] Update imports in __init__.py to expose only public APIs
- [ ] Update internal imports to use `from orchestrator._internal import ...`

---

### Task 2: Fix Mypy Type Errors (281 remaining)
**Duration**: 1-2 sessions  
**Goal**: Get all non-critical modules type-clean

**Strategy**:
1. Focus on modules imported by public API
2. Fix highest-impact errors first (see NOT_YET_COMPLETED.md)
3. Use `# type: ignore` sparingly for genuinely unfixable cases

**Key Files to Fix**:
- orchestrator/execution/*.py (except workspace.py which is done)
- orchestrator/observability/*.py (31 errors)
- orchestrator/infra/redis_cache.py (24 errors)
- orchestrator/workflows/*.py (23 errors)
- orchestrator/planning/*.py (20 errors)

**Target**: All critical modules 0 errors, standard modules <10 errors each

---

### Task 3: Add CI Lint for _internal
**Duration**: 2-3 hours  
**Goal**: Prevent accidental public code importing internals

**Implementation**:
- Add GitHub Actions job to check:
  - No `from orchestrator._internal import` in examples/
  - No `from orchestrator._internal import` in public tests
  - All examples use only public API
  - orchestrator/__all__ matches actual exports

**Files**:
- Update .github/workflows/type-check.yml or create new lint-internal.yml

---

### Task 4: Expand Logging Usage
**Duration**: 2-3 hours  
**Goal**: Make debugging easier with structured logs

**Strategy**:
- Add logging to major execution paths
- Log tool registration, execution, errors
- Use TOOLWEAVER_LOG_LEVEL env var to control verbosity

**Key Areas**:
- Tool registration (decorators.py, loaders.py)
- Tool discovery (discovery_api.py)
- Tool execution (execution/*.py)
- Workspace operations (workspace.py)
- Skill operations (skill_bridge.py)

---

### Task 5: Full Clean Install Smoke Test
**Duration**: 1-2 hours  
**Goal**: Validate fresh install works end-to-end

**CI Job Implementation**:
```yaml
clean-install-smoke:
  runs-on: ubuntu-latest
  steps:
    - pip install -e . --no-deps
    - python -c "from orchestrator import mcp_tool"
    - python -c "from orchestrator import search_tools"
    - python -c "from orchestrator import load_tools_from_yaml"
    - python -c "from orchestrator import get_config"
    - # Run minimal end-to-end test
```

---

### Task 6 (PHASE 2): Decorator Validation
**Duration**: 1 day  
**Goal**: Catch user mistakes at registration time

**Implementation**:
- Add checks in decorators.py when @mcp_tool/@a2a_agent runs
- Warn on missing docstring
- Warn on missing type hints
- Warn on non-async without reason
- Fail on invalid parameter names

**Testing**: Add test_decorator_validation.py with comprehensive warning tests

---

### Task 7 (PHASE 2): Registry Formalization
**Duration**: 1 day  
**Goal**: Centralize tool registration logic

**Implementation**:
- Finalize orchestrator/tools/registry.py
- Add validation on registration
- Add deduplication checks
- Auto-detect domain from tool metadata
- Integration with discovery API

**Testing**: Add test_registry.py with validation tests

---

## 🚀 Execution Order

**Session 1** (2-3 hours):
1. ✅ Task 1: Audit & plan internal migration
2. ✅ Task 3: Add CI lint for _internal

**Session 2** (2-3 hours):
3. ✅ Task 5: Full clean install smoke test
4. ✅ Task 4: Expand logging usage

**Session 3** (3-4 hours):
5. ⏳ Task 2: Fix mypy errors (281 → 0)

**Session 4** (1-2 hours):
6. ✅ Task 6: Decorator validation
7. ✅ Task 7: Registry formalization

**Total: 2-3 days to completion**

---

## ✅ Success Criteria

- [ ] All Phase 0 tasks completed
- [ ] orchestrator/__all__ is comprehensive and accurate
- [ ] Examples only use public API
- [ ] CI has _internal import lint check
- [ ] Clean install test passes
- [ ] Mypy errors < 50 (focused on non-critical modules only)
- [ ] All tests pass (37+ tests)
- [ ] No breaking changes to public API

---

## 📝 Tracking

See master todo list in manage_todo_list for progress tracking.
