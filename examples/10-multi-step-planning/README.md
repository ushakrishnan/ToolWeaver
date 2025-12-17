# Example 10: Multi-Step Planning

**Capability Demonstrated:** Complex multi-step workflows with automatic planning

## What This Shows

- LLM generates execution plans from natural language
- Dependency resolution and DAG construction
- Parallel execution where possible
- Error handling and recovery
- Plan optimization and validation

## How It Works

```
User: "Process receipt, categorize items, send to Slack if > $100"
         ↓
    Planner (GPT-4)
         ↓
    Execution Plan (JSON):
    1. upload_receipt
    2. extract_text (depends on 1)
    3. parse_items (depends on 2)
    4. check_total (depends on 3)
    5. send_slack (depends on 4, conditional)
         ↓
    Orchestrator executes plan
```

## Example Plans

### Simple Linear
```
A → B → C → D
```

### Parallel Branches
```
     ┌→ B → D
A → ─┤       ├→ F
     └→ C → E
```

### Conditional
```
A → B → [if X: C, else: D] → E
```

## Setup

```bash
cp .env.example .env
python planning_demo.py
```

## Files

- `planning_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file