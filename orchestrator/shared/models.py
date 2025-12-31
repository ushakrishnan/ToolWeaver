from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Tool Definition Models (Phase 1: Foundation) ---

class ToolExample(BaseModel):
    """
    Example of how to use a tool, including scenario, input, output, and notes.
    Helps LLMs understand tool usage patterns and parameter conventions.
    
    Examples improve parameter accuracy from 72% to 90%+ by showing:
    - Format conventions (dates, IDs, etc.)
    - Optional parameter usage patterns
    - Typical scenarios and expected outputs
    """
    scenario: str = Field(..., description="Description of when to use this tool in this way")
    input: dict[str, Any] = Field(..., description="Example input parameters")
    output: Any = Field(..., description="Example output result")
    notes: str | None = Field(None, description="Additional usage notes or conventions")

class ToolParameter(BaseModel):
    """
    Individual tool parameter definition with validation.
    
    Supports JSON Schema types and nested objects/arrays.
    """
    name: str
    type: str  # "string", "integer", "number", "boolean", "object", "array"
    description: str
    required: bool = False
    enum: list[str] | None = None
    properties: dict[str, Any] | None = None  # For nested objects
    items: dict[str, Any] | None = None  # For arrays
    default: Any | None = None

class ToolDefinition(BaseModel):
    """
    Complete capability definition with metadata.

    Represents a capability that can be used by the planner/orchestrator.
    Supports MCP tools, Python functions, code execution, and agents (A2A).
    """
    name: str
    # Allow broader type taxonomy used in tests and discovery
    type: Literal["mcp", "function", "code_exec", "agent", "tool"]
    description: str
    # Optional provider (e.g., "mcp", "a2a", "custom")
    provider: str | None = None
    # Parameters default to empty list for backward compatibility
    parameters: list[ToolParameter] = Field(default_factory=list)
    # Optional JSON Schema-style IO definitions used by streaming tests
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    # Alternative return schema
    returns: dict[str, Any] | None = None  # Return type schema
    metadata: dict[str, Any] = Field(default_factory=dict)  # Usage stats, etc.
    source: str = "unknown"  # Where tool was discovered from
    version: str = "1.0"
    defer_loading: bool = False  # Phase 3: For semantic search
    examples: list[ToolExample] = Field(default_factory=list)  # Phase 5: Usage examples
    domain: str = "general"  # Phase 7: Tool domain for sharding (github, slack, aws, etc.)

    def to_llm_format(self, include_examples: bool = True) -> dict[str, Any]:
        """
        Convert to OpenAI/Anthropic function calling format.
        
        Returns standardized tool definition that works with:
        - OpenAI function calling
        - Azure OpenAI function calling
        - Anthropic tool use
        - Google Gemini function calling
        
        Args:
            include_examples: If True, appends examples to description (Phase 5)
        """
        description = self.description

        # Append examples to description for better LLM understanding
        if include_examples and self.examples:
            description += "\n\nExamples:\n"
            for i, ex in enumerate(self.examples, 1):
                description += f"\n{i}. {ex.scenario}\n"
                description += f"   Input: {ex.input}\n"
                description += f"   Output: {ex.output}\n"
                if ex.notes:
                    description += f"   Notes: {ex.notes}\n"

        return {
            "name": self.name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        **({"enum": p.enum} if p.enum else {}),
                        **({"default": p.default} if p.default is not None else {})
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }

class ToolCatalog(BaseModel):
    """
    Collection of tools with discovery metadata.
    
    Manages the lifecycle of tool definitions:
    - Registration
    - Discovery timestamp tracking
    - Filtering by type
    - Conversion to LLM formats
    """
    tools: dict[str, ToolDefinition] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"
    version: str = "1.0"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_tool(self, tool: ToolDefinition) -> None:
        """Register a new tool in the catalog."""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Retrieve tool by name."""
        return self.tools.get(name)

    def get_by_type(self, tool_type: str) -> list[ToolDefinition]:
        """Get all tools of specific type (mcp, function, code_exec)."""
        return [t for t in self.tools.values() if t.type == tool_type]

    def to_llm_format(self, defer_loading: bool = False, include_examples: bool = True) -> list[dict[str, Any]]:
        """
        Convert all tools to LLM function calling format.
        
        Args:
            defer_loading: If True, only include tools with defer_loading=False
            include_examples: If True, include usage examples in descriptions (Phase 5)
        """
        return [
            t.to_llm_format(include_examples=include_examples)
            for t in self.tools.values()
            if not defer_loading or not t.defer_loading
        ]

# --- Plan schema models ---
class RetryPolicy(BaseModel):
    retries: int = 1
    backoff_s: int = 1

class StepModel(BaseModel):
    id: str
    tool: str
    input: dict[str, Any]
    run_if: str | None = None
    depends_on: list[str] = []
    mode: str = "parallel"   # "parallel" or "sequential"
    idempotency_key: str | None = None
    retry_policy: RetryPolicy | None = None

class FinalSynthesisModel(BaseModel):
    prompt_template: str
    meta: dict[str, Any] | None = {}

class PlanModel(BaseModel):
    request_id: str
    steps: list[StepModel]
    final_synthesis: FinalSynthesisModel

# --- Receipt example models ---
class ReceiptOCRIn(BaseModel):
    image_uri: str

class ReceiptOCROut(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)

class LineItem(BaseModel):
    description: str
    quantity: int | None = 1
    unit_price: float | None = None
    total: float | None = None

class LineItemParserIn(BaseModel):
    ocr_text: str

class LineItemParserOut(BaseModel):
    items: list[LineItem]

class CategorizerIn(BaseModel):
    items: list[dict[str, Any]]

class CategorizerOut(BaseModel):
    categorized: list[dict[str, Any]]

# --- Function Call Models ---
class FunctionCallInput(BaseModel):
    name: str
    args: dict[str, Any]

class FunctionCallOutput(BaseModel):
    result: Any

# --- Code-exec models ---
class CodeExecInput(BaseModel):
    code: str
    input_data: dict[str, Any]

class CodeExecOutput(BaseModel):
    output: Any
