# Error Recovery

## Simple Explanation
Design workflows that keep going when parts fail. Detect errors, retry safely, skip when appropriate, and record what happened.

## Technical Explanation
Use explicit error handling: classify failures (transient vs permanent), apply retries with backoff for transient cases, and fall back or skip for permanent ones. Track idempotency keys to avoid duplicates, and record events for auditing.

**When to use**
- External dependencies with intermittent errors
- Long-running workflows where partial success is acceptable

**Key Primitives**
- Error taxonomy and handlers
- Retry/backoff and skip/fallback policies
- Idempotency and event logs
- Compensating actions for side-effects

**Try it**
- Run the workflow: [samples/21-error-recovery/workflow.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/21-error-recovery/workflow.py)
- Tests and examples: [samples/21-error-recovery/test_example.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/21-error-recovery/test_example.py)
- See the README: [samples/21-error-recovery/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/21-error-recovery/README.md)

**Gotchas**
- Keep retries bounded; avoid infinite loops
- Make side-effects compensable or idempotent
- Distinguish user errors from system errors for correct policies
