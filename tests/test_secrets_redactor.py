"""
Tests for Secrets Redaction in Logging

Validates that sensitive information is properly filtered from log messages.
"""

import logging

import pytest

from orchestrator._internal.security.secrets_redactor import (
    SecretsRedactor,
    install_secrets_redactor,
    remove_secrets_redactor,
)


@pytest.fixture
def redactor():
    """Create a SecretsRedactor instance."""
    return SecretsRedactor()


@pytest.fixture
def logger():
    """Create a test logger."""
    test_logger = logging.getLogger('test_secrets')
    test_logger.handlers.clear()
    test_logger.filters.clear()
    test_logger.setLevel(logging.DEBUG)
    return test_logger


class TestSecretsRedactor:
    """Test the SecretsRedactor logging filter."""

    def test_redact_openai_key(self, redactor):
        """Should redact OpenAI API keys."""
        text = "Using API key: sk-proj123456789012345678901234567890123456789012"
        result = redactor.redact_secrets(text)
        assert "sk-proj" not in result
        assert "[REDACTED_OPENAI_KEY]" in result

    def test_redact_github_token_ghp(self, redactor):
        """Should redact GitHub ghp_ tokens."""
        text = "Token: ghp_1234567890123456789012345678901234"
        result = redactor.redact_secrets(text)
        assert "ghp_" not in result
        assert "[REDACTED_GITHUB_TOKEN]" in result

    def test_redact_github_pat(self, redactor):
        """Should redact GitHub PAT tokens."""
        text = "PAT: github_pat_11ABCDEFG0123456789_" + "A" * 50
        result = redactor.redact_secrets(text)
        assert "github_pat_" not in result
        assert "[REDACTED_GITHUB_TOKEN]" in result

    def test_redact_bearer_token(self, redactor):
        """Should redact Bearer tokens."""
        text = "Authorization: Bearer abc123def456ghi789jkl012mno345"
        result = redactor.redact_secrets(text)
        assert "abc123" not in result
        assert "[REDACTED_BEARER_TOKEN]" in result

    def test_redact_aws_key(self, redactor):
        """Should redact AWS access keys."""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redactor.redact_secrets(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED_AWS_KEY]" in result

    def test_redact_jwt(self, redactor):
        """Should redact JWT tokens."""
        text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = redactor.redact_secrets(text)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[REDACTED_JWT]" in result

    def test_redact_api_key_equals(self, redactor):
        """Should redact api_key=value format."""
        text = "Config: api_key=abc123def456ghi789jkl012"
        result = redactor.redact_secrets(text)
        assert "abc123" not in result
        assert "api_key=[REDACTED_API_KEY]" in result

    def test_redact_api_key_colon(self, redactor):
        """Should redact api_key: value format."""
        text = "Headers: apikey: abc123def456ghi789jkl012"
        result = redactor.redact_secrets(text)
        assert "abc123" not in result
        assert "[REDACTED_API_KEY]" in result

    def test_redact_password_equals(self, redactor):
        """Should redact password=value format."""
        text = "Credentials: password=mySecretPass123!"
        result = redactor.redact_secrets(text)
        assert "mySecretPass123!" not in result
        assert "password=[REDACTED_PASSWORD]" in result

    def test_redact_pwd_colon(self, redactor):
        """Should redact pwd: value format."""
        text = "Auth: pwd: p@ssw0rd123"
        result = redactor.redact_secrets(text)
        assert "p@ssw0rd123" not in result
        assert "pwd=[REDACTED_PASSWORD]" in result

    def test_redact_anthropic_key(self, redactor):
        """Should redact Anthropic API keys."""
        text = "Key: sk-ant-" + "A" * 95
        result = redactor.redact_secrets(text)
        assert "sk-ant-" not in result
        assert "[REDACTED_ANTHROPIC_KEY]" in result

    def test_preserve_safe_text(self, redactor):
        """Should not modify text without secrets."""
        text = "Normal log message with no secrets"
        result = redactor.redact_secrets(text)
        assert result == text

    def test_multiple_secrets(self, redactor):
        """Should redact multiple secrets in one message."""
        text = "API: sk-proj123456789012345678901234567890123456789012 Token: ghp_1234567890123456789012345678901234"
        result = redactor.redact_secrets(text)
        assert "sk-proj" not in result
        assert "ghp_" not in result
        assert "[REDACTED_OPENAI_KEY]" in result
        assert "[REDACTED_GITHUB_TOKEN]" in result

    def test_filter_log_record(self, redactor):
        """Should filter log record messages."""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg="API Key: sk-proj123456789012345678901234567890123456789012",
            args=(),
            exc_info=None
        )

        result = redactor.filter(record)
        assert result is True  # Always pass
        assert "[REDACTED_OPENAI_KEY]" in record.msg

    def test_filter_log_args_dict(self, redactor):
        """Should filter log record args (dict)."""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg="Config: %s",
            args=(),
            exc_info=None
        )
        # Manually set args to avoid LogRecord constructor issue
        record.args = {'key': 'sk-proj123456789012345678901234567890123456789012'}

        result = redactor.filter(record)
        assert result is True
        assert "[REDACTED_OPENAI_KEY]" in record.args['key']

    def test_filter_log_args_tuple(self, redactor):
        """Should filter log record args (tuple)."""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg="Key: %s",
            args=('sk-proj123456789012345678901234567890123456789012',),
            exc_info=None
        )

        result = redactor.filter(record)
        assert result is True
        assert "[REDACTED_OPENAI_KEY]" in record.args[0]

    def test_filter_non_string_args(self, redactor):
        """Should preserve non-string args."""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg="Value: %d",
            args=(42,),
            exc_info=None
        )

        result = redactor.filter(record)
        assert result is True
        assert record.args[0] == 42


class TestInstallation:
    """Test redactor installation helpers."""

    def test_install_on_logger(self, logger):
        """Should install redactor on logger."""
        install_secrets_redactor(logger)
        assert any(isinstance(f, SecretsRedactor) for f in logger.filters)

    def test_install_on_root_logger(self):
        """Should install on root logger by default."""
        root = logging.getLogger()
        remove_secrets_redactor(root)  # Clean first

        install_secrets_redactor()
        assert any(isinstance(f, SecretsRedactor) for f in root.filters)

        remove_secrets_redactor(root)  # Clean up

    def test_install_idempotent(self, logger):
        """Should not install duplicate filters."""
        install_secrets_redactor(logger)
        install_secrets_redactor(logger)

        redactor_count = sum(1 for f in logger.filters if isinstance(f, SecretsRedactor))
        assert redactor_count == 1

    def test_remove_redactor(self, logger):
        """Should remove redactor from logger."""
        install_secrets_redactor(logger)
        assert any(isinstance(f, SecretsRedactor) for f in logger.filters)

        remove_secrets_redactor(logger)
        assert not any(isinstance(f, SecretsRedactor) for f in logger.filters)


class TestIntegration:
    """Test integration with actual logging."""

    def test_logs_with_secrets_redacted(self, logger, caplog):
        """Should redact secrets in actual log output."""
        install_secrets_redactor(logger)
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        with caplog.at_level(logging.INFO, logger='test_secrets'):
            logger.info("API Key: sk-proj123456789012345678901234567890123456789012")

        assert "sk-proj" not in caplog.text
        assert "[REDACTED_OPENAI_KEY]" in caplog.text

    def test_formatted_logs_redacted(self, logger, caplog):
        """Should redact secrets in formatted logs."""
        install_secrets_redactor(logger)
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        api_key = "sk-proj123456789012345678901234567890123456789012"
        with caplog.at_level(logging.INFO, logger='test_secrets'):
            logger.info(f"Using key: {api_key}")

        assert "sk-proj" not in caplog.text
        assert "[REDACTED_OPENAI_KEY]" in caplog.text

    def test_direct_log_message_redacted(self, logger, caplog):
        """Should redact secrets in direct log messages."""
        install_secrets_redactor(logger)
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        with caplog.at_level(logging.ERROR, logger='test_secrets'):
            logger.error("Failed with key sk-proj123456789012345678901234567890123456789012")

        assert "sk-proj" not in caplog.text
        assert "[REDACTED_OPENAI_KEY]" in caplog.text
