# Error Recovery & Resilience Tutorial

Learn how to build production-ready AI workflows that gracefully handle failures through retries, fallbacks, circuit breakers, and self-healing patterns.

## What You'll Learn

By the end of this tutorial, you'll understand:

- Common failure scenarios and how to handle them
- Retry strategies (exponential backoff, jitter, max attempts)
- Circuit breakers (when to stop trying)
- Fallback chains (primary → secondary → tertiary)
- Self-healing workflows (diagnose → fix → retry)

## Prerequisites

- Basic understanding of [ToolWeaver orchestration](../get-started/quickstart.md)
- Familiarity with [async/await in Python](https://docs.python.org/3/library/asyncio.html)

## The Failure Problem

**Reality:** External services fail. A lot.

| Failure Type | Frequency | Example |
|--------------|-----------|---------|
| **Timeouts** | 5-10% | API takes >30s to respond |
| **Rate Limits** | 2-5% | 429 Too Many Requests |
| **Model Unavailable** | 1-2% | OpenAI outage, Ollama crash |
| **Bad Input** | 1-5% | Malformed data, missing fields |

**Without error handling:**
- One failure = entire workflow stops
- Manual intervention required
- User sees cryptic error messages

**With error recovery:**
- Automatic retries with backoff
- Fallback to alternative services
- Graceful degradation
- Self-healing workflows

---

## Core Concepts

### 1. Retry Strategies

**When to retry:**
- ✅ Transient failures (timeout, network glitch, rate limit)
- ❌ Permanent failures (auth error, invalid input, not found)

**How many times:**
- **3 retries** = good default (covers 95% of transient failures)
- **5+ retries** = excessive (wastes time if service is down)
- **0 retries** = only for idempotent operations where failure is acceptable

### 2. Exponential Backoff

Don't retry immediately—wait longer each time:

```
Attempt 1: Fail → wait 0.1s
Attempt 2: Fail → wait 0.2s
Attempt 3: Fail → wait 0.4s
Attempt 4: Fail → wait 0.8s
```

**Formula:** `delay = base_delay * (2 ** attempt)`

### 3. Circuit Breakers

Stop trying after repeated failures:

**States:**
- **CLOSED** (normal): Requests go through
- **OPEN** (broken): Requests fail fast (no attempt)
- **HALF_OPEN** (testing): Try one request to check recovery

**Transitions:**
```
CLOSED → OPEN: After 5 consecutive failures
OPEN → HALF_OPEN: After 60s cooldown
HALF_OPEN → CLOSED: If test request succeeds
HALF_OPEN → OPEN: If test request fails
```

### 4. Fallback Chains

Try alternatives when primary fails:

```
Primary (expensive, accurate) → Secondary (cheap, decent) → Tertiary (fallback)
GPT-4 Vision ($0.10) → Claude ($0.05) → Local OCR ($0.01)
```

---

## Common Failure Scenarios

### Scenario 1: API Timeout

**Problem:** LLM takes >30s, your code times out.

**Solution:** Retry with longer timeout + exponential backoff.

```python
import asyncio

async def call_llm_with_retry(prompt: str, max_retries: int = 3):
    base_timeout = 30
    
    for attempt in range(max_retries):
        timeout = base_timeout * (2 ** attempt)  # 30s, 60s, 120s
        
        try:
            result = await asyncio.wait_for(
                llm.generate(prompt),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise  # Final attempt failed
            print(f"Timeout after {timeout}s, retrying...")
            await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
```

---

### Scenario 2: Rate Limit (429 Error)

**Problem:** Exceeded API quota, got 429 error.

**Solution:** Wait and retry with exponential backoff.

```python
from openai import RateLimitError

async def call_with_rate_limit_handling(prompt: str):
    max_retries = 5
    base_delay = 1.0  # Start with 1 second
    
    for attempt in range(max_retries):
        try:
            return await openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            delay = base_delay * (2 ** attempt)
            print(f"Rate limited, waiting {delay}s...")
            await asyncio.sleep(delay)
```

---

### Scenario 3: Model Unavailable

**Problem:** OpenAI is down, can't reach API.

**Solution:** Fallback to alternative model.

```python
async def call_with_fallback(prompt: str):
    """Try GPT-4, fallback to Claude, fallback to local model."""
    
    # Try primary (GPT-4)
    try:
        return await openai_client.generate(prompt, model="gpt-4")
    except Exception as e:
        print(f"GPT-4 failed: {e}, trying Claude...")
    
    # Try secondary (Claude)
    try:
        return await anthropic_client.generate(prompt, model="claude-3")
    except Exception as e:
        print(f"Claude failed: {e}, trying local model...")
    
    # Try tertiary (local Ollama)
    try:
        return await ollama_client.generate(prompt, model="phi3")
    except Exception as e:
        print(f"All models failed: {e}")
        raise RuntimeError("No available models")
```

---

### Scenario 4: Circuit Breaker (Repeated Failures)

**Problem:** Service is completely down, retrying wastes time.

**Solution:** Circuit breaker stops attempts after threshold.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = 0
    
    async def call(self, func, *args, **kwargs):
        # Check if circuit is open
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success → reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
            
            raise

# Usage
breaker = CircuitBreaker()
result = await breaker.call(expensive_api_call, data)
```

---

## Self-Healing Workflows

**Pattern:** fail → diagnose → fix → retry

### Step 1: Detect Failure

```python
async def process_receipt(receipt_id: str):
    try:
        result = await ocr_tool.extract(receipt_id)
        return result
    except Exception as e:
        print(f"OCR failed: {e}")
        # Move to diagnosis
        return await diagnose_and_fix(receipt_id, error=e)
```

### Step 2: Diagnose with Agent

```python
async def diagnose_and_fix(receipt_id: str, error: Exception):
    """Use diagnostic agent to suggest fix."""
    
    # Ask diagnostic agent for recommendations
    diagnosis = await orchestrator.execute_agent_step(
        agent_name="diagnostic_agent",
        request={
            "resource": receipt_id,
            "error": str(error),
            "context": "OCR extraction failed"
        }
    )
    
    print(f"Diagnosis: {diagnosis}")
    
    # Apply remediation
    return await apply_fix(receipt_id, diagnosis)
```

### Step 3: Apply Remediation

```python
async def apply_fix(receipt_id: str, diagnosis: dict):
    """Apply recommended fix."""
    
    if "image_quality" in diagnosis.get("issue", ""):
        # Preprocessing fix
        await orchestrator.execute_tool(
            "preprocess_image",
            {"receipt_id": receipt_id, "enhance": True}
        )
    
    if "encoding" in diagnosis.get("issue", ""):
        # Encoding fix
        await orchestrator.execute_tool(
            "fix_encoding",
            {"receipt_id": receipt_id}
        )
    
    # Retry original operation
    return await retry_with_backoff(receipt_id)
```

### Step 4: Retry Original Operation

```python
async def retry_with_backoff(receipt_id: str, max_retries: int = 3):
    """Retry after applying fix."""
    
    for attempt in range(max_retries):
        try:
            result = await ocr_tool.extract(receipt_id)
            print(f"✓ Success on retry {attempt + 1}")
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed after {max_retries} retries")
            
            delay = 0.5 * (2 ** attempt)
            await asyncio.sleep(delay)
```

---

## Practical Patterns

### Pattern 1: Retry with Jitter

Add randomness to prevent thundering herd:

```python
import random

async def retry_with_jitter(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff + jitter
            base_delay = 2 ** attempt
            jitter = random.uniform(0, base_delay * 0.5)
            delay = base_delay + jitter
            
            await asyncio.sleep(delay)
```

### Pattern 2: Fallback Chain

```python
async def call_with_fallback_chain(prompt: str):
    """Try multiple tools in order of preference."""
    
    tools = [
        ("gpt4", 0.10, 0.99),      # Expensive, accurate
        ("claude", 0.05, 0.95),    # Medium cost, good accuracy
        ("local", 0.01, 0.85),     # Cheap, decent accuracy
    ]
    
    for tool_name, cost, accuracy in tools:
        try:
            result = await execute_tool(tool_name, prompt)
            print(f"✓ Success with {tool_name} (${cost}, {accuracy*100}% accuracy)")
            return result
        except Exception as e:
            print(f"✗ {tool_name} failed: {e}")
            continue
    
    raise RuntimeError("All tools in fallback chain failed")
```

### Pattern 3: Partial Success

Return partial results instead of failing completely:

```python
async def process_batch_with_partial_success(items: list):
    """Process batch, return successes + failures."""
    
    successes = []
    failures = []
    
    for item in items:
        try:
            result = await process_item(item)
            successes.append({"item": item, "result": result})
        except Exception as e:
            failures.append({"item": item, "error": str(e)})
    
    return {
        "successes": successes,
        "failures": failures,
        "success_rate": len(successes) / len(items)
    }
```

---

## Real-World Example: Receipt Processing Pipeline

```python
from orchestrator.tools.error_recovery import ErrorRecoveryExecutor
from orchestrator.selection.registry import ErrorRecoveryPolicy, ErrorStrategy

async def build_resilient_pipeline():
    """Build production-ready receipt processing with error recovery."""
    
    executor = ErrorRecoveryExecutor()
    
    # Define retry policy for OCR tool
    ocr_policy = ErrorRecoveryPolicy(
        strategy=ErrorStrategy.RETRY,
        max_retries=3,
        retry_backoff=2.0,  # Exponential: 2s, 4s, 8s
    )
    
    # Define fallback policy for vision tool
    vision_policy = ErrorRecoveryPolicy(
        strategy=ErrorStrategy.FALLBACK,
        max_retries=0,  # Don't retry, just fallback
        fallback_tools=["claude_vision", "local_ocr"],
    )
    
    # Register tools with policies
    registry.register(gpt4_vision, error_policy=vision_policy)
    registry.register(tesseract_ocr, error_policy=ocr_policy)
    
    # Execute with automatic error handling
    results = []
    for receipt in receipts:
        try:
            result = await executor.execute_with_recovery(
                tool_name="gpt4_vision",
                params={"receipt_id": receipt.id},
                policy=vision_policy
            )
            results.append(result)
        except Exception as e:
            # All retries and fallbacks exhausted
            print(f"Receipt {receipt.id} failed permanently: {e}")
            results.append({"error": str(e)})
    
    return results
```

---

## Best Practices

### ✅ Do's

1. **Always use exponential backoff** - Prevents overwhelming failed service
2. **Set max retries (3-5)** - Don't retry forever
3. **Log every failure** - Essential for debugging
4. **Use circuit breakers for external services** - Fail fast when service is down
5. **Implement fallback chains** - Have plan B and C
6. **Add jitter to retries** - Prevents thundering herd
7. **Monitor retry rates** - High retry rate = systemic issue

### ❌ Don'ts

1. **Don't retry immediately** - Wastes resources, amplifies load
2. **Don't retry on auth errors** - Permanent failures
3. **Don't ignore idempotency** - Retries can cause duplicates
4. **Don't hide errors from users** - Show graceful degradation messages
5. **Don't retry expensive operations without backoff** - Cost explosion

---

## Measuring Resilience

Track error recovery effectiveness:

```python
from orchestrator.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

async def monitored_execution(tool_name: str, params: dict):
    """Execute with metrics tracking."""
    
    start_time = time.time()
    attempt = 0
    
    while attempt < max_retries:
        attempt += 1
        try:
            result = await execute_tool(tool_name, params)
            
            # Log success metrics
            metrics.record({
                "tool": tool_name,
                "status": "success",
                "attempts": attempt,
                "duration": time.time() - start_time
            })
            
            return result
        except Exception as e:
            if attempt == max_retries:
                # Log final failure
                metrics.record({
                    "tool": tool_name,
                    "status": "failed",
                    "attempts": attempt,
                    "error": str(e)
                })
                raise
            
            await asyncio.sleep(2 ** attempt)

# Analyze metrics
print(f"Success rate: {metrics.success_rate():.1f}%")
print(f"Avg attempts: {metrics.avg_attempts():.1f}")
print(f"Retry rate: {metrics.retry_rate():.1f}%")
```

---

## Next Steps

- **How-To Guide:** [Implement Retry Logic](../how-to/implement-retry-logic.md) - Step-by-step implementation
- **Deep Dive:** [Error Recovery](../reference/deep-dives/error-recovery.md) - Advanced patterns
- **Sample:** [21-error-recovery](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/21-error-recovery) - Self-healing workflow

## Related Topics

- [Cost Optimization](cost-optimization.md) - Don't waste money on retries
- [Idempotency & Retry](../reference/deep-dives/idempotency-retry.md) - Prevent duplicate operations
- [Parallel Agents](parallel-agents.md) - Circuit breakers for parallel dispatch

