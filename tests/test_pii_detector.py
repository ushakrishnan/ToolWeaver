"""
Tests for PII detection and response filtering.
"""

import pytest
from orchestrator._internal.security.pii_detector import (
    PIIDetector,
    ResponseFilter,
    PIIFinding,
)


class TestPIIDetector:
    """Test PII detection patterns."""
    
    def test_ssn_detection(self):
        """Test SSN pattern detection."""
        detector = PIIDetector()
        
        findings = detector.scan("My SSN is 123-45-6789")
        
        assert len(findings) == 1
        assert findings[0].type == 'ssn'
        assert findings[0].match == '123-45-6789'
    
    def test_email_detection(self):
        """Test email pattern detection."""
        detector = PIIDetector()
        
        findings = detector.scan("Contact me at user@example.com")
        
        assert len(findings) == 1
        assert findings[0].type == 'email'
        assert findings[0].match == 'user@example.com'
    
    def test_credit_card_detection(self):
        """Test credit card pattern detection."""
        detector = PIIDetector()
        
        # With dashes
        findings1 = detector.scan("Card: 4111-1111-1111-1111")
        assert len(findings1) == 1
        assert findings1[0].type == 'credit_card'
        
        # Without dashes
        findings2 = detector.scan("Card: 4111111111111111")
        assert len(findings2) == 1
        assert findings2[0].type == 'credit_card'
    
    def test_phone_detection(self):
        """Test phone number pattern detection."""
        detector = PIIDetector()
        
        # Various formats
        test_cases = [
            "(555) 123-4567",
            "555-123-4567",
            "5551234567",
            "+1-555-123-4567",
        ]
        
        for phone in test_cases:
            findings = detector.scan(f"Call {phone}")
            assert len(findings) >= 1, f"Failed to detect: {phone}"
            assert any(f.type == 'phone' for f in findings)
    
    def test_openai_key_detection(self):
        """Test OpenAI API key detection."""
        detector = PIIDetector()
        
        fake_key = "sk-" + "a" * 48
        findings = detector.scan(f"Key: {fake_key}")
        
        assert len(findings) == 1
        assert findings[0].type == 'openai_key'
    
    def test_github_token_detection(self):
        """Test GitHub token detection."""
        detector = PIIDetector()
        
        fake_token = "ghp_" + "a" * 36
        findings = detector.scan(f"Token: {fake_token}")
        
        assert len(findings) == 1
        assert findings[0].type == 'github_token'
    
    def test_aws_key_detection(self):
        """Test AWS access key detection."""
        detector = PIIDetector()
        
        fake_key = "AKIAIOSFODNN7EXAMPLE"
        findings = detector.scan(f"AWS Key: {fake_key}")
        
        assert len(findings) == 1
        assert findings[0].type == 'aws_key'
    
    def test_jwt_detection(self):
        """Test JWT token detection."""
        detector = PIIDetector()
        
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        findings = detector.scan(f"JWT: {fake_jwt}")
        
        assert len(findings) == 1
        assert findings[0].type == 'jwt'
    
    def test_multiple_pii_detection(self):
        """Test detecting multiple PII types in one text."""
        detector = PIIDetector()
        
        text = "Email user@test.com and SSN 123-45-6789"
        findings = detector.scan(text)
        
        assert len(findings) == 2
        types = {f.type for f in findings}
        assert 'email' in types
        assert 'ssn' in types
    
    def test_no_pii(self):
        """Test text without PII."""
        detector = PIIDetector()
        
        findings = detector.scan("This is safe text with no PII")
        
        assert len(findings) == 0
    
    def test_has_pii_method(self):
        """Test has_pii quick check."""
        detector = PIIDetector()
        
        assert detector.has_pii("SSN: 123-45-6789") is True
        assert detector.has_pii("Safe text") is False


class TestPIIRedaction:
    """Test PII redaction functionality."""
    
    def test_ssn_redaction(self):
        """Test SSN redaction."""
        detector = PIIDetector()
        
        redacted = detector.redact("My SSN is 123-45-6789")
        
        assert "123-45-6789" not in redacted
        assert "[REDACTED_SSN]" in redacted
        assert "My SSN is" in redacted
    
    def test_email_redaction(self):
        """Test email redaction."""
        detector = PIIDetector()
        
        redacted = detector.redact("Email: user@example.com")
        
        assert "user@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
    
    def test_api_key_redaction(self):
        """Test API key redaction."""
        detector = PIIDetector()
        
        fake_key = "sk-" + "a" * 48
        redacted = detector.redact(f"API Key: {fake_key}")
        
        assert fake_key not in redacted
        assert "[REDACTED_OPENAI_KEY]" in redacted
    
    def test_multiple_pii_redaction(self):
        """Test redacting multiple PII instances."""
        detector = PIIDetector()
        
        text = "Contact user@test.com or call 555-123-4567"
        redacted = detector.redact(text)
        
        assert "user@test.com" not in redacted
        assert "555-123-4567" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "[REDACTED_PHONE]" in redacted
        assert "Contact" in redacted
        assert "or call" in redacted
    
    def test_redaction_preserves_structure(self):
        """Test that redaction preserves text structure."""
        detector = PIIDetector()
        
        original = "Name: John, Email: john@test.com, Phone: 555-1234"
        redacted = detector.redact(original)
        
        assert "Name: John" in redacted
        assert "Email:" in redacted
        assert "Phone:" in redacted
        assert "john@test.com" not in redacted


class TestResponseFilter:
    """Test response filtering functionality."""
    
    def test_filter_sensitive_keys(self):
        """Test removal of sensitive field keys."""
        filter = ResponseFilter()
        
        response = {
            "result": "success",
            "password": "secret123",
            "api_key": "key123",
        }
        
        filtered = filter.filter_response(response)
        
        assert "result" in filtered
        assert "password" not in filtered
        assert "api_key" not in filtered
        assert "_field_pii_detected" in filtered
        assert "password" in filtered["_field_pii_detected"]
    
    def test_filter_pii_in_values(self):
        """Test PII redaction in string values."""
        filter = ResponseFilter()
        
        response = {
            "message": "User email is user@example.com"
        }
        
        filtered = filter.filter_response(response)
        
        assert "user@example.com" not in filtered["message"]
        assert "[REDACTED_EMAIL]" in filtered["message"]
        assert "email" in filtered["_field_pii_detected"]
    
    def test_filter_nested_dict(self):
        """Test filtering nested dictionaries."""
        filter = ResponseFilter()
        
        response = {
            "user": {
                "name": "John",
                "email": "john@test.com",
                "password": "secret"
            }
        }
        
        filtered = filter.filter_response(response)
        
        assert "name" in filtered["user"]
        assert "password" not in filtered["user"]
        assert "[REDACTED_EMAIL]" in filtered["user"]["email"]
    
    def test_filter_list_values(self):
        """Test filtering lists."""
        filter = ResponseFilter()
        
        response = {
            "emails": ["user1@test.com", "user2@test.com"]
        }
        
        filtered = filter.filter_response(response)
        
        assert "user1@test.com" not in filtered["emails"][0]
        assert "[REDACTED_EMAIL]" in filtered["emails"][0]
    
    def test_filter_string_response(self):
        """Test filtering non-dict response."""
        filter = ResponseFilter()
        
        response = "My SSN is 123-45-6789"
        filtered = filter.filter_response(response)
        
        assert "123-45-6789" not in filtered
        assert "[REDACTED_SSN]" in filtered
    
    def test_filter_passthrough_types(self):
        """Test that non-sensitive types pass through."""
        filter = ResponseFilter()
        
        response = {
            "count": 42,
            "enabled": True,
            "items": [1, 2, 3]
        }
        
        filtered = filter.filter_response(response)
        
        assert filtered["count"] == 42
        assert filtered["enabled"] is True
        assert filtered["items"] == [1, 2, 3]
    
    def test_no_metadata_when_clean(self):
        """Test that clean responses don't get metadata."""
        filter = ResponseFilter()
        
        response = {
            "message": "All good",
            "status": "ok"
        }
        
        filtered = filter.filter_response(response)
        
        assert "_field_pii_detected" not in filtered
    
    def test_filter_string_method(self):
        """Test filter_string helper method."""
        filter = ResponseFilter()
        
        text = "Email: user@test.com and SSN: 123-45-6789"
        filtered, pii_types = filter.filter_string(text)
        
        assert "user@test.com" not in filtered
        assert "123-45-6789" not in filtered
        assert "email" in pii_types
        assert "ssn" in pii_types


class TestEdgeCases:
    """Test edge cases and unusual inputs."""
    
    def test_empty_string(self):
        """Test empty string handling."""
        detector = PIIDetector()
        
        findings = detector.scan("")
        assert len(findings) == 0
        
        redacted = detector.redact("")
        assert redacted == ""
    
    def test_none_values_in_response(self):
        """Test None value handling."""
        filter = ResponseFilter()
        
        response = {
            "result": None,
            "message": "test"
        }
        
        filtered = filter.filter_response(response)
        assert filtered["result"] is None
    
    def test_overlapping_patterns(self):
        """Test handling of overlapping PII patterns."""
        detector = PIIDetector()
        
        # Should detect email, not mistake it for something else
        text = "admin@company.com"
        findings = detector.scan(text)
        
        assert len(findings) == 1
        assert findings[0].type == 'email'
    
    def test_case_insensitive_keys(self):
        """Test case-insensitive sensitive key matching."""
        filter = ResponseFilter()
        
        response = {
            "PASSWORD": "secret",
            "Api_Key": "key123"
        }
        
        filtered = filter.filter_response(response)
        
        assert "PASSWORD" not in filtered
        assert "Api_Key" not in filtered
