# Development Guide (Contributors)

- Use Python 3.10+ and `pip install -e "./[dev]"`.
- Keep implementation in `orchestrator._internal` when it is not public API.
- Public API lives in `orchestrator/__init__.py`; add exports deliberately.
- Logging: `from orchestrator._internal.logger import get_logger`.
- Optional deps: guard with `_internal.errors` helpers.
- Run `pytest` and `mypy` before PRs.

## CI Overview

- Workflow: see [.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- Jobs:
	- Matrix: Ubuntu/Windows/macOS × Python 3.10–3.12
	- Lint: `ruff check .`
	- Types: `mypy orchestrator`
	- Tests: `pytest` with coverage gates and XML/HTML reports
	- Codecov: uploads `coverage.xml` (requires `CODECOV_TOKEN` secret)
	- Internal import lint on examples: prevents `orchestrator._internal` usage in public code

## Release Workflow

- Tags: pushing `v*.*.*` triggers [.github/workflows/release.yml](../../.github/workflows/release.yml)
- Build: `python -m build` → sdist + wheel
- Publish: `pypa/gh-action-pypi-publish` (requires `PYPI_API_TOKEN`)

## Coverage Policy

- Pytest gate: `--cov-fail-under=75` (ratchet ↑ to 80%+)
- Codecov: project ≈75%, patch ≈80% with small thresholds

## Pre-PR Checklist

- Tests pass locally (`pytest`)
- Type checks pass (`mypy orchestrator`)
- No public imports from `_internal` in examples
- Public API additions documented and scoped in `__all__`
