"""
Secrets Redaction for Logging

Filters sensitive information from log messages to prevent credential leakage
across distributed agent systems.

Threats Mitigated:
- AS-3: Credential Harvesting (API keys in logs × 100 agents)
- Security breach via log files
"""

import logging
import re
from re import Pattern


class SecretsRedactor(logging.Filter):
    """
    Logging filter that redacts secrets from log messages.
    
    Automatically detects and redacts:
    - OpenAI API keys (sk-...)
    - GitHub tokens (ghp_..., github_pat_...)
    - Bearer tokens (Bearer ...)
    - Generic API keys (api_key=..., apikey=...)
    - Passwords (password=..., pwd=...)
    - AWS access keys (AKIA...)
    - JWT tokens (eyJ...)
    
    Usage:
        # Install on root logger
        import logging
        logging.getLogger().addFilter(SecretsRedactor())
        
        # Or install via helper
        install_secrets_redactor()
        
        # Now logging is safe
        logging.info(f"API Key: sk-abc123...")  # Logs as: API Key: [REDACTED_OPENAI_KEY]
    """

    # Regex patterns for secret detection
    PATTERNS: list[tuple[str, Pattern]] = [
        # OpenAI API keys (variable length after prefix)
        ('OPENAI_KEY', re.compile(r'\bsk-[A-Za-z0-9]{20,}\b')),

        # GitHub tokens (multiple formats)
        ('GITHUB_TOKEN', re.compile(r'\bghp_[A-Za-z0-9]{20,}\b')),
        ('GITHUB_TOKEN', re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}\b')),

        # Generic bearer tokens
        ('BEARER_TOKEN', re.compile(r'[Bb]earer\s+[A-Za-z0-9_\-\.]{20,}')),

        # AWS access keys
        ('AWS_KEY', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),

        # JWT tokens
        ('JWT', re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b')),

        # Generic API key patterns (api_key=..., apikey=..., 'api-key': '...')
        ('API_KEY', re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?')),

        # Password patterns (password=..., pwd=...)
        ('PASSWORD', re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?')),

        # Anthropic API keys (variable length)
        ('ANTHROPIC_KEY', re.compile(r'\bsk-ant-[A-Za-z0-9_-]{90,}\b')),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by redacting secrets.
        
        Args:
            record: Log record to filter
            
        Returns:
            True (always pass the record, just modify it)
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redact_secrets(record.msg)

        # Also redact in args if present
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.redact_secrets(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self.redact_secrets(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True

    def redact_secrets(self, text: str) -> str:
        """
        Redact all secrets from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Text with secrets replaced by [REDACTED_TYPE]
        """
        result = text

        for secret_type, pattern in self.PATTERNS:
            # Handle patterns with capture groups
            if secret_type in ('API_KEY', 'PASSWORD'):
                # These patterns have capture groups for key=value format
                result = pattern.sub(
                    lambda m: f"{m.group(1)}=[REDACTED_{secret_type}]",
                    result
                )
            else:
                # Simple replacement
                result = pattern.sub(f'[REDACTED_{secret_type}]', result)

        return result


def install_secrets_redactor(logger: logging.Logger = None) -> None:
    """
    Install secrets redactor on a logger.
    
    Args:
        logger: Logger to install on (defaults to root logger)
    """
    if logger is None:
        logger = logging.getLogger()

    # Check if already installed
    for filter_obj in logger.filters:
        if isinstance(filter_obj, SecretsRedactor):
            return  # Already installed

    logger.addFilter(SecretsRedactor())


def remove_secrets_redactor(logger: logging.Logger = None) -> None:
    """
    Remove secrets redactor from a logger.
    
    Args:
        logger: Logger to remove from (defaults to root logger)
    """
    if logger is None:
        logger = logging.getLogger()

    # Remove all SecretsRedactor instances
    logger.filters = [
        f for f in logger.filters
        if not isinstance(f, SecretsRedactor)
    ]
