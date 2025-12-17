"""Shim module for backwards compatibility. Re-exports from orchestrator.infra."""
from .infra.mcp_client import MCPClientShim
__all__ = ["MCPClientShim"]
