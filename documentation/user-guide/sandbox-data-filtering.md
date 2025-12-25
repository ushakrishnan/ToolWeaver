# Sandbox Data Filtering & PII Tokenization

Filter large datasets, reduce token costs, and protect sensitive information.

## Features

- **Output Size Limiting**: Truncate large results intelligently
- **PII Detection & Tokenization**: Protect emails, phones, SSNs, credit cards, etc.
- **Data Summarization**: Preserve structure while reducing size
- **Reversible Tokenization**: Detokenize if needed (secure context only)

## Quick Start

```python
from orchestrator.execution import filter_and_tokenize, FilterConfig

# Process data with default settings
data = {"users": [...1000 records...]}
result = filter_and_tokenize(data, tokenize_pii=True)

# Access filtered data
processed = result["data"]
pii_tokens = result.get("token_map", {})  # For detokenization
```

## Basic Usage

### Data Filtering Only

```python
from orchestrator.execution import DataFilter, FilterConfig

# Configure filter
config = FilterConfig(
    max_rows=100,           # Limit lists/arrays to 100 items
    max_bytes=50000,        # 50KB max output
    max_string_length=500,  # Truncate long strings
    summarize_truncated=True
)

filter = DataFilter(config)
result = filter.apply(large_data)

print(result["data"])        # Filtered data
print(result["truncated"])   # True if truncation occurred
print(result["stats"])       # Truncation statistics
print(result["summary"])     # Human-readable summary
```

### PII Tokenization Only

```python
from orchestrator.execution import PIITokenizer, PIIType

# Default: tokenizes email, phone, SSN, credit cards
tokenizer = PIITokenizer()

data = {
    "user": "john@example.com",
    "phone": "555-1234",
    "ssn": "123-45-6789"
}

sanitized = tokenizer.tokenize(data)
# {"user": "TOKEN_EMAIL_a1b2c3", "phone": "TOKEN_PHONE_d4e5f6", ...}

# Get token map for later detokenization
token_map = tokenizer.get_token_map()
```

### Combined Filtering & Tokenization

```python
from orchestrator.execution import (
    filter_and_tokenize,
    FilterConfig,
    TokenizationConfig,
    PIIType
)

filter_config = FilterConfig(
    max_rows=100,
    max_string_length=500
)

tokenize_config = TokenizationConfig(
    enabled_types={PIIType.EMAIL, PIIType.PHONE}
)

result = filter_and_tokenize(
    data,
    filter_config=filter_config,
    tokenize_config=tokenize_config,
    tokenize_pii=True
)

processed_data = result["data"]
stats = result["stats"]
token_map = result.get("token_map", {})
```

## Realistic Scenarios

### Database Query Results

```python
from orchestrator.execution import filter_and_tokenize, FilterConfig

# Large database query
query_result = {
    "query": "SELECT * FROM users",
    "results": [
        {
            "id": i,
            "email": f"user{i}@company.com",
            "phone": f"555-{i:04d}",
            "notes": "..." * 100  # Long text
        }
        for i in range(5000)
    ]
}

# Apply filtering and PII protection
config = FilterConfig(
    max_rows=200,           # Only first 200 rows
    max_string_length=500,  # Truncate long notes
    summarize_truncated=True
)

result = filter_and_tokenize(
    query_result,
    filter_config=config,
    tokenize_pii=True
)

# Reduced from 5000 rows to 200, PII tokenized
processed = result["data"]
print(f"Reduced by {result['stats']['bytes_original'] - result['stats']['bytes_filtered']} bytes")
print(f"PII detected: {result['pii_detected']}")
```

### API Response Processing

```python
from orchestrator.execution import DataFilter, PIITokenizer

# Large API response
api_response = {
    "status": "success",
    "data": {
        "records": [...],  # 1000s of records
        "metadata": {...}
    }
}

# Step 1: Filter to manageable size
filter = DataFilter(FilterConfig(max_rows=50, max_bytes=20000))
filtered = filter.apply(api_response)

# Step 2: Tokenize PII
tokenizer = PIITokenizer()
sanitized = tokenizer.tokenize(filtered["data"])

# Result: Small, safe data for model context
```

### Log File Processing

```python
from orchestrator.execution import filter_and_tokenize, FilterConfig

# Process large log file
log_data = {
    "logs": [
        f"User user{i}@company.com logged in from 192.168.1.{i}"
        for i in range(10000)
    ]
}

# Keep only recent logs, tokenize IPs
result = filter_and_tokenize(
    log_data,
    filter_config=FilterConfig(max_rows=100),
    tokenize_pii=True  # Tokenizes IPs and emails
)

# Safe to pass to model
safe_logs = result["data"]
```

## Configuration Options

### FilterConfig

```python
FilterConfig(
    max_bytes=50000,         # Max output size in bytes (None = unlimited)
    max_rows=1000,           # Max rows for tabular data
    max_items=1000,          # Max items for lists/arrays
    truncate_strings=True,   # Truncate long strings
    max_string_length=1000,  # Max string length
    summarize_truncated=True,# Include truncation summary
    preserve_structure=True  # Keep data structure (keys, types)
)
```

### TokenizationConfig

```python
from orchestrator.execution import PIIType

TokenizationConfig(
    enabled_types={          # PII types to detect
        PIIType.EMAIL,
        PIIType.PHONE,
        PIIType.SSN,
        PIIType.CREDIT_CARD,
        PIIType.IP_ADDRESS,
        # PIIType.NAME,      # (coming soon)
        # PIIType.ADDRESS,   # (coming soon)
    },
    token_prefix="TOKEN_",   # Prefix for generated tokens
    preserve_format=True,    # Keep token format similar
    case_sensitive=False     # Case-sensitive matching
)
```

## PII Types Detected

| Type | Pattern | Example |
|------|---------|---------|
| EMAIL | Standard email format | user@example.com |
| PHONE | US phone numbers | 555-123-4567, (555) 123-4567 |
| SSN | Social Security Number | 123-45-6789 |
| CREDIT_CARD | 16-digit card numbers | 4532-1234-5678-9010 |
| IP_ADDRESS | IPv4 addresses | 192.168.1.100 |

## Advanced Usage

### Detokenization (Secure Context)

```python
tokenizer = PIITokenizer()

# Tokenize
original = {"email": "user@example.com"}
tokenized = tokenizer.tokenize(original)

# Later, in secure context, detokenize
restored = tokenizer.detokenize(tokenized)
# {"email": "user@example.com"}

# Save token map for later
token_map = tokenizer.get_token_map()
```

### Custom PII Types

```python
# Extend PIITokenizer with custom patterns (future feature)
# tokenizer.add_pattern("API_KEY", r"sk-[a-zA-Z0-9]{32}")
```

### Progressive Filtering

```python
# Filter in stages for very large data
filter_stage1 = DataFilter(FilterConfig(max_rows=1000))
filter_stage2 = DataFilter(FilterConfig(max_bytes=50000))

result1 = filter_stage1.apply(huge_data)
result2 = filter_stage2.apply(result1["data"])
```

## Integration with Sandbox Execution

```python
from orchestrator.execution import (
    SandboxEnvironment,
    filter_and_tokenize,
    FilterConfig
)

# Execute code in sandbox
sandbox = SandboxEnvironment()
exec_result = sandbox.execute(code)

# Filter output before returning to model
filtered = filter_and_tokenize(
    exec_result.output,
    filter_config=FilterConfig(max_bytes=20000),
    tokenize_pii=True
)

# Return safe, compact result
return filtered["data"]
```

## Best Practices

1. **Filter First, Tokenize Second**: Apply size limits before PII detection
2. **Choose Appropriate Limits**: Balance context size vs information loss
3. **Token Map Security**: Store token maps securely, don't expose to model
4. **Test with Real Data**: Validate filtering on actual use cases
5. **Monitor Stats**: Track truncation to tune limits

## Token Cost Reduction

Typical reductions from real-world data:

- Database queries: **60-90%** reduction
- API responses: **50-80%** reduction
- Log files: **70-95%** reduction
- Large JSON: **40-70%** reduction

Example:
```python
result = filter_and_tokenize(large_data)
original = result["stats"]["bytes_original"]
filtered = result["stats"]["bytes_filtered"]
reduction = 100 * (1 - filtered / original)
print(f"Reduced by {reduction:.1f}%")
```

## Security Considerations

- PII tokens are **deterministic** (same value → same token) for consistency
- Tokens use **SHA-256 hash** of original value
- Token maps should be stored **securely** (not in model context)
- Detokenization should only occur in **secure, audited contexts**
- Consider regulations (GDPR, CCPA, HIPAA) when handling PII

## Performance

- Filtering: O(n) where n = data size
- PII detection: O(n × p) where p = number of patterns
- Typical overhead: **<100ms for 1MB data**
- Memory efficient: streaming for large structures

## Troubleshooting

### "Max depth exceeded"
Deeply nested data structures (>10 levels) are truncated automatically.

### "Token not found in map"
Clear token map between sessions: `tokenizer.clear_tokens()`

### False Positives
Adjust patterns or disable specific PII types in config.

### Over-truncation
Increase limits in FilterConfig or disable summarization.

## See Also

- [Sandbox Execution](./sandbox-execution.md)
- [Code-Mode Security](./code-mode-security.md)
- [Tool Discovery](./discovering-tools.md)
