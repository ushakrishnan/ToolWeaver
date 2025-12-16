# Example 1: Basic Receipt Processing

## What This Does

Processes a single receipt image using Azure Computer Vision OCR to extract text.

**Complexity:** ⭐ Basic  
**Concepts:** MCP workers, execution plans  
**Time:** 5 minutes

## What You'll Learn

- How to create a simple execution plan
- Using MCP workers (receipt_ocr)
- Basic orchestrator execution

## Prerequisites

- Azure Computer Vision resource (or use mock mode)
- Python 3.10+

## Setup

1. Copy `.env` to parent directory or configure:
```bash
cp .env ../../.env
# Edit ../../.env with your Azure CV endpoint
```

2. Install ToolWeaver:
```bash
pip install -e ../..
```

## Run

```bash
# With real Azure Computer Vision
python process_receipt.py

# With mock data (no Azure account needed)
OCR_MODE=mock python process_receipt.py
```

## Expected Output

```json
{
  "steps": {
    "extract_text": {
      "text": "RESTAURANT XYZ\\nDate: 2024-01-15\\nBurger $12.99\\nFries $4.50\\nTotal: $17.49",
      "confidence": 0.95
    }
  }
}
```

## What's Happening

1. **Plan definition** - JSON with single step
2. **OCR execution** - Azure Computer Vision extracts text
3. **Result** - Structured JSON with extracted text and confidence

## Next Steps

- Try with your own receipt images
- Explore [02-receipt-with-categorization](../02-receipt-with-categorization) to parse and categorize items
