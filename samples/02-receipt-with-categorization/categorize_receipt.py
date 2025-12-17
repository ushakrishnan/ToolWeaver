"""
Example 2: Receipt with Categorization

Demonstrates multi-step workflow:
- OCR extraction
- Line item parsing (Phi-3 or keyword matching)
- Expense categorization (Phi-3 or rules)
- Statistical computation (function call)
"""

import asyncio
import json
from pathlib import Path

from orchestrator import execute_plan, final_synthesis


# Define multi-step execution plan
categorization_plan = {
    "request_id": "example-02-categorization",
    "steps": [
        # Step 1: Extract text from receipt
        {
            "id": "extract_text",
            "tool": "receipt_ocr",
            "input": {
                "image_uri": "https://example.com/receipts/grocery-receipt.jpg"
            }
        },
        # Step 2: Parse line items (uses Phi-3 if enabled)
        {
            "id": "parse_items",
            "tool": "line_item_parser",
            "input": {
                "text": "step:extract_text"  # Reference step 1 output
            },
            "depends_on": ["extract_text"]
        },
        # Step 3: Categorize items (uses Phi-3 if enabled)
        {
            "id": "categorize",
            "tool": "expense_categorizer",
            "input": {
                "items": "step:parse_items"  # Reference step 2 output
            },
            "depends_on": ["parse_items"]
        },
        # Step 4: Compute statistics (function call)
        {
            "id": "compute_stats",
            "tool": "function_call",
            "input": {
                "name": "compute_item_statistics",
                "args": {
                    "items": "step:categorize"
                }
            },
            "depends_on": ["categorize"]
        }
    ],
    "final_synthesis": {
        "prompt_template": "Receipt processing complete:\n{{steps}}"
    }
}


async def main():
    """Run receipt categorization workflow."""
    print("=" * 60)
    print("EXAMPLE 2: Receipt with Categorization")
    print("=" * 60)
    print()
    
    print("📝 Plan Overview:")
    print("   Step 1: Extract text from receipt (OCR)")
    print("   Step 2: Parse line items (Phi-3 or keyword matching)")
    print("   Step 3: Categorize expenses (Phi-3 or rules)")
    print("   Step 4: Compute statistics (function call)")
    print()
    
    print("💡 Using Phi-3? Check USE_SMALL_MODEL in .env")
    print("   - true:  Phi-3 via Ollama (intelligent parsing)")
    print("   - false: Keyword matching (fast, basic)")
    print()
    
    # Execute plan
    print("🚀 Executing plan...")
    context = await execute_plan(categorization_plan)
    
    # Display results
    print()
    print("✅ Execution complete!")
    print()
    print("📊 Detailed Results:")
    print(json.dumps(context, indent=2))
    print()
    
    # Show summary
    if 'compute_stats' in context['steps']:
        stats = context['steps']['compute_stats']['result']
        print("💰 Summary:")
        print(f"   Total Amount: ${stats['total_amount']:.2f}")
        print(f"   Item Count: {stats['count']}")
        print(f"   Average: ${stats['avg_amount']:.2f}")
        print()
        print("   By Category:")
        for category, cat_stats in stats['categories'].items():
            print(f"   - {category}: ${cat_stats['total']:.2f}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
