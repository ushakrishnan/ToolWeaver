# Programmatic Execution: Execute Complex Workflows at Once

## Problem: The LLM Round-Trip Tax

When orchestrating complex multi-step workflows with traditional tool calling, you face a fundamental tradeoff:

```
Scenario: Get team expenses and find budget overages

Traditional Approach (with parallel function calling):
  Round 1: "Get team members"
    → LLM calls get_team_members()
    → Result: 20 members (5KB)
    
  Round 2: "Get Q3 expenses for all members"
    → LLM calls get_expenses() [PARALLEL for all 20]
    → Result: 100 expense records (100KB)
    → LLM must now see and reason about 100+ records
    
  Round 3: "Find who exceeded budget"
    → LLM analyzes the 100 records in its context window
    → Returns result
    
Cost Breakdown:
  • 3 LLM API calls
  • ~100KB context (all expense data stays in LLM context)
  • ~2 seconds (3 round-trips)
  • $0.03 cost
  • ⚠️  LLM wasted tokens on data analysis instead of orchestration logic
```

The issue isn't just API calls—it's **context bloat**. The LLM receives all raw data and must reason through it, wasting tokens on manual analysis.

## Solution: Programmatic Execution

Let the LLM generate code ONCE that orchestrates everything:

```
Programmatic Approach:

1. LLM Call (single):
   "Given the tools: get_team_members, get_expenses, write Python code to:
    1. Get all team members
    2. Fetch their Q3 expenses (in parallel)
    3. Filter for those over $10k budget
    4. Return the list"
    
   LLM generates:
   ```python
   import asyncio
   
   team = await get_team_members()
   expenses = await asyncio.gather(*[
       get_expenses(m["id"], "Q3") for m in team
   ])
   
   exceeded = [
       m for m, exp in zip(team, expenses)
       if sum(e["amount"] for e in exp) > 10000
   ]
   
   return {"exceeded_count": len(exceeded), "list": exceeded}
   ```

2. Code Execution (in ToolWeaver sandbox):
   - Fetches all 20 members (parallel)
   - Calls get_expenses 20x (parallel in one batch)
   - Filters locally (NO context sent to LLM)
   - Returns only summary (2KB)

Cost Breakdown:
  • 1 LLM API call
  • ~2KB context (only final summary)
  • <1 second (all parallel)
  • $0.01 cost
  • ✅ LLM didn't see raw data—only generated orchestration logic
```

### Comparison

| Aspect | Traditional | Programmatic | Improvement |
|--------|-------------|--------------|-------------|
| **LLM API Calls** | 3 | 1 | **67% fewer** |
| **Context Size** | 100KB | 2KB | **98% smaller** |
| **Latency** | ~2 seconds | <1 second | **2x faster** |
| **Cost** | $0.03 | $0.01 | **67% savings** |
| **LLM Reasoning** | Over raw data | Over generated code | **Eliminated bloat** |
| **Scalability** | 1000 items = +1000KB | 1000 items = +0.02KB | **Linear cost** |

## Why It Matters

### 1. Context Efficiency
Traditional tool calling forces LLMs to see and reason about all intermediate data. This is expensive.

```
Traditional: LLM sees
  [20 team members] + [100 expense records] + "analyze this manually"
  → LLM tokens wasted on reading raw data

Programmatic: LLM generates code that does the filtering
  → LLM only sees summary result
  → Context stays minimal
```

### 2. Token Efficiency
LLM tokens are consumed by reasoning, not just input/output.
analyzing data, not just input/output.

```
Traditional: LLM must analyze
  100 expense records in context to find overages
  → Tokens spent on data analysis (could be done locally)

Programmatic: LLM generates code once
  Code performs all analysis locally in sandbox
  → LLM only generates orchestration logic (higher-value use of token
```

### 3. Scalability
Traditional approaches don't scale—more data = more expensive.

```
Processing 100 items:
  Traditional: +100KB context × 3 calls = expensive
  Programmatic: +0.1KB result × 1 call = cheap

Processing 1000 items:
  Traditional: +1000KB context × 3 calls = prohibitively expensive
  Programmatic: +1KB result × 1 call = same cost
```

## When to Use Programmatic Execution

✅ **Use programmatic execution when:**
- Processing batches of items (10+)
- Multi-step workflows with filtering/aggregation
- Parallel operations needed
- Intermediate data is large but final result is small
- Complex logic (loops, conditionals, transformations)

❌ **Avoid programmatic execution when:**
- Single simple tool call needed
- LLM must iterate based on results
- Complex reasoning needed on intermediate data

## Example: Batch Processing

**Scenario:** Process 500 leads through qualification workflow

```python
# Traditional: LLM needs to see/reason about all 500 leads
#  → 500 × "is this a qualified lead?" rounds
#  → 500KB+ context
#  → Very expensive

# Programmatic: LLM generates code that handles all leads
leads_code = """
import asyncio

leads = await get_leads(query="unqualified")
results = []

for lead in leads:
    score = await score_lead(lead)
    if score > 0.8:
        company = await get_company(lead.company_id)
        results.append({
            "lead": lead,
            "score": score,
            "company": company
        })

return results
"""

# LLM generates this code ONCE
# Code processes all 500 leads locally
# Only qualified leads (maybe 50) returned to LLM
# Cost: 1 LLM call vs 500
```

## Example: Multi-Step Workflow

**Scenario:** "Find the highest-paying job offer from tech companies"

```python
# Traditional: Multiple rounds
#  Round 1: LLM calls get_job_offers()
#  Round 2-N: LLM analyzes each offer, queries company details
#  Result: expensive round-trip dance

# Programmatic: Generate code ONCE
code = """
import asyncio, json

# Get all offers
offers = await get_job_offers()

# Get company details for all (parallel)
company_tasks = [get_company_details(o.company_id) for o in offers]
companies = await asyncio.gather(*company_tasks)

# Filter tech companies
tech_offers = [
    o for o, c in zip(offers, companies)
    if 'tech' in c.industry.lower()
]

# Find highest paying
best_offer = max(tech_offers, key=lambda o: o.salary)

# Return structured result
print(json.dumps({
    "offer": best_offer.to_dict(),
    "company": companies[offers.index(best_offer)].to_dict(),
    "salary": best_offer.salary
}))
"""

# LLM generates this ONCE
# All logic runs in sandbox (parallel fetch of company details)
# Only best offer returned
# Cost: 1 call + parallel execution vs 3-5 round-trips
```

## Getting Started

See the [Orchestrate with Code](../how-to/orchestrate-with-code.md) guide for implementation details and security considerations.

## Key Takeaways

| Traditional | Programmatic |
|-------------|--------------|
| Multi-round reasoning | Single code generation |
| LLM sees all data | LLM generates orchestration logic |
| Expensive at scale | Linear cost |
| Better for simple tasks | Better for complex workflows |

**Programmatic execution is most powerful when you have:**
1. Multiple items to process (batch operations)
2. Parallel fetches needed (asyncio.gather)
3. Local filtering/aggregation (LLM doesn't see raw data)
4. Cost sensitivity (fewer API calls, less context)
