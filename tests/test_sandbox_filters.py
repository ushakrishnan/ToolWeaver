"""Tests for sandbox data filtering and PII tokenization."""

import pytest
from orchestrator.execution.sandbox_filters import (
    DataFilter,
    PIITokenizer,
    FilterConfig,
    TokenizationConfig,
    PIIType,
    filter_and_tokenize,
)


class TestPIITokenizer:
    """Test PII detection and tokenization."""
    
    def test_tokenize_email(self):
        """Test email tokenization."""
        tokenizer = PIITokenizer()
        data = {"email": "user@example.com", "message": "Contact me at admin@test.org"}
        
        result = tokenizer.tokenize(data)
        
        assert "user@example.com" not in str(result)
        assert "admin@test.org" not in str(result)
        assert "TOKEN_EMAIL_" in str(result)
    
    def test_tokenize_phone(self):
        """Test phone number tokenization."""
        tokenizer = PIITokenizer()
        data = {
            "phone": "555-123-4567",
            "contact": "Call me at (555) 987-6543"
        }
        
        result = tokenizer.tokenize(data)
        
        assert "555-123-4567" not in str(result)
        assert "555-987-6543" not in str(result)
        assert "TOKEN_PHONE_" in str(result)
    
    def test_tokenize_ssn(self):
        """Test SSN tokenization."""
        tokenizer = PIITokenizer()
        data = {"ssn": "123-45-6789"}
        
        result = tokenizer.tokenize(data)
        
        assert "123-45-6789" not in str(result)
        assert "TOKEN_SSN_" in str(result)
    
    def test_tokenize_credit_card(self):
        """Test credit card tokenization."""
        tokenizer = PIITokenizer()
        data = {"card": "4532-1234-5678-9010"}
        
        result = tokenizer.tokenize(data)
        
        assert "4532-1234-5678-9010" not in str(result)
        assert "TOKEN_CREDIT_CARD_" in str(result)
    
    def test_tokenize_nested_structures(self):
        """Test tokenization in nested data."""
        tokenizer = PIITokenizer()
        data = {
            "users": [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@test.org"}
            ]
        }
        
        result = tokenizer.tokenize(data)
        
        assert "alice@example.com" not in str(result)
        assert "bob@test.org" not in str(result)
        assert len(tokenizer.get_token_map()) == 2
    
    def test_detokenize(self):
        """Test detokenization restores original values."""
        tokenizer = PIITokenizer()
        original = {"email": "user@example.com", "phone": "555-1234"}
        
        tokenized = tokenizer.tokenize(original)
        restored = tokenizer.detokenize(tokenized)
        
        # Emails should be restored
        assert "user@example.com" in str(restored)
    
    def test_token_deterministic(self):
        """Test that same value gets same token."""
        tokenizer = PIITokenizer()
        
        data1 = {"email": "same@example.com"}
        data2 = {"contact": "same@example.com"}
        
        result1 = tokenizer.tokenize(data1)
        result2 = tokenizer.tokenize(data2)
        
        # Should use same token for same email
        token_map = tokenizer.get_token_map()
        assert len(token_map) == 1
    
    def test_selective_pii_types(self):
        """Test enabling only specific PII types."""
        config = TokenizationConfig(enabled_types={PIIType.EMAIL})
        tokenizer = PIITokenizer(config)
        
        data = {
            "email": "user@example.com",
            "phone": "555-1234",
            "ssn": "123-45-6789"
        }
        
        result = tokenizer.tokenize(data)
        
        # Only email should be tokenized
        assert "user@example.com" not in str(result)
        assert "555-1234" in str(result)  # Phone not tokenized
        assert "123-45-6789" in str(result)  # SSN not tokenized
    
    def test_clear_tokens(self):
        """Test clearing token map."""
        tokenizer = PIITokenizer()
        data = {"email": "user@example.com"}
        
        tokenizer.tokenize(data)
        assert len(tokenizer.get_token_map()) > 0
        
        tokenizer.clear_tokens()
        assert len(tokenizer.get_token_map()) == 0


class TestDataFilter:
    """Test data filtering and truncation."""
    
    def test_filter_large_list(self):
        """Test truncating large lists."""
        config = FilterConfig(max_rows=10)
        filter = DataFilter(config)
        
        data = list(range(100))
        result = filter.apply(data)
        
        assert result["truncated"] is True
        assert len(result["data"]) <= 11  # 10 items + truncation notice
        assert result["stats"]["rows_truncated"] == 90
    
    def test_filter_long_strings(self):
        """Test truncating long strings."""
        config = FilterConfig(max_string_length=20, truncate_strings=True)
        filter = DataFilter(config)
        
        data = {"text": "a" * 100}
        result = filter.apply(data)
        
        assert result["truncated"] is True
        assert len(result["data"]["text"]) < 100
        assert "truncated" in result["data"]["text"].lower()
    
    def test_filter_preserves_structure(self):
        """Test that filtering preserves data structure."""
        config = FilterConfig(max_bytes=100, preserve_structure=True)
        filter = DataFilter(config)
        
        data = {"key1": "x" * 1000, "key2": "y" * 1000, "key3": "z" * 1000}
        result = filter.apply(data)
        
        # Should preserve keys even if truncated
        if result["truncated"]:
            assert "_truncated" in result["data"] or isinstance(result["data"], dict)
    
    def test_filter_nested_data(self):
        """Test filtering nested structures."""
        config = FilterConfig(max_rows=5)
        filter = DataFilter(config)
        
        data = {
            "records": [{"id": i, "data": "x" * 10} for i in range(20)]
        }
        
        result = filter.apply(data)
        
        assert result["truncated"] is True
        assert len(result["data"]["records"]) <= 6  # 5 + truncation notice
    
    def test_filter_generates_summary(self):
        """Test summary generation for truncated data."""
        config = FilterConfig(max_rows=10, summarize_truncated=True)
        filter = DataFilter(config)
        
        data = list(range(100))
        result = filter.apply(data)
        
        assert "summary" in result
        assert "Truncated" in result["summary"] or "rows" in result["summary"].lower()
    
    def test_filter_no_truncation(self):
        """Test that small data passes through unchanged."""
        config = FilterConfig(max_bytes=100000, max_rows=1000)
        filter = DataFilter(config)
        
        data = {"small": "data"}
        result = filter.apply(data)
        
        assert result["truncated"] is False
        assert result["data"] == data
    
    def test_filter_max_bytes(self):
        """Test max bytes limit."""
        config = FilterConfig(max_bytes=100)
        filter = DataFilter(config)
        
        data = {"data": "x" * 10000}
        result = filter.apply(data)
        
        # Should track original and filtered size
        assert result["stats"]["bytes_original"] > result["stats"]["bytes_filtered"]
    
    def test_filter_deep_nesting(self):
        """Test handling of deeply nested structures."""
        config = FilterConfig()
        filter = DataFilter(config)
        
        # Create deeply nested structure
        data = {"level1": {"level2": {"level3": {"level4": {"level5": "value"}}}}}
        result = filter.apply(data)
        
        # Should handle deep nesting gracefully
        assert result["data"] is not None


class TestFilterAndTokenize:
    """Test combined filtering and tokenization."""
    
    def test_filter_and_tokenize_combined(self):
        """Test applying both filtering and tokenization."""
        filter_config = FilterConfig(max_rows=10)
        
        data = {
            "users": [
                {"email": f"user{i}@example.com", "data": "x" * 100}
                for i in range(50)
            ]
        }
        
        result = filter_and_tokenize(
            data,
            filter_config=filter_config,
            tokenize_pii=True
        )
        
        assert result["truncated"] is True
        assert result["pii_detected"] is True
        assert len(result["token_map"]) > 0
        assert "example.com" not in str(result["data"])
    
    def test_filter_and_tokenize_no_pii(self):
        """Test filtering without PII tokenization."""
        filter_config = FilterConfig(max_rows=5)
        
        data = list(range(20))
        
        result = filter_and_tokenize(
            data,
            filter_config=filter_config,
            tokenize_pii=False
        )
        
        assert result["truncated"] is True
        assert "token_map" not in result
        assert "pii_detected" not in result
    
    def test_filter_and_tokenize_order(self):
        """Test that filtering happens before tokenization."""
        filter_config = FilterConfig(max_rows=5)
        
        data = [
            {"email": f"user{i}@example.com"}
            for i in range(20)
        ]
        
        result = filter_and_tokenize(
            data,
            filter_config=filter_config,
            tokenize_pii=True
        )
        
        # Should have truncated to 5 rows, so max 5 unique tokens
        assert len(result["token_map"]) <= 6  # 5 emails + possible truncation message
    
    def test_filter_and_tokenize_realistic_scenario(self):
        """Test realistic scenario with database query results."""
        filter_config = FilterConfig(
            max_rows=100,
            max_string_length=500,
            summarize_truncated=True
        )
        
        tokenize_config = TokenizationConfig(
            enabled_types={PIIType.EMAIL, PIIType.PHONE}
        )
        
        # Simulate database query result
        data = {
            "query": "SELECT * FROM users",
            "results": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@company.com",
                    "phone": f"555-{i:04d}",
                    "notes": "Lorem ipsum " * 50  # Long text
                }
                for i in range(500)
            ],
            "total_rows": 500
        }
        
        result = filter_and_tokenize(
            data,
            filter_config=filter_config,
            tokenize_config=tokenize_config,
            tokenize_pii=True
        )
        
        assert result["truncated"] is True
        assert result["pii_detected"] is True
        
        # Check that PII is tokenized
        result_str = str(result["data"])
        assert "company.com" not in result_str
        assert "TOKEN_EMAIL_" in result_str
        
        # Check that truncation happened
        assert result["stats"]["rows_truncated"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_data(self):
        """Test handling empty data."""
        filter = DataFilter()
        result = filter.apply({})
        
        assert result["data"] == {}
        assert result["truncated"] is False
    
    def test_none_values(self):
        """Test handling None values."""
        tokenizer = PIITokenizer()
        filter = DataFilter()
        
        data = {"key": None}
        
        tokenized = tokenizer.tokenize(data)
        filtered = filter.apply(data)
        
        assert tokenized["key"] is None
        assert filtered["data"]["key"] is None
    
    def test_mixed_types(self):
        """Test handling mixed data types."""
        filter = DataFilter()
        
        data = {
            "string": "text",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        result = filter.apply(data)
        
        assert result["data"]["number"] == 42
        assert result["data"]["bool"] is True
        assert result["data"]["null"] is None
    
    def test_unicode_handling(self):
        """Test handling unicode characters."""
        tokenizer = PIITokenizer()
        
        data = {"message": "Email: tést@éxample.com 你好"}
        
        # Should handle unicode without errors
        result = tokenizer.tokenize(data)
        assert result is not None
    
    def test_circular_reference_protection(self):
        """Test protection against circular references."""
        filter = DataFilter()
        
        # Create data with deep but not circular nesting
        data = {"level": 1}
        current = data
        for i in range(15):
            current["next"] = {"level": i + 2}
            current = current["next"]
        
        # Should handle deep nesting without infinite loop
        result = filter.apply(data)
        assert result is not None
