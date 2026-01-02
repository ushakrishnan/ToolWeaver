# How to Orchestrate with Code

Programmatic execution allows LLMs to generate code that orchestrates tools, enabling parallel execution, complex workflows, and local data aggregation without the context bloat of traditional multi-round tool calling.

## Quick Start

### Basic Setup

```python
from orchestrator.shared.models import ToolCatalog
from orchestrator._internal.execution.programmatic_executor import ProgrammaticToolExecutor

# Create executor with your tool catalog
executor = ProgrammaticToolExecutor(
    catalog=tool_catalog,
    enable_stubs=True  # Use tool stubs for testing
)

# Generate code (from LLM or static)
code = """
import asyncio
results = await get_data()
processed = [r for r in results if r.value > 100]
return processed
"""

# Execute in sandbox
result = await executor.execute(code)
```

## Pattern 1: Parallel Fetches

Instead of sequential LLM calls, fetch multiple items in parallel:

```python
code = """
import asyncio
import json

# Get all user IDs first
users = await get_users()

# Fetch all orders IN PARALLEL
order_tasks = [get_user_orders(u['id']) for u in users]
all_orders = await asyncio.gather(*order_tasks)

# Process results (stays in sandbox)
summary = {
    'total_users': len(users),
    'total_orders': sum(len(o) for o in all_orders),
    'users_with_orders': len([o for o in all_orders if o])
}

print(json.dumps(summary))
"""

result = await executor.execute(code)
```

**Benefits:**
- Fetches 100 items in ~same time as 1
- No intermediate data sent to LLM
- Aggregation happens locally

## Pattern 2: Conditional Workflows

Chain operations based on results without LLM round-trips:

```python
code = """
import asyncio
import json

# Step 1: Get lead
lead = await get_lead(lead_id)

# Step 2: Check qualification
score = lead.get('qualification_score', 0)

if score > 0.8:
    # Step 3a: If qualified, get full company details
    company = await get_company(lead['company_id'])
    next_step = 'send_proposal'
else:
    # Step 3b: If not qualified, get nurture campaign
    company = await get_company_basic(lead['company_id'])
    next_step = 'nurture_campaign'

result = {
    'lead': lead,
    'company': company,
    'next_step': next_step,
    'action_taken': 'auto_routed'
}

print(json.dumps(result))
"""

result = await executor.execute(code)
```

**Benefits:**
- Complex logic in code, not LLM reasoning
- Different paths handled without context switching
- Faster execution

## Pattern 3: Local Aggregation

Process large intermediate data locally:

```python
code = """
import asyncio
import json

# Fetch detailed records
records = await fetch_records(query='2024')

# Process locally (100KB+ data stays in sandbox)
aggregations = {
    'by_category': {},
    'totals': {},
    'outliers': []
}

for record in records:
    cat = record['category']
    aggregations['by_category'].setdefault(cat, []).append(record)
    
    # Track totals
    aggregations['totals'][cat] = aggregations['totals'].get(cat, 0) + record['value']
    
    # Identify outliers
    if record['value'] > 10000:
        aggregations['outliers'].append(record)

# Return only summary (2KB instead of 200KB)
summary = {
    'categories': list(aggregations['by_category'].keys()),
    'totals': aggregations['totals'],
    'outlier_count': len(aggregations['outliers']),
    'outliers': aggregations['outliers'][:5]  # Top 5
}

print(json.dumps(summary))
"""

result = await executor.execute(code)
```

**Benefits:**
- Raw data never sent to LLM
- Context efficient (only summary returned)
- Better token utilization

## Pattern 4: Type-Safe Tool Calls

Use Pydantic models for type safety:

```python
code = """
import asyncio
import json
from tools.api import GetUserInput, GetUserOutput

# Type-safe input
user_input = GetUserInput(user_id='usr_123')

# Type-safe output
user: GetUserOutput = await get_user(user_input)

# Access typed fields
result = {
    'user_id': user.id,
    'email': user.email,
    'name': user.name
}

print(json.dumps(result))
"""

result = await executor.execute(code)
```

## Advanced: Streaming Results

For large result sets, stream output:

```python
code = """
import asyncio
import json

users = await get_users()

for user in users:
    # Stream each result
    print(json.dumps({
        'user_id': user['id'],
        'name': user['name']
    }))
"""

# Collect streaming output
outputs = []
async for line in executor.execute_streaming(code):
    outputs.append(json.loads(line))
```

## Security Features

Programmatic execution runs code in a restricted sandbox:

### Restrictions
- No `import os`, `import subprocess`, `import socket`
- No file access
- No network calls (only tool calls)
- No infinite loops (5-minute timeout)
- Max 10,000 tool calls per execution
- Restricted builtins (no `eval`, `exec`, `compile`)

### Example: Invalid Code (Blocked)

```python
code = """
import os
os.system('rm -rf /')  # ❌ BLOCKED - os module not allowed
"""

# Raises: SecurityValidationError
```

### Example: Valid Code (Allowed)

```python
code = """
# ✅ ALLOWED - only tool calls and data processing
results = await get_data()
filtered = [r for r in results if r['status'] == 'active']
print(json.dumps(filtered))
"""
```

## Error Handling

```python
from orchestrator._internal.execution.errors import (
    SecurityValidationError,
    ExecutionTimeoutError,
    ToolCallError
)

try:
    result = await executor.execute(code)
except SecurityValidationError as e:
    print(f"Code contains restricted operations: {e}")
except ExecutionTimeoutError:
    print("Code took too long (>5 minutes)")
except ToolCallError as e:
    print(f"Tool call failed: {e}")
```

## Monitoring & Debugging

```python
# Enable detailed logging
import logging
logging.getLogger('orchestrator.execution').setLevel(logging.DEBUG)

# Execute with instrumentation
result = await executor.execute(code)

# Access execution metadata
print(f"Tools called: {result.metadata.tool_calls}")
print(f"Execution time: {result.metadata.elapsed_time}")
print(f"Tokens estimated: {result.metadata.tokens_estimated}")
```

## Performance Tips

### ✅ DO: Use asyncio.gather for parallelism

```python
# Good - parallel
tasks = [fetch_item(i) for i in items]
results = await asyncio.gather(*tasks)
```

### ❌ DON'T: Sequential loops

```python
# Bad - sequential
for item in items:
    result = await fetch_item(item)  # Slow!
```

### ✅ DO: Filter locally

```python
# Good - filter in sandbox
items = await fetch_items()
filtered = [i for i in items if i['value'] > 100]  # Stays local
print(json.dumps(filtered))
```

### ❌ DON'T: Send raw data back to LLM

```python
# Bad - context bloat
items = await fetch_items()
print(json.dumps(items))  # All 10,000 items!
```

### ✅ DO: Aggregate before returning

```python
# Good - return summary
items = await fetch_items()
summary = {
    'count': len(items),
    'avg_value': sum(i['value'] for i in items) / len(items),
    'total': sum(i['value'] for i in items)
}
print(json.dumps(summary))
```

## Real-World Examples

### Example 1: Qualified Lead Pipeline

```python
code = """
import asyncio
import json

# Get all leads from last 30 days
leads = await get_leads(days=30)

# Fetch scoring for all (parallel)
score_tasks = [score_lead(l['id']) for l in leads]
scores = await asyncio.gather(*score_tasks)

# Filter qualified only
qualified = [
    {'lead': l, 'score': s}
    for l, s in zip(leads, scores)
    if s > 0.75
]

# For qualified, get company details
company_tasks = [get_company(l['lead']['company_id']) for l in qualified]
companies = await asyncio.gather(*company_tasks)

# Return structured result
result = {
    'total_leads': len(leads),
    'qualified_count': len(qualified),
    'qualified': [
        {
            'lead_id': l['lead']['id'],
            'score': l['score'],
            'company': c['name'],
            'industry': c['industry']
        }
        for l, c in zip(qualified, companies)
    ]
}

print(json.dumps(result))
"""
```

**Cost comparison:**
- Traditional: 30 leads × 3 calls (qualify, get company, etc) = 90 LLM calls
- Programmatic: 1 LLM call + parallel execution

### Example 2: Batch Report Generation

```python
code = """
import asyncio
import json

# Get all teams
teams = await get_teams()

# Fetch department metrics (parallel)
metric_tasks = [get_department_metrics(t['id']) for t in teams]
metrics = await asyncio.gather(*metric_tasks)

# Generate report locally
report = {
    'timestamp': datetime.now().isoformat(),
    'teams': len(teams),
    'report_sections': [
        {
            'team_name': t['name'],
            'headcount': m['headcount'],
            'performance_score': m['performance'],
            'budget_utilization': m['budget_used'] / m['budget_total']
        }
        for t, m in zip(teams, metrics)
    ]
}

print(json.dumps(report))
"""
```

## See Also

- [Programmatic Execution Tutorial](../tutorials/programmatic-execution.md) - Conceptual overview
- [Sample 14: Progressive Discovery](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/14-programmatic-execution/) - Full working example
