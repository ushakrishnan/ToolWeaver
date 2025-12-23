# Example 1: Basic Receipt Processing

## What This Does

Demonstrates the simplest way to register and use a tool with ToolWeaver. This example shows:
- Registering a receipt OCR tool using the `@mcp_tool` decorator
- Discovering tools using `search_tools()`
- Calling the tool to extract text from a receipt image

**Complexity:** ⭐ Basic  
**Concepts:** Tool registration, tool discovery, tool execution  
**Time:** 5 minutes

## What You'll Learn

- How to register a tool using `@mcp_tool`
- How to search for tools using `search_tools()`
- How to execute a registered tool directly
- Basic tool definition with parameters and return types

## Prerequisites

- Python 3.10+
- No external API keys required (uses mock data)

## Setup

1. Install ToolWeaver:
```bash
pip install -e ../..
```

2. (Optional) For real Azure Computer Vision:
```bash
# Edit .env with your Azure CV credentials
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your-key-here
```

## Run

```bash
# With mock data (no Azure account needed)
python process_receipt.py

# With real Azure Computer Vision (if configured)
python process_receipt.py
```

## Expected Output

```
============================================================
EXAMPLE 1: Basic Receipt Processing
============================================================

🔍 Searching for receipt tools...
   Found 1 tool(s)

📝 Using tool: receipt_ocr
   Description: Extract text from receipt images

🚀 Processing receipt...

✅ Result:
   Confidence: 95.0%
   Lines extracted: 12

📄 Extracted Text:
RESTAURANT XYZ
    Date: 2024-01-15

    Burger       $12.99
    Fries        $ 4.50
    Soda         $ 2.50
    -------------
    Subtotal:    $19.99
    Tax (8%):    $ 1.60
    -------------
    TOTAL:       $21.59

    Thank you!

============================================================
```

## What's Happening

1. **Tool Registration** - `@mcp_tool` decorator registers `receipt_ocr` function
2. **Tool Discovery** - `search_tools(query="receipt")` finds registered tool
3. **Tool Execution** - Direct function call with parameters dict
4. **Result** - Structured dict with extracted text, confidence, and line count

## Code Walkthrough

```python
# 1. Register a tool
@mcp_tool(domain="receipts", description="Extract text from receipt images")
async def receipt_ocr(image_uri: str) -> dict:
    # Tool implementation
    return {"text": "...", "confidence": 0.95, "line_count": 12}

# 2. Search for tools
tools = search_tools(query="receipt")

# 3. Execute the tool
result = await receipt_ocr({"image_uri": "https://example.com/receipt.jpg"})
```

## Next Steps

- Try [02-receipt-with-categorization](../02-receipt-with-categorization) to parse and categorize items
- Explore [04-vector-search-discovery](../04-vector-search-discovery) for semantic tool search
- Check [05-workflow-library](../05-workflow-library) for YAML-based tool workflows
