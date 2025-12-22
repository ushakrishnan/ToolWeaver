"""
Sandbox Data Filtering & PII Tokenization

Provides utilities for filtering, transforming, and sanitizing data before
returning to the model. Reduces token usage and protects sensitive information.

Features:
- Output size limiting with intelligent truncation
- PII detection and tokenization (email, phone, SSN, credit cards, names)
- Data aggregation and summarization
- Configurable filtering rules

Usage:
    from orchestrator._internal.execution import DataFilter, PIITokenizer
    
    # Filter large output
    filter = DataFilter(max_bytes=10000, max_rows=100)
    filtered = filter.apply(large_data)
    
    # Tokenize PII
    tokenizer = PIITokenizer()
    sanitized = tokenizer.tokenize(data_with_pii)
    token_map = tokenizer.get_token_map()  # For detokenization
"""

import re
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected and tokenized."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"


@dataclass
class FilterConfig:
    """Configuration for data filtering."""
    max_bytes: Optional[int] = 50000  # 50KB max output
    max_rows: Optional[int] = 1000  # Max rows for tabular data
    max_items: Optional[int] = 1000  # Max items for lists/arrays
    truncate_strings: bool = True
    max_string_length: int = 1000  # Max length for individual strings
    summarize_truncated: bool = True  # Include summary of truncated data
    preserve_structure: bool = True  # Keep data structure (keys, types)


@dataclass
class TokenizationConfig:
    """Configuration for PII tokenization."""
    enabled_types: Set[PIIType] = field(default_factory=lambda: {
        PIIType.EMAIL,
        PIIType.PHONE,
        PIIType.SSN,
        PIIType.CREDIT_CARD,
    })
    token_prefix: str = "TOKEN_"
    preserve_format: bool = True  # Keep token format similar to original
    case_sensitive: bool = False


class PIITokenizer:
    """Detects and tokenizes PII in data structures.
    
    Example:
        tokenizer = PIITokenizer()
        data = {"email": "user@example.com", "phone": "555-1234"}
        sanitized = tokenizer.tokenize(data)
        # {"email": "TOKEN_EMAIL_a1b2c3", "phone": "TOKEN_PHONE_d4e5f6"}
        
        # Later, detokenize if needed
        original = tokenizer.detokenize(sanitized)
    """
    
    # PII detection patterns
    PATTERNS = {
        PIIType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        PIIType.PHONE: re.compile(
            r'\b(?:\+?1[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b'
        ),
        PIIType.SSN: re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ),
    }
    
    def __init__(self, config: Optional[TokenizationConfig] = None):
        self.config = config or TokenizationConfig()
        self._token_map: Dict[str, str] = {}  # token -> original
        self._reverse_map: Dict[str, str] = {}  # original -> token
    
    def tokenize(self, data: Any) -> Any:
        """Tokenize PII in data structure.
        
        Args:
            data: Data to tokenize (dict, list, str, or primitive)
        
        Returns:
            Data with PII replaced by tokens
        """
        if isinstance(data, dict):
            return {k: self.tokenize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.tokenize(item) for item in data]
        elif isinstance(data, str):
            return self._tokenize_string(data)
        else:
            return data
    
    def _tokenize_string(self, text: str) -> str:
        """Tokenize PII in a string."""
        result = text
        
        for pii_type in self.config.enabled_types:
            if pii_type not in self.PATTERNS:
                continue
            
            pattern = self.PATTERNS[pii_type]
            
            # Find all matches and their full text
            for match in pattern.finditer(result):
                original = match.group(0)  # Get the full matched text
                token = self._get_or_create_token(original, pii_type)
                result = result.replace(original, token)
        
        return result
    
    def _get_or_create_token(self, original: str, pii_type: PIIType) -> str:
        """Get existing token or create new one."""
        if original in self._reverse_map:
            return self._reverse_map[original]
        
        # Create deterministic token from hash
        hash_val = hashlib.sha256(original.encode()).hexdigest()[:8]
        token = f"{self.config.token_prefix}{pii_type.value.upper()}_{hash_val}"
        
        self._token_map[token] = original
        self._reverse_map[original] = token
        
        return token
    
    def detokenize(self, data: Any) -> Any:
        """Restore original values from tokens.
        
        Args:
            data: Tokenized data
        
        Returns:
            Data with tokens replaced by original values
        """
        if isinstance(data, dict):
            return {k: self.detokenize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.detokenize(item) for item in data]
        elif isinstance(data, str):
            result = data
            for token, original in self._token_map.items():
                result = result.replace(token, original)
            return result
        else:
            return data
    
    def get_token_map(self) -> Dict[str, str]:
        """Get mapping of tokens to original values."""
        return self._token_map.copy()
    
    def clear_tokens(self):
        """Clear all stored tokens."""
        self._token_map.clear()
        self._reverse_map.clear()


class DataFilter:
    """Filters and truncates data to reduce token usage.
    
    Example:
        filter = DataFilter(max_bytes=10000, max_rows=100)
        large_data = {"records": [...1000 records...]}
        filtered = filter.apply(large_data)
        # Returns truncated data + summary
    """
    
    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()
        self.stats = {
            "bytes_original": 0,
            "bytes_filtered": 0,
            "rows_truncated": 0,
            "items_truncated": 0,
            "strings_truncated": 0,
        }
    
    def apply(self, data: Any) -> Dict[str, Any]:
        """Apply filtering to data.
        
        Returns:
            Dict with:
            - data: Filtered data
            - truncated: Whether truncation occurred
            - stats: Truncation statistics
            - summary: Human-readable summary
        """
        import json
        
        # Track original size
        try:
            self.stats["bytes_original"] = len(json.dumps(data))
        except Exception:
            self.stats["bytes_original"] = len(str(data))
        
        # Apply filtering
        filtered_data = self._filter_recursive(data)
        
        # Track filtered size
        try:
            self.stats["bytes_filtered"] = len(json.dumps(filtered_data))
        except Exception:
            self.stats["bytes_filtered"] = len(str(filtered_data))
        
        truncated = any(v > 0 for k, v in self.stats.items() if k.endswith("_truncated"))
        
        result = {
            "data": filtered_data,
            "truncated": truncated,
            "stats": self.stats.copy(),
        }
        
        if truncated and self.config.summarize_truncated:
            result["summary"] = self._generate_summary()
        
        return result
    
    def _filter_recursive(self, data: Any, depth: int = 0) -> Any:
        """Recursively filter data structure."""
        if depth > 10:  # Prevent infinite recursion
            return "...[max depth exceeded]"
        
        if isinstance(data, dict):
            return self._filter_dict(data, depth)
        elif isinstance(data, list):
            return self._filter_list(data, depth)
        elif isinstance(data, str):
            return self._filter_string(data)
        else:
            return data
    
    def _filter_dict(self, data: Dict, depth: int) -> Dict:
        """Filter dictionary, preserving structure."""
        if self.config.max_bytes:
            # Check if we're over budget
            import json
            try:
                current_size = len(json.dumps(data))
                if current_size > self.config.max_bytes:
                    # Truncate to summary if preserve_structure
                    if self.config.preserve_structure:
                        return {
                            "_truncated": True,
                            "_keys": list(data.keys())[:20],
                            "_size": len(data),
                            "_sample": {k: self._filter_recursive(v, depth + 1) 
                                      for k, v in list(data.items())[:5]}
                        }
            except Exception:
                pass
        
        return {k: self._filter_recursive(v, depth + 1) for k, v in data.items()}
    
    def _filter_list(self, data: List, depth: int) -> List:
        """Filter list, truncating if needed."""
        if self.config.max_rows and len(data) > self.config.max_rows:
            self.stats["rows_truncated"] = len(data) - self.config.max_rows
            truncated = data[:self.config.max_rows]
            
            if self.config.summarize_truncated:
                return truncated + [{
                    "_truncated": True,
                    "_total_rows": len(data),
                    "_showing": self.config.max_rows,
                    "_omitted": len(data) - self.config.max_rows
                }]
            return truncated
        
        return [self._filter_recursive(item, depth + 1) for item in data]
    
    def _filter_string(self, text: str) -> str:
        """Filter string, truncating if needed."""
        if self.config.truncate_strings and len(text) > self.config.max_string_length:
            self.stats["strings_truncated"] += 1
            truncated = text[:self.config.max_string_length]
            if self.config.summarize_truncated:
                return f"{truncated}... [truncated {len(text) - self.config.max_string_length} chars]"
            return truncated
        return text
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary of filtering."""
        parts = []
        
        if self.stats["bytes_original"] > 0:
            reduction = 100 * (1 - self.stats["bytes_filtered"] / self.stats["bytes_original"])
            parts.append(f"Reduced output by {reduction:.1f}%")
        
        if self.stats["rows_truncated"] > 0:
            parts.append(f"Truncated {self.stats['rows_truncated']} rows")
        
        if self.stats["strings_truncated"] > 0:
            parts.append(f"Truncated {self.stats['strings_truncated']} strings")
        
        return "; ".join(parts) if parts else "No truncation applied"


def filter_and_tokenize(
    data: Any,
    filter_config: Optional[FilterConfig] = None,
    tokenize_config: Optional[TokenizationConfig] = None,
    tokenize_pii: bool = True,
) -> Dict[str, Any]:
    """Convenience function to filter and tokenize data in one call.
    
    Args:
        data: Data to process
        filter_config: Filter configuration
        tokenize_config: Tokenization configuration
        tokenize_pii: Whether to tokenize PII (default: True)
    
    Returns:
        Dict with:
        - data: Processed data
        - truncated: Whether truncation occurred
        - stats: Processing statistics
        - token_map: PII token mapping (if tokenization enabled)
    
    Example:
        result = filter_and_tokenize(large_data, tokenize_pii=True)
        processed_data = result["data"]
        token_map = result.get("token_map", {})
    """
    # Apply filtering first
    data_filter = DataFilter(filter_config)
    result = data_filter.apply(data)
    
    # Then tokenize PII if enabled
    if tokenize_pii:
        tokenizer = PIITokenizer(tokenize_config)
        result["data"] = tokenizer.tokenize(result["data"])
        result["token_map"] = tokenizer.get_token_map()
        result["pii_detected"] = len(tokenizer.get_token_map()) > 0
    
    return result
