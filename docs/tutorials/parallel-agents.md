# Tutorial: Parallel Agents

## Simple Explanation
Run many tools/agents at once with limits on cost and concurrency; combine results for a robust decision.

## Technical Explanation
Fan-out dispatcher batches work under a semaphore (`max_parallel`), enforces budgets and failure-rate thresholds, applies idempotency for instant retries, and aggregates results via vote/rank/best.

Fan out work with guardrails for cost, concurrency, and safety.

Run:
```bash
python samples/25-parallel-agents/parallel_deep_dive.py
```

Prerequisites:
- Install from PyPI: `pip install toolweaver`

What you will see:
- Batch processing: 20 receipts in ~0.2s
- Multi-model consensus with majority vote
- Semaphore control batches work (max_parallel)
- Quota protection stops cost bombs
- Idempotency cache makes retries instant

Files:
- [samples/25-parallel-agents/parallel_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/parallel_deep_dive.py)
- [samples/25-parallel-agents/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/README.md)
