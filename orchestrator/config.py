"""
Configuration management for ToolWeaver.

Phase 0.c: All configuration via environment variables.
No source code configuration files.

Usage:
    from orchestrator.config import get_config

    config = get_config()
    print(config.skill_path)  # ~/.toolweaver/skills
    print(config.log_level)   # INFO

Environment Variables:
    TOOLWEAVER_SKILL_PATH - Where to store skills (default: ~/.toolweaver/skills)
    TOOLWEAVER_LOG_LEVEL - Logging level (default: INFO)
    TOOLWEAVER_REDIS_URL - Redis connection URL (optional)
    TOOLWEAVER_QDRANT_URL - Qdrant connection URL (optional)
    TOOLWEAVER_WANDB_PROJECT - W&B project name (optional)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================
# Default Values
# ============================================================

DEFAULT_SKILL_PATH = Path.home() / ".toolweaver" / "skills"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CACHE_PATH = Path.home() / ".toolweaver" / "cache"


# ============================================================
# Configuration Class
# ============================================================

@dataclass
class ToolWeaverConfig:
    """
    ToolWeaver configuration loaded from environment variables.

    All settings have sensible defaults. Users only set what they need.

    Attributes:
        skill_path: Where to store skills
        log_level: Logging level
        cache_path: Where to cache data
        redis_url: Redis connection URL (optional)
        qdrant_url: Qdrant vector DB URL (optional)
        qdrant_api_key: Qdrant API key (optional)
        wandb_project: W&B project name (optional)
        wandb_entity: W&B entity name (optional)
    """

    # Core paths
    skill_path: Path = field(default_factory=lambda: DEFAULT_SKILL_PATH)
    log_level: str = DEFAULT_LOG_LEVEL
    cache_path: Path = field(default_factory=lambda: DEFAULT_CACHE_PATH)

    # Optional: Redis caching
    redis_url: str | None = None

    # Optional: Qdrant vector database
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # Optional: W&B monitoring
    wandb_project: str | None = None
    wandb_entity: str | None = None

    # Optional: Prometheus monitoring
    prometheus_port: int = 8000

    @classmethod
    def from_env(cls) -> "ToolWeaverConfig":
        """
        Load configuration from environment variables.

        Returns:
            ToolWeaverConfig instance

        Example:
            >>> config = ToolWeaverConfig.from_env()
            >>> print(config.skill_path)
            /home/user/.toolweaver/skills
        """
        # Core paths
        skill_path_str = os.getenv("TOOLWEAVER_SKILL_PATH")
        skill_path = Path(skill_path_str) if skill_path_str else DEFAULT_SKILL_PATH

        log_level = os.getenv("TOOLWEAVER_LOG_LEVEL", DEFAULT_LOG_LEVEL)

        cache_path_str = os.getenv("TOOLWEAVER_CACHE_PATH")
        cache_path = Path(cache_path_str) if cache_path_str else DEFAULT_CACHE_PATH

        # Optional: Redis
        redis_url = os.getenv("TOOLWEAVER_REDIS_URL")

        # Optional: Qdrant
        qdrant_url = os.getenv("TOOLWEAVER_QDRANT_URL")
        qdrant_api_key = os.getenv("TOOLWEAVER_QDRANT_API_KEY")

        # Optional: W&B
        wandb_project = os.getenv("TOOLWEAVER_WANDB_PROJECT")
        wandb_entity = os.getenv("TOOLWEAVER_WANDB_ENTITY")

        # Optional: Prometheus
        prometheus_port = int(os.getenv("TOOLWEAVER_PROMETHEUS_PORT", "8000"))

        return cls(
            skill_path=skill_path,
            log_level=log_level,
            cache_path=cache_path,
            redis_url=redis_url,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            wandb_project=wandb_project,
            wandb_entity=wandb_entity,
            prometheus_port=prometheus_port,
        )

    def ensure_directories(self) -> None:
        """
        Create required directories if they don't exist.

        Example:
            >>> config = get_config()
            >>> config.ensure_directories()
            # Creates ~/.toolweaver/skills and ~/.toolweaver/cache
        """
        self.skill_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def is_redis_enabled(self) -> bool:
        """Check if Redis caching is configured."""
        return self.redis_url is not None

    def is_qdrant_enabled(self) -> bool:
        """Check if Qdrant vector search is configured."""
        return self.qdrant_url is not None

    def is_wandb_enabled(self) -> bool:
        """Check if W&B monitoring is configured."""
        return self.wandb_project is not None

    def __repr__(self) -> str:
        """String representation hiding sensitive data."""
        redis_status = "enabled" if self.redis_url else "disabled"
        qdrant_status = "enabled" if self.qdrant_url else "disabled"
        wandb_status = "enabled" if self.wandb_project else "disabled"

        return (
            f"ToolWeaverConfig(\n"
            f"  skill_path={self.skill_path},\n"
            f"  log_level={self.log_level},\n"
            f"  cache_path={self.cache_path},\n"
            f"  redis={redis_status},\n"
            f"  qdrant={qdrant_status},\n"
            f"  wandb={wandb_status}\n"
            f")"
        )


# ============================================================
# Global Configuration Singleton
# ============================================================

_config: ToolWeaverConfig | None = None


def get_config(reload: bool = False) -> ToolWeaverConfig:
    """
    Get the global ToolWeaver configuration.

    Configuration is loaded once from environment variables and cached.

    Args:
        reload: If True, reload configuration from environment

    Returns:
        ToolWeaverConfig instance

    Example:
        >>> config = get_config()
        >>> print(config.skill_path)
        /home/user/.toolweaver/skills

        >>> config.ensure_directories()  # Create directories
    """
    global _config

    if _config is None or reload:
        _config = ToolWeaverConfig.from_env()
        _config.ensure_directories()

    return _config


def reset_config() -> None:
    """
    Reset configuration (mainly for testing).

    Example:
        >>> reset_config()
        >>> config = get_config()  # Reloads from environment
    """
    global _config
    _config = None


# ============================================================
# Configuration Validation
# ============================================================

def validate_config() -> list[str]:
    """
    Validate configuration and return list of warnings/errors.

    Returns:
        List of warning messages (empty if all OK)

    Example:
        >>> warnings = validate_config()
        >>> for warning in warnings:
        ...     print(f"Warning: {warning}")
    """
    config = get_config()
    warnings = []

    # Check Redis if configured
    if config.redis_url:
        try:
            from orchestrator._internal.errors import check_package_available
            if not check_package_available("redis"):
                warnings.append(
                    "TOOLWEAVER_REDIS_URL is set but redis package not installed. "
                    "Install with: pip install toolweaver[redis]"
                )
        except ImportError:
            pass

    # Check Qdrant if configured
    if config.qdrant_url:
        try:
            from orchestrator._internal.errors import check_package_available
            if not check_package_available("qdrant_client"):
                warnings.append(
                    "TOOLWEAVER_QDRANT_URL is set but qdrant-client not installed. "
                    "Install with: pip install toolweaver[qdrant]"
                )
        except ImportError:
            pass

    # Check W&B if configured
    if config.wandb_project:
        try:
            from orchestrator._internal.errors import check_package_available
            if not check_package_available("wandb"):
                warnings.append(
                    "TOOLWEAVER_WANDB_PROJECT is set but wandb not installed. "
                    "Install with: pip install toolweaver[monitoring]"
                )
        except ImportError:
            pass

    return warnings


# ============================================================
# Export
# ============================================================

__all__ = [
    "ToolWeaverConfig",
    "get_config",
    "reset_config",
    "validate_config",
]
