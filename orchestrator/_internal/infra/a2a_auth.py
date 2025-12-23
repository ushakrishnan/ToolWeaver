"""
Authentication Configuration and Management for A2A Calls

Provides structured authentication configuration for agent-to-agent communication,
supporting bearer tokens, API keys, and future OAuth2/mTLS extensions.
"""

from dataclasses import dataclass
from typing import Dict, Literal, Optional
import os


AuthType = Literal["bearer", "api_key", "none"]


@dataclass
class AuthConfig:
    """
    Authentication configuration for external service calls.
    
    Attributes:
        type: Authentication type ("bearer", "api_key", or "none")
        token_env: Environment variable name containing the token/key
        header_name: HTTP header name for the auth token
    """
    type: AuthType
    token_env: Optional[str] = None
    header_name: str = "Authorization"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.type in ("bearer", "api_key") and not self.token_env:
            raise ValueError(
                f"token_env is required for auth type '{self.type}'"
            )


class AuthManager:
    """
    Manages authentication headers for HTTP requests.
    
    Usage:
        # Bearer token authentication
        config = AuthConfig(
            type="bearer",
            token_env="OPENAI_API_KEY"
        )
        manager = AuthManager()
        headers = manager.get_headers(config)
        # {'Authorization': 'Bearer sk-...'}
        
        # API key authentication
        config = AuthConfig(
            type="api_key",
            token_env="GITHUB_TOKEN",
            header_name="X-GitHub-Token"
        )
        headers = manager.get_headers(config)
        # {'X-GitHub-Token': 'ghp_...'}
        
        # No authentication
        config = AuthConfig(type="none")
        headers = manager.get_headers(config)
        # {}
    """
    
    def get_headers(self, config: AuthConfig) -> Dict[str, str]:
        """
        Generate authentication headers from configuration.
        
        Args:
            config: Authentication configuration
            
        Returns:
            Dictionary of HTTP headers
            
        Raises:
            ValueError: If required token is missing from environment
        """
        if config.type == "none":
            return {}
        
        # Get token from environment
        if not config.token_env:
            raise ValueError(
                f"token_env is required for auth type '{config.type}'"
            )
        
        token = os.getenv(config.token_env)
        if not token:
            raise ValueError(
                f"Authentication token not found in environment variable "
                f"'{config.token_env}'"
            )
        
        # Format based on auth type
        if config.type == "bearer":
            # Bearer token format: "Bearer {token}"
            return {config.header_name: f"Bearer {token}"}
        elif config.type == "api_key":
            # API key format: plain token
            return {config.header_name: token}
        else:
            raise ValueError(f"Unsupported auth type: {config.type}")
    
    def validate_config(self, config: AuthConfig) -> bool:
        """
        Validate that configuration is usable (token exists, etc.).
        
        Args:
            config: Authentication configuration
            
        Returns:
            True if valid and usable, False otherwise
        """
        if config.type == "none":
            return True
        
        if not config.token_env:
            return False
        
        # Check if token exists in environment
        return os.getenv(config.token_env) is not None


# Predefined configurations for common services
OPENAI_AUTH = AuthConfig(
    type="bearer",
    token_env="OPENAI_API_KEY",
    header_name="Authorization"
)

ANTHROPIC_AUTH = AuthConfig(
    type="api_key",
    token_env="ANTHROPIC_API_KEY",
    header_name="x-api-key"
)

GITHUB_AUTH = AuthConfig(
    type="bearer",
    token_env="GITHUB_TOKEN",
    header_name="Authorization"
)

AZURE_AUTH = AuthConfig(
    type="api_key",
    token_env="AZURE_API_KEY",
    header_name="api-key"
)
