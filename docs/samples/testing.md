# Testing the Samples

How to run and validate the curated samples.

## Pre-checks
- Verify dependencies: `python scripts/verify_install.py`
- Ensure each sample has `.env` (copy from `.env.example` where provided) and `requirements.txt` installed.

## Run a single sample
```bash
cd samples/01-basic-receipt-processing
python process_receipt.py
```
Expect: completes without import errors; outputs parsed receipt data.

## Run all samples (batch)
```bash
cd samples
python test_all_examples.py
```
What it does: discovers sample dirs, runs primary script with timeouts, reports success/failure summary.

## Env/provider notes
- Basic/no-API samples: set `OCR_MODE=mock` when available (e.g., sample 01) to avoid external calls.
- LLM-required samples: set `OPENAI_API_KEY` or `AZURE_OPENAI_KEY` (e.g., 02, 10, 22).
- GitHub samples: set `GITHUB_TOKEN` (e.g., 03, 19, 20).
- Parallel/agent samples: watch async output and timing (e.g., 16, 17, 25).

## Verification checklist (per sample)
- README present and purpose clear
- requirements installed
- .env configured
- Runs to completion (<60s for basics) with sensible output
- Links in README work

## Troubleshooting
- Import error `No module named orchestrator`: run `pip install -e " .[dev]"` from repo root.
- Auth errors: populate `.env` with required keys.
- Hangs/timeouts: run with a timeout; check network/backends.
