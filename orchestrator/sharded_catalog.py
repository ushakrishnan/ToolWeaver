"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.sharded_catalog import ShardedCatalog
__all__ = ["ShardedCatalog"]
