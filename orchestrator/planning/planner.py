"""
Large Model Planner - Uses GPT-4o or Claude to generate execution plans.

This module provides a high-level planner that uses large language models
to convert natural language requests into structured execution plans.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)
load_dotenv()

# Optional imports - only loaded if API keys are available
try:
    from openai import AsyncOpenAI, AsyncAzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed. Install with: pip install anthropic")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini package not installed. Install with: pip install google-generativeai")


class LargePlanner:
    """
    Uses a large language model (GPT-4o, Claude 3.5) to generate execution plans
    from natural language user requests.
    
    The planner understands available tools and generates JSON plans with:
    - Step definitions (tool type, inputs, dependencies)
    - Dependency resolution (DAG structure)
    - Parallel vs sequential execution modes
    """
    
    def __init__(
        self, 
        provider: str = None, 
        model: str = None,
        tool_catalog: Optional[ToolCatalog] = None,
        use_tool_search: bool = True,
        search_threshold: int = 20,
        use_programmatic_calling: bool = True
    ):
        """
        Initialize the planner with specified LLM provider.
        
        Args:
            provider: "openai", "azure-openai", "anthropic", or "gemini" (defaults to PLANNER_PROVIDER env var)
            model: Specific model name (defaults to PLANNER_MODEL env var)
            tool_catalog: Optional ToolCatalog with tool definitions (defaults to legacy hardcoded tools)
            use_tool_search: Enable semantic search for tool selection (Phase 3, default: True)
            search_threshold: Only use search if tool count exceeds this (default: 20)
            use_programmatic_calling: Enable programmatic tool calling (Phase 4, default: True)
        
        Phase 2 Usage - Tool Discovery:
            To use auto-discovered tools, run discovery first:
            
                from orchestrator.tool_discovery import discover_tools
                catalog = await discover_tools(mcp_client=client, ...)
                planner = LargePlanner(tool_catalog=catalog)
        
        Phase 3 Usage - Semantic Search:
            When tool_catalog has >20 tools, semantic search automatically selects
            the most relevant 5-10 tools for each request, reducing token usage by 80-90%.
        
        Phase 4 Usage - Programmatic Tool Calling:
            When enabled, LLM can generate code that orchestrates tool calls in parallel,
            reducing latency by 60-80% and saving 37% additional tokens.
        """
        # Get provider from env if not specified
        self.provider = (provider or os.getenv("PLANNER_PROVIDER", "openai")).lower()
        
        # Store tool catalog (will use default if None)
        self.tool_catalog = tool_catalog
        
        # Phase 3: Semantic search configuration
        self.use_tool_search = use_tool_search
        self.search_threshold = search_threshold
        self.search_engine = None  # Lazy init
        
        # Phase 4: Programmatic calling configuration
        self.use_programmatic_calling = use_programmatic_calling
        
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI package not installed")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model or os.getenv("PLANNER_MODEL", "gpt-4o")
            
        elif self.provider == "azure-openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI package not installed")
            
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
            use_ad = os.getenv("AZURE_OPENAI_USE_AD", "false").lower() == "true"
            
            if not endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable required")
            
            if use_ad:
                # Use Azure AD (Entra ID) authentication
                try:
                    from azure.identity.aio import DefaultAzureCredential
                    self.credential = DefaultAzureCredential()
                    
                    # Token provider must be async and return just the token string
                    async def get_azure_token():
                        token = await self.credential.get_token("https://cognitiveservices.azure.com/.default")
                        return token.token
                    
                    self.client = AsyncAzureOpenAI(
                        azure_ad_token_provider=get_azure_token,
                        azure_endpoint=endpoint,
                        api_version=api_version
                    )
                    logger.info("Using Azure AD authentication for Azure OpenAI")
                except ImportError:
                    raise RuntimeError("azure-identity package not installed. Install with: pip install azure-identity")
            else:
                # Use API key authentication
                self.credential = None
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("AZURE_OPENAI_API_KEY environment variable required (or set AZURE_OPENAI_USE_AD=true)")
                self.client = AsyncAzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=api_version
                )
                logger.info("Using API key authentication for Azure OpenAI")
            self.model = model or os.getenv("PLANNER_MODEL", "gpt-4o")
            
        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("Anthropic package not installed")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = model or os.getenv("PLANNER_MODEL", "claude-3-5-sonnet-20241022")
            
        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise RuntimeError("Google Gemini package not installed")
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model or os.getenv("PLANNER_MODEL", "gemini-1.5-pro"))
            self.model = model or os.getenv("PLANNER_MODEL", "gemini-1.5-pro")
            
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'openai', 'azure-openai', 'anthropic', or 'gemini'")
        
        logger.info(f"Initialized LargePlanner with {self.provider} ({self.model})")
    
    async def close(self):
        """Clean up resources (Azure AD credential, HTTP clients)."""
        if hasattr(self, 'client') and hasattr(self.client, 'close'):
            await self.client.close()
        
        if hasattr(self, 'credential') and self.credential is not None:
            await self.credential.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _get_default_catalog(self) -> ToolCatalog:
        """
        Create default tool catalog with legacy hardcoded tools.
        Provides backward compatibility for existing code.
        
        Returns:
            ToolCatalog with receipt processing tools
        """
        catalog = ToolCatalog(source="legacy_hardcoded", version="1.0")
        
        # MCP Tools
        catalog.add_tool(ToolDefinition(
            name="receipt_ocr",
            type="mcp",
            description="Extract text from receipt images using OCR",
            parameters=[
                ToolParameter(name="image_uri", type="string", description="URL or path to receipt image", required=True)
            ],
            metadata={
                "output_schema": {"text": "string", "confidence": "float"}
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="line_item_parser",
            type="mcp",
            description="Parse OCR text into structured line items with prices",
            parameters=[
                ToolParameter(name="ocr_text", type="string", description="Raw text from receipt", required=True)
            ],
            metadata={
                "output_schema": {"items": "array"}
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="expense_categorizer",
            type="mcp",
            description="Categorize line items into expense categories (food, beverage, etc.)",
            parameters=[
                ToolParameter(name="items", type="array", description="List of line items", required=True)
            ],
            metadata={
                "output_schema": {"categorized": "array"}
            }
        ))
        
        # Function Tools
        catalog.add_tool(ToolDefinition(
            name="compute_tax",
            type="function",
            description="Calculate tax amount",
            parameters=[
                ToolParameter(name="amount", type="number", description="Amount to tax", required=True),
                ToolParameter(name="tax_rate", type="number", description="Tax rate (0-1)", required=True)
            ],
            metadata={
                "output_type": "float"
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="merge_items",
            type="function",
            description="Merge items and compute aggregate statistics",
            parameters=[
                ToolParameter(name="items", type="array", description="List of items", required=True)
            ],
            metadata={
                "output_schema": {"total_sum": "number", "count": "number", "avg_total": "number"}
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="apply_discount",
            type="function",
            description="Apply percentage discount to amount",
            parameters=[
                ToolParameter(name="amount", type="number", description="Original amount", required=True),
                ToolParameter(name="discount_percent", type="number", description="Discount percentage", required=True)
            ],
            metadata={
                "output_schema": {"original": "number", "discount": "number", "final": "number"}
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="filter_items_by_category",
            type="function",
            description="Filter items by category",
            parameters=[
                ToolParameter(name="items", type="array", description="List of items", required=True),
                ToolParameter(name="category", type="string", description="Category to filter by", required=True)
            ],
            metadata={
                "output_type": "array"
            }
        ))
        
        catalog.add_tool(ToolDefinition(
            name="compute_item_statistics",
            type="function",
            description="Compute comprehensive statistics about items",
            parameters=[
                ToolParameter(name="items", type="array", description="List of items", required=True)
            ],
            metadata={
                "output_schema": {"count": "number", "total_amount": "number", "categories": "object"}
            }
        ))
        
        # Code Execution
        catalog.add_tool(ToolDefinition(
            name="code_exec",
            type="code_exec",
            description="Execute arbitrary Python code for custom transformations",
            parameters=[
                ToolParameter(name="code", type="string", description="Python code to execute", required=True),
                ToolParameter(name="input_data", type="object", description="Dict of input variables", required=True)
            ],
            metadata={
                "safety": "Sandboxed execution with safe builtins only",
                "available_builtins": ["len", "sum", "min", "max", "str", "int", "float", "list", "dict", "range", "sorted", "enumerate", "zip"],
                "output_variable": "output"
            }
        ))
        
        return catalog
    
    def _get_tool_catalog(self, available_tools: Optional[List[ToolDefinition]] = None) -> ToolCatalog:
        """
        Get the tool catalog to use for planning.
        
        Priority:
        1. available_tools parameter (Phase 3 semantic search results)
        2. self.tool_catalog (injected at init)
        3. Auto-discovered catalog (Phase 2, if auto_discover=True)
        4. Default catalog (legacy hardcoded tools)
        
        Args:
            available_tools: Optional list of tools from semantic search (Phase 3)
            
        Returns:
            ToolCatalog instance
        """
        # Phase 3: Use search results if provided
        if available_tools is not None:
            catalog = ToolCatalog(source="semantic_search", version="1.0")
            for tool in available_tools:
                catalog.add_tool(tool)
            return catalog
        
        # Phase 1: Use injected catalog if provided
        if self.tool_catalog is not None:
            return self.tool_catalog
        
        # Backward compatibility: Use default catalog
        return self._get_default_catalog()
    
    def _build_system_prompt(self, available_tools: Optional[List[ToolDefinition]] = None) -> str:
        """
        Build the system prompt for the planner.
        
        Args:
            available_tools: Optional list of tools from semantic search
            
        Returns:
            System prompt string with tool definitions in LLM format
        """
        tool_catalog = self._get_tool_catalog(available_tools)
        
        # Group tools by type for better organization
        tools_by_type = {
            "mcp": tool_catalog.get_by_type("mcp"),
            "function": tool_catalog.get_by_type("function"),
            "code_exec": tool_catalog.get_by_type("code_exec")
        }
        
        # Build tool descriptions
        tool_descriptions = {}
        for tool_type, tools in tools_by_type.items():
            if tools:
                tool_descriptions[f"{tool_type}_tools"] = {
                    tool.name: {
                        "description": tool.description,
                        "parameters": {p.name: p.type for p in tool.parameters},
                        "required": [p.name for p in tool.parameters if p.required],
                        "metadata": tool.metadata
                    }
                    for tool in tools
                }
        
        # Build programmatic calling section if enabled
        ptc_section = ""
        if self.use_programmatic_calling:
            ptc_section = """

PROGRAMMATIC TOOL CALLING (Advanced):

When you need to:
- Call multiple tools in parallel (faster than sequential)
- Filter/transform large datasets before returning to context
- Loop over collections with tool calls
- Apply complex logic (conditionals, aggregations)

Use code_exec with tool orchestration code instead of multiple tool steps:

Example (BAD - Sequential, slow, wastes tokens):
Step 1: get_team_members("engineering") → 20 members (5KB into context)
Step 2: get_expenses(member1) → (10KB into context)
Step 3-21: get_expenses(member2-20) → (200KB+ into context!)
Step 22: Manual comparison in next LLM call

Example (GOOD - Parallel, fast, minimal context):
Step 1: code_exec with:
```python
# All tools are available as async functions
team = await get_team_members(team_id="engineering")
budgets = {{level: await get_budget(level) for level in set(m["level"] for m in team)}}

# Parallel execution (much faster!)
expenses = await asyncio.gather(*[get_expenses(user_id=m["id"], period="Q3") for m in team])

# Filter in code (keeps 200KB out of LLM context!)
exceeded = []
for member, exp in zip(team, expenses):
    total = sum(e["amount"] for e in exp)
    if total > budgets[member["level"]]:
        exceeded.append({{"name": member["name"], "spent": total}})

# Only return summary (2KB vs 200KB!)
print(json.dumps(exceeded))
```

Use programmatic calling when:
✅ Need to call same tool multiple times (list iteration)
✅ Can filter/aggregate results before LLM sees them
✅ Operations are independent (can run in parallel)
✅ Dealing with large intermediate data

DON'T use programmatic calling when:
❌ Single tool call is sufficient
❌ LLM needs to see full intermediate results
❌ Simple, straightforward workflows
❌ Tools have complex dependencies
"""
        
        return f"""You are an execution planner for a hybrid orchestration system. Your job is to convert natural language requests into structured JSON execution plans.

Available Tools:
{json.dumps(tool_descriptions, indent=2)}

Plan Structure:
{{
  "request_id": "unique-id",
  "steps": [
    {{
      "id": "step-1",
      "tool": "tool_name",
      "input": {{"param": "value or step:previous-step"}},
      "depends_on": ["step-id-1", "step-id-2"],
      "mode": "parallel" or "sequential",
      "idempotency_key": "optional-key"
    }}
  ],
  "final_synthesis": {{
    "prompt_template": "Template for final output",
    "meta": {{"expose_inputs_to_reasoner": false}}
  }}
}}

Guidelines:
1. Use step references ("step:step-id") to pass outputs between steps
2. Set dependencies correctly to ensure proper execution order
3. Use "parallel" mode for independent steps, "sequential" for dependent steps
4. Choose the right tool type: MCP for deterministic tasks, functions for structured APIs, code_exec for custom logic
5. Generate valid JSON only, no explanations outside the JSON{ptc_section}

Respond with only the JSON execution plan."""

    async def generate_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[ToolDefinition]] = None
    ) -> Dict[str, Any]:
        """
        Generate an execution plan from a natural language request.
        
        Args:
            user_request: Natural language description of what to do
            context: Optional additional context (image URLs, data, etc.)
            available_tools: Optional list of tools from semantic search (Phase 3)
            
        Returns:
            Dictionary containing the execution plan
            
        Example:
            # Basic usage (uses default or injected catalog)
            planner = LargePlanner(provider="openai")
            plan = await planner.generate_plan(
                "Process this receipt and calculate the total with tax",
                context={"image_url": "https://..."}
            )
            
            # With custom tool catalog (Phase 1)
            catalog = ToolCatalog(source="custom")
            planner = LargePlanner(provider="openai", tool_catalog=catalog)
            plan = await planner.generate_plan(...)
            
            # Phase 3: Semantic search automatically selects relevant tools
            planner = LargePlanner(provider="openai", tool_catalog=large_catalog)
            plan = await planner.generate_plan("send slack message")
            # Automatically searches and uses only relevant tools
        """
        logger.info(f"Generating plan for request: {user_request[:100]}...")
        
        # Phase 3: Adaptive tool selection with semantic search
        if available_tools is None:
            # Get or create tool catalog
            catalog = self._get_tool_catalog()
            total_tools = len(catalog.tools)
            
            # Decide whether to use semantic search
            if self.use_tool_search and total_tools > self.search_threshold:
                # Lazy init search engine
                if self.search_engine is None:
                    from orchestrator.tool_search import ToolSearchEngine
                    self.search_engine = ToolSearchEngine()
                    logger.info("Initialized semantic search engine")
                
                # Search for relevant tools
                search_results = self.search_engine.search(
                    query=user_request,
                    catalog=catalog,
                    top_k=10,  # Get top 10 most relevant tools
                    min_score=0.3
                )
                
                available_tools = [tool for tool, score in search_results]
                
                # Calculate token savings
                tokens_without_search = total_tools * 150  # ~150 tokens per tool
                tokens_with_search = len(available_tools) * 150
                savings_pct = ((tokens_without_search - tokens_with_search) / tokens_without_search) * 100
                
                logger.info(
                    f"Semantic search: {total_tools} tools → {len(available_tools)} relevant tools "
                    f"(~{savings_pct:.1f}% token reduction, ~{tokens_without_search - tokens_with_search:,} tokens saved)"
                )
            else:
                # Use all tools (small catalog or search disabled)
                available_tools = list(catalog.tools.values())
                if total_tools <= self.search_threshold:
                    logger.info(f"Using all {total_tools} tools (below search threshold)")
                else:
                    logger.info(f"Using all {total_tools} tools (search disabled)")
        else:
            # Tools explicitly provided (e.g., from external search)
            logger.info(f"Using {len(available_tools)} explicitly provided tools")
        
        # Build the user message
        user_message = f"User Request: {user_request}\n"
        if context:
            user_message += f"\nContext: {json.dumps(context, indent=2)}"
        
        try:
            if self.provider in ["openai", "azure-openai"]:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1  # Low temperature for consistent planning
                )
                plan_json = response.choices[0].message.content
                
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self._build_system_prompt(available_tools),
                    messages=[
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1
                )
                plan_json = response.content[0].text
                
            elif self.provider == "gemini":
                prompt = f"{self._build_system_prompt()}\n\n{user_message}"
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                plan_json = response.text
            
            # Parse and validate JSON
            plan = json.loads(plan_json)
            logger.info(f"Generated plan with {len(plan.get('steps', []))} steps")
            
            return plan
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate execution plan: {e}")
    
    async def refine_plan(
        self,
        original_plan: Dict[str, Any],
        feedback: str,
        available_tools: Optional[List[ToolDefinition]] = None
    ) -> Dict[str, Any]:
        """
        Refine an existing plan based on feedback or errors.
        
        Args:
            original_plan: The original execution plan
            feedback: Description of issues or desired changes
            available_tools: Optional list of tools from semantic search (Phase 3)
            
        Returns:
            Updated execution plan
        """
        logger.info(f"Refining plan based on feedback: {feedback[:100]}...")
        
        user_message = f"""Original Plan:
{json.dumps(original_plan, indent=2)}

Feedback/Issues:
{feedback}

Please generate an improved plan that addresses the feedback."""
        
        try:
            if self.provider in ["openai", "azure-openai"]:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                plan_json = response.choices[0].message.content
                
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self._build_system_prompt(available_tools),
                    messages=[
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1
                )
                plan_json = response.content[0].text
                
            elif self.provider == "gemini":
                prompt = f"{self._build_system_prompt(available_tools)}\n\n{user_message}"
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                plan_json = response.text
            
            refined_plan = json.loads(plan_json)
            logger.info("Plan refinement completed")
            
            return refined_plan
            
        except Exception as e:
            logger.error(f"Plan refinement failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to refine execution plan: {e}")
