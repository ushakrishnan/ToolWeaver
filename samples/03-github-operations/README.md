# Example 03: GitHub Operations with ToolWeaver

Showcase how ToolWeaver enables **LLM-driven orchestration**: just like Claude or Copilot, an LLM takes a user request, discovers available tools, decides which ones to use, and generates a multi-step execution plan.

## The Real Problem We Solve

You have a user request: *"List the top 5 repos in my org, search for Python repos, and give me statistics."*

When you ask Claude or Copilot this, **it figures out what to do**. It doesn't ask you "should I call function A or B?" It introspects, plans, and executes.

**Without ToolWeaver, building this yourself:**
```python
# You manually hardcode the steps:
repos = list_repositories(org)
py_repos = search_by_language("Python", org)
stats = analyze_stats([repos, py_repos])
# If user asks a different question, you write new code
# You're essentially building Claude yourself, manually
```
❌ **Brittle. Inflexible. You're rebuilding Claude for every use case.**

**With ToolWeaver (Claude/Copilot pattern):**
```python
# Tools self-register
@mcp_tool(domain="github")
async def list_repositories(org: str): ...

@mcp_tool(domain="github")
async def search_repositories_by_language(language: str): ...

@mcp_tool(domain="github")
async def analyze_repository_stats(repos: list): ...

# User asks. LLM (like Claude) generates the plan.
user_request = "List top 5 repos, search Python repos, give stats"
plan = await planner.generate_plan(
    user_request=user_request,
    available_tools=search_tools(domain="github")
)
# LLM figures out:
# Step 1: list_repositories(org=my-org, limit=5)
# Step 2: search_repositories_by_language(language=Python, org=my-org)
# Step 3: analyze_repository_stats(repos=from_step_1)

results = await execute_plan(plan)
```
✅ **This is the Claude pattern: tools + user request → LLM plans & executes.**

User asks a different question? LLM re-plans. Add 10 new tools? LLM uses them. **You've delegated workflow design to the LLM.**

## What This Sample Does

1. **Registers 4 GitHub tools** with `@mcp_tool`
2. **User makes a request** (e.g., "List top 5 repos, search Python")
3. **LLM discovers available tools** (yes, like MCP does)
4. **LLM GENERATES A MULTI-STEP PLAN** (this is the magic)
   - Breaks down user request into tool calls
   - Orders them correctly
   - Passes outputs between steps
5. **Executes the plan** with results saved to JSON

## Why This Matters

When you use Claude or Copilot, you describe what you want. They figure out what tools to call. ToolWeaver lets **you build systems that work the same way**.

| Aspect | Hardcoded Workflows | MCP Only | ToolWeaver (Claude Pattern) |
|--------|-------------------|----------|--------------------------|
| **Tool availability** | Manual list | Automatic (MCP) | Automatic (MCP) |
| **User request handling** | New code per request | Tools exist but you orchestrate | **LLM orchestrates (like Claude)** |
| **Multi-step workflows** | Hardcoded sequences | No support | **LLM builds them dynamically** |
| **User says "do this"** | You write code | You write code | **LLM figures it out** |
| **Adapts to new tools** | Rewrite code | MCP updates, but you write code | **LLM uses them immediately** |
| **Example:** "List repos and stats" | `repos = list(); stats = analyze(repos)` (hardcoded) | Tools available, but you write that code | `"List repos and stats" → LLM plans → Execute` |

**The pattern:** Tools register → LLM sees them → user makes request → LLM plans & executes. **This is what makes Claude/Copilot magical. ToolWeaver makes it easy for you to build.**

## Setup

1) Install and run
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Configure GitHub access
```bash
copy .env.example .env
# Edit .env: paste your GitHub token and owner
# GITHUB_TOKEN=ghp_xxxxx (create at https://github.com/settings/tokens)
# GITHUB_OWNER=your-org-or-username
```

3) Run
```bash
python github_ops.py
```

## What You'll See

**Console output:**
```
EXAMPLE 03: GitHub Operations with ToolWeaver

Target: your-org | API: https://api.github.com

Step 1: Discovering GitHub tools...
   Found 4 tools:
      - list_repositories
      - get_repository_info
      - search_repositories_by_language
      - analyze_repository_stats

Step 2: User request:
   List the top 5 repositories in your-org, then search Python repos...

Step 3: LLM generates execution plan...
   [LLM ANALYZES REQUEST & DISCOVERED TOOLS]
   Plan: 3 steps
      1. list_repositories(org="your-org", limit=5)
      2. search_repositories_by_language(language="Python", org="your-org")
      3. analyze_repository_stats(repos=[results_from_step_1])

Step 4: Executing plan...
   [OK] Plan executed successfully (3 tool calls)
```

**Output folder** (`execution_outputs/`):
- `plan_*.json` – **LLM-generated execution plan** (the key artifact)
- `results_*.json` – tool execution results
- `manifest.json` – execution history

## How It Differs from Sample 02

| Sample 02 | Sample 03 |
|-----------|-----------|
| **Fixed workflow** (OCR → parse → categorize) | **Dynamic workflow** (LLM builds it) |
| **User input:** receipt image | **User input:** natural language request |
| **Demo:** tool chaining + execution | **Demo:** LLM planning + orchestration + execution |

Sample 02 shows: *"How do we execute a fixed tool chain efficiently?"*

Sample 03 shows: *"How do we let users describe what they want, and have an LLM orchestrate tools to deliver it?"*

## Code Walkthrough

**Step 1: Tools self-register**
```python
@mcp_tool(domain="github", description="List repositories for an organization")
async def list_repositories(org: str, limit: int = 10) -> dict:
    ...

@mcp_tool(domain="github", description="Get repository details and statistics")
async def get_repository_info(org: str, repo: str) -> dict:
    ...

# Add 50 more tools? Just add @mcp_tool decorators.
```

**Step 2: User makes a request**
```python
user_request = (
    "List the top 5 repositories in ushakrishnan, "
    "then search for Python repositories and provide statistics."
)
```

**Step 3: LLM discovers tools & generates plan**
```python
github_tools = search_tools(domain="github")  # Like MCP
plan = await planner.generate_plan(  # THIS is the magic
    user_request=user_request,
    available_tools=github_tools,
)
# plan now has: ["list_repositories", "search_repositories_by_language", "analyze_repository_stats"]
# LLM figured out which tools, in what order, passing outputs between them
```

**Step 4: Execute the plan**
```python
results = await execute_plan(plan)
# Results saved to JSON for audit trail & integration
```

## Key Insight

**What Claude/Copilot do:**
- You describe a task
- They introspect available tools
- They plan what to call
- They execute
- They return results

**What this sample shows:**
- Tools register via `@mcp_tool`
- User makes a request
- LLM (gpt-4o) introspects available tools
- LLM generates a multi-step plan
- System executes the plan
- Results are logged

**This is how you build AI systems that think like Claude/Copilot.** You provide tools. You describe what you want. The LLM handles the rest.

MCP is the protocol. ToolWeaver is the orchestration engine that makes this pattern easy to build and scale.
