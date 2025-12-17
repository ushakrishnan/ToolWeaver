# Sample 2: Receipt with Categorization

> Status: PyPI package refresh is in progress. This sample may lag behind the latest source; for the most up-to-date code paths, use [examples/](../../examples/). Samples will be regenerated after the refresh.
> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


## What This Does

Processes a receipt end-to-end: OCR → Parse line items → Categorize expenses → Compute statistics.

**Complexity:** ⭐⭐ Intermediate  
**Concepts:** Multi-step plans, dependencies, small models, function calls  
**Time:** 10 minutes

## What You'll Learn

- Multi-step execution plans with dependencies
- Small model workers (Phi-3 via Ollama)
- Function calls for business logic
- Step output references (`step:step_id`)

## Prerequisites

- Azure Computer Vision (or mock mode)
- Ollama with Phi-3 model (optional, falls back to keyword matching)

## Setup

1. **Install Ollama (optional for small models):**
```bash
# Download from https://ollama.ai

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

ollama pull phi3
```

2. **Configure environment:**
```bash
cp .env ../../.env
# Edit if using real Azure CV

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

```

3. **Install ToolWeaver:**
```bash
pip install -e ../..
```

## Run

```bash
# With Ollama + mock OCR

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

python categorize_receipt.py

# Without Ollama (keyword matching)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

USE_SMALL_MODEL=false python categorize_receipt.py

# With real Azure CV

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

OCR_MODE=azure python categorize_receipt.py
```

## Expected Output

```json
{
  "extract_text": {
    "text": "GROCERY STORE\\nBread $3.99\\nMilk $4.50\\nBananas $2.99"
  },
  "parse_items": {
    "items": [
      {"name": "Bread", "price": 3.99},
      {"name": "Milk", "price": 4.50},
      {"name": "Bananas", "price": 2.99}
    ]
  },
  "categorize": {
    "categorized_items": [
      {"name": "Bread", "price": 3.99, "category": "Food"},
      {"name": "Milk", "price": 4.50, "category": "Groceries"},
      {"name": "Bananas", "price": 2.99, "category": "Groceries"}
    ]
  },
  "compute_stats": {
    "total": 11.48,
    "count": 3,
    "avg": 3.83,
    "by_category": {
      "Food": 3.99,
      "Groceries": 7.49
    }
  }
}
```

## What's Happening

1. **Step 1 (OCR)** - Extract text from receipt image
2. **Step 2 (Parse)** - Phi-3 parses line items from text
3. **Step 3 (Categorize)** - Phi-3 assigns categories to items
4. **Step 4 (Stats)** - Function call computes aggregated statistics

**Dependency Flow:**
```
extract_text → parse_items → categorize → compute_stats
```

## Cost Comparison

| Configuration | Cost | Speed |
|--------------|------|-------|
| **Phi-3 (Ollama)** | $0.002 | ~3 sec |
| **GPT-4o (all steps)** | $0.15 | ~8 sec |
| **Keyword matching** | $0.002 | ~1 sec |

💡 **98% cost savings** with Phi-3 for parsing/categorization!

## Next Steps

- Try with your own receipts
- Explore [03-batch-processing](../03-batch-processing) for parallel execution
- See [04-github-operations](../04-github-operations) for GitHub integration
