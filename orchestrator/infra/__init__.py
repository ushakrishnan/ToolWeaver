"""
Infrastructure subpackage.

Consolidates caching, MCP client, and other infrastructure utilities.
"""

from .redis_cache import RedisCache

from .mcp_client import MCPClientShim
from .a2a_client import (
    A2AClient,
    AgentCapability,
    AgentDelegationRequest,
    AgentDelegationResponse,
)

__all__ = [
    "RedisCache",
    "MCPClientShim",
    "A2AClient",
    "AgentCapability",
    "AgentDelegationRequest",
    "AgentDelegationResponse",
]
