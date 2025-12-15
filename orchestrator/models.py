from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone

# --- Tool Definition Models (Phase 1: Foundation) ---

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
    Complete tool definition with metadata.
    
    Represents a tool that can be used by the planner/orchestrator.
    Supports MCP tools, functions, and code execution.
    """
    name: str
    type: Literal["mcp", "function", "code_exec"]
    description: str
    parameters: List[ToolParameter]
    returns: Optional[Dict[str, Any]] = None  # Return type schema
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Usage stats, etc.
    source: str = "unknown"  # Where tool was discovered from
    version: str = "1.0"
    defer_loading: bool = False  # Phase 3: For semantic search
    
    def to_llm_format(self) -> Dict[str, Any]:
        """
        Convert to OpenAI/Anthropic function calling format.
        
        Returns standardized tool definition that works with:
        - OpenAI function calling
        - Azure OpenAI function calling
        - Anthropic tool use
        - Google Gemini function calling
        """
        return {
            "name": self.name,
            "description": self.description,
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
    
    def add_tool(self, tool: ToolDefinition):
        """Register a new tool in the catalog."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve tool by name."""
        return self.tools.get(name)
    
    def get_by_type(self, tool_type: str) -> List[ToolDefinition]:
        """Get all tools of specific type (mcp, function, code_exec)."""
        return [t for t in self.tools.values() if t.type == tool_type]
    
    def to_llm_format(self, defer_loading: bool = False) -> List[Dict[str, Any]]:
        """
        Convert all tools to LLM function calling format.
        
        Args:
            defer_loading: If True, only include tools with defer_loading=False
        """
        return [
            t.to_llm_format() 
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
