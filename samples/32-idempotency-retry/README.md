# Idempotency & Retry (Dispatch)

Demonstrates parallel dispatch with idempotency caching, per-agent timeouts, and rate limiting.

## Run
```bash
python samples/32-idempotency-retry/idempotency_retry_demo.py
```

## Prerequisites
- Install from PyPI:
```bash
pip install toolweaver
```

## What it shows
- Repeated arguments produce cache hits
- Slow tasks time out and count as failures
- Rate limiting controls request pace
