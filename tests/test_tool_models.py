"""
Unit tests for tool definition models (Phase 1: Foundation).

Tests cover:
- ToolParameter validation
- ToolDefinition validation and conversion
- ToolCatalog operations
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from orchestrator.models import ToolParameter, ToolDefinition, ToolCatalog


class TestToolParameter:
    """Test ToolParameter model validation and behavior."""
    
    def test_basic_parameter(self):
        """Test creating a basic parameter."""
        param = ToolParameter(
            name="user_id",
            type="string",
            description="User identifier",
            required=True
        )
        
        assert param.name == "user_id"
        assert param.type == "string"
        assert param.required is True
        assert param.enum is None
    
    def test_parameter_with_enum(self):
        """Test parameter with enum values."""
        param = ToolParameter(
            name="priority",
            type="string",
            description="Priority level",
            enum=["low", "medium", "high"],
            required=False
        )
        
        assert param.enum == ["low", "medium", "high"]
        assert param.required is False
    
    def test_parameter_with_default(self):
        """Test parameter with default value."""
        param = ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds",
            default=30
        )
        
        assert param.default == 30
    
    def test_nested_object_parameter(self):
        """Test parameter with nested object properties."""
        param = ToolParameter(
            name="config",
            type="object",
            description="Configuration object",
            properties={
                "host": {"type": "string"},
                "port": {"type": "integer"}
            }
        )
        
        assert param.properties is not None
        assert "host" in param.properties
    
    def test_array_parameter(self):
        """Test parameter with array items."""
        param = ToolParameter(
            name="tags",
            type="array",
            description="List of tags",
            items={"type": "string"}
        )
        
        assert param.items is not None
        assert param.items["type"] == "string"


class TestToolDefinition:
    """Test ToolDefinition model validation and conversion."""
    
    def test_basic_tool_definition(self):
        """Test creating a basic tool definition."""
        tool = ToolDefinition(
            name="get_user",
            type="function",
            description="Retrieve user information",
            parameters=[
                ToolParameter(name="user_id", type="string", description="User ID", required=True)
            ]
        )
        
        assert tool.name == "get_user"
        assert tool.type == "function"
        assert len(tool.parameters) == 1
        assert tool.version == "1.0"
        assert tool.defer_loading is False
    
    def test_tool_type_validation(self):
        """Test that tool type must be one of: mcp, function, code_exec."""
        with pytest.raises(ValidationError):
            ToolDefinition(
                name="invalid_tool",
                type="invalid_type",  # Should fail
                description="Test",
                parameters=[]
            )
    
    def test_mcp_tool(self):
        """Test MCP tool definition."""
        tool = ToolDefinition(
            name="receipt_ocr",
            type="mcp",
            description="Extract text from receipt images",
            parameters=[
                ToolParameter(name="image_url", type="string", description="Image URL", required=True)
            ],
            source="mcp:azure_cv",
            metadata={"provider": "azure"}
        )
        
        assert tool.type == "mcp"
        assert tool.source == "mcp:azure_cv"
        assert tool.metadata["provider"] == "azure"
    
    def test_code_exec_tool(self):
        """Test code execution tool definition."""
        tool = ToolDefinition(
            name="execute_code",
            type="code_exec",
            description="Execute Python code",
            parameters=[
                ToolParameter(name="code", type="string", description="Python code", required=True)
            ],
            defer_loading=False  # Code exec should not be deferred
        )
        
        assert tool.type == "code_exec"
        assert tool.defer_loading is False
    
    def test_to_llm_format_basic(self):
        """Test conversion to LLM function calling format."""
        tool = ToolDefinition(
            name="send_email",
            type="function",
            description="Send an email message",
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email", required=True),
                ToolParameter(name="subject", type="string", description="Email subject", required=True),
                ToolParameter(name="body", type="string", description="Email body", required=False)
            ]
        )
        
        llm_format = tool.to_llm_format()
        
        assert llm_format["name"] == "send_email"
        assert llm_format["description"] == "Send an email message"
        assert "parameters" in llm_format
        assert llm_format["parameters"]["type"] == "object"
        assert "to" in llm_format["parameters"]["properties"]
        assert "subject" in llm_format["parameters"]["properties"]
        assert "body" in llm_format["parameters"]["properties"]
        assert llm_format["parameters"]["required"] == ["to", "subject"]
    
    def test_to_llm_format_with_enum(self):
        """Test LLM format includes enum values."""
        tool = ToolDefinition(
            name="set_priority",
            type="function",
            description="Set priority level",
            parameters=[
                ToolParameter(
                    name="level",
                    type="string",
                    description="Priority",
                    enum=["low", "high"],
                    required=True
                )
            ]
        )
        
        llm_format = tool.to_llm_format()
        
        assert "enum" in llm_format["parameters"]["properties"]["level"]
        assert llm_format["parameters"]["properties"]["level"]["enum"] == ["low", "high"]
    
    def test_to_llm_format_with_default(self):
        """Test LLM format includes default values."""
        tool = ToolDefinition(
            name="wait",
            type="function",
            description="Wait for duration",
            parameters=[
                ToolParameter(
                    name="seconds",
                    type="integer",
                    description="Wait time",
                    default=10
                )
            ]
        )
        
        llm_format = tool.to_llm_format()
        
        assert llm_format["parameters"]["properties"]["seconds"]["default"] == 10


class TestToolCatalog:
    """Test ToolCatalog operations."""
    
    def test_empty_catalog(self):
        """Test creating an empty catalog."""
        catalog = ToolCatalog()
        
        assert len(catalog.tools) == 0
        assert isinstance(catalog.discovered_at, datetime)
        assert catalog.version == "1.0"
    
    def test_add_tool(self):
        """Test adding a tool to catalog."""
        catalog = ToolCatalog()
        tool = ToolDefinition(
            name="test_tool",
            type="function",
            description="Test",
            parameters=[]
        )
        
        catalog.add_tool(tool)
        
        assert len(catalog.tools) == 1
        assert "test_tool" in catalog.tools
    
    def test_get_tool(self):
        """Test retrieving a tool by name."""
        catalog = ToolCatalog()
        tool = ToolDefinition(
            name="my_tool",
            type="function",
            description="Test",
            parameters=[]
        )
        catalog.add_tool(tool)
        
        retrieved = catalog.get_tool("my_tool")
        
        assert retrieved is not None
        assert retrieved.name == "my_tool"
        
        # Test non-existent tool
        assert catalog.get_tool("nonexistent") is None
    
    def test_get_by_type(self):
        """Test filtering tools by type."""
        catalog = ToolCatalog()
        
        # Add different types
        catalog.add_tool(ToolDefinition(name="func1", type="function", description="Test", parameters=[]))
        catalog.add_tool(ToolDefinition(name="func2", type="function", description="Test", parameters=[]))
        catalog.add_tool(ToolDefinition(name="mcp1", type="mcp", description="Test", parameters=[]))
        catalog.add_tool(ToolDefinition(name="code1", type="code_exec", description="Test", parameters=[]))
        
        functions = catalog.get_by_type("function")
        mcp_tools = catalog.get_by_type("mcp")
        code_exec = catalog.get_by_type("code_exec")
        
        assert len(functions) == 2
        assert len(mcp_tools) == 1
        assert len(code_exec) == 1
    
    def test_to_llm_format(self):
        """Test converting entire catalog to LLM format."""
        catalog = ToolCatalog()
        
        catalog.add_tool(ToolDefinition(
            name="tool1",
            type="function",
            description="First tool",
            parameters=[ToolParameter(name="arg1", type="string", description="Arg", required=True)]
        ))
        catalog.add_tool(ToolDefinition(
            name="tool2",
            type="function",
            description="Second tool",
            parameters=[]
        ))
        
        llm_format = catalog.to_llm_format()
        
        assert len(llm_format) == 2
        assert all("name" in tool for tool in llm_format)
        assert all("description" in tool for tool in llm_format)
        assert all("parameters" in tool for tool in llm_format)
    
    def test_to_llm_format_with_defer_loading(self):
        """Test defer_loading filter in LLM format conversion."""
        catalog = ToolCatalog()
        
        # Add tools with different defer_loading settings
        catalog.add_tool(ToolDefinition(
            name="always_loaded",
            type="function",
            description="Always loaded",
            parameters=[],
            defer_loading=False
        ))
        catalog.add_tool(ToolDefinition(
            name="deferred",
            type="function",
            description="Deferred",
            parameters=[],
            defer_loading=True
        ))
        
        # Without defer_loading filter - should get all
        all_tools = catalog.to_llm_format(defer_loading=False)
        assert len(all_tools) == 2
        
        # With defer_loading filter - should only get non-deferred
        immediate_tools = catalog.to_llm_format(defer_loading=True)
        assert len(immediate_tools) == 1
        assert immediate_tools[0]["name"] == "always_loaded"
    
    def test_multiple_operations(self):
        """Test multiple catalog operations in sequence."""
        catalog = ToolCatalog(source="test_suite", version="test_v1")
        
        # Add multiple tools
        for i in range(5):
            catalog.add_tool(ToolDefinition(
                name=f"tool_{i}",
                type="function" if i % 2 == 0 else "mcp",
                description=f"Tool number {i}",
                parameters=[]
            ))
        
        assert len(catalog.tools) == 5
        assert len(catalog.get_by_type("function")) == 3
        assert len(catalog.get_by_type("mcp")) == 2
        assert catalog.source == "test_suite"
        assert catalog.version == "test_v1"


class TestToolCatalogIntegration:
    """Integration tests for tool catalog with realistic scenarios."""
    
    def test_receipt_processing_catalog(self):
        """Test catalog for receipt processing use case."""
        catalog = ToolCatalog(source="receipt_processor")
        
        # Add OCR tool
        catalog.add_tool(ToolDefinition(
            name="receipt_ocr",
            type="mcp",
            description="Extract text from receipt images using Azure Computer Vision",
            parameters=[
                ToolParameter(name="image_url", type="string", description="URL or path to receipt image", required=True)
            ],
            source="mcp:azure_cv"
        ))
        
        # Add parser tool
        catalog.add_tool(ToolDefinition(
            name="parse_line_items",
            type="function",
            description="Parse receipt text into structured line items",
            parameters=[
                ToolParameter(name="text", type="string", description="Receipt text", required=True)
            ]
        ))
        
        # Add categorizer
        catalog.add_tool(ToolDefinition(
            name="categorize_expenses",
            type="function",
            description="Categorize expenses by type",
            parameters=[
                ToolParameter(name="items", type="array", description="Line items", items={"type": "object"}, required=True)
            ]
        ))
        
        assert len(catalog.tools) == 3
        assert catalog.get_tool("receipt_ocr") is not None
        
        llm_tools = catalog.to_llm_format()
        assert len(llm_tools) == 3
        
        # Verify structure for LLM
        ocr_tool = next(t for t in llm_tools if t["name"] == "receipt_ocr")
        assert "image_url" in ocr_tool["parameters"]["properties"]


class TestToolExamples:
    """Test tool examples functionality (Phase 5)."""
    
    def test_tool_example_creation(self):
        """Test creating a tool example."""
        from orchestrator.models import ToolExample
        
        example = ToolExample(
            scenario="Critical production bug requiring urgent attention",
            input={
                "title": "Database connection timeout in production",
                "description": "Users cannot login, error logs show connection timeouts",
                "priority": "critical",
                "assignee": "USR-12345"
            },
            output={"ticket_id": "TICK-001", "status": "created", "sla_hours": 2},
            notes="Use critical priority for production outages, include escalation path"
        )
        
        assert example.scenario == "Critical production bug requiring urgent attention"
        assert example.input["priority"] == "critical"
        assert example.output["ticket_id"] == "TICK-001"
        assert "production outages" in example.notes
    
    def test_tool_definition_with_examples(self):
        """Test ToolDefinition with examples."""
        from orchestrator.models import ToolExample
        
        tool = ToolDefinition(
            name="create_ticket",
            type="function",
            description="Create a support ticket",
            parameters=[
                ToolParameter(name="title", type="string", description="Ticket title", required=True),
                ToolParameter(name="priority", type="string", description="Priority level", 
                            enum=["low", "medium", "high", "critical"], required=True)
            ],
            examples=[
                ToolExample(
                    scenario="Critical production bug",
                    input={"title": "DB timeout", "priority": "critical"},
                    output={"ticket_id": "TICK-001", "sla_hours": 2}
                ),
                ToolExample(
                    scenario="Feature request",
                    input={"title": "Add dark mode", "priority": "low"},
                    output={"ticket_id": "TICK-002", "sla_hours": 72}
                )
            ]
        )
        
        assert len(tool.examples) == 2
        assert tool.examples[0].scenario == "Critical production bug"
        assert tool.examples[1].input["priority"] == "low"
    
    def test_llm_format_with_examples(self):
        """Test to_llm_format includes examples in description."""
        from orchestrator.models import ToolExample
        
        tool = ToolDefinition(
            name="create_ticket",
            type="function",
            description="Create a support ticket",
            parameters=[
                ToolParameter(name="title", type="string", description="Ticket title", required=True)
            ],
            examples=[
                ToolExample(
                    scenario="Critical bug",
                    input={"title": "DB timeout"},
                    output={"ticket_id": "TICK-001"}
                )
            ]
        )
        
        llm_format = tool.to_llm_format(include_examples=True)
        
        # Examples should be appended to description
        assert "Examples:" in llm_format["description"]
        assert "Critical bug" in llm_format["description"]
        assert "DB timeout" in llm_format["description"]
        assert "TICK-001" in llm_format["description"]
    
    def test_llm_format_without_examples(self):
        """Test to_llm_format excludes examples when requested."""
        from orchestrator.models import ToolExample
        
        tool = ToolDefinition(
            name="create_ticket",
            type="function",
            description="Create a support ticket",
            parameters=[
                ToolParameter(name="title", type="string", description="Ticket title", required=True)
            ],
            examples=[
                ToolExample(
                    scenario="Critical bug",
                    input={"title": "DB timeout"},
                    output={"ticket_id": "TICK-001"}
                )
            ]
        )
        
        llm_format = tool.to_llm_format(include_examples=False)
        
        # Examples should NOT be in description
        assert "Examples:" not in llm_format["description"]
        assert "Critical bug" not in llm_format["description"]
    
    def test_catalog_with_examples(self):
        """Test ToolCatalog propagates include_examples parameter."""
        from orchestrator.models import ToolExample
        
        catalog = ToolCatalog(source="test")
        
        catalog.add_tool(ToolDefinition(
            name="tool1",
            type="function",
            description="First tool",
            parameters=[],
            examples=[
                ToolExample(
                    scenario="Example scenario",
                    input={},
                    output={"result": "success"}
                )
            ]
        ))
        
        # With examples
        llm_tools_with = catalog.to_llm_format(include_examples=True)
        assert "Examples:" in llm_tools_with[0]["description"]
        
        # Without examples
        llm_tools_without = catalog.to_llm_format(include_examples=False)
        assert "Examples:" not in llm_tools_without[0]["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
