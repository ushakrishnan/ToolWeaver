"""
Tests for Code Stub Generator

Tests stub generation from tool definitions.
"""

import pytest
from pathlib import Path
import shutil

from orchestrator.execution.code_generator import StubGenerator, GeneratedStub
from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter


@pytest.fixture
def test_catalog():
    """Create test tool catalog"""
    catalog = ToolCatalog(source="test", version="1.0")
    
    # Add simple tool
    catalog.add_tool(ToolDefinition(
        name="get_document",
        type="function",
        description="Get a document by ID",
        domain="google_drive",
        parameters=[
            ToolParameter(
                name="doc_id",
                type="string",
                description="Document ID",
                required=True
            )
        ]
    ))
    
    # Add tool with multiple parameters
    catalog.add_tool(ToolDefinition(
        name="create_ticket",
        type="function",
        description="Create a Jira ticket",
        domain="jira",
        parameters=[
            ToolParameter(name="title", type="string", description="Ticket title", required=True),
            ToolParameter(name="description", type="string", description="Ticket description", required=False),
            ToolParameter(name="priority", type="integer", description="Priority level", required=False)
        ]
    ))
    
    # Add tool with no parameters
    catalog.add_tool(ToolDefinition(
        name="list_users",
        type="function",
        description="List all users",
        domain="default",
        parameters=[]
    ))
    
    # Add github tool
    catalog.add_tool(ToolDefinition(
        name="list_repositories",
        type="function",
        description="List all repositories",
        domain="github",
        parameters=[]
    ))
    
    return catalog


@pytest.fixture
def stub_dir(tmp_path):
    """Create temporary stub directory"""
    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir()
    
    yield stub_dir
    
    # Cleanup
    if stub_dir.exists():
        shutil.rmtree(stub_dir)


@pytest.fixture
def generator(test_catalog, stub_dir):
    """Create stub generator"""
    return StubGenerator(test_catalog, stub_dir)


class TestStubGenerator:
    """Test stub generation"""
    
    def test_initialization(self, generator, test_catalog, stub_dir):
        """Verify generator initializes correctly"""
        assert generator.catalog == test_catalog
        assert generator.output_dir == stub_dir
        assert len(generator.generated_stubs) == 0
        
    def test_group_by_server(self, generator):
        """Verify tools are grouped by server"""
        grouped = generator._group_by_server()
        
        assert "google_drive" in grouped
        assert "jira" in grouped
        assert "default" in grouped
        
        assert len(grouped["google_drive"]) == 1
        assert len(grouped["jira"]) == 1
        assert len(grouped["default"]) == 1
        
    def test_generate_input_model_simple(self, generator, test_catalog):
        """Verify input model generation"""
        tool = test_catalog.get_tool("get_document")
        
        input_model = generator._generate_input_model(tool)
        
        assert "class GetDocumentInput(BaseModel)" in input_model
        assert "doc_id: str" in input_model
        assert "Document ID" in input_model
        
    def test_generate_input_model_multiple_params(self, generator, test_catalog):
        """Verify input model with multiple parameters"""
        tool = test_catalog.get_tool("create_ticket")
        
        input_model = generator._generate_input_model(tool)
        
        assert "class CreateTicketInput(BaseModel)" in input_model
        assert "title: str" in input_model
        assert "description: Optional[str]" in input_model
        assert "priority: Optional[int]" in input_model
        
    def test_generate_input_model_no_params(self, generator, test_catalog):
        """Verify input model with no parameters"""
        tool = test_catalog.get_tool("list_repositories")
        
        input_model = generator._generate_input_model(tool)
        
        assert "class ListRepositoriesInput(BaseModel)" in input_model
        assert "pass" in input_model
        
    def test_generate_output_model(self, generator, test_catalog):
        """Verify output model generation"""
        tool = test_catalog.get_tool("get_document")
        
        output_model = generator._generate_output_model(tool)
        
        assert "class GetDocumentOutput(BaseModel)" in output_model
        assert "result: Any" in output_model
        assert "success: bool" in output_model
        assert "error: Optional[str]" in output_model
        
    def test_generate_function(self, generator, test_catalog):
        """Verify function generation"""
        tool = test_catalog.get_tool("get_document")
        
        function = generator._generate_function(tool)
        
        assert "async def get_document" in function
        assert "GetDocumentInput" in function
        assert "GetDocumentOutput" in function
        assert "call_tool" in function
        assert "google_drive" in function
        
    def test_generate_docstring(self, generator, test_catalog):
        """Verify docstring generation"""
        tool = test_catalog.get_tool("get_document")
        
        docstring = generator._generate_docstring(tool)
        
        assert "Get a document by ID" in docstring
        assert "Args:" in docstring
        assert "doc_id" in docstring
        assert "Returns:" in docstring
        
    def test_python_type_conversion(self, generator):
        """Verify type conversion"""
        assert generator._python_type("string") == "str"
        assert generator._python_type("integer") == "int"
        assert generator._python_type("number") == "float"
        assert generator._python_type("boolean") == "bool"
        assert generator._python_type("array") == "List[Any]"
        assert generator._python_type("object") == "Dict[str, Any]"
        assert generator._python_type("unknown") == "Any"
        
    def test_camel_case_conversion(self, generator):
        """Verify snake_case to CamelCase"""
        assert generator._camel_case("get_document") == "GetDocument"
        assert generator._camel_case("create_ticket") == "CreateTicket"
        assert generator._camel_case("list_users") == "ListUsers"
        assert generator._camel_case("single") == "Single"
        
    def test_generate_stub_complete(self, generator, test_catalog):
        """Verify complete stub generation"""
        tool = test_catalog.get_tool("get_document")
        
        stub = generator._generate_stub(tool)
        
        # Check all components present
        assert '"""' in stub  # Module docstring
        assert "from typing import" in stub
        assert "from pydantic import" in stub
        assert "class GetDocumentInput" in stub
        assert "class GetDocumentOutput" in stub
        assert "async def get_document" in stub
        
        # Verify it's valid Python
        compile(stub, "<string>", "exec")
        
    def test_generate_all(self, generator, stub_dir):
        """Verify complete stub generation"""
        stubs = generator.generate_all()
        
        # Check correct number of stubs
        assert len(stubs) == 4
        
        # Check files created
        assert (stub_dir / "tools" / "google_drive" / "get_document.py").exists()
        assert (stub_dir / "tools" / "jira" / "create_ticket.py").exists()
        assert (stub_dir / "tools" / "default" / "list_users.py").exists()
        
        # Check __init__.py files created
        assert (stub_dir / "tools" / "google_drive" / "__init__.py").exists()
        assert (stub_dir / "tools" / "jira" / "__init__.py").exists()
        assert (stub_dir / "tools" / "__init__.py").exists()
        
    def test_generated_stub_info(self, generator):
        """Verify generated stub tracking"""
        generator.generate_all()
        
        # Check stub info
        info = generator.get_stub_info("get_document")
        
        assert info is not None
        assert isinstance(info, GeneratedStub)
        assert info.tool_name == "get_document"
        assert info.file_path.name == "get_document.py"
        assert "async def get_document" in info.code
        
    def test_list_generated_stubs(self, generator):
        """Verify listing of generated stubs"""
        generator.generate_all()
        
        stubs = generator.list_generated_stubs()
        
        assert len(stubs) == 4
        assert "get_document" in stubs
        assert "create_ticket" in stubs
        assert "list_users" in stubs
        
    def test_extract_imports(self, generator):
        """Verify import extraction"""
        code = """
import os
from typing import Any
from pydantic import BaseModel

class Test:
    pass
"""
        
        imports = generator._extract_imports(code)
        
        assert len(imports) == 3
        assert "import os" in imports
        assert "from typing import Any" in imports
        
    def test_extract_classes(self, generator):
        """Verify class name extraction"""
        code = """
class InputModel(BaseModel):
    pass

class OutputModel(BaseModel):
    pass
"""
        
        classes = generator._extract_classes(code)
        
        assert len(classes) == 2
        assert "InputModel" in classes
        assert "OutputModel" in classes
        
    def test_server_init_generation(self, generator, stub_dir):
        """Verify server __init__.py generation"""
        generator.generate_all()
        
        init_path = stub_dir / "tools" / "google_drive" / "__init__.py"
        assert init_path.exists()
        
        content = init_path.read_text()
        
        assert "from .get_document import get_document" in content
        assert "GetDocumentInput" in content
        assert "GetDocumentOutput" in content
        assert "__all__" in content
        
    def test_generated_stub_is_importable(self, generator, stub_dir):
        """Verify generated stubs can be imported"""
        import sys
        import importlib
        
        generator.generate_all()
        
        # Add stub dir to path
        sys.path.insert(0, str(stub_dir))
        
        try:
            # Import generated module (groups by domain when specified)
            importlib.invalidate_caches()
            from tools.google_drive import get_document, GetDocumentInput, GetDocumentOutput
            
            # Verify types
            assert callable(get_document)
            assert issubclass(GetDocumentInput, object)
            assert issubclass(GetDocumentOutput, object)
            
        finally:
            # Cleanup
            if str(stub_dir) in sys.path:
                sys.path.remove(str(stub_dir))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
