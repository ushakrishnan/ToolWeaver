"""
PII Detection and Response Filtering for Multi-Agent Security

Detects and redacts personally identifiable information (PII) in agent responses
to prevent data exfiltration and ensure GDPR/CCPA compliance.

Threats Mitigated:
- AS-4: PII Exfiltration (GDPR/CCPA violation)
- Data breach via compromised agents
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class PIIFinding:
    """A detected PII instance."""
    type: str
    match: str
    start: int
    end: int


class PIIDetector:
    """
    Detects personally identifiable information using regex patterns.

    Patterns:
    - SSN: 123-45-6789
    - Email: user@example.com
    - Credit Card: 4111-1111-1111-1111
    - Phone: (555) 123-4567, 555-123-4567
    - API Keys: sk-..., ghp_..., etc.

    Usage:
        detector = PIIDetector()
        findings = detector.scan("My SSN is 123-45-6789")
        # [PIIFinding(type='ssn', match='123-45-6789', ...)]

        redacted = detector.redact("My SSN is 123-45-6789")
        # "My SSN is [REDACTED_SSN]"
    """

    # Regex patterns for common PII types
    PATTERNS = {
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        'phone': re.compile(r'\b(\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b'),
        'openai_key': re.compile(r'\bsk-[A-Za-z0-9]{48}\b'),
        'github_token': re.compile(r'\bghp_[A-Za-z0-9]{36}\b'),
        'aws_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
        'jwt': re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b'),
    }

    def scan(self, text: str) -> list[PIIFinding]:
        """
        Scan text for PII instances.

        Args:
            text: Text to scan

        Returns:
            List of PII findings
        """
        findings = []

        for pii_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(PIIFinding(
                    type=pii_type,
                    match=match.group(),
                    start=match.start(),
                    end=match.end()
                ))

        # Sort by position for consistent processing
        findings.sort(key=lambda f: f.start)
        return findings

    def redact(self, text: str) -> str:
        """
        Redact all PII from text.

        Args:
            text: Text to redact

        Returns:
            Text with PII replaced by [REDACTED_TYPE]
        """
        findings = self.scan(text)

        # Replace from end to start to preserve positions
        result = text
        for finding in reversed(findings):
            redaction = f"[REDACTED_{finding.type.upper()}]"
            result = result[:finding.start] + redaction + result[finding.end:]

        return result

    def has_pii(self, text: str) -> bool:
        """
        Quick check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected
        """
        return len(self.scan(text)) > 0


class ResponseFilter:
    """
    Filters agent responses to remove sensitive data.

    Features:
    - Remove sensitive field keys (password, secret, token, etc.)
    - Redact PII in string values
    - Add metadata about what was filtered

    Usage:
        filter = ResponseFilter()
        response = {
            "result": "User email is user@example.com",
            "password": "secret123"
        }
        filtered = filter.filter_response(response)
        # {
        #   "result": "User email is [REDACTED_EMAIL]",
        #   "_field_pii_detected": ["password", "email"]
        # }
    """

    # Sensitive field names to remove
    SENSITIVE_KEYS = {
        'password', 'passwd', 'pwd',
        'secret', 'api_key', 'apikey', 'token',
        'private_key', 'access_token', 'refresh_token',
        'credit_card', 'ssn', 'social_security',
    }

    def __init__(self):
        self.pii_detector = PIIDetector()

    def filter_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Filter sensitive data from response dictionary.

        Args:
            response: Agent response dictionary

        Returns:
            Filtered response with metadata
        """
        if not isinstance(response, dict):
            # Handle non-dict responses
            if isinstance(response, str):
                return self.pii_detector.redact(response)
            return response

        filtered = {}
        removed_fields = []
        pii_types = []

        for key, value in response.items():
            # Check if key is sensitive
            if key.lower() in self.SENSITIVE_KEYS:
                removed_fields.append(key)
                continue

            # Recursively filter nested dicts
            if isinstance(value, dict):
                filtered[key] = self.filter_response(value)
            # Filter lists
            elif isinstance(value, list):
                filtered[key] = [
                    self.filter_response(item) if isinstance(item, dict)
                    else (self.pii_detector.redact(item) if isinstance(item, str) else item)
                    for item in value
                ]
            # Redact PII in strings
            elif isinstance(value, str):
                findings = self.pii_detector.scan(value)
                if findings:
                    pii_types.extend([f.type for f in findings])
                    filtered[key] = self.pii_detector.redact(value)
                else:
                    filtered[key] = value
            # Pass through other types
            else:
                filtered[key] = value

        # Add metadata about filtering
        if removed_fields or pii_types:
            metadata = []
            if removed_fields:
                metadata.extend(removed_fields)
            if pii_types:
                metadata.extend(set(pii_types))
            filtered['_field_pii_detected'] = sorted(set(metadata))

        return filtered

    def filter_string(self, text: str) -> tuple[str, list[str]]:
        """
        Filter PII from a string and return what was found.

        Args:
            text: String to filter

        Returns:
            Tuple of (filtered_text, pii_types_found)
        """
        findings = self.pii_detector.scan(text)
        pii_types = sorted({f.type for f in findings})

        if findings:
            filtered = self.pii_detector.redact(text)
            return filtered, pii_types

        return text, []
