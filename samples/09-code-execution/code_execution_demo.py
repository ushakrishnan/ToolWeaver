"""Example 09: Code Execution"""
import asyncio
from pathlib import Path
import sys

from orchestrator.code_exec_worker import CodeExecutionWorker
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

async def main():
    print("="*70)
    print(" "*20 + "CODE EXECUTION EXAMPLE")
    print("="*70)
    
    worker = CodeExecutionWorker(timeout=5)
    
    # Example 1: Simple calculation
    print("\nExample 1: Calculate Receipt Total")
    print("-" * 40)
    code1 = """
items = [
    {"name": "Burger", "price": 12.99, "quantity": 2},
    {"name": "Fries", "price": 4.99, "quantity": 1},
    {"name": "Drink", "price": 2.50, "quantity": 2}
]

subtotal = sum(item["price"] * item["quantity"] for item in items)
tax = subtotal * 0.08
total = subtotal + tax

result = {
    "subtotal": subtotal,
    "tax": tax,
    "total": total,
    "item_count": sum(item["quantity"] for item in items)
}
"""
    try:
        result = await worker.execute(code1, {})
        print(f"  Subtotal: ${result['subtotal']:.2f}")
        print(f"  Tax: ${result['tax']:.2f}")
        print(f"  Total: ${result['total']:.2f}")
        print(f"  Items: {result['item_count']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 2: Data validation
    print("\nExample 2: Validate Receipt Data")
    print("-" * 40)
    code2 = """
data = {
    "merchant": "Restaurant XYZ",
    "date": "2025-12-17",
    "items": [{"name": "Burger", "price": 12.99}],
    "total": 12.99
}

errors = []
if not data.get("merchant"):
    errors.append("Missing merchant name")
if not data.get("items"):
    errors.append("No items found")

item_total = sum(item["price"] for item in data["items"])
if abs(item_total - data["total"]) > 0.01:
    errors.append(f"Total mismatch: {item_total} != {data['total']}")

result = {
    "valid": len(errors) == 0,
    "errors": errors
}
"""
    try:
        result = await worker.execute(code2, {})
        if result["valid"]:
            print("  ✓ Data is valid")
        else:
            print("  ✗ Validation failed:")
            for error in result["errors"]:
                print(f"    - {error}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 3: Security - restricted operations
    print("\nExample 3: Security Test (Restricted Operations)")
    print("-" * 40)
    code3 = """
import os  # This should be restricted
result = os.listdir('/')
"""
    try:
        result = await worker.execute(code3, {})
        print(f"  ✗ Security failed: {result}")
    except Exception as e:
        print(f"  ✓ Security working: Blocked restricted operation")
        print(f"    {str(e)[:60]}...")
    
    print("\n✓ Example completed!")
    print("\nSecurity Features:")
    print("  - Restricted imports (no os, sys, subprocess)")
    print("  - Timeout limits (prevent infinite loops)")
    print("  - Process isolation (separate process)")
    print("  - Memory limits (prevent resource exhaustion)")

if __name__ == "__main__":
    asyncio.run(main())
