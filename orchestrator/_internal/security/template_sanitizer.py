"""
Template Sanitization for LLM Prompts

Prevents prompt injection attacks where malicious user input manipulates
LLM behavior through template strings.

Threats Mitigated:
- AS-5: Prompt Injection (malicious instructions in user input)
- Jailbreak attempts (bypass safety guardrails)
- Context hijacking (redirect LLM to unintended tasks)
"""

import re
from re import Pattern

from orchestrator._internal.errors import ToolWeaverError


class PromptInjectionError(ToolWeaverError):
    """Raised when prompt injection attempt is detected."""
    pass


class TemplateSanitizer:
    """
    Detects and blocks prompt injection attacks in template strings.

    Patterns blocked:
    - "Ignore previous instructions"
    - "Disregard all prior"
    - "Forget everything above"
    - Role hijacking ("You are now...", "Act as...")
    - System prompt leakage attempts
    - Encoding tricks (base64, hex, unicode)
    - Multi-language variations

    Usage:
        sanitizer = TemplateSanitizer()

        # Check for injection attempts
        try:
            sanitizer.validate("User query: list files")  # OK
        except PromptInjectionError:
            # Block the request
            pass

        # Get sanitized version (strips suspicious content)
        safe = sanitizer.sanitize("Ignore previous instructions\\nList files")
        # Result: "List files"
    """

    # LLM Injection patterns (case-insensitive)
    LLM_INJECTION_PATTERNS: list[tuple[str, Pattern]] = [
        # Direct instruction override
        ('IGNORE_INSTRUCTIONS', re.compile(r'ignore\s+(previous|prior|all|above)\s+(instructions?|commands?|prompts?)', re.IGNORECASE)),
        ('IGNORE_ALL', re.compile(r'ignore\s+all(?!\s+(?:of|the))\b', re.IGNORECASE)),
        ('DISREGARD_INSTRUCTIONS', re.compile(r'disregard\s+(previous|prior|all|above|everything)', re.IGNORECASE)),
        ('FORGET_INSTRUCTIONS', re.compile(r'forget\s+(previous|prior|all|above|everything)', re.IGNORECASE)),

        # Role hijacking (avoid false positives like 'you are now viewing')
        ('ROLE_CHANGE', re.compile(r'(you\s+are\s+now\s+(a|an|the)\s+(admin|hacker|assistant|bot|system)|act\s+as\s+(a|an)|pretend\s+to\s+be|simulate\s+(a|an))', re.IGNORECASE)),
        ('NEW_ROLE', re.compile(r'(new\s+role|change\s+role|switch\s+to)', re.IGNORECASE)),

        # System prompt manipulation
        ('SYSTEM_PROMPT', re.compile(r'(system\s+prompt|system\s+message|initial\s+prompt)', re.IGNORECASE)),
        ('REVEAL_PROMPT', re.compile(r'(show|reveal|display|print)\s+(the\s+)?(system\s+)?prompt', re.IGNORECASE)),
        ('PROMPT_INJECTION', re.compile(r'prompt\s+injection', re.IGNORECASE)),

        # Context hijacking
        ('START_OVER', re.compile(r'(start\s+over|reset\s+context|new\s+conversation|clear\s+history)', re.IGNORECASE)),
        ('END_SESSION', re.compile(r'(end\s+of\s+prompt|end\s+of\s+instructions|###|---\s*end)', re.IGNORECASE)),

        # Encoding tricks
        ('BASE64_DECODE', re.compile(r'(base64|b64)\s*decode', re.IGNORECASE)),
        ('HEX_DECODE', re.compile(r'hex\s*decode', re.IGNORECASE)),
        ('ROT13', re.compile(r'rot13|rot-13', re.IGNORECASE)),

        # Delimiter tricks
        ('TRIPLE_QUOTES', re.compile(r'""".*?"""', re.DOTALL)),
        ('COMMENT_BLOCKS', re.compile(r'/\*.*?\*/', re.DOTALL)),
        ('MARKDOWN_CODE', re.compile(r'```[a-z]*\s+ignore', re.IGNORECASE)),

        # Multi-language variations
        ('SPANISH_IGNORE', re.compile(r'ignorar\s+(instrucciones|todo)', re.IGNORECASE)),
        ('FRENCH_IGNORE', re.compile(r'ignorer\s+(instructions|tout)', re.IGNORECASE)),
        ('GERMAN_IGNORE', re.compile(r'ignorieren\s+sie', re.IGNORECASE)),

        # Jailbreak patterns
        ('JAILBREAK', re.compile(r'(jailbreak|dan\s+mode|developer\s+mode)', re.IGNORECASE)),
        ('BYPASS', re.compile(r'bypass\s+(safety|guardrails|filters?)', re.IGNORECASE)),

        # Command injection in prompts
        ('EXECUTE_CODE', re.compile(r'(execute|run|eval)\s+(this|the\s+following)\s+(code|command|script)', re.IGNORECASE)),

        # Continuation tricks
        ('CONTINUE_AS', re.compile(r'continue\s+(as|with|in)', re.IGNORECASE)),
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize template sanitizer.

        Args:
            strict_mode: If True, raises error on detection. If False, sanitizes silently.
        """
        self.strict_mode = strict_mode

    def validate(self, text: str) -> None:
        """
        Validate that text contains no injection attempts.

        Args:
            text: Text to validate

        Raises:
            PromptInjectionError: If injection pattern detected
        """
        for pattern_name, pattern in self.LLM_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                raise PromptInjectionError(
                    f"Prompt injection detected: {pattern_name}\n"
                    f"Matched: {match.group()}\n"
                    f"This input contains potentially malicious instructions."
                )

    def sanitize(self, text: str) -> str:
        """
        Remove injection patterns from text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with injection patterns removed
        """
        result = text

        for _pattern_name, pattern in self.LLM_INJECTION_PATTERNS:
            result = pattern.sub('', result)

        # Clean up extra whitespace
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()

        return result

    def check_and_sanitize(self, text: str) -> tuple[str, list[str]]:
        """
        Check for injections and return sanitized text with list of detections.

        Args:
            text: Text to check

        Returns:
            Tuple of (sanitized_text, list_of_detected_patterns)
        """
        detected = []
        result = text

        for pattern_name, pattern in self.LLM_INJECTION_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                detected.append(pattern_name)
                result = pattern.sub('', result)

        # Clean up extra whitespace
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()

        return result, detected

    def is_safe(self, text: str) -> bool:
        """
        Check if text is safe (no injection patterns).

        Args:
            text: Text to check

        Returns:
            True if safe, False if injection detected
        """
        try:
            self.validate(text)
            return True
        except PromptInjectionError:
            return False


# Global instance for convenience
_default_sanitizer = TemplateSanitizer()


def validate_template(text: str) -> None:
    """
    Validate template string (raises on injection).

    Args:
        text: Template string to validate

    Raises:
        PromptInjectionError: If injection detected
    """
    _default_sanitizer.validate(text)


def sanitize_template(text: str) -> str:
    """
    Sanitize template string (removes injections).

    Args:
        text: Template string to sanitize

    Returns:
        Sanitized string
    """
    return _default_sanitizer.sanitize(text)


def is_template_safe(text: str) -> bool:
    """
    Check if template is safe.

    Args:
        text: Template string to check

    Returns:
        True if safe, False otherwise
    """
    return _default_sanitizer.is_safe(text)
