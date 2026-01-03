"""
Example 09: Code Execution with ToolWeaver

Demonstrates:
- Safe code execution through tools
- Receipt calculation and validation
- Data processing and transformation
- Error handling and validation

Use Case:
Execute computational tasks through a controlled, safe tool interface
"""

import asyncio
from typing import Any

from orchestrator import mcp_tool, search_tools

# ============================================================
# Code Execution Tools - Demonstrate Safe Computation Pattern
# ============================================================

@mcp_tool(domain="computation", description="Calculate receipt totals with tax")
async def calculate_receipt(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate receipt total with items and tax."""
    if not items:
        return {"error": "No items provided"}

    try:
        subtotal: float = 0.0
        item_count = 0

        for item in items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 1))
            subtotal += price * quantity
            item_count += quantity

        tax_rate = 0.08
        tax = subtotal * tax_rate
        total = subtotal + tax

        return {
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "item_count": item_count,
            "tax_rate": tax_rate
        }
    except (ValueError, TypeError) as e:
        return {"error": f"Calculation error: {str(e)}"}


@mcp_tool(domain="computation", description="Validate receipt data structure")
async def validate_receipt_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate that receipt data is structurally correct."""
    errors = []

    # Check required fields
    if not data.get("merchant"):
        errors.append("Missing merchant name")
    if not data.get("items"):
        errors.append("No items found")
    elif not isinstance(data.get("items"), list):
        errors.append("Items must be a list")

    # Check item structure
    if isinstance(data.get("items"), list):
        for i, item in enumerate(data["items"]):
            if not item.get("name"):
                errors.append(f"Item {i}: Missing name")
            try:
                float(item.get("price", 0))
            except (ValueError, TypeError):
                errors.append(f"Item {i}: Invalid price")

    # Check total if provided
    if "total" in data:
        try:
            item_total = sum(
                float(item.get("price", 0)) * int(item.get("quantity", 1))
                for item in data.get("items", [])
            )
            total_with_tax = item_total * 1.08
            if abs(float(data["total"]) - total_with_tax) > 0.01:
                errors.append(
                    f"Total mismatch: {data['total']} vs calculated {total_with_tax:.2f}"
                )
        except (ValueError, TypeError):
            errors.append("Invalid total value")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors)
    }


@mcp_tool(domain="computation", description="Transform currency values")
async def transform_prices(items: list[dict[str, Any]], multiplier: float = 1.0) -> dict[str, Any]:
    """Apply a transformation to all prices in items."""
    if not items:
        return {"error": "No items provided"}

    try:
        transformed = []
        for item in items:
            original_price = float(item.get("price", 0))
            new_price = round(original_price * multiplier, 2)
            transformed.append({
                "name": item.get("name", "Unknown"),
                "original_price": original_price,
                "new_price": new_price,
                "multiplier": multiplier
            })

        return {
            "items": transformed,
            "count": len(transformed),
            "multiplier": multiplier
        }
    except (ValueError, TypeError) as e:
        return {"error": f"Transform error: {str(e)}"}


@mcp_tool(domain="computation", description="Generate receipt summary report")
async def generate_receipt_report(receipt: dict[str, Any]) -> dict[str, Any]:
    """Generate a formatted receipt report."""
    report = []
    report.append("=" * 50)
    report.append("RECEIPT REPORT")
    report.append("=" * 50)

    # Merchant info
    report.append(f"\nMerchant: {receipt.get('merchant', 'N/A')}")
    report.append(f"Date: {receipt.get('date', 'N/A')}")

    # Items
    report.append("\nItems:")
    report.append("-" * 50)

    items = receipt.get("items", [])
    total_price: float = 0.0
    total_qty = 0

    for item in items:
        name = item.get("name", "Unknown")
        price = float(item.get("price", 0))
        qty = int(item.get("quantity", 1))
        item_total = price * qty
        total_price += item_total
        total_qty += qty

        report.append(f"  {name:20} x{qty:2} @ ${price:7.2f} = ${item_total:7.2f}")

    # Totals
    tax = total_price * 0.08
    final_total = total_price + tax

    report.append("-" * 50)
    report.append(f"  Subtotal: ${total_price:>40.2f}")
    report.append(f"  Tax (8%): ${tax:>40.2f}")
    report.append(f"  Total:    ${final_total:>40.2f}")
    report.append("=" * 50)

    return {
        "report": "\n".join(report),
        "item_count": len(items),
        "total_quantity": total_qty,
        "subtotal": total_price,
        "tax": tax,
        "total": final_total
    }


# ============================================================
# Main Demo
# ============================================================

async def main() -> None:
    """Run code execution demonstration."""
    print("=" * 70)
    print("EXAMPLE 09: Code Execution with ToolWeaver")
    print("=" * 70)
    print()

    # Sample data
    sample_receipt = {
        "merchant": "Restaurant XYZ",
        "date": "2025-12-17",
        "items": [
            {"name": "Burger", "price": 12.99, "quantity": 2},
            {"name": "Fries", "price": 4.99, "quantity": 1},
            {"name": "Drink", "price": 2.50, "quantity": 2}
        ]
    }

    print("Step 1: Validate Receipt Data")
    print("-" * 70)
    validation = await validate_receipt_data(sample_receipt)
    print(f"  Valid: {validation['valid']}")
    if validation['errors']:
        for error in validation['errors']:
            print(f"    Error: {error}")
    else:
        print("  No errors found")
    print()

    print("Step 2: Calculate Receipt Total")
    print("-" * 70)
    calculation = await calculate_receipt(sample_receipt['items'])
    print(f"  Subtotal: ${calculation['subtotal']:.2f}")
    print(f"  Tax (8%): ${calculation['tax']:.2f}")
    print(f"  Total:    ${calculation['total']:.2f}")
    print(f"  Items:    {calculation['item_count']}")
    print()

    print("Step 3: Apply Price Discount (10% off)")
    print("-" * 70)
    discounted = await transform_prices(sample_receipt['items'], multiplier=0.9)
    print("  Original vs Discounted Prices:")
    for item in discounted['items']:
        print(f"    {item['name']:15} ${item['original_price']:7.2f} -> ${item['new_price']:7.2f}")
    print()

    print("Step 4: Generate Receipt Report")
    print("-" * 70)
    report = await generate_receipt_report(sample_receipt)
    print(report['report'])
    print()

    print("Step 5: Discover Computation Tools")
    print("-" * 70)
    comp_tools = list(search_tools(domain="computation"))
    print(f"  Found {len(comp_tools)} computation tools:")
    for tool in comp_tools:
        name = getattr(tool, "name", None) or str(getattr(tool, "id", "unknown"))
        desc = getattr(tool, "description", "")
        print(f"    • {name:30} - {desc}")
    print()

    print("=" * 70)
    print("[OK] Code execution demonstration complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
