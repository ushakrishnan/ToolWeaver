# Example 11: Programmatic Executor

**Capability Demonstrated:** Execute workflows programmatically without sending intermediate results to LLM

## What This Shows

- Keep large intermediate results out of LLM context
- Python-based workflow orchestration
- Direct tool invocation without LLM overhead
- Efficient for large data processing

## Why This Matters

**Problem:** LLM context limits (200K tokens)
- Processing 1000 receipts generates 50MB of data
- Can't fit in LLM context
- Expensive to send back and forth

**Solution:** Programmatic execution
- LLM plans the workflow once
- Python executes it with direct tool calls
- Intermediate results stay in memory
- Only final summary sent to LLM

## Performance Comparison

**LLM-in-the-loop (traditional):**
```
Process receipt 1 → LLM → Process receipt 2 → LLM → ...
Time: 100s, Cost: $5.00, Context: Overflows
```

**Programmatic (ToolWeaver):**
```
LLM: Create plan → Python: Execute 1000 receipts → LLM: Summarize
Time: 15s, Cost: $0.10, Context: Under control
```

## Setup

```bash
cp .env.example .env
python programmatic_demo.py
```

## Files

- `programmatic_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file