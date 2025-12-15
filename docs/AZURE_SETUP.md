# Azure Computer Vision Setup Guide

## Overview
This project uses **Azure Computer Vision OCR (Read API)** to extract text from receipt images. You can run in either mock mode (for testing) or with real Azure Computer Vision.

## Option 1: Mock Mode (Default)
No setup needed! The system uses fake receipt data for testing.

## Option 2: Azure Computer Vision (Real OCR)

### Step 1: Create Azure Computer Vision Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource**
3. Search for **Computer Vision**
4. Click **Create** and fill in:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose closest to you (e.g., East US)
   - **Name**: `my-receipt-ocr` (or any unique name)
   - **Pricing Tier**: 
     - **Free (F0)**: 5,000 transactions/month, 20/min
     - **Standard (S1)**: Pay-as-you-go, $1 per 1,000 transactions
5. Click **Review + Create**, then **Create**

### Step 2: Get Your Credentials

1. Once deployed, go to your Computer Vision resource
2. Click **Keys and Endpoint** in the left menu
3. Copy:
   - **Endpoint**: `https://your-resource-name.cognitiveservices.azure.com/`
   - **Key 1**: Your API key (keep this secret!)

### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   AZURE_CV_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
   AZURE_CV_KEY=your-actual-api-key-here
   OCR_MODE=azure
   ```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test It

```bash
python run_demo.py
```

The system will now use real Azure Computer Vision to extract text from images!

## Pricing

### Azure Computer Vision - Read API
- **Free Tier (F0)**: 
  - 5,000 transactions/month
  - 20 requests/minute
  - Perfect for development and testing

- **Standard Tier (S1)**:
  - $1.00 per 1,000 transactions (first 1M)
  - $0.65 per 1,000 transactions (1M-10M)
  - $0.40 per 1,000 transactions (10M+)
  - Up to 10 requests/second

### Cost Examples
- 100 receipts/day = ~3,000/month = **FREE** (within free tier)
- 500 receipts/day = ~15,000/month = **$10/month**
- 1,000 receipts/day = ~30,000/month = **$30/month**

## Using Your Own Images

Update the example plans with your image URLs:

```json
{
  "tool": "receipt_ocr",
  "input": {
    "image_uri": "https://your-domain.com/receipts/receipt1.jpg"
  }
}
```

**Supported formats**: JPG, PNG, BMP, PDF (first page)
**Max file size**: 50 MB
**Image requirements**: Minimum 50x50 pixels

## Troubleshooting

### Error: "Azure CV credentials not configured"
- Make sure `.env` file exists
- Verify `AZURE_CV_ENDPOINT` and `AZURE_CV_KEY` are set
- Set `OCR_MODE=azure`

### Error: "Module 'azure.ai.vision.imageanalysis' not found"
- Run: `pip install -r requirements.txt`

### Error: "Access denied" or "Invalid subscription key"
- Verify your API key is correct
- Check that your Azure resource is active
- Ensure your subscription has available credits

### Using Local Images
Azure Computer Vision requires publicly accessible URLs. For local images:
1. Upload to Azure Blob Storage
2. Use Azure Storage SAS URLs
3. Or use a temporary hosting service for testing

## Switching Between Modes

Edit `.env`:
- **Mock mode**: `OCR_MODE=mock` (or comment out)
- **Azure mode**: `OCR_MODE=azure`

No code changes needed!

## Security Best Practices

1. ✅ Never commit `.env` file to git (already in `.gitignore`)
2. ✅ Rotate API keys periodically
3. ✅ Use Azure Key Vault for production
4. ✅ Enable Azure Monitor to track usage
5. ✅ Set up spending alerts in Azure Portal

## Next Steps

- [ ] Create your Azure Computer Vision resource
- [ ] Configure `.env` with your credentials
- [ ] Test with your own receipt images
- [ ] Monitor usage in Azure Portal
- [ ] Scale up to Standard tier if needed

## Resources

- [Azure Computer Vision Documentation](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/)
- [Read API Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/quickstarts-sdk/client-library?pivots=programming-language-python)
- [Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
