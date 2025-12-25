# Migration Guide

Notes for upgrading between ToolWeaver versions.

General steps
- Pin versions in production; test upgrades in staging.
- Review changelog for breaking changes (API signatures, env vars).
- Re-run `load_tools_from_directory` to validate YAML schemas after upgrades.

Common areas to check
- Decorator/template parameters that tightened validation.
- Registry/discovery defaults (top-k, thresholds).
- Analytics backend env vars (e.g., OTLP/Prometheus flags).
- Cache locations and TTL defaults.

Testing
- Run unit tests and `examples/test_all_examples.py` with representative env vars.
- Validate REST endpoints if you expose the FastAPI adapter.
