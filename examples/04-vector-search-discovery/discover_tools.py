"""
Example 04: Vector Search and Tool Discovery

Demonstrates:
- Registering multiple tools across different domains
- Using search_tools() for keyword-based search
- Using semantic_search_tools() for intelligent discovery
- Comparing search strategies

Use Case:
Find the right tool among many registered tools using semantic understanding
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator import mcp_tool, search_tools, semantic_search_tools, get_available_tools


# ============================================================
# Register a diverse set of tools across multiple domains
# ============================================================

@mcp_tool(domain="finance", description="Calculate compound interest for investments")
async def compound_interest(principal: float, rate: float, years: int) -> dict:
    """Calculate compound interest."""
    amount = principal * ((1 + rate) ** years)
    return {"principal": principal, "final_amount": amount, "interest_earned": amount - principal}


@mcp_tool(domain="finance", description="Convert currency from one type to another")
async def currency_converter(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert between currencies."""
    # Mock conversion rates
    rates = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73, "JPY": 110.0}
    converted = amount * (rates.get(to_currency, 1.0) / rates.get(from_currency, 1.0))
    return {"amount": amount, "from": from_currency, "to": to_currency, "converted": converted}


@mcp_tool(domain="data", description="Analyze CSV file and generate statistics")
async def csv_analyzer(file_path: str) -> dict:
    """Analyze CSV data."""
    return {"rows": 1000, "columns": 10, "summary": "Data looks healthy"}


@mcp_tool(domain="data", description="Merge multiple dataframes together")
async def dataframe_merger(files: list) -> dict:
    """Merge dataframes."""
    return {"merged_rows": 5000, "source_files": len(files)}


@mcp_tool(domain="communication", description="Send email with attachments")
async def email_sender(to: str, subject: str, body: str) -> dict:
    """Send email."""
    return {"status": "sent", "recipient": to, "subject": subject}


@mcp_tool(domain="communication", description="Post message to Slack channel")
async def slack_notifier(channel: str, message: str) -> dict:
    """Send Slack notification."""
    return {"status": "posted", "channel": channel}


@mcp_tool(domain="web", description="Scrape content from website URL")
async def web_scraper(url: str) -> dict:
    """Scrape web content."""
    return {"url": url, "content_length": 5000, "links_found": 42}


@mcp_tool(domain="web", description="Check if website is online and measure response time")
async def uptime_checker(url: str) -> dict:
    """Check website uptime."""
    return {"url": url, "status": "online", "response_time_ms": 150}


@mcp_tool(domain="receipts", description="Extract text from receipt images using OCR")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract receipt text."""
    return {"text": "Receipt data...", "confidence": 0.95}


@mcp_tool(domain="receipts", description="Parse line items and prices from receipt text")
async def receipt_parser(text: str) -> dict:
    """Parse receipt items."""
    return {"items": [{"name": "Item 1", "price": 10.00}], "total": 10.00}


# ============================================================
# Demonstration Functions
# ============================================================

async def demo_keyword_search():
    """Demonstrate keyword-based search."""
    print("\n" + "="*70)
    print("DEMO 1: Keyword Search")
    print("="*70)
    print()
    
    # Search by keyword
    print("Searching for 'currency'...")
    results = search_tools(query="currency")
    print(f"   Found {len(results)} tool(s):\n")
    for tool in results:
        print(f"   • {tool.name}")
        print(f"     {tool.description}")
        print(f"     Domain: {tool.domain}")
        print()


async def demo_domain_search():
    """Demonstrate domain-based search."""
    print("\n" + "="*70)
    print("DEMO 2: Domain-Based Search")
    print("="*70)
    print()
    
    # Search by domain
    domains = ["finance", "data", "communication", "web", "receipts"]
    for domain in domains:
        results = search_tools(query="", domain=domain)
        print(f"{domain.upper()}: {len(results)} tool(s)")
    print()


async def demo_semantic_search():
    """Demonstrate semantic search (embedding-based)."""
    print("\n" + "="*70)
    print("DEMO 3: Semantic Search")
    print("="*70)
    print()
    
    queries = [
        "I need to calculate investment returns",
        "How can I notify my team?",
        "Process receipt from restaurant",
        "Check if my website is working"
    ]
    
    for query in queries:
        print(f"Query: \"{query}\"")
        try:
            # Semantic search uses embeddings for better matching
            results = semantic_search_tools(query=query, top_k=2)
            print(f"   Best matches:")
            for i, tool in enumerate(results[:2], 1):
                print(f"   {i}. {tool.name} ({tool.domain})")
                print(f"      {tool.description}")
        except Exception as e:
            # Fallback to keyword search if semantic search not configured
            print(f"   WARNING: Semantic search not configured, using keyword search")
            results = search_tools(query=query.split()[-1])  # Use last word as keyword
            if results:
                print(f"   Best match: {results[0].name}")
        print()


async def demo_compare_strategies():
    """Compare different search strategies."""
    print("\n" + "="*70)
    print("DEMO 4: Comparing Search Strategies")
    print("="*70)
    print()
    
    test_query = "send notification"
    
    print(f"Query: \"{test_query}\"\n")
    
    # Strategy 1: Keyword search
    print("Strategy 1: Keyword Search")
    keyword_results = search_tools(query="send")
    print(f"   Results: {len(keyword_results)} tools")
    for tool in keyword_results[:3]:
        print(f"   • {tool.name}")
    print()
    
    # Strategy 2: Domain filter
    print("Strategy 2: Domain Filter (communication)")
    domain_results = search_tools(query="", domain="communication")
    print(f"   Results: {len(domain_results)} tools")
    for tool in domain_results:
        print(f"   • {tool.name}")
    print()
    
    # Strategy 3: Semantic (if available)
    print("Strategy 3: Semantic Search")
    try:
        semantic_results = semantic_search_tools(query=test_query, top_k=3)
        print(f"   Results: {len(semantic_results)} tools")
        for tool in semantic_results[:3]:
            print(f"   • {tool.name}")
    except:
        print("   WARNING: Semantic search requires embeddings configuration")
    print()


async def demo_catalog_overview():
    """Show overall catalog statistics."""
    print("\n" + "="*70)
    print("DEMO 5: Catalog Overview")
    print("="*70)
    print()
    
    all_tools = get_available_tools()
    print(f"Total Tools Registered: {len(all_tools)}\n")
    
    # Group by domain
    domains = {}
    for tool in all_tools:
        domain = getattr(tool, 'domain', 'general')
        domains[domain] = domains.get(domain, 0) + 1
    
    print("By Domain:")
    for domain, count in sorted(domains.items()):
        print(f"   {domain:15} : {count} tools")
    print()


# ============================================================
# Main
# ============================================================

async def main():
    """Run all discovery demos."""
    print("\n" + "="*70)
    print("EXAMPLE 04: Vector Search and Tool Discovery")
    print("="*70)
    print()
    print("This example demonstrates different strategies for finding tools")
    print("in a large catalog using keyword, domain, and semantic search.")
    print()
    
    # Run all demos
    await demo_catalog_overview()
    await demo_keyword_search()
    await demo_domain_search()
    await demo_semantic_search()
    await demo_compare_strategies()
    
    print("="*70)
    print("[OK] All demos complete!")
    print("="*70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
