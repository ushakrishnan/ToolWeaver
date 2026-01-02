"""
Complete End-to-End Pipeline Demo

Demonstrates all ToolWeaver features in a production-ready pipeline:
- Tool discovery with caching
- Semantic search for tool selection
- Multi-step planning with GPT-4
- Hybrid execution (GPT-4 + Phi-3)
- Redis caching for performance
- WandB monitoring for observability
- Code execution for calculations
- Programmatic executor for batch processing

⚠️ NOTE: Performance numbers are based on mock data and simulated execution.
Real-world results vary depending on:
  - Actual cache hit rate (assumed 85%; real: 30-90%)
  - Tool catalog quality (search effectiveness: 70-90%)
  - Network latency and API availability
  - Error rates and retry overhead (assumed 0%; real: 5-15% adds 10-15%)
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Note: This is a demonstration script showing the conceptual pipeline
# The actual orchestrator uses execute_plan() with JSON plans


def print_header(text: str):
    """Print a section header"""
    print(f"\n{'=' * 72}")
    print(f"{text:^72}")
    print('=' * 72)


def print_section(text: str):
    """Print a subsection"""
    print(f"\n{text}")
    print('-' * 72)


def create_mock_tools():
    """Create mock tools for demonstration"""
    return [
        {
            "name": "receipt_ocr",
            "description": "Extract text from receipt images using Azure Computer Vision OCR",
            "parameters": {"image_path": "string"},
            "returns": "Extracted text with line items"
        },
        {
            "name": "parse_items",
            "description": "Parse receipt text into structured line items with prices",
            "parameters": {"text": "string"},
            "returns": "List of items with names and prices"
        },
        {
            "name": "categorize_items",
            "description": "Categorize receipt items into expense categories (Food, Beverages, etc)",
            "parameters": {"items": "array"},
            "returns": "Items grouped by category"
        },
        {
            "name": "validate_data",
            "description": "Validate receipt data consistency and totals",
            "parameters": {"data": "object"},
            "returns": "Validation results with any errors"
        },
        {
            "name": "calculate_stats",
            "description": "Calculate statistics like total, average, min, max from receipt data",
            "parameters": {"items": "array"},
            "returns": "Statistical summary"
        },
        # Add more tools to simulate realistic catalog
        *[
            {
                "name": f"helper_tool_{i}",
                "description": f"Helper function for data processing task {i}",
                "parameters": {"data": "any"},
                "returns": "Processed data"
            }
            for i in range(1, 38)  # 37 additional tools = 42 total
        ]
    ]


def phase1_discovery(use_cache: bool = True):
    """Phase 1: Tool Discovery with caching"""
    print_section("Phase 1: Tool Discovery")

    start_time = time.time()

    # Simulate discovery (in real scenario, would auto-discover from MCP servers, functions, etc.)
    tools = create_mock_tools()

    elapsed = (time.time() - start_time) * 1000
    cache_status = "(from cache, 2ms)" if use_cache and elapsed < 10 else f"({elapsed:.0f}ms)"

    print(f"✓ Discovered {len(tools)} tools {cache_status}")
    print("  - 15 MCP tools")
    print("  - 18 function tools")
    print("  - 9 code execution patterns")

    return tools


def phase2_search(query: str):
    """Phase 2: Semantic Search"""
    print_section("Phase 2: Semantic Search")

    print(f'Query: "{query}"')

    start_time = time.time()

    # Mock search results (in real scenario, would use vector search)
    relevant_tools = [
        ("receipt_ocr", 0.95),
        ("parse_items", 0.89),
        ("categorize_items", 0.84),
        ("calculate_stats", 0.78),
        ("validate_data", 0.72)
    ]

    elapsed = (time.time() - start_time) * 1000
    token_reduction = 94  # Mock value

    print(f"✓ Found {len(relevant_tools)} relevant tools in {elapsed:.0f}ms ({token_reduction}% token reduction)")
    for i, (tool_name, score) in enumerate(relevant_tools, 1):
        print(f"  {i}. {tool_name} ({score:.2f})")

    return relevant_tools


def phase3_planning(query: str, relevant_tools: list):
    """Phase 3: Multi-Step Planning with GPT-4"""
    print_section("Phase 3: Multi-Step Planning (GPT-4)")

    start_time = time.time()

    # Mock plan (in real scenario, would use Planner with GPT-4)
    plan = {
        "steps": [
            {"id": 1, "name": "extract_text", "tool": "receipt_ocr", "parallel": False},
            {"id": 2, "name": "parse_items", "tool": "parse_items", "parallel": False},
            {"id": 3, "name": "categorize", "tool": "categorize_items", "parallel": True},
            {"id": 4, "name": "validate", "tool": "validate_data", "parallel": True},
            {"id": 5, "name": "stats", "tool": "calculate_stats", "parallel": False}
        ]
    }

    elapsed = (time.time() - start_time) * 1000
    cost = 0.02

    print(f"✓ Generated execution plan ({elapsed:.0f}ms, ${cost:.2f})")
    for step in plan["steps"]:
        parallel = " [parallel]" if step["parallel"] else ""
        step_id = f"Step {step['id']}" if not step["parallel"] else f"Step {step['id']}{chr(96 + step['id'] - 2)}"
        print(f"  {step_id}: {step['name']} ({step['tool']}){parallel}")

    return plan


def phase4_execution(plan: dict):
    """Phase 4: Hybrid Execution (GPT-4 + Phi-3 + Code)"""
    print_section("Phase 4: Hybrid Execution")

    # Step 1: OCR (Azure CV)
    time.sleep(0.34)
    print("Step 1: extract_text (Azure CV) ✓ 340ms")
    print("  → Extracted 12 line items from receipt")

    # Step 2: Parse (Phi-3 local)
    time.sleep(0.18)
    print("\nStep 2: parse_items (Phi-3 local) ✓ 180ms")
    print("  → Parsed: Burger $12.99, Fries $4.99, Drink $2.50...")

    # Steps 3a & 3b: Parallel execution
    time.sleep(0.11)
    print("\nStep 3a: categorize (Phi-3 local) ✓ 95ms [parallel]")
    print("  → Food: $15.48, Beverages: $5.00")

    print("\nStep 3b: validate (Code execution) ✓ 110ms [parallel]")
    print("  → Validation: PASSED (totals match)")

    # Step 4: Stats (Code execution)
    time.sleep(0.045)
    print("\nStep 4: stats (Code execution) ✓ 45ms")
    print("  → Total: $20.48, Average: $1.71, Items: 12")

    results = {
        "items": 12,
        "total": 20.48,
        "categories": {"Food": 15.48, "Beverages": 5.00},
        "validation": "PASSED"
    }

    return results


def phase5_batch_processing():
    """Phase 5: Batch Processing with Programmatic Executor"""
    print_section("Phase 5: Batch Processing (100 receipts)")

    print("Using programmatic executor to avoid LLM overhead...\n")

    batch_size = 10
    num_batches = 10

    for batch in range(1, num_batches + 1):
        start = (batch - 1) * batch_size + 1
        end = batch * batch_size

        # Simulate processing with increasing cache hit rate
        cache_rate = min(70 + batch * 2, 95)
        duration = max(2.1 - (batch * 0.05), 1.5)

        time.sleep(duration)
        print(f"Processing batch {start}-{end}: ✓ {duration:.1f}s ({cache_rate}% from cache)")

    total_time = 18.5
    print(f"\n✓ Processed 100 receipts in {total_time}s")

    return {
        "processed": 100,
        "time": total_time,
        "avg_time": total_time / 100
    }


def phase6_monitoring(batch_results: dict):
    """Phase 6: Monitoring & Analytics"""
    print_section("Phase 6: Monitoring & Analytics")

    print("WandB Dashboard: https://wandb.ai/usha-krishnan/ToolWeaver/runs/xyz123\n")

    print("Metrics Summary:")
    print("  Total requests: 101 (1 plan + 100 executions)")
    print("  Success rate: 100% (101/101)")
    print(f"  Average latency: {batch_results['avg_time'] * 1000:.0f}ms per receipt")
    print("  Total tokens: 45,890")
    print("  Total cost: $0.75")
    print("  Cache hit rate: 85%")

    print("\nCost Breakdown:")
    print("  Planning (GPT-4): $0.02 (2.7%)")
    print("  Execution (Phi-3): $0.01 (1.3%)")
    print("  OCR (Azure CV): $0.10 (13.3%)")
    print("  Cached results: $0.62 saved (45% of operations)")

    print("\nTool Usage:")
    print("  receipt_ocr: 100 calls (15 from cache)")
    print("  parse_items: 100 calls (85 from cache)")
    print("  categorize_items: 100 calls (90 from cache)")
    print("  calculate_stats: 100 calls (100% code exec, $0)")


def main():
    """Run the complete pipeline demo"""

    print_header("COMPLETE END-TO-END PIPELINE DEMO")

    # Phase 1: Discovery
    phase1_discovery(use_cache=True)

    # Phase 2: Semantic Search
    query = "Process receipt, categorize items, calculate statistics"
    relevant_tools = phase2_search(query)

    # Phase 3: Planning
    plan = phase3_planning(query, relevant_tools)

    # Phase 4: Execution
    phase4_execution(plan)

    # Phase 5: Batch Processing
    batch_results = phase5_batch_processing()

    # Phase 6: Monitoring
    phase6_monitoring(batch_results)

    # Summary
    print_header("✓ Complete pipeline demo finished successfully!")

    print("\nSummary:")
    print("  Without ToolWeaver: $15.00, 200s")
    print("  With ToolWeaver:    $0.75, 18.5s")
    print("\n  Savings: $14.25 (95% cost reduction)")
    print("  Speedup: 10.8x faster")

    print("\nKey Optimizations:")
    print("  1. Semantic search: 70-90% token reduction (varies by catalog)")
    print("  2. Hybrid models: 60% cost reduction (GPT-4 → Phi-3)")
    print("  3. Caching: 85% cache hit rate assumed (varies 30-90%)")
    print("  4. Parallelization: 10-30% faster depending on I/O concurrency")
    print("  5. Programmatic executor: Up to 99% context reduction")
    print("  6. Code execution: $0 LLM cost (minimal sandbox compute cost)")


if __name__ == "__main__":
    main()
