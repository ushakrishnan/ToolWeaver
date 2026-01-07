"""
Demo 1: Naive Approach - Using Only Large Language Models

This demo shows what happens when you call GPT-4o for EVERY step.
Result: Works, but expensive and slow.

Cost Breakdown:
  - receipt_ocr (GPT-4o vision): $0.01
  - line_item_parser (GPT-4o): $0.03
  - expense_categorizer (GPT-4o): $0.03
  - compute_statistics (GPT-4o): $0.03
  ────────────────────────────────
  TOTAL per receipt: $0.10
"""

import asyncio

from orchestrator import mcp_tool


# Mock GPT-4o calls (in reality, these would call Azure OpenAI)
@mcp_tool(
    domain="ocr",
    description="Extract text from receipt images using GPT-4o vision"
)
async def gpt4o_receipt_ocr(image_uri: str) -> dict:
    """GPT-4o vision call for OCR. Cost: $0.01"""
    # Simulate API latency
    await asyncio.sleep(0.5)
    return {
        "text": """WHOLE FOODS MARKET
2024-01-15 15:30

Milk 2%                    $3.99
Eggs Large 12ct            $4.50
Organic Chicken Breast     $12.99
Spinach Organic            $2.50
Almond Butter              $8.99
Greek Yogurt Plain 32oz    $6.00
Baby Carrots 2lb           $1.50

Subtotal:      $40.47
Tax (8.875%):  $3.59
────────────────────
TOTAL:         $44.06

Thank you!""",
        "confidence": 0.98,
        "cost": "$0.01"
    }


@mcp_tool(
    domain="parsing",
    description="Parse line items from receipt text using GPT-4o"
)
async def gpt4o_line_item_parser(receipt_text: str) -> dict:
    """GPT-4o call to parse items. Cost: $0.03"""
    # Simulate API latency
    await asyncio.sleep(0.3)
    return {
        "items": [
            {"name": "Milk 2%", "price": 3.99},
            {"name": "Eggs Large 12ct", "price": 4.50},
            {"name": "Organic Chicken Breast", "price": 12.99},
            {"name": "Spinach Organic", "price": 2.50},
            {"name": "Almond Butter", "price": 8.99},
            {"name": "Greek Yogurt Plain 32oz", "price": 6.00},
            {"name": "Baby Carrots 2lb", "price": 1.50}
        ],
        "item_count": 7,
        "cost": "$0.03"
    }


@mcp_tool(
    domain="categorization",
    description="Categorize expense items using GPT-4o"
)
async def gpt4o_expense_categorizer(items: list) -> dict:
    """GPT-4o call to categorize. Cost: $0.03"""
    # Simulate API latency
    await asyncio.sleep(0.4)
    return {
        "items": [
            {"name": "Milk 2%", "price": 3.99, "category": "food"},
            {"name": "Eggs Large 12ct", "price": 4.50, "category": "food"},
            {"name": "Organic Chicken Breast", "price": 12.99, "category": "food"},
            {"name": "Spinach Organic", "price": 2.50, "category": "food"},
            {"name": "Almond Butter", "price": 8.99, "category": "food"},
            {"name": "Greek Yogurt Plain 32oz", "price": 6.00, "category": "food"},
            {"name": "Baby Carrots 2lb", "price": 1.50, "category": "food"}
        ],
        "categories": {"food": 7},
        "cost": "$0.03"
    }


@mcp_tool(
    domain="statistics",
    description="Compute expense statistics using GPT-4o"
)
async def gpt4o_compute_statistics(categorized_items: list) -> dict:
    """GPT-4o call to compute stats. Cost: $0.03"""
    # Simulate API latency
    await asyncio.sleep(0.2)
    return {
        "total_amount": 44.06,
        "item_count": 7,
        "by_category": {
            "food": {
                "count": 7,
                "total": 44.06,
                "avg": 6.29
            }
        },
        "cost": "$0.03"
    }


async def main():
    """Run the naive all-LLM approach."""
    print("=" * 70)
    print("DEMO 1: Naive Approach - All Calls to GPT-4o")
    print("=" * 70)
    print()
    print("❌ Problem: Every step calls an expensive LLM")
    print()

    start_time = asyncio.get_event_loop().time()

    # Step 1: Extract text with GPT-4o
    print("[1/4] Calling GPT-4o Vision for OCR...")
    ocr_result = await gpt4o_receipt_ocr({"image_uri": "https://example.com/receipt.jpg"})
    print(f"      ✓ Extracted {len(ocr_result['text'].split())} words")
    print(f"      Cost: {ocr_result['cost']}")
    print()

    # Step 2: Parse items with GPT-4o
    print("[2/4] Calling GPT-4o to parse items...")
    parser_result = await gpt4o_line_item_parser({"receipt_text": ocr_result["text"]})
    print(f"      ✓ Parsed {parser_result['item_count']} items")
    print(f"      Cost: {parser_result['cost']}")
    print()

    # Step 3: Categorize with GPT-4o
    print("[3/4] Calling GPT-4o to categorize expenses...")
    categorizer_result = await gpt4o_expense_categorizer({"items": parser_result["items"]})
    print(f"      ✓ Categorized items: {categorizer_result['categories']}")
    print(f"      Cost: {categorizer_result['cost']}")
    print()

    # Step 4: Compute statistics with GPT-4o
    print("[4/4] Calling GPT-4o to compute statistics...")
    stats_result = await gpt4o_compute_statistics({"categorized_items": categorizer_result["items"]})
    print(f"      ✓ Total: ${stats_result['total_amount']:.2f}")
    print(f"      Cost: {stats_result['cost']}")
    print()

    elapsed_time = asyncio.get_event_loop().time() - start_time

    # Summary
    print("=" * 70)
    print("COST BREAKDOWN")
    print("=" * 70)
    print("  OCR (GPT-4o vision):      $0.01")
    print("  Parsing (GPT-4o):         $0.03")
    print("  Categorization (GPT-4o):  $0.03")
    print("  Statistics (GPT-4o):      $0.03")
    print(f"  {'-' * 40}")
    print("  TOTAL PER RECEIPT:        $0.10")
    print()
    print(f"Time: {elapsed_time:.2f}s")
    print()
    print("⚠️  For 100 receipts: $10.00 cost")
    print("⚠️  All work done by expensive LLM")
    print("⚠️  No deterministic guarantee")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
