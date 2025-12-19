from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone

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
    input: Dict[str, Any] = Field(..., description="Example input parameters")
    output: Any = Field(..., description="Example output result")
    notes: Optional[str] = Field(None, description="Additional usage notes or conventions")

class ToolParameter(BaseModel):
    """
    Individual tool parameter definition with validation.
    
    Supports JSON Schema types and nested objects/arrays.
    """
    name: str
    type: str  # "string", "integer", "number", "boolean", "object", "array"
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None  # For nested objects
    items: Optional[Dict[str, Any]] = None  # For arrays
    default: Optional[Any] = None

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
    provider: Optional[str] = None
    # Parameters default to empty list for backward compatibility
    parameters: List[ToolParameter] = Field(default_factory=list)
    # Optional JSON Schema-style IO definitions used by streaming tests
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    # Alternative return schema
    returns: Optional[Dict[str, Any]] = None  # Return type schema
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Usage stats, etc.
    source: str = "unknown"  # Where tool was discovered from
    version: str = "1.0"
    defer_loading: bool = False  # Phase 3: For semantic search
    examples: List[ToolExample] = Field(default_factory=list)  # Phase 5: Usage examples
    domain: str = "general"  # Phase 7: Tool domain for sharding (github, slack, aws, etc.)
    
    def to_llm_format(self, include_examples: bool = True) -> Dict[str, Any]:
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
    tools: Dict[str, ToolDefinition] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_tool(self, tool: ToolDefinition):
        """Register a new tool in the catalog."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve tool by name."""
        return self.tools.get(name)
    
    def get_by_type(self, tool_type: str) -> List[ToolDefinition]:
        """Get all tools of specific type (mcp, function, code_exec)."""
        return [t for t in self.tools.values() if t.type == tool_type]
    
    def to_llm_format(self, defer_loading: bool = False, include_examples: bool = True) -> List[Dict[str, Any]]:
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
    input: Dict[str, Any]
    run_if: Optional[str] = None
    depends_on: List[str] = []
    mode: str = "parallel"   # "parallel" or "sequential"
    idempotency_key: Optional[str] = None
    retry_policy: Optional[RetryPolicy] = None

class FinalSynthesisModel(BaseModel):
    prompt_template: str
    meta: Optional[Dict[str, Any]] = {}

class PlanModel(BaseModel):
    request_id: str
    steps: List[StepModel]
    final_synthesis: FinalSynthesisModel

# --- Receipt example models ---
class ReceiptOCRIn(BaseModel):
    image_uri: str

class ReceiptOCROut(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)

class LineItem(BaseModel):
    description: str
    quantity: Optional[int] = 1
    unit_price: Optional[float] = None
    total: Optional[float] = None

class LineItemParserIn(BaseModel):
    ocr_text: str

class LineItemParserOut(BaseModel):
    items: List[LineItem]

class CategorizerIn(BaseModel):
    items: List[Dict[str, Any]]

class CategorizerOut(BaseModel):
    categorized: List[Dict[str, Any]]

# --- Function Call Models ---
class FunctionCallInput(BaseModel):
    name: str
    args: Dict[str, Any]

class FunctionCallOutput(BaseModel):
    result: Any

# --- Code-exec models ---
class CodeExecInput(BaseModel):
    code: str
    input_data: Dict[str, Any]

class CodeExecOutput(BaseModel):
    output: Any
