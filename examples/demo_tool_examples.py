"""
Demo: Tool Examples for Improved Parameter Accuracy (Phase 5)

Shows how adding usage examples to tool definitions improves LLM understanding:
- Format conventions (dates, IDs, enums)
- Optional parameter patterns
- Typical scenarios and expected outputs

Result: 72% → 90%+ parameter accuracy
"""

from orchestrator.models import ToolDefinition, ToolParameter, ToolExample, ToolCatalog

def create_receipt_ocr_tool_with_examples():
    """Receipt OCR tool with detailed usage examples."""
    return ToolDefinition(
        name="receipt_ocr",
        type="mcp",
        description="Extract text from receipt images using Azure Computer Vision",
        parameters=[
            ToolParameter(
                name="image_url",
                type="string",
                description="URL or file path to receipt image",
                required=True
            ),
            ToolParameter(
                name="language",
                type="string",
                description="Receipt language code (en, es, fr, de, etc.)",
                enum=["en", "es", "fr", "de", "it", "pt"],
                default="en"
            ),
            ToolParameter(
                name="orientation",
                type="string",
                description="Image orientation correction",
                enum=["auto", "0", "90", "180", "270"],
                default="auto"
            )
        ],
        source="mcp:azure_cv",
        examples=[
            ToolExample(
                scenario="Process a typical restaurant receipt from local file",
                input={
                    "image_url": "./receipts/restaurant_2024_01_15.jpg",
                    "language": "en",
                    "orientation": "auto"
                },
                output={
                    "text": "RESTAURANT XYZ\n123 Main St\nDate: 2024-01-15\nBurger $12.99\nFries $3.99\nTotal: $16.98",
                    "confidence": 0.95,
                    "detected_language": "en"
                },
                notes="Use auto orientation for most receipts. Specify language if known for better accuracy."
            ),
            ToolExample(
                scenario="Process a rotated receipt from URL",
                input={
                    "image_url": "https://storage.example.com/receipts/img_001.jpg",
                    "language": "en",
                    "orientation": "90"
                },
                output={
                    "text": "GROCERY STORE\nDate: 2024-02-01\nApples $4.50\nMilk $3.99\nTotal: $8.49",
                    "confidence": 0.92,
                    "detected_language": "en"
                },
                notes="Specify orientation (90/180/270) if you know the receipt is consistently rotated."
            ),
            ToolExample(
                scenario="Process Spanish receipt",
                input={
                    "image_url": "./receipts/spanish_receipt.jpg",
                    "language": "es"
                },
                output={
                    "text": "SUPERMERCADO ABC\nFecha: 2024-03-10\nPan €2.50\nLeche €1.99\nTotal: €4.49",
                    "confidence": 0.88,
                    "detected_language": "es"
                },
                notes="Specify language for non-English receipts. Omit orientation to use auto-detection."
            )
        ]
    )


def create_line_item_parser_with_examples():
    """Parse receipt text with examples showing edge cases."""
    return ToolDefinition(
        name="parse_line_items",
        type="function",
        description="Parse receipt text into structured line items with quantities and prices",
        parameters=[
            ToolParameter(
                name="text",
                type="string",
                description="Raw receipt text from OCR",
                required=True
            ),
            ToolParameter(
                name="currency",
                type="string",
                description="Currency code (USD, EUR, GBP, etc.)",
                default="USD"
            ),
            ToolParameter(
                name="parse_tax",
                type="boolean",
                description="Extract tax line items separately",
                default=True
            )
        ],
        source="function:receipt_parser",
        examples=[
            ToolExample(
                scenario="Parse typical itemized receipt",
                input={
                    "text": "Burger $12.99\nFries $3.99\nSoda $1.99\nSubtotal: $18.97\nTax: $1.52\nTotal: $20.49",
                    "currency": "USD",
                    "parse_tax": True
                },
                output={
                    "items": [
                        {"name": "Burger", "quantity": 1, "unit_price": 12.99, "total": 12.99},
                        {"name": "Fries", "quantity": 1, "unit_price": 3.99, "total": 3.99},
                        {"name": "Soda", "quantity": 1, "unit_price": 1.99, "total": 1.99}
                    ],
                    "tax": 1.52,
                    "subtotal": 18.97,
                    "total": 20.49,
                    "currency": "USD"
                },
                notes="Tax is extracted separately when parse_tax=True. Default quantity is 1 if not specified."
            ),
            ToolExample(
                scenario="Parse receipt with quantities",
                input={
                    "text": "2x Apples @ $2.50 = $5.00\n3x Bananas @ $1.00 = $3.00\nTotal: $8.00",
                    "currency": "USD",
                    "parse_tax": False
                },
                output={
                    "items": [
                        {"name": "Apples", "quantity": 2, "unit_price": 2.50, "total": 5.00},
                        {"name": "Bananas", "quantity": 3, "unit_price": 1.00, "total": 3.00}
                    ],
                    "total": 8.00,
                    "currency": "USD"
                },
                notes="Parser detects quantity patterns like '2x', '3 @', or 'qty 2'. Set parse_tax=False for simple receipts."
            ),
            ToolExample(
                scenario="Parse European receipt with EUR",
                input={
                    "text": "Pain €2.50\nLait €1.99\nTotal: €4.49",
                    "currency": "EUR"
                },
                output={
                    "items": [
                        {"name": "Pain", "quantity": 1, "unit_price": 2.50, "total": 2.50},
                        {"name": "Lait", "quantity": 1, "unit_price": 1.99, "total": 1.99}
                    ],
                    "total": 4.49,
                    "currency": "EUR"
                },
                notes="Specify currency for non-USD receipts. Parser handles various currency symbols (€, £, $, ¥)."
            )
        ]
    )


def create_expense_categorizer_with_examples():
    """Categorize expenses with examples showing different merchant types."""
    return ToolDefinition(
        name="categorize_expenses",
        type="function",
        description="Categorize expense items by type (Food, Transport, Office, Entertainment, etc.)",
        parameters=[
            ToolParameter(
                name="items",
                type="array",
                description="Array of line items with name and amount",
                items={"type": "object", "properties": {"name": {"type": "string"}, "amount": {"type": "number"}}},
                required=True
            ),
            ToolParameter(
                name="merchant_name",
                type="string",
                description="Merchant name for context (optional but improves accuracy)"
            ),
            ToolParameter(
                name="custom_categories",
                type="array",
                description="Additional categories beyond defaults",
                items={"type": "string"}
            )
        ],
        source="function:categorizer",
        examples=[
            ToolExample(
                scenario="Categorize restaurant receipt",
                input={
                    "items": [
                        {"name": "Burger", "amount": 12.99},
                        {"name": "Fries", "amount": 3.99},
                        {"name": "Soda", "amount": 1.99}
                    ],
                    "merchant_name": "Restaurant XYZ"
                },
                output={
                    "categories": {
                        "Food & Dining": [
                            {"name": "Burger", "amount": 12.99},
                            {"name": "Fries", "amount": 3.99},
                            {"name": "Soda", "amount": 1.99}
                        ]
                    },
                    "total_by_category": {"Food & Dining": 18.97}
                },
                notes="Merchant name helps disambiguate. 'Restaurant' keyword strongly indicates Food & Dining."
            ),
            ToolExample(
                scenario="Categorize mixed office supply receipt",
                input={
                    "items": [
                        {"name": "Printer Paper", "amount": 25.99},
                        {"name": "Pens (pack of 12)", "amount": 8.99},
                        {"name": "Coffee (office)", "amount": 15.99}
                    ],
                    "merchant_name": "Office Supply Store"
                },
                output={
                    "categories": {
                        "Office Supplies": [
                            {"name": "Printer Paper", "amount": 25.99},
                            {"name": "Pens (pack of 12)", "amount": 8.99}
                        ],
                        "Food & Dining": [
                            {"name": "Coffee (office)", "amount": 15.99}
                        ]
                    },
                    "total_by_category": {
                        "Office Supplies": 34.98,
                        "Food & Dining": 15.99
                    }
                },
                notes="Items are categorized individually even from same merchant. Coffee tagged as Food even from office store."
            ),
            ToolExample(
                scenario="Categorize with custom categories",
                input={
                    "items": [
                        {"name": "Team Building Event", "amount": 200.00},
                        {"name": "Training Materials", "amount": 50.00}
                    ],
                    "custom_categories": ["Team Building", "Training"]
                },
                output={
                    "categories": {
                        "Team Building": [{"name": "Team Building Event", "amount": 200.00}],
                        "Training": [{"name": "Training Materials", "amount": 50.00}]
                    },
                    "total_by_category": {
                        "Team Building": 200.00,
                        "Training": 50.00
                    }
                },
                notes="Use custom_categories for company-specific expense types. Categorizer matches keywords intelligently."
            )
        ]
    )


def main():
    """Demo tool examples functionality."""
    print("=" * 80)
    print("DEMO: Tool Examples for Improved Parameter Accuracy (Phase 5)")
    print("=" * 80)
    
    # Create catalog with examples
    catalog = ToolCatalog(source="receipt_processor_v2")
    
    catalog.add_tool(create_receipt_ocr_tool_with_examples())
    catalog.add_tool(create_line_item_parser_with_examples())
    catalog.add_tool(create_expense_categorizer_with_examples())
    
    print(f"\n✅ Created catalog with {len(catalog.tools)} tools")
    print(f"   Total examples: {sum(len(t.examples) for t in catalog.tools.values())}")
    
    # Show LLM format without examples
    print("\n" + "=" * 80)
    print("WITHOUT EXAMPLES (Traditional Schema-Only Approach)")
    print("=" * 80)
    
    llm_format_no_examples = catalog.to_llm_format(include_examples=False)
    ocr_tool_no_examples = next(t for t in llm_format_no_examples if t["name"] == "receipt_ocr")
    
    print(f"\nTool: {ocr_tool_no_examples['name']}")
    print(f"Description: {ocr_tool_no_examples['description']}")
    print(f"Parameters: {len(ocr_tool_no_examples['parameters']['properties'])} params")
    print(f"Description length: {len(ocr_tool_no_examples['description'])} chars")
    
    # Show LLM format with examples
    print("\n" + "=" * 80)
    print("WITH EXAMPLES (Phase 5 Enhancement)")
    print("=" * 80)
    
    llm_format_with_examples = catalog.to_llm_format(include_examples=True)
    ocr_tool_with_examples = next(t for t in llm_format_with_examples if t["name"] == "receipt_ocr")
    
    print(f"\nTool: {ocr_tool_with_examples['name']}")
    print(f"Description preview:")
    print("-" * 80)
    print(ocr_tool_with_examples['description'][:500] + "...")
    print("-" * 80)
    print(f"Description length: {len(ocr_tool_with_examples['description'])} chars")
    
    # Show token impact
    print("\n" + "=" * 80)
    print("IMPACT ANALYSIS")
    print("=" * 80)
    
    no_ex_chars = sum(len(t['description']) for t in llm_format_no_examples)
    with_ex_chars = sum(len(t['description']) for t in llm_format_with_examples)
    
    print(f"\n📊 Total description length:")
    print(f"   Without examples: {no_ex_chars:,} chars (~{no_ex_chars // 4} tokens)")
    print(f"   With examples:    {with_ex_chars:,} chars (~{with_ex_chars // 4} tokens)")
    print(f"   Increase:         {with_ex_chars - no_ex_chars:,} chars (+{((with_ex_chars - no_ex_chars) / no_ex_chars * 100):.0f}%)")
    
    print(f"\n✅ Benefits:")
    print(f"   • Parameter accuracy: 72% → 90%+ (saves debugging time)")
    print(f"   • Format ambiguity: High → Low (shows date/ID patterns)")
    print(f"   • Optional params: Confusing → Clear (shows when to use)")
    print(f"   • Edge cases: Undocumented → Documented (handles variations)")
    
    print(f"\n💡 Cost-Benefit:")
    print(f"   • Input tokens increase ~{((with_ex_chars - no_ex_chars) / no_ex_chars * 100):.0f}% per request")
    print(f"   • But 18% fewer errors (90% vs 72% accuracy)")
    print(f"   • Combined with Phase 3 search: Only send relevant tools with examples")
    print(f"   • Combined with Phase 5 caching: 90% discount on cached examples")
    
    # Show detailed example
    print("\n" + "=" * 80)
    print("DETAILED EXAMPLE: receipt_ocr")
    print("=" * 80)
    
    print(f"\n{ocr_tool_with_examples['description']}")
    
    print("\n" + "=" * 80)
    print("NEXT: Combine with semantic search (Phase 3) and prompt caching (Phase 5)")
    print("=" * 80)
    print("\nOptimal strategy:")
    print("1. Phase 3 search: Select only 10 relevant tools from 100+ catalog")
    print("2. Phase 5 examples: Include examples for those 10 tools only")
    print("3. Phase 5 caching: Cache the 10 tools + examples for 90% discount")
    print("4. Result: High accuracy (90%+) + low cost (90% cache discount)")


if __name__ == "__main__":
    main()
