"""
User-friendly error messages for missing optional dependencies.

Phase 0.d: Clear error messages when users try to use features
that require optional dependencies they haven't installed.

Usage:
    from orchestrator._internal.errors import require_package

    @require_package("wandb", extra="monitoring")
    def enable_wandb_tracking():
        import wandb
        wandb.init()

If wandb not installed, user sees:
    MissingDependencyError: W&B monitoring not available.
    Install with: pip install toolweaver[monitoring]
"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar('F', bound=Callable[..., Any])


# ============================================================
# Exception Classes
# ============================================================

class ToolWeaverError(Exception):
    """Base exception for all ToolWeaver errors."""
    pass


class MissingDependencyError(ToolWeaverError):
    """Raised when an optional dependency is required but not installed."""

    def __init__(self, package: str, extra: str | None = None, suggestion: str | None = None):
        """
        Args:
            package: Name of the missing package (e.g., "wandb")
            extra: Optional extra name from pyproject.toml (e.g., "monitoring")
            suggestion: Optional custom suggestion message
        """
        self.package = package
        self.extra = extra

        if suggestion:
            message = suggestion
        elif extra:
            message = (
                f"{package} not available.\n"
                f"Install with: pip install toolweaver[{extra}]"
            )
        else:
            message = (
                f"{package} not available.\n"
                f"Install with: pip install {package}"
            )

        super().__init__(message)


class ConfigurationError(ToolWeaverError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(ToolWeaverError):
    """Raised when input validation fails."""
    pass


# ============================================================
# Dependency Checking
# ============================================================

def check_package_available(package: str) -> bool:
    """
    Check if a package is available for import.

    Args:
        package: Package name (e.g., "wandb", "redis")

    Returns:
        True if package can be imported, False otherwise

    Example:
        >>> check_package_available("wandb")
        False
        >>> check_package_available("pydantic")
        True
    """
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def require_package(package: str, extra: str | None = None, suggestion: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to require an optional package for a function.

    Args:
        package: Package name that must be installed
        extra: Optional extra name from pyproject.toml
        suggestion: Optional custom error message

    Returns:
        Decorator function

    Example:
        @require_package("wandb", extra="monitoring")
        def enable_wandb():
            import wandb
            wandb.init()

        # If wandb not installed:
        enable_wandb()  # Raises MissingDependencyError with helpful message
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not check_package_available(package):
                raise MissingDependencyError(package, extra, suggestion)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_packages(*packages: str, extra: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to require multiple optional packages.

    Args:
        *packages: Package names that must be installed
        extra: Optional extra name from pyproject.toml

    Returns:
        Decorator function

    Example:
        @require_packages("redis", "hiredis", extra="redis")
        def enable_redis_cache():
            import redis
            return redis.Redis()
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            missing = [pkg for pkg in packages if not check_package_available(pkg)]
            if missing:
                if len(missing) == 1:
                    raise MissingDependencyError(missing[0], extra)
                else:
                    packages_str = ", ".join(missing)
                    if extra:
                        message = (
                            f"Missing packages: {packages_str}\n"
                            f"Install with: pip install toolweaver[{extra}]"
                        )
                    else:
                        message = (
                            f"Missing packages: {packages_str}\n"
                            f"Install with: pip install {' '.join(missing)}"
                        )
                    raise MissingDependencyError(missing[0], suggestion=message)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# Context Manager for Optional Features
# ============================================================

class optional_feature:
    """
    Context manager for optional features.

    If package is not available, logs a warning instead of raising an error.

    Example:
        from orchestrator._internal.logger import get_logger
        from orchestrator._internal.errors import optional_feature

        logger = get_logger(__name__)

        with optional_feature("wandb", "monitoring", logger):
            import wandb
            wandb.init()

        # If wandb not available, logs warning and continues
    """

    def __init__(self, package: str, extra: str | None = None, logger: Any = None) -> None:
        """
        Args:
            package: Package name
            extra: Optional extra name
            logger: Optional logger for warnings
        """
        self.package = package
        self.extra = extra
        self.logger = logger
        self.available = False

    def __enter__(self) -> bool:
        self.available = check_package_available(self.package)
        if not self.available and self.logger:
            if self.extra:
                self.logger.warning(
                    f"{self.package} not available (install: pip install toolweaver[{self.extra}])"
                )
            else:
                self.logger.warning(
                    f"{self.package} not available (install: pip install {self.package})"
                )
        return self.available

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        # Suppress ImportError if package not available
        if exc_type is ImportError and not self.available:
            return True
        return None
        return False


# ============================================================
# Helpful Error Messages
# ============================================================

PACKAGE_EXTRAS_MAP = {
    # Monitoring
    "wandb": "monitoring",
    "prometheus_client": "monitoring",

    # Vector databases
    "qdrant_client": "qdrant",
    "pinecone": "pinecone",

    # Cache
    "redis": "redis",
    "hiredis": "redis",

    # LLM providers
    "openai": "openai",
    "anthropic": "anthropic",
    "google.generativeai": "gemini",

    # Local models
    "transformers": "local-models",
    "torch": "local-models",
    "accelerate": "local-models",
}


def get_install_suggestion(package: str) -> str:
    """
    Get helpful install suggestion for a package.

    Args:
        package: Package name

    Returns:
        Install command suggestion

    Example:
        >>> get_install_suggestion("wandb")
        "pip install toolweaver[monitoring]"
        >>> get_install_suggestion("unknown_package")
        "pip install unknown_package"
    """
    extra = PACKAGE_EXTRAS_MAP.get(package)
    if extra:
        return f"pip install toolweaver[{extra}]"
    return f"pip install {package}"


# ============================================================
# Export
# ============================================================

__all__ = [
    # Base exceptions
    "ToolWeaverError",
    "MissingDependencyError",
    "ConfigurationError",
    "ValidationError",
    # Dependency checking
    "check_package_available",
    "require_package",
    "require_packages",
    "optional_feature",
    "get_install_suggestion",
]
