# Migration Guide: ToolCatalog Architecture

This guide helps you upgrade existing code to use the **ToolCatalog** architecture.

## Summary of Changes

### What Changed?
- **LargePlanner** now accepts an optional `tool_catalog` parameter
- **generate_plan()** and **refine_plan()** now accept an optional `available_tools` parameter
- Tool definitions moved from hardcoded dicts to **Pydantic models** (ToolParameter, ToolDefinition, ToolCatalog)
- **Azure AD authentication** now supported for Azure OpenAI

### What Stayed the Same?
- ✅ **All existing code works without changes** (backward compatible)
- ✅ Default tool catalog matches legacy hardcoded tools
- ✅ Same JSON plan format
- ✅ Same orchestrator execution behavior

---

## Migration Scenarios

### Scenario 1: No Changes Needed (Backward Compatible)

**Your existing code:**
```python
from orchestrator.planner import LargePlanner

planner = LargePlanner(provider="azure-openai")
plan = await planner.generate_plan(
    "Process receipt and calculate total",
    context={"image_url": "https://example.com/receipt.jpg"}
)
```

**Status:** ✅ **Works as-is, no migration needed**

The planner automatically uses the default catalog with all legacy tools (receipt_ocr, line_item_parser, compute_tax, etc.).

---

### Scenario 2: Migrating to Custom Tool Definitions

**Before (hardcoded in your code):**
```python
# You had to modify planner.py to add new tools
# Or pass tools as context strings
```

**After (using ToolCatalog):**
```python
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.planner import LargePlanner

# Define your custom catalog
catalog = ToolCatalog(source="my_application", version="1.0")

# Add custom tools
catalog.add_tool(ToolDefinition(
    name="invoice_parser",
    type="mcp",
    description="Parse invoice data with line items",
    parameters=[
        ToolParameter(
            name="invoice_data", 
            type="string", 
            description="Raw invoice text", 
            required=True
        )
    ],
    metadata={"output_schema": {"items": "array", "total": "number"}}
))

catalog.add_tool(ToolDefinition(
    name="validate_invoice",
    type="function",
    description="Validate invoice totals match line items",
    parameters=[
        ToolParameter(name="items", type="array", description="Line items", required=True),
        ToolParameter(name="total", type="number", description="Invoice total", required=True)
    ]
))

# Use custom catalog
planner = LargePlanner(provider="azure-openai", tool_catalog=catalog)
plan = await planner.generate_plan("Validate this invoice...")
```

**Benefits:**
- 🔒 Type safety with Pydantic validation
- 📝 JSON Schema for parameters
- 🔄 Reusable across multiple planners
- 🧪 Easier to test

---

### Scenario 3: Azure AD Authentication (New Feature)

**Before (API Key only):**
```bash
# .env
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=abc123...
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
```

**After (Azure AD - Recommended):**
```bash
# .env
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_USE_AD=true
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
```

Then run:
```bash
az login
```

**Your code stays the same:**
```python
planner = LargePlanner(provider="azure-openai")
# Automatically uses Azure AD authentication
```

**Requirements:**
- `aiohttp` package installed (added to requirements.txt)
- Azure CLI login with `Cognitive Services OpenAI User` role assigned

---

### Scenario 4: Preparing for Phase 3 (Semantic Search)

**Current (Phase 1):**
```python
planner = LargePlanner(provider="azure-openai", tool_catalog=my_catalog)
plan = await planner.generate_plan("Process receipt...")
# Uses all tools in my_catalog
```

**Future (Phase 3 - Preview):**
```python
from orchestrator.tool_search import ToolSearch

# Initialize search engine (Phase 3)
search = ToolSearch(catalog=my_large_catalog)  # 1000+ tools

# Search for relevant tools
relevant_tools = search.search("receipt processing", top_k=10)
# Returns 10 most relevant tools (semantic + BM25)

# Use only relevant tools for planning
plan = await planner.generate_plan(
    "Process receipt...",
    available_tools=relevant_tools  # Only 10 tools vs 1000
)
```

**What to do now:**
- ✅ Migrate to ToolCatalog (done if following Scenario 2)
- ✅ Use `available_tools` parameter is already supported in Phase 1
- ⏳ Wait for Phase 3 ToolSearch implementation

---

## API Reference Changes

### LargePlanner.__init__()

**Before:**
```python
def __init__(self, provider: str = None, model: str = None)
```

**After:**
```python
def __init__(
    self, 
    provider: str = None, 
    model: str = None,
    tool_catalog: Optional[ToolCatalog] = None  # NEW
)
```

### LargePlanner.generate_plan()

**Before:**
```python
async def generate_plan(
    self,
    user_request: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**After:**
```python
async def generate_plan(
    self,
    user_request: str,
    context: Optional[Dict[str, Any]] = None,
    available_tools: Optional[List[ToolDefinition]] = None  # NEW
) -> Dict[str, Any]
```

### LargePlanner.refine_plan()

**Before:**
```python
async def refine_plan(
    self,
    original_plan: Dict[str, Any],
    feedback: str
) -> Dict[str, Any]
```

**After:**
```python
async def refine_plan(
    self,
    original_plan: Dict[str, Any],
    feedback: str,
    available_tools: Optional[List[ToolDefinition]] = None  # NEW
) -> Dict[str, Any]
```

---

## Testing Your Migration

### 1. Run Existing Tests
```bash
# Activate venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run all tests
python -m pytest tests/ -v

# Should see: 29/29 tests passing
```

### 2. Test with Your Code
```python
# Test backward compatibility
from orchestrator.planner import LargePlanner

async def test_backward_compat():
    planner = LargePlanner(provider="azure-openai")
    plan = await planner.generate_plan("Process receipt...")
    
    assert "steps" in plan
    assert len(plan["steps"]) > 0
    print("✓ Backward compatibility works!")

# Test custom catalog
async def test_custom_catalog():
    from orchestrator.models import ToolCatalog, ToolDefinition
    
    catalog = ToolCatalog(source="test", version="1.0")
    catalog.add_tool(ToolDefinition(
        name="test_tool",
        type="function",
        description="Test tool",
        parameters=[]
    ))
    
    planner = LargePlanner(provider="azure-openai", tool_catalog=catalog)
    assert planner._get_tool_catalog().source == "test"
    print("✓ Custom catalog works!")
```

### 3. Verify Azure AD Authentication (if using)
```bash
# Login to Azure
az login

# Test connection
python test_azure_connection.py

# Should see: ✓ Connection successful!
```

---

## Breaking Changes

### None! 🎉

This release is **100% backward compatible**. All existing code continues to work without modifications.

---

## New Environment Variables

Add to your `.env` file:

```bash
# Azure AD Authentication (optional, for Azure OpenAI)
AZURE_OPENAI_USE_AD=true  # Set to 'true' to use Azure AD instead of API key

# Future Phase 3 (coming soon)
# USE_TOOL_SEARCH=true
# EMBEDDING_MODEL=text-embedding-3-small
```

---

## Common Issues

### Issue 1: "aiohttp package is not installed"
**Solution:**
```bash
pip install aiohttp
```

### Issue 2: Azure AD authentication fails
**Solution:**
```bash
# Ensure you're logged in
az login

# Verify your account
az account show

# Check you have the right role on Azure OpenAI resource
# Required: "Cognitive Services OpenAI User"
```

### Issue 3: Tests fail with "OPENAI_API_KEY not set"
**Solution:**
Tests use mocked API keys. Make sure you're running tests with pytest:
```bash
python -m pytest tests/test_planner_integration.py -v
```

Not directly:
```bash
# Don't do this:
python tests/test_planner_integration.py
```

---

## Rollback Plan

If you encounter issues, you can temporarily revert to the old behavior:

1. **Don't pass `tool_catalog` parameter** - planner uses legacy behavior
2. **Don't pass `available_tools` parameter** - planner uses all tools
3. **Keep using API keys** - don't set `AZURE_OPENAI_USE_AD=true`

Your code will work exactly as before.

---

## Next Steps

### Immediate
- ✅ Test your existing code (should work as-is)
- ✅ Consider migrating to Azure AD authentication (more secure)
- ✅ Explore custom ToolCatalog for new tools

### Future (Phase 2-5)
- ⏳ **Phase 2**: Automatic tool discovery from MCP servers and decorators
- ⏳ **Phase 3**: Semantic search for large tool catalogs (1000+ tools)
- ⏳ **Phase 4**: Programmatic tool calling (70-80% latency reduction)
- ⏳ **Phase 5**: Prompt caching, examples, monitoring

---

## Support

- **Issues**: Check [DYNAMIC_TOOL_DISCOVERY_IMPLEMENTATION.md](DYNAMIC_TOOL_DISCOVERY_IMPLEMENTATION.md) for implementation details
- **Tests**: See `tests/test_tool_models.py` and `tests/test_planner_integration.py` for examples
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

## Changelog

### Phase 1 (December 2025) - ✅ Complete
- Added `ToolParameter`, `ToolDefinition`, `ToolCatalog` Pydantic models
- Refactored `LargePlanner` to accept optional `tool_catalog` parameter
- Added `available_tools` parameter to `generate_plan()` and `refine_plan()`
- Implemented Azure AD authentication for Azure OpenAI
- Added 29 comprehensive tests (20 unit + 9 integration)
- 100% backward compatible with existing code
