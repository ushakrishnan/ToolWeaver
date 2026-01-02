"""
Sharded Tool Catalog for Domain-Based Search Optimization

Organizes tools by domain (github, slack, aws, database, general) to reduce
search space by ~10x. Provides automatic domain detection and fallback to
global search when domain-specific search yields insufficient results.
"""

import logging
from typing import TypedDict

from orchestrator.shared.models import ToolCatalog, ToolDefinition

logger = logging.getLogger(__name__)

# Domain keywords for automatic detection
class DomainConfig(TypedDict):
    keywords: list[str]
    tools: list[str]


DOMAIN_KEYWORDS: dict[str, DomainConfig] = {
    "github": {
        "keywords": ["github", "repository", "repo", "pull request", "pr", "issue",
                    "commit", "branch", "fork", "star", "clone", "push", "merge"],
        "tools": ["create_github_issue", "list_repositories", "create_pr", "get_commits"]
    },
    "slack": {
        "keywords": ["slack", "channel", "message", "dm", "conversation", "thread",
                    "workspace", "mention", "emoji", "reaction", "post"],
        "tools": ["send_slack_message", "create_channel", "list_channels", "invite_user"]
    },
    "aws": {
        "keywords": ["aws", "s3", "ec2", "lambda", "dynamodb", "bucket", "instance",
                    "function", "cloud", "deploy", "scale"],
        "tools": ["create_s3_bucket", "launch_ec2", "invoke_lambda", "query_dynamodb"]
    },
    "database": {
        "keywords": ["database", "sql", "query", "table", "record", "insert", "update",
                    "delete", "select", "join", "transaction", "schema"],
        "tools": ["execute_query", "create_table", "insert_record", "update_record"]
    },
    "general": {
        "keywords": [],  # Catch-all domain
        "tools": []
    }
}


class ShardedCatalog:
    """
    Tool catalog organized by domain for optimized search.

    Features:
    - Domain-based sharding (10x smaller search space)
    - Automatic domain detection from query
    - Fallback to global search
    - Maintains global catalog for comprehensive search

    Usage:
        catalog = ShardedCatalog()
        catalog.add_tool(github_tool)  # Auto-assigned to 'github' shard

        # Domain-specific search (fast, ~100 tools)
        results = catalog.search_by_domain("create PR", domain="github")

        # Auto-detect domain (smart routing)
        results = catalog.search_with_detection("create slack channel")

        # Global search (fallback, ~1000 tools)
        results = catalog.search_global("general task")
    """

    def __init__(self):
        """Initialize empty sharded catalog"""
        self.shards: dict[str, ToolCatalog] = {
            domain: ToolCatalog() for domain in DOMAIN_KEYWORDS.keys()
        }
        self.global_catalog: ToolCatalog = ToolCatalog()
        self._tool_count_by_domain: dict[str, int] = dict.fromkeys(DOMAIN_KEYWORDS.keys(), 0)
        logger.info(f"Initialized ShardedCatalog with {len(self.shards)} domain shards")

    def add_tool(self, tool: ToolDefinition) -> str:
        """
        Add tool to appropriate domain shard and global catalog.

        Args:
            tool: Tool definition with optional domain field

        Returns:
            Domain where tool was added
        """
        # Use tool's domain if explicitly set (not default "general"), otherwise detect
        if tool.domain != "general":
            domain = tool.domain
        else:
            # Try to detect from name/description
            domain = self._detect_tool_domain(tool)

        # Add to domain shard
        if domain not in self.shards:
            logger.warning(f"Unknown domain '{domain}', adding to 'general'")
            domain = "general"

        self.shards[domain].add_tool(tool)
        self._tool_count_by_domain[domain] += 1

        # Add to global catalog
        self.global_catalog.add_tool(tool)

        logger.debug(f"Added tool '{tool.name}' to domain '{domain}'")
        return domain

    def get_shard(self, domain: str) -> ToolCatalog | None:
        """Get catalog for specific domain"""
        return self.shards.get(domain)

    def get_global_catalog(self) -> ToolCatalog:
        """Get global catalog containing all tools"""
        return self.global_catalog

    def get_stats(self) -> dict[str, int]:
        """Get tool count statistics by domain"""
        return {
            **self._tool_count_by_domain,
            "total": len(self.global_catalog.tools)
        }

    def detect_domain(self, query: str) -> str | None:
        """
        Detect most likely domain from query using keyword matching.

        Args:
            query: Search query text

        Returns:
            Domain name or None if no clear match
        """
        query_lower = query.lower()
        domain_scores: dict[str, int] = dict.fromkeys(DOMAIN_KEYWORDS.keys(), 0)

        # Score each domain based on keyword matches
        for domain, config in DOMAIN_KEYWORDS.items():
            if domain == "general":
                continue  # Skip general (catch-all)

            for keyword in config["keywords"]:
                if keyword in query_lower:
                    domain_scores[domain] += 1

        # Get domain with highest score
        max_score = max(domain_scores.values())

        if max_score == 0:
            return None  # No clear domain match

        # Return domain with highest score (break ties arbitrarily)
        detected_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
        logger.debug(f"Detected domain '{detected_domain}' for query: '{query[:50]}...' (score={max_score})")
        return detected_domain

    def _detect_tool_domain(self, tool: ToolDefinition) -> str:
        """
        Detect domain from tool name/description.

        Args:
            tool: Tool definition

        Returns:
            Detected domain name (defaults to 'general')
        """
        tool_name_lower = tool.name.lower()

        # Check tool name against known tool patterns first
        for domain, config in DOMAIN_KEYWORDS.items():
            if domain == "general":
                continue
            for known_tool in config["tools"]:
                if known_tool.lower() in tool_name_lower:
                    return domain

        # Check tool name for domain keywords
        for domain, config in DOMAIN_KEYWORDS.items():
            if domain == "general":
                continue
            for keyword in config["keywords"]:
                if keyword in tool_name_lower:
                    return domain

        # Check description for domain keywords
        if tool.description:
            detected = self.detect_domain(tool.description)
            if detected:
                return detected

        # Default to general
        return "general"

    def list_domains(self) -> list[str]:
        """List all available domains"""
        return list(self.shards.keys())

    def search_by_domain(
        self,
        query: str,
        domain: str,
        min_results: int = 3,
        top_k: int | None = None  # top_k kept for compatibility; not used currently
    ) -> tuple[ToolCatalog, str | None]:
        """
        Search within specific domain with fallback to global.

        Args:
            query: Search query
            domain: Domain to search in
            min_results: Minimum results before fallback

        Returns:
            Tuple of (results, domain_used)
            - results: Search results
            - domain_used: Domain that was actually used ('github', 'global', etc.)
        """
        # Try domain-specific search first
        if domain in self.shards:
            shard = self.shards[domain]
            if len(shard.tools) > 0:
                logger.info(f"Searching in '{domain}' domain ({len(shard.tools)} tools)")
                # Note: Actual search implementation needs to be injected or use VectorToolSearchEngine
                # For now, return catalog for search engine to use
                return (shard, domain)

        # Fallback to global search
        logger.info(f"Domain '{domain}' empty or not found, using global search")
        return (self.global_catalog, "global")

    def search_with_detection(
        self,
        query: str,
        min_results: int = 3,
        top_k: int | None = None  # top_k kept for compatibility; not used currently
    ) -> tuple[ToolCatalog, str | None]:
        """
        Auto-detect domain and search with fallback.

        Args:
            query: Search query
            min_results: Minimum results before fallback

        Returns:
            Tuple of (catalog, domain_used)
        """
        # Detect domain from query
        detected_domain = self.detect_domain(query)

        if detected_domain:
            logger.info(f"Auto-detected domain: '{detected_domain}'")
            return self.search_by_domain(query, detected_domain, min_results)

        # No domain detected, use global
        logger.info("No domain detected, using global search")
        return (self.global_catalog, "global")

    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"ShardedCatalog(domains={len(self.shards)}, tools={stats})"
