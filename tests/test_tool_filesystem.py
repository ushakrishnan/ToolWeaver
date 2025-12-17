"""
Tests for ToolFileSystem: Progressive tool discovery interface
"""

import pytest
from pathlib import Path
import tempfile

from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.code_generator import StubGenerator
from orchestrator.tool_filesystem import ToolFileSystem, ToolInfo


@pytest.fixture
def tool_catalog():
    """Create a sample tool catalog"""
    catalog = ToolCatalog(source="test", version="1.0")
    
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
            ToolParameter(name="title", type="string", description="Document title", required=True)
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
            ToolParameter(name="priority", type="integer", description="Priority level", required=False)
        ]
    ))
    
    return catalog


@pytest.fixture
def stub_dir(tool_catalog):
    """Generate stubs and return directory"""
    with tempfile.TemporaryDirectory() as tmp:
        stub_path = Path(tmp) / "stubs"
        generator = StubGenerator(tool_catalog, stub_path)
        generator.generate_all()
        yield stub_path


@pytest.fixture
def filesystem(stub_dir):
    """Create ToolFileSystem instance"""
    return ToolFileSystem(stub_dir)


class TestToolFileSystem:
    """Test suite for ToolFileSystem"""
    
    def test_initialization(self, stub_dir):
        """Test filesystem initialization"""
        fs = ToolFileSystem(stub_dir)
        
        assert fs.stub_dir == stub_dir
        assert fs.tools_dir == stub_dir / "tools"
        assert fs.tools_dir.exists()
    
    def test_initialization_invalid_dir(self):
        """Test initialization with invalid directory"""
        with pytest.raises(ValueError, match="Tools directory not found"):
            ToolFileSystem(Path("/nonexistent"))
    
    def test_list_servers(self, filesystem):
        """Test listing all servers"""
        servers = filesystem.list_servers()
        
        assert len(servers) == 2
        assert "google_drive" in servers
        assert "jira" in servers
        assert sorted(servers) == servers  # Should be sorted
    
    def test_list_tools_all(self, filesystem):
        """Test listing all tools"""
        tools = filesystem.list_tools()
        
        assert len(tools) == 3
        assert "get_document" in tools
        assert "create_document" in tools
        assert "create_ticket" in tools
    
    def test_list_tools_by_server(self, filesystem):
        """Test listing tools for specific server"""
        gd_tools = filesystem.list_tools("google_drive")
        assert len(gd_tools) == 2
        assert "get_document" in gd_tools
        assert "create_document" in gd_tools
        
        jira_tools = filesystem.list_tools("jira")
        assert len(jira_tools) == 1
        assert "create_ticket" in jira_tools
    
    def test_list_tools_invalid_server(self, filesystem):
        """Test listing tools for non-existent server"""
        tools = filesystem.list_tools("nonexistent")
        assert tools == []
    
    def test_get_tool_info(self, filesystem):
        """Test getting tool information"""
        info = filesystem.get_tool_info("get_document")
        
        assert info is not None
        assert info.name == "get_document"
        assert info.server == "google_drive"
        assert "Google Doc" in info.description
        assert info.input_class == "GetDocumentInput"
        assert info.output_class == "GetDocumentOutput"
        assert info.file_path.exists()
    
    def test_get_tool_info_caching(self, filesystem):
        """Test that tool info is cached"""
        info1 = filesystem.get_tool_info("get_document")
        info2 = filesystem.get_tool_info("get_document")
        
        assert info1 is info2  # Same object instance
    
    def test_get_tool_info_invalid(self, filesystem):
        """Test getting info for non-existent tool"""
        info = filesystem.get_tool_info("nonexistent_tool")
        assert info is None
    
    def test_get_tool_info_parameters(self, filesystem):
        """Test parameter extraction from tool info"""
        info = filesystem.get_tool_info("get_document")
        
        assert info is not None
        assert len(info.parameters) >= 1  # At least doc_id
        
        # Check if doc_id parameter is present
        param_names = [p["name"] for p in info.parameters]
        assert "doc_id" in param_names
        
        # Find doc_id param and verify details
        doc_id_param = next(p for p in info.parameters if p["name"] == "doc_id")
        assert doc_id_param["required"] is True
        assert "Document ID" in doc_id_param["description"]
    
    def test_get_import_statement(self, filesystem):
        """Test import statement generation"""
        stmt = filesystem.get_import_statement("get_document")
        
        assert stmt is not None
        assert "from tools.google_drive import" in stmt
        assert "get_document" in stmt
        assert "GetDocumentInput" in stmt
    
    def test_get_import_statement_invalid(self, filesystem):
        """Test import statement for non-existent tool"""
        stmt = filesystem.get_import_statement("nonexistent")
        assert stmt is None
    
    def test_search_tools_by_name(self, filesystem):
        """Test searching tools by name"""
        results = filesystem.search_tools("document")
        
        assert len(results) == 2
        assert "get_document" in results
        assert "create_document" in results
    
    def test_search_tools_by_description(self, filesystem):
        """Test searching tools by description"""
        results = filesystem.search_tools("jira")
        
        assert len(results) >= 1
        assert "create_ticket" in results
    
    def test_search_tools_case_insensitive(self, filesystem):
        """Test that search is case-insensitive"""
        results1 = filesystem.search_tools("DOCUMENT")
        results2 = filesystem.search_tools("document")
        
        assert set(results1) == set(results2)
    
    def test_search_tools_no_matches(self, filesystem):
        """Test search with no matches"""
        results = filesystem.search_tools("xyz_nonexistent")
        assert results == []
    
    def test_get_directory_tree(self, filesystem):
        """Test directory tree generation"""
        tree = filesystem.get_directory_tree()
        
        assert "tools/" in tree
        assert "google_drive/" in tree
        assert "jira/" in tree
        assert "get_document.py" in tree
        assert "create_ticket.py" in tree
    
    def test_find_tool_file(self, filesystem):
        """Test internal tool file finder"""
        path = filesystem._find_tool_file("get_document")
        
        assert path is not None
        assert path.exists()
        assert path.name == "get_document.py"
        assert "google_drive" in str(path)
    
    def test_find_tool_file_invalid(self, filesystem):
        """Test finding non-existent tool file"""
        path = filesystem._find_tool_file("nonexistent")
        assert path is None
    
    def test_extract_parameters(self, filesystem):
        """Test parameter extraction from docstrings"""
        docstring = '''
        Test function
        
        Args:
            param1 (string, required): First parameter
            param2 (integer, optional): Second parameter
        
        Returns:
            Result
        '''
        
        params = filesystem._extract_parameters(docstring)
        
        assert len(params) == 2
        
        assert params[0]["name"] == "param1"
        assert params[0]["type"] == "string"
        assert params[0]["required"] is True
        
        assert params[1]["name"] == "param2"
        assert params[1]["type"] == "integer"
        assert params[1]["required"] is False
    
    def test_extract_parameters_no_args(self, filesystem):
        """Test parameter extraction with no Args section"""
        docstring = "Simple function with no args"
        params = filesystem._extract_parameters(docstring)
        assert params == []


class TestToolFileSystemIntegration:
    """Integration tests for ToolFileSystem"""
    
    def test_full_workflow(self, filesystem):
        """Test complete workflow: list → info → import"""
        # 1. List servers
        servers = filesystem.list_servers()
        assert len(servers) > 0
        
        # 2. List tools in first server
        tools = filesystem.list_tools(servers[0])
        assert len(tools) > 0
        
        # 3. Get info for first tool
        info = filesystem.get_tool_info(tools[0])
        assert info is not None
        assert info.name == tools[0]
        
        # 4. Get import statement
        stmt = filesystem.get_import_statement(tools[0])
        assert stmt is not None
        assert info.name in stmt
    
    def test_progressive_discovery_pattern(self, filesystem):
        """Test the progressive discovery pattern used by AI models"""
        # Phase 1: High-level exploration (minimal tokens)
        servers = filesystem.list_servers()
        assert isinstance(servers, list)
        
        # Phase 2: Server-level exploration
        for server in servers:
            tools = filesystem.list_tools(server)
            assert isinstance(tools, list)
        
        # Phase 3: On-demand tool details (only when needed)
        all_tools = filesystem.list_tools()
        target_tool = all_tools[0]
        
        info = filesystem.get_tool_info(target_tool)
        assert info is not None
        
        # Phase 4: Import generation
        stmt = filesystem.get_import_statement(target_tool)
        assert stmt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
