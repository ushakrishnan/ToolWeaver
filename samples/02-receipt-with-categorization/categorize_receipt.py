"""
Example 2: Receipt with Categorization

Demonstrates multi-step workflow using tool chaining:
- Register multiple tools (@mcp_tool)
- Chain tools together (OCR -> Parse -> Categorize -> Stats)
- Show how to build complex workflows from simple tools
"""

import asyncio
import json
from typing import Dict, List, Any

from orchestrator import mcp_tool, search_tools


# ============================================================
# Tool 1: OCR - Extract text from receipt image
# ============================================================
@mcp_tool(domain="receipts", description="Extract text from receipt images")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract text from a receipt image using OCR."""
    # Mock OCR result with realistic receipt text
    mock_receipt_text = """GROCERY MART
Date: 2024-01-15

Milk 2%              $3.99
Eggs Large 12ct      $4.50
Bread Whole Wheat    $2.99
Chicken Breast 2lb   $12.98
Apples Gala 3lb      $5.97
Shampoo              $8.99
Toothpaste           $4.49
-------------
Subtotal:           $43.91
Tax (8%):           $ 3.51
-------------
TOTAL:              $47.42

Thank you!"""
    
    return {
        "text": mock_receipt_text.strip(),
        "confidence": 0.96,
        "line_count": 18
    }


# ============================================================
# Tool 2: Parser - Extract line items from text
# ============================================================
@mcp_tool(domain="receipts", description="Parse line items from receipt text")
async def line_item_parser(text: str) -> dict:
    """Parse receipt text into structured line items."""
    # Simple keyword-based parsing (could use LLM for smarter parsing)
    lines = text.split('\n')
    items = []
    
    # Look for lines with prices (dollar sign + amount)
    import re
    price_pattern = r'\$\s*(\d+\.\d{2})'
    
    for line in lines:
        price_match = re.search(price_pattern, line)
        if price_match and not any(keyword in line.lower() for keyword in ['subtotal', 'tax', 'total', 'thank']):
            price = float(price_match.group(1))
            # Extract item name (everything before the price)
            name = line[:price_match.start()].strip()
            if name:
                items.append({
                    "name": name,
                    "price": price,
                    "raw_line": line.strip()
                })
    
    return {
        "items": items,
        "item_count": len(items),
        "parsing_method": "keyword_based"
    }


# ============================================================
# Tool 3: Categorizer - Categorize expenses
# ============================================================
@mcp_tool(domain="receipts", description="Categorize expense items")
async def expense_categorizer(items: List[Dict[str, Any]]) -> dict:
    """Categorize expense items into food, household, etc."""
    # Simple rule-based categorization
    categories = {
        "food": ["milk", "eggs", "bread", "chicken", "apples", "grocery"],
        "household": ["shampoo", "toothpaste", "soap", "detergent", "cleaner"],
        "other": []
    }
    
    categorized_items = []
    category_totals = {"food": 0.0, "household": 0.0, "other": 0.0}
    
    for item in items:
        name_lower = item["name"].lower()
        assigned_category = "other"
        
        # Match against category keywords
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                assigned_category = category
                break
        
        categorized_item = {
            **item,
            "category": assigned_category
        }
        categorized_items.append(categorized_item)
        category_totals[assigned_category] += item["price"]
    
    return {
        "items": categorized_items,
        "category_totals": category_totals,
        "categorization_method": "rule_based"
    }


# ============================================================
# Tool 4: Statistics - Compute summary statistics
# ============================================================
@mcp_tool(domain="receipts", description="Compute receipt statistics")
async def compute_statistics(items: List[Dict[str, Any]], category_totals: Dict[str, float]) -> dict:
    """Compute summary statistics for categorized items."""
    if not items:
        return {
            "total_amount": 0.0,
            "item_count": 0,
            "avg_amount": 0.0,
            "categories": {}
        }
    
    total = sum(item["price"] for item in items)
    count = len(items)
    avg = total / count if count > 0 else 0.0
    
    # Category breakdowns
    categories_detail = {}
    for category, cat_total in category_totals.items():
        cat_items = [item for item in items if item.get("category") == category]
        categories_detail[category] = {
            "total": cat_total,
            "count": len(cat_items),
            "percentage": (cat_total / total * 100) if total > 0 else 0.0
        }
    
    return {
        "total_amount": total,
        "item_count": count,
        "avg_amount": avg,
        "categories": categories_detail
    }


# ============================================================
# Main Workflow - Chain tools together
# ============================================================
async def main():
    """Run receipt categorization workflow."""
    print("=" * 60)
    print("EXAMPLE 2: Receipt with Categorization")
    print("=" * 60)
    print()
    
    print("📝 Workflow Overview:")
    print("   Step 1: Extract text from receipt (OCR)")
    print("   Step 2: Parse line items")
    print("   Step 3: Categorize expenses")
    print("   Step 4: Compute statistics")
    print()
    
    # Step 1: OCR
    print("🔍 Step 1: Extracting text from receipt...")
    ocr_result = await receipt_ocr({"image_uri": "https://example.com/receipts/grocery.jpg"})
    print(f"   ✓ Extracted {ocr_result['line_count']} lines (confidence: {ocr_result['confidence']*100:.1f}%)")
    print()
    
    # Step 2: Parse items
    print("📋 Step 2: Parsing line items...")
    parse_result = await line_item_parser({"text": ocr_result["text"]})
    print(f"   ✓ Found {parse_result['item_count']} items")
    print()
    
    # Step 3: Categorize
    print("🏷️  Step 3: Categorizing expenses...")
    categorize_result = await expense_categorizer({"items": parse_result["items"]})
    print(f"   ✓ Categorized into {len(categorize_result['category_totals'])} categories")
    print()
    
    # Step 4: Compute statistics
    print("📊 Step 4: Computing statistics...")
    stats_result = await compute_statistics({
        "items": categorize_result["items"],
        "category_totals": categorize_result["category_totals"]
    })
    print("   ✓ Statistics computed")
    print()
    
    # Display summary
    print("=" * 60)
    print("📄 FINAL RESULTS")
    print("=" * 60)
    print()
    
    print(f"💰 Total Amount: ${stats_result['total_amount']:.2f}")
    print(f"🧾 Item Count: {stats_result['item_count']}")
    print(f"📈 Average per Item: ${stats_result['avg_amount']:.2f}")
    print()
    
    print("📊 By Category:")
    for category, details in stats_result['categories'].items():
        if details['count'] > 0:
            print(f"   {category.upper()}:")
            print(f"      Total: ${details['total']:.2f} ({details['percentage']:.1f}%)")
            print(f"      Items: {details['count']}")
    print()
    
    print("🛒 Item Details:")
    for item in categorize_result['items']:
        print(f"   • {item['name']:25} ${item['price']:6.2f}  [{item['category']}]")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
