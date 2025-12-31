"""
Input validation and sanitization for ToolWeaver.

Phase 0.m: Security-focused validation to prevent injection attacks,
validate LLM-generated parameters, and ensure safe execution.

Features:
- String sanitization (SQL injection, XSS, etc.)
- File path validation (path traversal prevention)
- URL validation (safe protocols only)
- Code validation (basic AST checks)
- Parameter validation against Pydantic schemas
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError

from orchestrator._internal.errors import ToolWeaverError
from orchestrator._internal.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# Validation Errors
# ============================================================

class ValidationErrorBase(ToolWeaverError):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationErrorBase):
    """Input failed validation."""
    pass


class UnsafeInputError(ValidationErrorBase):
    """Input contains potentially dangerous content."""
    pass


class PathTraversalError(ValidationErrorBase):
    """File path attempts directory traversal."""
    pass


class UnsafeURLError(ValidationErrorBase):
    """URL uses unsafe protocol or destination."""
    pass


class InvalidCodeError(ValidationErrorBase):
    """Code contains dangerous constructs."""
    pass


# ============================================================
# String Sanitization
# ============================================================

# Dangerous patterns that might indicate injection attempts
DANGEROUS_PATTERNS = [
    r";\s*rm\s+-rf",           # Shell rm -rf
    r";\s*del\s+",             # Windows delete
    r"\$\(.*\)",               # Shell command substitution
    r"`.*`",                   # Shell backticks
    r"<script",                # XSS script tag
    r"javascript:",            # XSS javascript protocol
    r"on\w+\s*=",              # HTML event handlers
    r"--",                     # SQL comment
    r";\s*DROP\s+",            # SQL DROP command
    r"UNION\s+SELECT",         # SQL injection
    r"\.\./",                  # Path traversal
    r"\.\.\\",                 # Windows path traversal
]

DANGEROUS_REGEX = re.compile("|".join(DANGEROUS_PATTERNS), re.IGNORECASE)


# ============================================================
# Tool Schemas (Pydantic)
# ============================================================

class ToolParameter(BaseModel):
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type, e.g., string, number, object")
    required: bool = Field(default=False, description="Whether the parameter is required")
    description: str | None = Field(default=None, description="Human-readable description")
    default: object | None = Field(default=None, description="Default value, if any")


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Tool name (unique)")
    description: str = Field(..., description="Short description of the tool")
    parameters: list[ToolParameter] = Field(default_factory=list, description="List of parameters")
    domain: str | None = Field(default=None, description="Optional domain/category")
    version: str | None = Field(default=None, description="Optional version tag")
    tags: list[str] | None = Field(default=None, description="Optional tags for discovery")


def sanitize_string(
    input_str: str,
    max_length: int = 10000,
    allow_newlines: bool = True,
    allow_special_chars: bool = True
) -> str:
    """
    Sanitize string input by removing dangerous patterns.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters
        allow_special_chars: Whether to allow special characters
        
    Returns:
        Sanitized string
        
    Raises:
        InvalidInputError: If input is too long
        UnsafeInputError: If dangerous patterns detected
        
    Example:
        >>> sanitize_string("Hello, world!")
        'Hello, world!'
        
        >>> sanitize_string("; rm -rf /")
        UnsafeInputError: Dangerous pattern detected: ; rm -rf
    """
    if not isinstance(input_str, str):
        raise InvalidInputError(f"Expected string, got {type(input_str)}")

    # Check length
    if len(input_str) > max_length:
        raise InvalidInputError(
            f"Input too long: {len(input_str)} > {max_length} characters"
        )

    # Check for dangerous patterns
    match = DANGEROUS_REGEX.search(input_str)
    if match:
        raise UnsafeInputError(
            f"Dangerous pattern detected: {match.group()}\n"
            f"Input may contain injection attack or unsafe command."
        )

    # Remove newlines if not allowed
    if not allow_newlines:
        input_str = input_str.replace("\n", "").replace("\r", "")

    # Remove special chars if not allowed
    if not allow_special_chars:
        input_str = re.sub(r"[^\w\s.-]", "", input_str)

    return input_str


def sanitize_dict(
    input_dict: dict[str, Any],
    max_keys: int = 100,
    max_depth: int = 10
) -> dict[str, Any]:
    """
    Recursively sanitize dictionary values.
    
    Args:
        input_dict: Input dictionary
        max_keys: Maximum number of keys allowed
        max_depth: Maximum nesting depth
        
    Returns:
        Sanitized dictionary
        
    Raises:
        InvalidInputError: If dict too large or too deep
        
    Example:
        >>> sanitize_dict({"name": "test", "cmd": "ls"})
        {'name': 'test', 'cmd': 'ls'}
    """
    if not isinstance(input_dict, dict):
        raise InvalidInputError(f"Expected dict, got {type(input_dict)}")

    if len(input_dict) > max_keys:
        raise InvalidInputError(
            f"Dictionary too large: {len(input_dict)} > {max_keys} keys"
        )

    def _sanitize_recursive(obj: Any, depth: int = 0) -> Any:
        if depth > max_depth:
            raise InvalidInputError(f"Dictionary too deeply nested (depth > {max_depth})")

        if isinstance(obj, dict):
            return {
                sanitize_string(str(k), max_length=1000): _sanitize_recursive(v, depth + 1)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [_sanitize_recursive(item, depth + 1) for item in obj]
        elif isinstance(obj, str):
            return sanitize_string(obj)
        else:
            return obj

    result: dict[str, Any] = _sanitize_recursive(input_dict)
    return result


# ============================================================
# File Path Validation
# ============================================================


def validate_file_path(
    file_path: str | Path,
    base_dir: str | Path | None = None,
    must_exist: bool = False,
    allow_symlinks: bool = False
) -> Path:
    """
    Validate file path and prevent directory traversal attacks.
    
    Args:
        file_path: Path to validate
        base_dir: Base directory that path must be within
        must_exist: If True, path must exist
        allow_symlinks: If False, reject symbolic links
        
    Returns:
        Resolved absolute path
        
    Raises:
        PathTraversalError: If path attempts traversal
        InvalidInputError: If path doesn't exist (when must_exist=True)
        
    Example:
        >>> validate_file_path("data/file.txt", base_dir="/app")
        PosixPath('/app/data/file.txt')
        
        >>> validate_file_path("../../../etc/passwd", base_dir="/app")
        PathTraversalError: Path traversal detected
    """
    if not isinstance(file_path, (str, Path)):
        raise InvalidInputError(f"Expected str or Path, got {type(file_path)}")

    path = Path(file_path).resolve()

    # Check for symlinks
    if not allow_symlinks and path.is_symlink():
        raise PathTraversalError(
            f"Symbolic links not allowed: {file_path}"
        )

    # Check base directory constraint
    if base_dir is not None:
        base = Path(base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected: {file_path} is outside {base_dir}"
            )

    # Check existence
    if must_exist and not path.exists():
        raise InvalidInputError(f"Path does not exist: {file_path}")

    return path


# ============================================================
# URL Validation
# ============================================================

SAFE_URL_SCHEMES = {"http", "https", "ftp", "ftps"}


def validate_url(
    url: str,
    allowed_schemes: set[str] | None = None,
    block_private_ips: bool = True
) -> str:
    """
    Validate URL and ensure it uses safe protocols.
    
    Args:
        url: URL to validate
        allowed_schemes: Set of allowed schemes (default: http, https)
        block_private_ips: If True, block private/local IPs
        
    Returns:
        Validated URL
        
    Raises:
        UnsafeURLError: If URL uses unsafe scheme or targets private IP
        
    Example:
        >>> validate_url("https://example.com/api")
        'https://example.com/api'
        
        >>> validate_url("file:///etc/passwd")
        UnsafeURLError: Unsafe URL scheme: file
    """
    if not isinstance(url, str):
        raise InvalidInputError(f"Expected string, got {type(url)}")

    if allowed_schemes is None:
        allowed_schemes = SAFE_URL_SCHEMES

    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in allowed_schemes:
        raise UnsafeURLError(
            f"Unsafe URL scheme: {parsed.scheme}\n"
            f"Allowed schemes: {', '.join(allowed_schemes)}"
        )

    # Check for private IPs (basic check)
    if block_private_ips:
        hostname = parsed.hostname
        if hostname:
            # Block localhost and common private ranges
            if hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
                raise UnsafeURLError(f"Localhost access not allowed: {url}")

            # Block private IP ranges (basic check)
            if (hostname.startswith("192.168.") or
                hostname.startswith("10.") or
                hostname.startswith("172.16.") or
                hostname.startswith("172.17.") or
                hostname.startswith("172.18.") or
                hostname.startswith("172.19.") or
                hostname.startswith("172.20.") or
                hostname.startswith("172.21.") or
                hostname.startswith("172.22.") or
                hostname.startswith("172.23.") or
                hostname.startswith("172.24.") or
                hostname.startswith("172.25.") or
                hostname.startswith("172.26.") or
                hostname.startswith("172.27.") or
                hostname.startswith("172.28.") or
                hostname.startswith("172.29.") or
                hostname.startswith("172.30.") or
                hostname.startswith("172.31.")):
                raise UnsafeURLError(f"Private IP access not allowed: {url}")

    return url


# ============================================================
# Code Validation
# ============================================================

# Dangerous AST node types
DANGEROUS_AST_NODES = {
    ast.Import,        # import statements
    ast.ImportFrom,    # from X import Y
    ast.Global,        # global keyword
}

# Dangerous function calls
DANGEROUS_FUNCTIONS = {
    "eval", "exec", "compile", "__import__",
    "open", "file",  # File I/O
    "input", "raw_input",  # User input
    "os.system", "subprocess.call", "subprocess.run",  # Command execution
    "pickle.loads", "pickle.load",  # Unsafe deserialization
}


def validate_code(
    code: str,
    allow_imports: bool = False,
    allow_file_io: bool = False,
    max_length: int = 50000
) -> str:
    """
    Validate Python code for dangerous constructs.
    
    Args:
        code: Python code to validate
        allow_imports: If False, reject import statements
        allow_file_io: If False, reject file I/O operations
        max_length: Maximum code length
        
    Returns:
        Validated code
        
    Raises:
        InvalidCodeError: If code contains dangerous constructs
        
    Example:
        >>> validate_code("x = 1 + 2")
        'x = 1 + 2'
        
        >>> validate_code("import os; os.system('rm -rf /')")
        InvalidCodeError: Dangerous construct: import statement
    """
    if not isinstance(code, str):
        raise InvalidInputError(f"Expected string, got {type(code)}")

    if len(code) > max_length:
        raise InvalidInputError(
            f"Code too long: {len(code)} > {max_length} characters"
        )

    # Parse code into AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise InvalidCodeError(f"Syntax error in code: {e}")

    # Check for dangerous node types
    for node in ast.walk(tree):
        node_type = type(node)

        # Check imports
        if not allow_imports and node_type in {ast.Import, ast.ImportFrom}:
            raise InvalidCodeError(
                "Dangerous construct: import statement not allowed"
            )

        # Check function calls
        if isinstance(node, ast.Call):
            func_name = None

            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"

            if func_name in DANGEROUS_FUNCTIONS:
                if not allow_file_io and func_name in {"open", "file"}:
                    raise InvalidCodeError(
                        f"Dangerous function call: {func_name} (file I/O not allowed)"
                    )
                else:
                    raise InvalidCodeError(
                        f"Dangerous function call: {func_name}"
                    )

    return code


# ============================================================
# Parameter Validation
# ============================================================

def validate_params(
    params: dict[str, Any],
    schema: type[BaseModel]
) -> BaseModel:
    """
    Validate parameters against Pydantic schema.
    
    Args:
        params: Parameters to validate
        schema: Pydantic model class
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValidationErrorBase: If validation fails
        
    Example:
        >>> from pydantic import BaseModel
        >>> class UserParams(BaseModel):
        ...     name: str
        ...     age: int
        >>> validate_params({"name": "Alice", "age": 30}, UserParams)
        UserParams(name='Alice', age=30)
    """
    try:
        return schema(**params)
    except ValidationError as e:
        error_msgs = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_msgs.append(f"  {field}: {msg}")

        raise ValidationErrorBase(
            "Parameter validation failed:\n" + "\n".join(error_msgs)
        )


# ============================================================
# Bulk Validation
# ============================================================

def validate_tool_input(
    params: dict[str, Any],
    schema: type[BaseModel] | None = None,
    sanitize: bool = True
) -> dict[str, Any]:
    """
    Comprehensive validation for tool inputs.
    
    Combines sanitization and schema validation.
    
    Args:
        params: Tool parameters
        schema: Optional Pydantic schema
        sanitize: If True, sanitize string values
        
    Returns:
        Validated (and possibly sanitized) parameters
        
    Raises:
        ValidationErrorBase: If validation fails
        
    Example:
        >>> validate_tool_input({"query": "SELECT * FROM users"})
        {'query': 'SELECT * FROM users'}
    """
    # Sanitize if requested
    if sanitize:
        params = sanitize_dict(params)

    # Validate against schema if provided
    if schema is not None:
        validated_model = validate_params(params, schema)
        return validated_model.model_dump()

    return params


# ============================================================
# Export
# ============================================================

__all__ = [
    # Errors
    "ValidationErrorBase",
    "InvalidInputError",
    "UnsafeInputError",
    "PathTraversalError",
    "UnsafeURLError",
    "InvalidCodeError",
    # Tool schemas
    "ToolParameter",
    "ToolDefinition",
    # String sanitization
    "sanitize_string",
    "sanitize_dict",
    # Path validation
    "validate_file_path",
    # URL validation
    "validate_url",
    # Code validation
    "validate_code",
    # Parameter validation
    "validate_params",
    "validate_tool_input",
    # Tool schemas
    "ToolParameter",
    "ToolDefinition",
]
