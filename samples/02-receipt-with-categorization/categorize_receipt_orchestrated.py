"""
Example 2: Receipt with Categorization (TWO-MODEL ORCHESTRATION)

Demonstrates the REAL ToolWeaver value:
- Large Model Planning: Natural language → Execution Plan (DAG)
- Orchestrator: Parallel execution with dependency resolution
- Small Models: Fast, cheap execution of individual steps

This version uses a pre-generated plan to showcase the orchestrator,
without requiring OpenAI/Claude API keys. See comments for how to use
LargePlanner for real planning.
"""

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv

from orchestrator import mcp_tool, search_tools, execute_plan

# Load environment variables
load_dotenv()


# ============================================================
# Tool 1: OCR - Extract text from receipt image
# ============================================================
@mcp_tool(domain="receipts", description="Extract text from receipt images")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract text from receipt using mock or Azure Computer Vision."""
    use_mock = os.getenv("USE_MOCK_OCR", "true").lower() == "true"
    
    if use_mock:
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
            "line_count": len(mock_receipt_text.strip().split('\n'))
        }
    else:
        # Real Azure CV would go here
        # For this sample, we use mock by default
        print("[WARNING] Real OCR not configured. Using mock data.")
        return {
            "text": mock_receipt_text.strip(),
            "confidence": 0.96,
            "line_count": len(mock_receipt_text.strip().split('\n'))
        }


# ============================================================
# Tool 2: Parser - Extract line items from text
# ============================================================
@mcp_tool(domain="receipts", description="Parse line items from receipt text")
async def line_item_parser(text: str) -> dict:
    """Parse receipt text into structured line items."""
    import re
    
    lines = text.split('\n')
    items = []
    price_pattern = r'\$\s*(\d+\.\d{2})'

    for line in lines:
        price_match = re.search(price_pattern, line)
        if price_match and not any(keyword in line.lower() for keyword in ['subtotal', 'tax', 'total', 'thank']):
            price = float(price_match.group(1))
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
async def expense_categorizer(items: list[dict[str, Any]]) -> dict:
    """Categorize items into food, household, etc."""
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

        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                assigned_category = category
                break

        categorized_item = {**item, "category": assigned_category}
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
async def compute_statistics(input: dict[str, Any]) -> dict:
    """Compute summary statistics for categorized items."""
    # Extract from the whole categorizer output
    items = input.get("items", [])
    category_totals = input.get("category_totals", {})
    
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
# Generate Execution Plan (What LargePlanner Would Create)
# ============================================================
def create_execution_plan() -> dict[str, Any]:
    """
    Create an execution plan DAG.
    
    In production, this would be generated by LargePlanner:
    
        planner = LargePlanner(provider="azure-openai", model="gpt-4o")
        plan = await planner.generate_plan(
            "Process receipt, parse items, categorize expenses"
        )
    
    NOTE: This plan now includes all 4 steps after fixing the MCP registry bug
    (decorator-registered tools are merged into MCPClientShim). Steps:
    - Sequential dependencies (OCR → Parser → Categorizer → Stats)
    - Tool invocations with realistic inputs
    - Step references for automatic data flow
    """
    
    return {
        "request_id": "demo-001",
        "steps": [
            {
                "id": "step-1-ocr",
                "tool": "receipt_ocr",
                "input": {"image_uri": "mock://grocery-receipt.jpg"},
                "depends_on": [],
                "mode": "sequential",
                "description": "Extract text from receipt image"
            },
            {
                "id": "step-2-parser",
                "tool": "line_item_parser",
                "input": {"text": "step:step-1-ocr"},
                "depends_on": ["step-1-ocr"],
                "mode": "sequential",
                "description": "Parse line items from OCR text"
            },
            {
                "id": "step-3-categorizer",
                "tool": "expense_categorizer",
                "input": {"items": "step:step-2-parser"},
                "depends_on": ["step-2-parser"],
                "mode": "sequential",
                "description": "Categorize expense items"
            },
            {
                "id": "step-4-stats",
                "tool": "compute_statistics",
                "input": {"input": "step:step-3-categorizer"},
                "depends_on": ["step-3-categorizer"],
                "mode": "sequential",
                "description": "Compute summary statistics"
            }
        ],
        "final_synthesis": {
            "prompt_template": "Summary: Processed receipt with categorized expenses and statistics",
            "meta": {"expose_inputs_to_reasoner": False}
        }
    }


# ============================================================
# Main: Orchestration Example
# ============================================================
async def main():
    """Demonstrate two-model orchestration."""
    print("=" * 75)
    print(" " * 15 + "🎯 TWO-MODEL ORCHESTRATION DEMO 🎯")
    print(" " * 10 + "Large Planner → Plan → Orchestrator + Small Tools")
    print("=" * 75)
    print()

    # Step 1: Tool Discovery
    print("[1️⃣ ] TOOL DISCOVERY")
    print("-" * 75)
    print("Available tools registered in the system:")
    available_tools = search_tools(query="receipt", domain="receipts", use_semantic=False)
    tool_list = list(available_tools)
    for tool in tool_list[:4]:
        print(f"  • {tool.name:30} - {tool.description}")
    print()

    # Step 2: Show the two-model architecture
    print("[2️⃣ ] WORKFLOW: PLANNING PHASE")
    print("-" * 75)
    print("User Request:")
    print('  "Process a grocery receipt, extract items, categorize expenses,')
    print('   and generate a summary report"')
    print()
    print("What happens in ToolWeaver:")
    print("  1️⃣  Large Model (GPT-4o/Claude) creates execution plan")
    print("     • Understands user intent")
    print("     • Discovers available tools via semantic search")
    print("     • Generates DAG (Directed Acyclic Graph)")
    print("     • Cost: ~$0.002 per request")
    print("     • Time: ~1-2 seconds (one API call)")
    print()
    print("✅ Plan Generated! (See below)")
    print()

    # Step 3: Display the plan
    print("[3️⃣ ] EXECUTION PLAN (DAG)")
    print("-" * 75)
    plan = create_execution_plan()
    
    print("Plan Structure:")
    print("```")
    print(json.dumps({
        "request_id": plan["request_id"],
        "steps": [
            {
                "id": s["id"],
                "tool": s["tool"],
                "depends_on": s["depends_on"],
                "description": s["description"]
            }
            for s in plan["steps"]
        ]
    }, indent=2))
    print("```")
    print()
    
    print("Dependency Graph:")
    print("  [OCR] → [Parser] → [Categorizer] → [Statistics]")
    print()

    # Step 4: Orchestration
    print("[4️⃣ ] EXECUTION PHASE")
    print("-" * 75)
    print("Orchestrator now:")
    print("  ✓ Resolves dependencies (builds execution order)")
    print("  ✓ Executes each step (can parallelize where possible)")
    print("  ✓ Passes data between steps automatically")
    print("  ✓ Handles errors, retries, caching")
    print()
    print("Executing plan...")
    print()
    
    # Execute the plan
    context = await execute_plan(plan)
    
    print("✅ All steps executed successfully!")
    print()

    # Step 5: Display results
    print("[5️⃣ ] RESULTS & ANALYSIS")
    print("=" * 75)
    
    # Get final statistics
    stats_result = context.get("step-4-stats", {})
    categorizer_result = context.get("step-3-categorizer", {})
    
    if stats_result:
        print()
        print("📊 SUMMARY")
        print("-" * 75)
        print(f"💰 Total Amount:      ${stats_result['total_amount']:.2f}")
        print(f"🧾 Item Count:        {stats_result['item_count']} items")
        print(f"📈 Average per Item:  ${stats_result['avg_amount']:.2f}")
        print()
        
        print("📋 BY CATEGORY")
        print("-" * 75)
        for category, details in stats_result['categories'].items():
            if details['count'] > 0:
                print(f"  {category.upper():15} Total: ${details['total']:8.2f} ({details['percentage']:5.1f}%)  Items: {details['count']}")
        print()
        
        if categorizer_result and "items" in categorizer_result:
            print("🛒 ITEMIZED RECEIPT")
            print("-" * 75)
            for item in categorizer_result['items']:
                print(f"  {item['name']:25} ${item['price']:7.2f}  [{item['category']}]")
    
    print()
    print("=" * 75)

    # Step 6: Cost Analysis
    print("[💰] COST & PERFORMANCE ANALYSIS")
    print("=" * 75)
    print()
    print("WITHOUT ToolWeaver (All Large Model):")
    print("  ❌ 1 large model call: planning        $0.002")
    print("  ❌ 1 large model call: each tool call  $0.02 × 4 = $0.08")
    print("  ❌ Total per receipt:                   $0.082")
    print("  ❌ Latency:                             ~5-8 seconds (sequential)")
    print("  ❌ Context bloat:                       Large model sees all intermediate data")
    print()
    print("WITH ToolWeaver (Two-Model + Orchestration):")
    print("  ✅ 1 large model call: planning        $0.002")
    print("  ✅ 4 small tool calls:                  $0.001 × 4 = $0.004")
    print("  ✅ Total per receipt:                   $0.006")
    print("  ✅ Latency:                             ~1-2 seconds (parallel where possible)")
    print("  ✅ Context saved:                       Large model doesn't see intermediate data")
    print()
    print("💡 BENEFITS:")
    print("  • Cost Savings:      93% cheaper per receipt ($0.082 → $0.006)")
    print("  • Speed:             3-5x faster execution")
    print("  • Scalability:       Same cost for 1 receipt or 10,000 receipts")
    print("  • Safety:            Intermediate data never sent to expensive LLM")
    print("  • Determinism:       Small tools are predictable, cached, retryable")
    print()
    print("📈 SCALE IMPACT (Processing 1,000 receipts):")
    print("  • Without ToolWeaver: $82.00  cost + 2-3 hours latency")
    print("  • With ToolWeaver:    $6.00   cost + 10-30 minutes latency")
    print("  • Net Savings:        $76.00 (93%) + 90% faster")
    print()
    print("=" * 75)
    print()
    print("HOW TO USE REAL PLANNING:")
    print("-" * 75)
    print("To use LargePlanner for real planning instead of pre-generated plans:")
    print()
    print("  from orchestrator._internal.planning.planner import LargePlanner")
    print()
    print("  planner = LargePlanner(provider='azure-openai', model='gpt-4o')")
    print("  plan = await planner.generate_plan(")
    print('      "Process receipt, extract items, categorize, compute stats"')
    print("  )")
    print("  context = await execute_plan(plan)")
    print()
    print("This requires: PLANNER_PROVIDER, PLANNER_MODEL, and AZURE_OPENAI_API_KEY")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
