"""Tests for ShardedCatalog domain-based tool organization"""

import pytest
from orchestrator.shared.models import ToolDefinition, ToolParameter, ToolCatalog
from orchestrator.tools.sharded_catalog import ShardedCatalog, DOMAIN_KEYWORDS


@pytest.fixture
def sample_tools():
    """Create sample tools for different domains"""
    return [
        # GitHub tools
        ToolDefinition(
            name="create_github_issue",
            type="function",
            description="Create a new issue in a GitHub repository",
            parameters=[
                ToolParameter(name="repo", type="string", description="Repository name", required=True),
                ToolParameter(name="title", type="string", description="Issue title", required=True)
            ],
            domain="github"
        ),
        ToolDefinition(
            name="create_pr",
            type="function",
            description="Create a pull request in GitHub",
            parameters=[
                ToolParameter(name="repo", type="string", description="Repository name", required=True)
            ],
            domain="github"
        ),
        # Slack tools
        ToolDefinition(
            name="send_slack_message",
            type="function",
            description="Send a message to a Slack channel",
            parameters=[
                ToolParameter(name="channel", type="string", description="Channel name", required=True),
                ToolParameter(name="text", type="string", description="Message text", required=True)
            ],
            domain="slack"
        ),
        ToolDefinition(
            name="create_channel",
            type="function",
            description="Create a new Slack channel",
            parameters=[
                ToolParameter(name="name", type="string", description="Channel name", required=True)
            ],
            domain="slack"
        ),
        # AWS tools
        ToolDefinition(
            name="create_s3_bucket",
            type="function",
            description="Create a new S3 bucket in AWS",
            parameters=[
                ToolParameter(name="bucket_name", type="string", description="Bucket name", required=True)
            ],
            domain="aws"
        ),
        ToolDefinition(
            name="launch_ec2",
            type="function",
            description="Launch an EC2 instance",
            parameters=[
                ToolParameter(name="instance_type", type="string", description="Instance type", required=True)
            ],
            domain="aws"
        ),
        # Database tools
        ToolDefinition(
            name="execute_query",
            type="function",
            description="Execute a SQL query on the database",
            parameters=[
                ToolParameter(name="query", type="string", description="SQL query", required=True)
            ],
            domain="database"
        ),
        # General tools (no domain specified)
        ToolDefinition(
            name="send_email",
            type="function",
            description="Send an email to recipients",
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email", required=True)
            ]
        ),
        ToolDefinition(
            name="calculate_sum",
            type="function",
            description="Calculate the sum of numbers",
            parameters=[
                ToolParameter(name="numbers", type="array", description="Array of numbers", required=True)
            ]
        ),
    ]


def test_initialization():
    """Test ShardedCatalog initialization"""
    catalog = ShardedCatalog()
    
    # Should have all domain shards
    assert len(catalog.shards) == len(DOMAIN_KEYWORDS)
    assert "github" in catalog.shards
    assert "slack" in catalog.shards
    assert "aws" in catalog.shards
    assert "database" in catalog.shards
    assert "general" in catalog.shards
    
    # All shards should be empty
    for shard in catalog.shards.values():
        assert len(shard.tools) == 0
    
    # Global catalog should be empty
    assert len(catalog.global_catalog.tools) == 0


def test_add_tool_with_explicit_domain(sample_tools):
    """Test adding tools with explicit domain"""
    catalog = ShardedCatalog()
    
    # Add GitHub tool
    github_tool = sample_tools[0]
    domain = catalog.add_tool(github_tool)
    
    assert domain == "github"
    assert github_tool.name in catalog.shards["github"].tools
    assert github_tool.name in catalog.global_catalog.tools


def test_add_tool_auto_detect_domain(sample_tools):
    """Test automatic domain detection for tools without domain"""
    catalog = ShardedCatalog()
    
    # Tool without domain but with descriptive name
    tool = ToolDefinition(
        name="send_slack_notification",
        type="function",
        description="Send notification via Slack",
        parameters=[]
    )
    
    domain = catalog.add_tool(tool)
    
    # Should detect 'slack' from tool name
    assert domain == "slack"
    assert tool.name in catalog.shards["slack"].tools


def test_add_multiple_tools(sample_tools):
    """Test adding multiple tools to different shards"""
    catalog = ShardedCatalog()
    
    # Add all sample tools
    for tool in sample_tools:
        catalog.add_tool(tool)
    
    # Check stats
    stats = catalog.get_stats()
    assert stats["github"] == 2
    assert stats["slack"] == 2
    assert stats["aws"] == 2
    assert stats["database"] == 1
    assert stats["general"] == 2  # Tools without explicit domain
    assert stats["total"] == 9


def test_get_shard():
    """Test getting specific domain shard"""
    catalog = ShardedCatalog()
    
    # Add tool to github shard
    tool = ToolDefinition(
        name="test_tool",
        type="function",
        description="Test",
        parameters=[],
        domain="github"
    )
    catalog.add_tool(tool)
    
    # Get github shard
    github_shard = catalog.get_shard("github")
    assert github_shard is not None
    assert "test_tool" in github_shard.tools
    
    # Get non-existent shard
    invalid_shard = catalog.get_shard("nonexistent")
    assert invalid_shard is None


def test_detect_domain_github():
    """Test domain detection for GitHub queries"""
    catalog = ShardedCatalog()
    
    test_cases = [
        ("create a GitHub issue", "github"),
        ("list all repositories", "github"),
        ("create pull request", "github"),
        ("merge this PR", "github"),
        ("commit changes to branch", "github"),
    ]
    
    for query, expected_domain in test_cases:
        detected = catalog.detect_domain(query)
        assert detected == expected_domain, f"Failed for query: '{query}'"


def test_detect_domain_slack():
    """Test domain detection for Slack queries"""
    catalog = ShardedCatalog()
    
    test_cases = [
        ("send message to slack channel", "slack"),
        ("create new channel", "slack"),
        ("post in conversation", "slack"),
        ("add emoji reaction", "slack"),
    ]
    
    for query, expected_domain in test_cases:
        detected = catalog.detect_domain(query)
        assert detected == expected_domain, f"Failed for query: '{query}'"


def test_detect_domain_aws():
    """Test domain detection for AWS queries"""
    catalog = ShardedCatalog()
    
    test_cases = [
        ("create s3 bucket", "aws"),
        ("launch ec2 instance", "aws"),
        ("invoke lambda function", "aws"),
        ("deploy to cloud", "aws"),
    ]
    
    for query, expected_domain in test_cases:
        detected = catalog.detect_domain(query)
        assert detected == expected_domain, f"Failed for query: '{query}'"


def test_detect_domain_database():
    """Test domain detection for database queries"""
    catalog = ShardedCatalog()
    
    test_cases = [
        ("execute SQL query", "database"),
        ("create table in database", "database"),
        ("insert record", "database"),
        ("update records with join", "database"),
    ]
    
    for query, expected_domain in test_cases:
        detected = catalog.detect_domain(query)
        assert detected == expected_domain, f"Failed for query: '{query}'"


def test_detect_domain_no_match():
    """Test domain detection returns None for generic queries"""
    catalog = ShardedCatalog()
    
    test_cases = [
        "send email",
        "calculate sum",
        "convert units",
        "format text",
    ]
    
    for query in test_cases:
        detected = catalog.detect_domain(query)
        assert detected is None, f"Should not detect domain for: '{query}'"


def test_search_by_domain(sample_tools):
    """Test searching within specific domain"""
    catalog = ShardedCatalog()
    
    # Add tools
    for tool in sample_tools:
        catalog.add_tool(tool)
    
    # Search in GitHub domain
    shard, domain_used = catalog.search_by_domain("create issue", "github")
    
    assert domain_used == "github"
    assert len(shard.tools) == 2  # 2 GitHub tools
    assert "create_github_issue" in shard.tools
    assert "create_pr" in shard.tools


def test_search_by_domain_fallback():
    """Test fallback to global when domain is empty"""
    catalog = ShardedCatalog()
    
    # Add only general tools
    tool = ToolDefinition(
        name="test_tool",
        type="function",
        description="Test",
        parameters=[],
        domain="general"
    )
    catalog.add_tool(tool)
    
    # Search in empty GitHub domain
    shard, domain_used = catalog.search_by_domain("test query", "github")
    
    # Should fall back to global
    assert domain_used == "global"
    assert len(shard.tools) == 1


def test_search_with_detection(sample_tools):
    """Test search with automatic domain detection"""
    catalog = ShardedCatalog()
    
    # Add tools
    for tool in sample_tools:
        catalog.add_tool(tool)
    
    # Query with clear GitHub keywords
    shard, domain_used = catalog.search_with_detection("create a GitHub pull request")
    
    assert domain_used == "github"
    assert len(shard.tools) == 2


def test_search_with_detection_no_domain(sample_tools):
    """Test search falls back to global when no domain detected"""
    catalog = ShardedCatalog()
    
    # Add tools
    for tool in sample_tools:
        catalog.add_tool(tool)
    
    # Generic query
    shard, domain_used = catalog.search_with_detection("do something")
    
    assert domain_used == "global"
    assert len(shard.tools) == 9  # All tools


def test_get_stats(sample_tools):
    """Test getting catalog statistics"""
    catalog = ShardedCatalog()
    
    # Add tools
    for tool in sample_tools:
        catalog.add_tool(tool)
    
    stats = catalog.get_stats()
    
    assert "github" in stats
    assert "slack" in stats
    assert "aws" in stats
    assert "database" in stats
    assert "general" in stats
    assert "total" in stats
    assert stats["total"] == 9


def test_list_domains():
    """Test listing available domains"""
    catalog = ShardedCatalog()
    
    domains = catalog.list_domains()
    
    assert len(domains) == len(DOMAIN_KEYWORDS)
    assert "github" in domains
    assert "slack" in domains
    assert "aws" in domains
    assert "database" in domains
    assert "general" in domains


def test_repr():
    """Test string representation"""
    catalog = ShardedCatalog()
    
    repr_str = repr(catalog)
    
    assert "ShardedCatalog" in repr_str
    assert "domains=" in repr_str
    assert "tools=" in repr_str


def test_domain_detection_case_insensitive():
    """Test domain detection is case-insensitive"""
    catalog = ShardedCatalog()
    
    test_cases = [
        ("CREATE GITHUB ISSUE", "github"),
        ("Send SLACK Message", "slack"),
        ("create S3 Bucket", "aws"),
    ]
    
    for query, expected_domain in test_cases:
        detected = catalog.detect_domain(query)
        assert detected == expected_domain


def test_multiple_domain_keywords():
    """Test query with keywords from multiple domains"""
    catalog = ShardedCatalog()
    
    # Query with both GitHub and Slack keywords
    # Should return domain with most matches
    query = "create a github issue and send slack message"
    detected = catalog.detect_domain(query)
    
    # Should detect one domain (implementation picks highest score)
    assert detected in ["github", "slack"]


def test_empty_catalog_search():
    """Test searching in empty catalog"""
    catalog = ShardedCatalog()
    
    shard, domain_used = catalog.search_with_detection("test query")
    
    assert domain_used == "global"
    assert len(shard.tools) == 0


def test_unknown_domain_defaults_to_general():
    """Test unknown domain defaults to general"""
    catalog = ShardedCatalog()
    
    tool = ToolDefinition(
        name="test_tool",
        type="function",
        description="Test",
        parameters=[],
        domain="unknown_domain"
    )
    
    domain = catalog.add_tool(tool)
    
    assert domain == "general"
    assert "test_tool" in catalog.shards["general"].tools
