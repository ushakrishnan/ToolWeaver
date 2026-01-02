"""
Demo: Code Stub Generation for Progressive Disclosure

Shows how the StubGenerator converts ToolCatalog definitions
into importable Python stubs with Pydantic models.

This enables AI models to:
1. Explore tool directories without loading full definitions
2. Import only needed tools on-demand (30-50% context reduction)
3. Use type-safe interfaces with IDE support
"""

import asyncio
import tempfile
from pathlib import Path

from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter


def create_sample_catalog() -> ToolCatalog:
    """Create a sample tool catalog with diverse tools"""
    catalog = ToolCatalog(source="demo", version="1.0")

    # Google Drive tools
    catalog.add_tool(ToolDefinition(
        name="get_document",
        type="function",
        description="Retrieve a Google Doc by ID",
        domain="google_drive",
        parameters=[
            ToolParameter(name="doc_id", type="string", description="Document ID", required=True),
            ToolParameter(name="format", type="string", description="Export format", required=False)
        ]
    ))

    catalog.add_tool(ToolDefinition(
        name="create_document",
        type="function",
        description="Create a new Google Doc",
        domain="google_drive",
        parameters=[
            ToolParameter(name="title", type="string", description="Document title", required=True),
            ToolParameter(name="content", type="string", description="Initial content", required=False)
        ]
    ))

    # Jira tools
    catalog.add_tool(ToolDefinition(
        name="create_ticket",
        type="function",
        description="Create a Jira ticket",
        domain="jira",
        parameters=[
            ToolParameter(name="title", type="string", description="Ticket title", required=True),
            ToolParameter(name="description", type="string", description="Ticket description", required=False),
            ToolParameter(name="priority", type="integer", description="Priority (1-5)", required=False)
        ]
    ))

    # Slack tools
    catalog.add_tool(ToolDefinition(
        name="send_message",
        type="function",
        description="Send a Slack message",
        domain="slack",
        parameters=[
            ToolParameter(name="channel", type="string", description="Channel ID", required=True),
            ToolParameter(name="text", type="string", description="Message text", required=True),
            ToolParameter(name="thread_ts", type="string", description="Thread timestamp", required=False)
        ]
    ))

    return catalog


def show_generated_structure(stub_dir: Path):
    """Display the generated file structure"""
    print("\n📁 Generated File Structure:")
    print("=" * 60)

    for path in sorted(stub_dir.rglob("*.py")):
        rel_path = path.relative_to(stub_dir)
        indent = "  " * (len(rel_path.parts) - 1)
        print(f"{indent}└── {rel_path.name}")


def show_stub_content(stub_dir: Path, tool_name: str):
    """Show content of a specific stub"""
    print(f"\n📄 Content of {tool_name}:")
    print("=" * 60)

    # Find the stub file
    stub_files = list(stub_dir.rglob(f"{tool_name}.py"))
    if stub_files:
        content = stub_files[0].read_text()
        # Show first 40 lines
        lines = content.split("\n")[:40]
        print("\n".join(lines))
        if len(content.split("\n")) > 40:
            print(f"\n... ({len(content.split('\n')) - 40} more lines)")


def show_usage_example():
    """Show how AI models would use the generated stubs"""
    print("\n💡 Usage Example (in AI-generated code):")
    print("=" * 60)
    print("""
# Step 1: Explore available tools (file tree - minimal tokens)
from pathlib import Path
tools_dir = Path("tools")
servers = [d.name for d in tools_dir.iterdir() if d.is_dir()]
print(f"Available servers: {servers}")  # ['google_drive', 'jira', 'slack']

# Step 2: Import only needed tools (on-demand loading)
from tools.google_drive import get_document, GetDocumentInput

# Step 3: Use type-safe interface
doc_input = GetDocumentInput(doc_id="1234", format="pdf")
result = await get_document(doc_input)

if result.success:
    print(f"Document retrieved: {result.result}")
else:
    print(f"Error: {result.error}")
""")


async def main():
    """Run the demo"""
    print("🚀 Code Stub Generation Demo")
    print("=" * 60)

    # Create sample catalog
    print("\n1. Creating sample tool catalog...")
    catalog = create_sample_catalog()
    print(f"   ✓ Created catalog with {len(catalog.tools)} tools")
    print(f"   Domains: {', '.join({t.domain for t in catalog.tools.values()})}")

    # Generate stubs
    with tempfile.TemporaryDirectory() as tmp:
        stub_dir = Path(tmp) / "stubs"
        print(f"\n2. Generating stubs in: {stub_dir}")

        generator = StubGenerator(catalog, stub_dir)
        stubs = generator.generate_all()

        print(f"   ✓ Generated {len(stubs)} stub files")

        # Show structure
        show_generated_structure(stub_dir)

        # Show sample stub
        show_stub_content(stub_dir, "get_document")

        # Show generated stub info
        print("\n📊 Generated Stubs Info:")
        print("=" * 60)
        stub_list = generator.list_generated_stubs()
        for stub_name in stub_list:
            stub_info = generator.get_stub_info(stub_name)
            if stub_info:
                print(f"\n{stub_name}:")
                print(f"  Tool: {stub_info.tool_name}")
                print(f"  Path: {Path(stub_info.file_path).relative_to(stub_dir)}")
                print(f"  Classes: {', '.join(stub_info.classes)}")
                print(f"  Imports: {len(stub_info.imports)} import statements")

        # Show usage example
        show_usage_example()

        # Show context reduction
        print("\n📉 Context Reduction Benefits:")
        print("=" * 60)

        # Calculate tokens for full catalog
        full_format = catalog.to_llm_format()
        full_tokens = sum(len(str(tool)) for tool in full_format)

        # Calculate tokens for file tree (just exploring)
        file_tree_tokens = len(str([d.name for d in stub_dir.glob("tools/*")]))

        # Calculate tokens for single tool import
        single_stub = stub_dir / "tools" / "google_drive" / "get_document.py"
        single_tokens = len(single_stub.read_text()) if single_stub.exists() else 0

        print(f"Full catalog in context: ~{full_tokens} tokens")
        print(f"File tree exploration: ~{file_tree_tokens} tokens ({100*file_tree_tokens/full_tokens:.1f}% of full)")
        print(f"Single tool import: ~{single_tokens} tokens ({100*single_tokens/full_tokens:.1f}% of full)")
        print(f"\nContext reduction: {100*(1 - single_tokens/full_tokens):.1f}% when loading one tool")


if __name__ == "__main__":
    asyncio.run(main())
