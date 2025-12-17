"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.sharded_catalog import ShardedCatalog, DOMAIN_KEYWORDS
__all__ = ["ShardedCatalog", "DOMAIN_KEYWORDS"]
