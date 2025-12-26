# How to Implement Retry Logic

Step-by-step guide to add retry logic, exponential backoff, and circuit breakers to your ToolWeaver workflows.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [Error Recovery](../tutorials/error-recovery.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Basic retry logic with exponential backoff  
✅ Circuit breaker to prevent repeated failures  
✅ Jitter to prevent thundering herd  
✅ Retry policies for different error types  
✅ Monitoring for retry metrics  

**Estimated time:** 25 minutes

---

## Step 1: Install Dependencies

```bash
# Install required packages
pip install tenacity  # Retry library
pip install circuit-breaker  # Circuit breaker
```

---

## Step 2: Basic Retry with Exponential Backoff

### 2.1 Simple Retry Decorator

**File:** `utils/retry.py`

```python
import asyncio
from typing import Callable
import time

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Retry function with exponential backoff."""
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed
                raise
            
            # Calculate exponential backoff delay
            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
            await asyncio.sleep(delay)
```

### 2.2 Usage Example

```python
async def call_llm():
    """Example function that might fail."""
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    return response

# Use retry wrapper
result = await retry_with_backoff(call_llm, max_retries=3, base_delay=1.0)
```

---

## Step 3: Add Jitter to Prevent Thundering Herd

### 3.1 Retry with Jitter

```python
import random

async def retry_with_jitter(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Retry with exponential backoff + jitter."""
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter (random 0-50% of delay)
            jitter = random.uniform(0, delay * 0.5)
            total_delay = delay + jitter
            
            print(f"Retry {attempt + 1} after {total_delay:.1f}s...")
            await asyncio.sleep(total_delay)
```

**Why jitter?** Prevents multiple clients from retrying simultaneously (thundering herd).

---

## Step 4: Use Tenacity Library for Advanced Retries

### 4.1 Install and Configure Tenacity

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),                # Max 3 attempts
    wait=wait_exponential(multiplier=1, min=1, max=60),  # 1s, 2s, 4s, ...
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),  # Only retry these
    before_sleep=before_sleep_log(logger, logging.WARNING)  # Log before retry
)
async def call_api_with_retry():
    """API call with automatic retry."""
    response = await http_client.get("https://api.example.com/data")
    return response.json()
```

### 4.2 Retry on Specific Status Codes

```python
from tenacity import retry_if_result

def is_retryable_status(response):
    """Check if HTTP status code is retryable."""
    return response.status_code in [429, 500, 502, 503, 504]

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=120),
    retry=retry_if_result(is_retryable_status)
)
async def call_api():
    response = await http_client.get("https://api.example.com")
    return response
```

---

## Step 5: Implement Circuit Breaker

### 5.1 Basic Circuit Breaker

**File:** `utils/circuit_breaker.py`

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Too many failures, block requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,  # Open circuit after 5 failures
        timeout: int = 60,           # Try recovery after 60s
        expected_exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                # Try recovery
                self.state = CircuitState.HALF_OPEN
                print("Circuit breaker: HALF_OPEN (testing recovery)")
            else:
                raise RuntimeError(f"Circuit breaker OPEN (waiting {self.timeout}s)")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success → reset circuit
            if self.state == CircuitState.HALF_OPEN:
                print("Circuit breaker: CLOSED (recovery successful)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
        
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"Circuit breaker: OPEN (after {self.failure_count} failures)")
            
            raise
```

### 5.2 Usage Example

```python
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

async def call_external_api():
    """Expensive API call protected by circuit breaker."""
    
    try:
        result = await breaker.call(expensive_api_call, data)
        return result
    except RuntimeError as e:
        if "Circuit breaker OPEN" in str(e):
            # Circuit is open, use fallback
            print("Using fallback due to circuit breaker")
            return await cheap_fallback_call(data)
        raise
```

---

## Step 6: Define Retry Policies by Error Type

### 6.1 Error Classification

```python
class ErrorType(Enum):
    TRANSIENT = "TRANSIENT"      # Retry (timeout, network glitch)
    RATE_LIMIT = "RATE_LIMIT"    # Retry with longer backoff
    PERMANENT = "PERMANENT"      # Don't retry (auth error, not found)

def classify_error(error: Exception) -> ErrorType:
    """Classify error to determine retry strategy."""
    
    if isinstance(error, TimeoutError):
        return ErrorType.TRANSIENT
    
    if isinstance(error, ConnectionError):
        return ErrorType.TRANSIENT
    
    if hasattr(error, 'status_code'):
        if error.status_code == 429:
            return ErrorType.RATE_LIMIT
        if error.status_code in [500, 502, 503, 504]:
            return ErrorType.TRANSIENT
        if error.status_code in [401, 403, 404]:
            return ErrorType.PERMANENT
    
    return ErrorType.PERMANENT
```

### 6.2 Adaptive Retry Strategy

```python
async def retry_adaptive(func: Callable, max_retries: int = 5):
    """Retry with strategy based on error type."""
    
    for attempt in range(max_retries):
        try:
            return await func()
        
        except Exception as e:
            error_type = classify_error(e)
            
            # Don't retry permanent errors
            if error_type == ErrorType.PERMANENT:
                print(f"Permanent error, not retrying: {e}")
                raise
            
            # Final attempt
            if attempt == max_retries - 1:
                raise
            
            # Calculate delay based on error type
            if error_type == ErrorType.RATE_LIMIT:
                # Longer backoff for rate limits
                delay = 2 ** (attempt + 2)  # 4s, 8s, 16s, 32s
            else:
                # Standard backoff for transient errors
                delay = 2 ** attempt  # 1s, 2s, 4s, 8s
            
            print(f"Retry {attempt + 1} after {delay}s ({error_type.value})")
            await asyncio.sleep(delay)
```

---

## Step 7: Create Retry Policy Configuration

### 7.1 Define Retry Policies

**File:** `config/retry_policies.py`

```python
from dataclasses import dataclass

@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: tuple = (TimeoutError, ConnectionError)

# Predefined policies
DEFAULT_POLICY = RetryPolicy(
    max_retries=3,
    base_delay=1.0,
    retry_on=(TimeoutError, ConnectionError)
)

AGGRESSIVE_POLICY = RetryPolicy(
    max_retries=5,
    base_delay=0.5,
    retry_on=(TimeoutError, ConnectionError, OSError)
)

RATE_LIMIT_POLICY = RetryPolicy(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=3.0,  # Faster backoff
    retry_on=(Exception,)  # Retry all errors (assuming rate limit)
)

CONSERVATIVE_POLICY = RetryPolicy(
    max_retries=2,
    base_delay=2.0,
    retry_on=(TimeoutError,)
)
```

### 7.2 Apply Retry Policy

```python
async def execute_with_policy(func: Callable, policy: RetryPolicy):
    """Execute function with specified retry policy."""
    
    for attempt in range(policy.max_retries):
        try:
            return await func()
        
        except Exception as e:
            # Check if error is retryable
            if not isinstance(e, policy.retry_on):
                print(f"Error not in retry list: {type(e).__name__}")
                raise
            
            # Final attempt
            if attempt == policy.max_retries - 1:
                raise
            
            # Calculate delay
            delay = min(
                policy.base_delay * (policy.exponential_base ** attempt),
                policy.max_delay
            )
            
            # Add jitter if enabled
            if policy.jitter:
                jitter = random.uniform(0, delay * 0.5)
                delay += jitter
            
            print(f"Retry {attempt + 1}/{policy.max_retries} after {delay:.1f}s")
            await asyncio.sleep(delay)

# Usage
result = await execute_with_policy(call_llm, policy=AGGRESSIVE_POLICY)
```

---

## Step 8: Monitor Retry Metrics

### 8.1 Track Retry Statistics

```python
from collections import defaultdict

class RetryMetrics:
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retry_counts = defaultdict(int)  # {attempts: count}
    
    def record_success(self, attempts: int):
        """Record successful call after N attempts."""
        self.total_calls += 1
        self.successful_calls += 1
        self.retry_counts[attempts] += 1
    
    def record_failure(self, attempts: int):
        """Record failed call after N attempts."""
        self.total_calls += 1
        self.failed_calls += 1
        self.retry_counts[attempts] += 1
    
    def report(self):
        """Print retry statistics."""
        print(f"\n=== Retry Metrics ===")
        print(f"Total calls: {self.total_calls}")
        print(f"Success rate: {self.successful_calls / self.total_calls:.1%}")
        print(f"Failure rate: {self.failed_calls / self.total_calls:.1%}")
        
        print(f"\nRetry distribution:")
        for attempts in sorted(self.retry_counts.keys()):
            count = self.retry_counts[attempts]
            pct = count / self.total_calls
            print(f"  {attempts} attempts: {count} ({pct:.1%})")
        
        avg_retries = sum(
            attempts * count for attempts, count in self.retry_counts.items()
        ) / self.total_calls
        print(f"\nAvg retries: {avg_retries:.2f}")

metrics = RetryMetrics()
```

### 8.2 Instrumented Retry Function

```python
async def retry_with_metrics(func: Callable, policy: RetryPolicy):
    """Retry with metrics tracking."""
    
    attempt = 0
    
    for attempt in range(policy.max_retries):
        try:
            result = await func()
            metrics.record_success(attempts=attempt + 1)
            return result
        
        except Exception as e:
            if attempt == policy.max_retries - 1:
                metrics.record_failure(attempts=attempt + 1)
                raise
            
            delay = policy.base_delay * (policy.exponential_base ** attempt)
            await asyncio.sleep(delay)

# After processing batch
metrics.report()
```

---

## Step 9: Real-World Example

Complete retry setup for receipt processing.

**File:** `pipeline/receipt_processing.py`

```python
from utils.retry import retry_with_jitter
from utils.circuit_breaker import CircuitBreaker
from config.retry_policies import AGGRESSIVE_POLICY, RATE_LIMIT_POLICY

class ReceiptProcessor:
    def __init__(self):
        # Circuit breakers for each external service
        self.ocr_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        self.vision_breaker = CircuitBreaker(failure_threshold=3, timeout=120)
        
        self.metrics = RetryMetrics()
    
    async def process_receipt(self, receipt_id: str):
        """Process receipt with retry logic and circuit breakers."""
        
        # Step 1: OCR extraction (aggressive retry for transient failures)
        async def extract_text():
            return await self.ocr_breaker.call(
                self.ocr_tool.extract,
                receipt_id
            )
        
        try:
            text = await execute_with_policy(extract_text, AGGRESSIVE_POLICY)
        except RuntimeError as e:
            if "Circuit breaker OPEN" in str(e):
                # OCR service is down, use fallback
                text = await self.local_ocr.extract(receipt_id)
            else:
                raise
        
        # Step 2: Vision analysis (rate limit handling)
        async def analyze_image():
            return await self.vision_breaker.call(
                self.vision_tool.analyze,
                receipt_id
            )
        
        try:
            analysis = await execute_with_policy(analyze_image, RATE_LIMIT_POLICY)
        except RuntimeError as e:
            if "Circuit breaker OPEN" in str(e):
                # Vision service is down, skip analysis
                analysis = {"status": "skipped"}
            else:
                raise
        
        return {
            "text": text,
            "analysis": analysis
        }
    
    async def process_batch(self, receipt_ids: list):
        """Process batch with retry metrics."""
        results = []
        
        for receipt_id in receipt_ids:
            try:
                result = await self.process_receipt(receipt_id)
                results.append(result)
            except Exception as e:
                print(f"Receipt {receipt_id} failed: {e}")
                results.append({"error": str(e)})
        
        # Report metrics
        self.metrics.report()
        
        return results
```

---

## Verification

Test your retry logic:

```python
async def verify_retry_logic():
    """Verify retry logic is working."""
    
    print("Testing retry logic...")
    
    # Test 1: Successful retry after failure
    call_count = 0
    
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError("Simulated failure")
        return "success"
    
    result = await retry_with_backoff(flaky_function, max_retries=3)
    assert result == "success", "Retry didn't work"
    assert call_count == 3, f"Expected 3 calls, got {call_count}"
    print("✓ Retry logic working")
    
    # Test 2: Circuit breaker opens after failures
    breaker = CircuitBreaker(failure_threshold=2, timeout=5)
    
    async def always_fails():
        raise ConnectionError("Always fails")
    
    try:
        await breaker.call(always_fails)
    except ConnectionError:
        pass
    
    try:
        await breaker.call(always_fails)
    except ConnectionError:
        pass
    
    try:
        await breaker.call(always_fails)
        assert False, "Circuit breaker didn't open"
    except RuntimeError as e:
        assert "Circuit breaker OPEN" in str(e)
        print("✓ Circuit breaker working")
    
    print("\n✅ All checks passed!")

# Run verification
await verify_retry_logic()
```

---

## Common Issues

### Issue 1: Retries Not Happening

**Symptom:** Function fails immediately without retrying

**Solution:** Check exception type matches `retry_on` list

```python
# Debug: Log exception type
try:
    await func()
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Retry on: {policy.retry_on}")
```

### Issue 2: Circuit Breaker Stuck Open

**Symptom:** Circuit breaker never recovers

**Solution:** Reduce `timeout` or check for recovery logic

```python
# Lower timeout for faster recovery
breaker = CircuitBreaker(failure_threshold=5, timeout=30)  # Was 60

# Or manually reset
breaker.state = CircuitState.HALF_OPEN
```

### Issue 3: Thundering Herd After Outage

**Symptom:** All clients retry simultaneously, overwhelming service

**Solution:** Add jitter to spread out retries

```python
# Enable jitter in policy
policy = RetryPolicy(jitter=True)

# Or add random initial delay
await asyncio.sleep(random.uniform(0, 5))
result = await retry_with_policy(func, policy)
```

---

## Next Steps

- **Tutorial:** [Error Recovery](../tutorials/error-recovery.md) - Learn core concepts
- **Deep Dive:** [Idempotency & Retry](../reference/deep-dives/idempotency-retry.md) - Advanced patterns
- **Sample:** [21-error-recovery](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/21-error-recovery) - Complete example

## Related Guides

- [Implement Circuit Breakers](implement-circuit-breakers.md) - Advanced circuit breaker patterns
- [Monitor Performance](monitor-performance.md) - Track retry metrics
- [Optimize Tool Costs](optimize-tool-costs.md) - Don't waste money on retries

