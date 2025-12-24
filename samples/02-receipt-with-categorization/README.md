# Example 2: Receipt with Categorization

## What This Does

Demonstrates building complex workflows by chaining multiple tools:
- OCR extraction → Parse items → Categorize expenses → Compute statistics
- Shows how to register multiple related tools
- Demonstrates passing data between tools
- Realistic multi-step business process

**Complexity:** ⭐⭐ Intermediate  
**Concepts:** Tool chaining, multiple @mcp_tool decorators, workflow composition  
**Time:** 10 minutes

## What You'll Learn

- Registering multiple tools with `@mcp_tool`
- Chaining tools together to build workflows
- Passing data between tool invocations
- Building realistic business processes from simple tools

## Prerequisites

- Python 3.10+
- No external API keys required (uses mock data)

## Setup

1. **Install ToolWeaver (from PyPI):**
```bash
pip install toolweaver==0.5.0
```

2. **(Optional) For real OCR:**
```bash
# Edit .env with your Azure Computer Vision credentials
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your-key-here
## Run

```bash
cd examples/02-receipt-with-categorization
python categorize_receipt.py
```

## Expected Output

```
============================================================
EXAMPLE 2: Receipt with Categorization
============================================================

📝 Workflow Overview:
   Step 1: Extract text from receipt (OCR)
   Step 2: Parse line items
   Step 3: Categorize expenses
   Step 4: Compute statistics

🔍 Step 1: Extracting text from receipt...
   ✓ Extracted 18 lines (confidence: 96.0%)

📋 Step 2: Parsing line items...
   ✓ Found 7 items

🏷️  Step 3: Categorizing expenses...
   ✓ Categorized into 3 categories

📊 Step 4: Computing statistics...
   ✓ Statistics computed

============================================================
📄 FINAL RESULTS
============================================================

💰 Total Amount: $43.91
🧾 Item Count: 7
📈 Average per Item: $6.27

📊 By Category:
   FOOD:
      Total: $30.43 (69.3%)
      Items: 5
   HOUSEHOLD:
      Total: $13.48 (30.7%)
      Items: 2
```

## What's Happening

1. **Tool Registration** - Four tools registered with `@mcp_tool`:
   - `receipt_ocr` - Extracts text from receipt images
   - `line_item_parser` - Parses text into structured items  
   - `expense_categorizer` - Categorizes items (food, household, etc.)
   - `compute_statistics` - Calculates totals and breakdowns

2. **Tool Chaining** - Tools are called in sequence:
   ```python
   ocr_result = await receipt_ocr({...})
   parse_result = await line_item_parser({"text": ocr_result["text"]})
   categorize_result = await expense_categorizer({"items": parse_result["items"]})
   stats = await compute_statistics({...})
   ```

3. **Data Flow:**
   ```
   receipt_ocr → line_item_parser → expense_categorizer → compute_statistics
   ```

## Code Walkthrough

```python
# Register tools
@mcp_tool(domain="receipts")
async def receipt_ocr(image_uri: str) -> dict: ...

@mcp_tool(domain="receipts")
async def line_item_parser(text: str) -> dict: ...

# Chain them
ocr_result = await receipt_ocr({"image_uri": "..."})
parse_result = await line_item_parser({"text": ocr_result["text"]})
```

## Next Steps

- Explore [03-github-operations](../03-github-operations) for external API integration
- See [04-vector-search-discovery](../04-vector-search-discovery) for semantic tool search  
- Check [09-code-execution](../09-code-execution) for programmatic tool execution
