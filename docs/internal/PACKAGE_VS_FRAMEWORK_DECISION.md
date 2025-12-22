# Architecture Decision: Package vs Framework

**Decision**: ToolWeaver is a **PACKAGE**, not a **FRAMEWORK**  
**Date**: December 19, 2025  
**Status**: Final  
**Impact**: Shapes all phases of implementation plan

---

## 🎯 Executive Summary

ToolWeaver will be a lightweight, composable **package** that integrates into any architecture, not a framework that dictates application structure. This decision enables:
- ✅ Integration with existing codebases (FastAPI, Celery, etc.)
- ✅ Multiple execution contexts (LLM, CLI, async, sync)
- ✅ Independent skill library
- ✅ Community adoption (especially open source)
- ✅ Flexibility for diverse use cases

---

## 📖 Definitions

### Package Approach
A package is a **library you import and use** within your own application architecture.

```python
# User controls everything
from orchestrator import mcp_tool, search_tools

@mcp_tool(domain="finance")
async def get_balance(account_id: str) -> dict:
    return {"balance": 1000}

# In user's own FastAPI app, async script, or CLI
async def my_workflow():
    tools = search_tools(domain="finance")
    balance = await get_balance("123")
    return balance
```

**Characteristics**:
- User installs: `pip install toolweaver`
- User owns the application architecture
- ToolWeaver is **part of** the user's app
- User decides: how to call tools, when to call them, what to do with results
- User is the orchestrator

### Framework Approach
A framework is a **system that controls your application**.

```python
# Framework controls flow
from toolweaver_framework import BaseWorkflow

class MyWorkflow(BaseWorkflow):
    @define_tool(domain="finance")
    async def get_balance(self, account_id: str) -> dict:
        return {"balance": 1000}

# Framework runs it
workflow = MyWorkflow()
result = workflow.run()  # Framework decides execution
```

**Characteristics**:
- User installs: `pip install toolweaver-framework`
- Framework owns the application architecture
- Framework is the **heart** of the user's app
- Framework decides: how to call tools, when to call them, what to do with results
- Framework is the orchestrator

---

## 📊 Comparison Matrix

| Dimension | **Package** | **Framework** | Winner |
|-----------|-----------|--------------|--------|
| **User Control** | High (they decide) | Low (framework decides) | Package ✅ |
| **Flexibility** | Very high (use how you want) | Low (do it framework's way) | Package ✅ |
| **Learning Curve** | Shallow (just Python) | Steep (learn framework concepts) | Package ✅ |
| **Time to First Tool** | 5 minutes | 20+ minutes | Package ✅ |
| **Integration with Existing Code** | Easy (just import) | Hard (must refactor) | Package ✅ |
| **Multiple Tools Per App** | Natural | Depends on design | Package ✅ |
| **Mix with Other Libraries** | Easy (FastAPI, Celery, etc.) | Limited | Package ✅ |
| **Testing** | Standard Python testing | Framework-specific | Package ✅ |
| **Deployment Options** | Infinite (your app) | Limited (framework expectations) | Package ✅ |
| **Breaking Changes** | Low pain (you control updates) | High pain (breaks your app) | Package ✅ |
| **Community Packages** | Thriving ecosystem | Limited (must fit framework) | Package ✅ |
| **Opinionated Defaults** | Few opinions (user chooses) | Many (enforced) | Framework ✅ |
| **Batteries Included** | No (you assemble) | Yes (all included) | Framework ✅ |
| **Prevent User Mistakes** | Limited | Strong enforcement | Framework ✅ |

---

## ✅ When to Choose PACKAGE

### 1. You Have Existing Code
**Scenario**: "We have a FastAPI app, we want to add tools to it"

```python
# Package approach (ToolWeaver)
from fastapi import FastAPI
from orchestrator import mcp_tool

app = FastAPI()

@mcp_tool(domain="finance")
async def get_balance(account_id: str) -> dict:
    return {"balance": 1000}

@app.get("/workflow")
async def workflow():
    # Your app, your architecture
    balance = await get_balance("123")
    return {"result": balance}
```

✅ Package: Works seamlessly with existing FastAPI
❌ Framework: Would require refactoring entire app

### 2. You Want Maximum Flexibility
**Scenario**: "Tools might go into FastAPI, Lambda, async worker, CLI, whatever"

```python
# Package approach (ToolWeaver)
from orchestrator import mcp_tool

@mcp_tool()
async def process_data(data: str) -> str:
    return data.upper()

# Can use in FastAPI
# Can use in async function
# Can use in CLI
# Can use in Lambda
# Can use in Celery task
# Can use in websocket handler
```

✅ Package: Same code works everywhere
❌ Framework: Each context needs wrapper/adapter

### 3. You Need to Mix and Match Libraries
**Scenario**: "We use Pydantic, SQLAlchemy, FastAPI, Celery, etc."

```python
# Package approach (ToolWeaver)
from orchestrator import mcp_tool
from sqlalchemy import Session
from pydantic import BaseModel

class Balance(BaseModel):
    account_id: str
    amount: float

@mcp_tool()
async def get_balance(account_id: str, db: Session) -> Balance:
    # Works with SQLAlchemy
    account = db.query(Account).get(account_id)
    return Balance(account_id=account_id, amount=account.balance)
```

✅ Package: Integrates with any library
❌ Framework: Framework-specific replacements required

### 4. You Want to Build a Library of Tools
**Scenario**: "We're building reusable tools for our company"

```python
# Package approach (ToolWeaver)
# my_company_tools package
from orchestrator import mcp_tool

@mcp_tool(domain="hr", tags=["employee"])
async def get_employee_info(employee_id: str) -> dict:
    return {...}

# Installation: pip install my-company-tools
# Usage: Anyone in the company can use these tools
```

✅ Package: Anyone can `pip install` and use
❌ Framework: Requires everyone use framework

### 5. You Might Open Source It
**Scenario**: "We might publish ToolWeaver to PyPI"

✅ Package: Community loves packages, easy adoption
❌ Framework: Community avoids frameworks (too opinionated, lock-in)

### 6. You Have Multiple Teams with Different Stacks
**Scenario**: "Team A uses FastAPI, Team B uses Django, Team C uses async scripts"

```python
# Package approach (ToolWeaver)
# Single tool library works for all teams:
# Team A: FastAPI integration
# Team B: Django integration
# Team C: Async scripts
# All use same tools
```

✅ Package: One library, all teams happy
❌ Framework: Each team needs separate implementation

---

## ❌ When to Choose FRAMEWORK

### 1. You're Building a Monolithic Application
**Use Case**: Single app, tight integration, one team, no external dependencies

**Framework**: Everything opinionated, enforced, no decisions needed
**Package**: Too much freedom, analysis paralysis

### 2. You Want "Batteries Included"
**Use Case**: Workflow engine, scheduling, monitoring, UI all built-in

**Framework**: All included out of box ✅
**Package**: You assemble pieces yourself ⚠️

### 3. You Need Specific Execution Model
**Use Case**: "Tools must run in exact order, with circuit breakers, retries, etc."

**Framework**: Can enforce guarantees ✅
**Package**: Users might forget ⚠️

### 4. You Want to Prevent User Mistakes
**Use Case**: "Users must use error types, logging, validation—no way around it"

**Framework**: Hard to misuse (forced by structure) ✅
**Package**: User can misuse (their responsibility) ⚠️

### 5. You Have Simple, Unified Use Case
**Use Case**: All execution via single orchestrator, same patterns, no external integration

**Framework**: Clear path, less confusion ✅
**Package**: Multiple paths might confuse ⚠️

---

## 🚨 The Good, Bad & Ugly

### PACKAGE Approach

#### Good ✅
- ✅ Users keep control of architecture
- ✅ Works with **any** other library (FastAPI, Celery, etc.)
- ✅ Easy to integrate into existing code
- ✅ Clear responsibility split (we handle tools, you orchestrate)
- ✅ Can be used in infinite ways (LLM, CLI, API, worker, etc.)
- ✅ Easy to test (no magic lifecycle, just functions)
- ✅ Easy to deploy (just Python code in your app)
- ✅ Easy to debug (no hidden execution model)
- ✅ Great for open source (community adoption)

#### Bad ⚠️
- ⚠️ Users must make architectural decisions
- ⚠️ Multiple ways to do things = decision paralysis
- ⚠️ Users **can** misuse it (their responsibility)
- ⚠️ No enforcement of best practices
- ⚠️ More documentation needed (multiple paths)
- ⚠️ Users might write inefficient code
- ⚠️ No "one right way" = confusion for some

#### Ugly 🔴
- 🔴 If user misunderstands tool lifecycle → breaks
- 🔴 If user doesn't use error types → confusing errors
- 🔴 If user doesn't structure logging → hard to debug
- 🔴 Decorators can feel "magical" to new users
- 🔴 Type hints errors unclear to beginners
- 🔴 User responsible for validation (can forget)

---

### FRAMEWORK Approach

#### Good ✅
- ✅ One way to do things = clear, unambiguous
- ✅ Framework handles lifecycle = fewer bugs (framework bugs, not user bugs)
- ✅ Enforcement = can't misuse (good patterns enforced)
- ✅ Simpler mental model (follow the pattern)
- ✅ Built-in best practices (users get them automatically)
- ✅ Batteries included (everything you need)
- ✅ Specific performance guarantees (execution model defined)

#### Bad ⚠️
- ⚠️ Locks users into framework patterns
- ⚠️ Hard to use with existing code (must refactor)
- ⚠️ Breaking changes = major pain (user's app breaks)
- ⚠️ Opinionated = some users disagree with opinions
- ⚠️ Heavy abstraction = harder to debug when it breaks
- ⚠️ Scaling to new contexts requires framework changes
- ⚠️ Limited integration options (framework's way or highway)

#### Ugly 🔴
- 🔴 Users forced to use framework's error handling (not their choice)
- 🔴 Users forced to use framework's logging (not their choice)
- 🔴 Users can't use it with their existing CLI/API (refactor required)
- 🔴 New execution context = framework rewrite
- 🔴 Community forks because they want flexibility
- 🔴 Breaking changes cause ripple effects (dependency hell)
- 🔴 Hard to contribute (framework maintainers gatekeep)

---

## 🎯 Why ToolWeaver Chose PACKAGE

### 1. Claude/Opus is the Orchestrator
**Not ToolWeaver**

```python
# ToolWeaver doesn't orchestrate—Claude does
# You register tools:
@mcp_tool()
async def get_balance(account: str) -> dict:
    return {...}

# Claude orchestrates:
# Claude: "I see a get_balance tool. Should I call it?"
# You: "Yes, Claude, call it"
# Claude: "OK, I'll call it and see the result"
# You: "Great, now what, Claude?"
```

✅ Package fits: "Here are tools Claude can use"
❌ Framework fits: "Build your app around ToolWeaver" (wrong model!)

### 2. Tools in Different Contexts
**Same tool, many execution paths**

```python
# Same tool code:
@mcp_tool(domain="finance")
async def get_balance(account: str) -> dict:
    return {"balance": 1000}

# Used in:
# 1. Claude API (LLM calls it)
# 2. Your FastAPI endpoint
# 3. Your CLI command
# 4. Your async worker
# 5. Your Lambda function
# 6. Your test suite
```

✅ Package: One registration, works everywhere
❌ Framework: Each context needs framework wrapper

### 3. Skill Library Independence
**Skills are reusable code, not bound to framework**

```python
# Skills are independent
from orchestrator.execution.skill_library import get_skill

skill = get_skill("calculate_discount", version="1.0")
# Can use skill:
# - From a tool
# - From a script
# - From a workflow
# - From anywhere

# NOT:
# - From framework-specific context only
```

✅ Package: Skills independent of execution context
❌ Framework: Skills tied to framework lifecycle

### 4. Multiple Tool Sources
**Tools come from many places, not just framework**

```python
# Tools registered from:
# - MCP servers (external, not framework-controlled)
# - Python functions (user code, not framework-controlled)
# - A2A agents (external, not framework-controlled)
# - YAML configs (devops, not framework-controlled)
# - Code execution (dynamic, not framework-controlled)
```

✅ Package: Registry handles all sources
❌ Framework: Would need to be aware of all sources

### 5. User Control is Essential
**Different teams, different needs, different stacks**

```python
# Team A: "We integrate with FastAPI"
# Team B: "We use Celery"
# Team C: "We use async/await directly"
# Team D: "We use it in Lambda"

# Package: Works for all ✅
# Framework: Forces one way ❌
```

---

## 🔄 Decision Framework (When in Doubt)

Ask these questions in order:

### Question 1: Does the user have existing code?
- **YES** → Use PACKAGE
- **NO** → Go to Question 2

### Question 2: Could this be used in multiple execution contexts?
- **YES** → Use PACKAGE
- **NO** → Go to Question 3

### Question 3: Might this integrate with other libraries?
- **YES** → Use PACKAGE
- **NO** → Go to Question 4

### Question 4: Is this the heart of the application?
- **YES** → Use FRAMEWORK
- **NO** → Use PACKAGE

**Result**: If user said YES to Q1, Q2, or Q3 → **PACKAGE**

---

## 📋 Decision Checklist

- [x] ToolWeaver is NOT the orchestrator (Claude is)
- [x] Tools are orthogonal to execution context
- [x] Skills must be independent of registration method
- [x] Multiple tool sources (MCP, Python, A2A, YAML, exec)
- [x] Multiple execution contexts (LLM, CLI, API, worker, Lambda)
- [x] Multiple teams with different stacks
- [x] Want to open source
- [x] User control is essential
- [x] Integration with existing code important

**Conclusion**: ✅ **PACKAGE is correct choice**

---

## 🎬 Implications for Implementation

### Phase 0: Package Infrastructure
- [x] Clean public API (`orchestrator.*`)
- [x] Hidden internals (`_internal`)
- [x] Optional dependencies graceful
- [x] No framework-specific lifecycle
- [x] User controls when/how to use

### Phase 1: Templates
- [x] Templates are reusable patterns, not enforced structure
- [x] Multiple template types supported
- [x] Users can create custom templates
- [x] Skills independent of template choice

### Phase 2: Decorators
- [x] Decorators are optional (templates exist too)
- [x] Multiple registration paths
- [x] User chooses what fits their app

### Phase 3: YAML
- [x] YAML is alternate registration (not primary)
- [x] For teams that prefer config over code
- [x] Still compatible with all template types

### Phase 4: Examples
- [x] Show integration with FastAPI
- [x] Show use in async scripts
- [x] Show use in CLI
- [x] Show use with Claude API
- [x] All from **same tool registration**

### Phase 5: Extensions
- [x] Optional (not required)
- [x] UI adapters for different contexts
- [x] Monitoring plugins (opt-in)
- [x] Core never depends on extensions

---

## ✨ Success Metric

**Package-first is successful when**:

Users can say:
> "We have a FastAPI app. We wanted to add tools that Claude can call. We imported ToolWeaver, used decorators, registered our tools, and now Claude can call them. No refactoring, no learning a new framework, just Python code."

If they had to learn a framework to do that → we failed at package-first.

---

## 📝 Revision History

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-12-19 | Initial decision | Evaluated package vs framework for ToolWeaver |

---

## 🔗 Related Documents

- [TEMPLATE_IMPLEMENTATION_PLAN.md](TEMPLATE_IMPLEMENTATION_PLAN.md) - Implementation phases
- [../how-it-works/programmatic-tool-calling/](../how-it-works/programmatic-tool-calling/) - Technical documentation
- [../../examples/23-adding-new-tools/README.md](../../examples/23-adding-new-tools/README.md) - Real example
