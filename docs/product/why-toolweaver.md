# Why ToolWeaver

## Designed for production
- Package-first: pip install and use inside your apps—no heavy framework
- Guardrails built in: cost caps, concurrency, failure thresholds, timeouts
- Safe by default: secrets redactor, PII filtering, template sanitization, sandbox

## Developer experience
- Three ways to register tools: decorators, templates, YAML
- Discovery/search: domain, keywords, semantic search
- Aggregation patterns: majority vote, rank by metric, best result, collect-all

## Performance
- Dual-layer cache with file fallback
- Idempotency caching for instant replays
- Demonstrated speedups in tutorials (1.7x for batch parallelism)

## Fit
- Use with planners or call programmatically
- Expose tools via REST quickly (FastAPI adapter)
- Extend via plugins and share via skills

See:
- [Product Overview](overview.md)
- [Tutorials](../tutorials/parallel-agents.md)
- [Public API](../reference/api-python/overview.md)
