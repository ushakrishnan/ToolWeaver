"""
Example 1: Basic Receipt Processing

Demonstrates the simplest use case - extracting text from a receipt image.
"""

import asyncio
import json
from pathlib import Path

from orchestrator import execute_plan, final_synthesis


# Define execution plan
receipt_plan = {
    "request_id": "example-01-receipt",
    "steps": [
        {
            "id": "extract_text",
            "tool": "receipt_ocr",
            "input": {
                "image_uri": "https://example.com/receipts/sample-receipt.jpg"
            }
        }
    ],
    "final_synthesis": {
        "prompt_template": "Receipt text extracted:\n{{steps}}"
    }
}


async def main():
    """Run basic receipt processing."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Receipt Processing")
    print("=" * 60)
    print()
    
    print("📝 Plan:")
    print(f"   - Step 1: Extract text from receipt image")
    print()
    
    # Execute plan
    print("🚀 Executing plan...")
    context = await execute_plan(receipt_plan)
    
    # Display results
    print()
    print("✅ Execution complete!")
    print()
    print("📊 Results:")
    print(json.dumps(context, indent=2))
    print()
    
    # Generate synthesis
    synthesis = await final_synthesis(receipt_plan, context)
    print("📋 Summary:")
    print(synthesis['synthesis'])
    print()


if __name__ == "__main__":
    asyncio.run(main())
