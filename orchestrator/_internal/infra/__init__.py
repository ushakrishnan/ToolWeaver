"""
Infrastructure subpackage.

Consolidates caching, MCP client, and other infrastructure utilities.
"""

from .a2a_client import (
    A2AClient,
    AgentCapability,
    AgentDelegationRequest,
    AgentDelegationResponse,
)
from .mcp_client import MCPClientShim
from .redis_cache import RedisCache

__all__ = [
    "RedisCache",
    "MCPClientShim",
    "A2AClient",
    "AgentCapability",
    "AgentDelegationRequest",
    "AgentDelegationResponse",
]
