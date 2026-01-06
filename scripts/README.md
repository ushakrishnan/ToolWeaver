# Scripts

Supported utility scripts for validation and hygiene.

## check_no_internal_imports.py
- Purpose: Ensure `samples/` do not import internal `orchestrator.*` modules.
- CI: Invoked in `.github/workflows/ci.yml`.
- Usage:
	```powershell
	python scripts/check_no_internal_imports.py samples
	```

## check_links.py
- Purpose: Verify external links in `docs/` are not broken (HTTP 4xx/5xx).
- Usage:
	```powershell
	python scripts/check_links.py
	```

## verify_install.py
- Purpose: Quick import sanity check for required and optional deps.
- Usage:
	```powershell
	python scripts/verify_install.py
	```

Notes:
- These scripts are kept minimal and are part of routine checks.
- For automated tests, use:
	```powershell
	pytest tests/ -v
	```
