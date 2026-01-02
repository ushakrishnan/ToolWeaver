"""
Example 1: Basic Receipt Processing

Demonstrates registering and using a simple MCP tool for receipt OCR.
This is the simplest example - shows tool registration and execution.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator import mcp_tool, search_tools


# Register a receipt OCR tool
@mcp_tool(domain="receipts", description="Extract text from receipt images")
async def receipt_ocr(image_uri: str) -> dict:
    """
    Extract text from a receipt image using OCR.

    Args:
        image_uri: URL or path to receipt image

    Returns:
        dict with 'text' and 'confidence' keys
    """
    # In production, this would call Azure CV API
    # For this demo, return mock data
    mock_receipt_text = """
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
    """

    return {
        "text": mock_receipt_text.strip(),
        "confidence": 0.95,
        "line_count": 12
    }


async def main():
    """Run basic receipt processing."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Receipt Processing")
    print("=" * 60)
    print()

    # Find the tool we just registered
    print("🔍 Searching for receipt tools...")
    tools = search_tools(query="receipt")
    print(f"   Found {len(tools)} tool(s)")
    print()

    if not tools:
        print("[X] No receipt tools found")
        return

    # Use the first tool
    tool_def = tools[0]
    print(f"📝 Using tool: {tool_def.name}")
    print(f"   Description: {tool_def.description}")
    print()

    # Execute the tool function directly
    print("🚀 Processing receipt...")
    result = await receipt_ocr({"image_uri": "https://example.com/receipts/sample-receipt.jpg"})

    print()
    print("[OK] Result:")
    print(f"   Confidence: {result['confidence']*100:.1f}%")
    print(f"   Lines extracted: {result['line_count']}")
    print()
    print("📄 Extracted Text:")
    print(result["text"])
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
