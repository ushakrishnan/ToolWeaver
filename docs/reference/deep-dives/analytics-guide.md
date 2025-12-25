# Analytics Guide

Choose a metrics backend and understand what is emitted.

Backends
- OTLP (Grafana Cloud): managed, simple; push over HTTP.
- Prometheus: self-hosted scrape; exposes /metrics.
- SQLite: local dev, file-based.

Metrics
- Execution counts (success/failure)
- Latency histogram
- Ratings and health scores

Setup
- Select backend via env (`ANALYTICS_BACKEND=otlp|prometheus|sqlite`).
- For OTLP: set endpoint, instance id, token, push interval.
- For Prometheus: enable metrics server (host/port) and configure scrape job.

Operational tips
- Prefer OTLP/Prometheus in production; SQLite only for local dev.
- Watch cardinality; keep metric labels bounded.
- Use alerts on error rate and latency p95/p99.
