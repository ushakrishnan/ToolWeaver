# Azure Computer Vision Setup

Use Azure Computer Vision OCR (Read API) for receipt extraction; mock mode stays available for tests.

## Option 1: Mock mode (default)
No setup needed. Uses fake receipt data.

## Option 2: Real Azure Computer Vision
1. Create resource in Azure Portal → Computer Vision (choose region, name, pricing tier).
2. Get credentials: endpoint + key.
3. Configure env:
```
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-key
OCR_MODE=azure
```
4. Install deps: `pip install -e .` (from repo root).
5. Test: `python run_demo.py` (or your receipt workflow).

Pricing (Read API)
- Free F0: 5,000 tx/mo, 20/min.
- S1: ~$1 per 1k (first 1M), cheaper at higher volumes.

Using your own images
Update the input plan with your image URL (JPG/PNG/BMP/PDF first page, <=50 MB).

Security best practices
- Keep `.env` out of git; rotate keys; prefer Key Vault in production; enable Azure Monitor + spending alerts.

Troubleshooting
- "credentials not configured": check env vars + OCR_MODE.
- Module missing: install requirements.
- Access denied: verify key/region and subscription status.
- Local images: host via blob SAS or any temporary HTTPS URL.

Switching modes
- Mock: `OCR_MODE=mock` (or unset)
- Azure: `OCR_MODE=azure`
