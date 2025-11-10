"""
Input sanitization and validation utilities.

Provides functions to sanitize user input, prevent XSS attacks,
and validate against SQL injection attempts.
"""

import re
import html
import logging
from typing import Any, Dict, List, Union, Optional

logger = logging.getLogger(__name__)

# Patterns that may indicate SQL injection attempts
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b)",
    r"(\bINSERT\b.*\bINTO\b.*\bVALUES\b)",
    r"(\bUPDATE\b.*\bSET\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(\bDROP\b.*\b(TABLE|DATABASE)\b)",
    r"(\bEXEC\b.*\()",
    r"(--\s*$)",
    r"(;\s*(DROP|DELETE|UPDATE|INSERT))",
    r"(\bOR\b.*=.*)",
    r"(\bAND\b.*=.*)",
    r"('.*--)",
    r"('.*OR.*'.*=.*')",
]

# Compile patterns for efficiency
COMPILED_SQL_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]

# Dangerous HTML/JS patterns for XSS
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",  # Event handlers like onclick, onload
    r"<iframe[^>]*>",
    r"<embed[^>]*>",
    r"<object[^>]*>",
    r"<applet[^>]*>",
    r"<meta[^>]*>",
    r"<link[^>]*>",
    r"<style[^>]*>.*?</style>",
    r"expression\s*\(",  # CSS expressions
    r"vbscript:",
    r"data:text/html",
]

COMPILED_XSS_PATTERNS = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in XSS_PATTERNS]


def sanitize_html(text: str, allow_basic_formatting: bool = False) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        text: Input text that may contain HTML
        allow_basic_formatting: If True, allows basic formatting tags (b, i, p, br)

    Returns:
        Sanitized text with dangerous HTML removed/escaped
    """
    if not isinstance(text, str):
        return text

    # Escape HTML entities
    sanitized = html.escape(text)

    if allow_basic_formatting:
        # Unescape safe tags
        safe_tags = ['<b>', '</b>', '<i>', '</i>', '<p>', '</p>', '<br>', '<br/>']
        for tag in safe_tags:
            escaped_tag = html.escape(tag)
            sanitized = sanitized.replace(escaped_tag, tag)

    return sanitized


def remove_xss_patterns(text: str) -> str:
    """
    Remove potentially dangerous XSS patterns from text.

    Args:
        text: Input text to scan

    Returns:
        Text with XSS patterns removed
    """
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern in COMPILED_XSS_PATTERNS:
        sanitized = pattern.sub('', sanitized)

    return sanitized


def validate_no_sql_injection(text: str, raise_on_suspicious: bool = True) -> bool:
    """
    Check if text contains potential SQL injection patterns.

    Args:
        text: Input text to validate
        raise_on_suspicious: If True, raises ValueError on suspicious patterns

    Returns:
        True if text appears safe, False otherwise

    Raises:
        ValueError: If raise_on_suspicious is True and patterns are detected
    """
    if not isinstance(text, str):
        return True

    # Check against SQL injection patterns
    for pattern in COMPILED_SQL_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning(f"Potential SQL injection detected: {match.group()}")
            if raise_on_suspicious:
                raise ValueError(
                    "Input contains potentially dangerous SQL patterns. "
                    "Please use only alphanumeric characters and basic punctuation."
                )
            return False

    return True


def sanitize_string(
    text: str,
    max_length: Optional[int] = None,
    allow_html: bool = False,
    allow_basic_formatting: bool = False,
    check_sql_injection: bool = True,
) -> str:
    """
    Comprehensive string sanitization.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (truncates if exceeded)
        allow_html: If True, allows HTML (still removes XSS patterns)
        allow_basic_formatting: If True, allows basic HTML formatting tags
        check_sql_injection: If True, validates against SQL injection patterns

    Returns:
        Sanitized text

    Raises:
        ValueError: If SQL injection patterns are detected
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""

    # Trim whitespace
    sanitized = text.strip()

    # Check for SQL injection
    if check_sql_injection:
        validate_no_sql_injection(sanitized)

    # Handle HTML
    if not allow_html:
        sanitized = sanitize_html(sanitized, allow_basic_formatting)
    else:
        # Even if HTML is allowed, remove XSS patterns
        sanitized = remove_xss_patterns(sanitized)

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.info(f"Text truncated from {len(text)} to {max_length} characters")

    return sanitized


def sanitize_dict(
    data: Dict[str, Any],
    max_string_length: Optional[int] = 10000,
    check_sql_injection: bool = True,
) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        max_string_length: Maximum length for string values
        check_sql_injection: If True, validates against SQL injection patterns

    Returns:
        Dictionary with sanitized string values
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(
                value,
                max_length=max_string_length,
                check_sql_injection=check_sql_injection,
            )
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_string_length, check_sql_injection)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value, max_string_length, check_sql_injection)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_list(
    data: List[Any],
    max_string_length: Optional[int] = 10000,
    check_sql_injection: bool = True,
) -> List[Any]:
    """
    Recursively sanitize all string values in a list.

    Args:
        data: List to sanitize
        max_string_length: Maximum length for string values
        check_sql_injection: If True, validates against SQL injection patterns

    Returns:
        List with sanitized string values
    """
    if not isinstance(data, list):
        return data

    sanitized = []
    for item in data:
        if isinstance(item, str):
            sanitized.append(
                sanitize_string(
                    item,
                    max_length=max_string_length,
                    check_sql_injection=check_sql_injection,
                )
            )
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item, max_string_length, check_sql_injection))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, max_string_length, check_sql_injection))
        else:
            sanitized.append(item)

    return sanitized


def sanitize_input(
    data: Union[str, Dict, List],
    max_string_length: Optional[int] = 10000,
    check_sql_injection: bool = True,
) -> Union[str, Dict, List]:
    """
    Sanitize input data of any type (string, dict, or list).

    Args:
        data: Input data to sanitize
        max_string_length: Maximum length for string values
        check_sql_injection: If True, validates against SQL injection patterns

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_string(data, max_length=max_string_length, check_sql_injection=check_sql_injection)
    elif isinstance(data, dict):
        return sanitize_dict(data, max_string_length, check_sql_injection)
    elif isinstance(data, list):
        return sanitize_list(data, max_string_length, check_sql_injection)
    else:
        return data


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid
    """
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str, allowed_schemes: List[str] = None) -> bool:
    """
    Validate URL format and scheme.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        True if URL format is valid and scheme is allowed
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    # Basic URL validation
    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url, re.IGNORECASE):
        return False

    # Check scheme
    scheme = url.split('://', 1)[0].lower()
    return scheme in allowed_schemes


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Filename to sanitize

    Returns:
        Safe filename
    """
    # Remove path separators and null bytes
    sanitized = filename.replace('/', '').replace('\\', '').replace('\0', '')

    # Remove dangerous patterns
    sanitized = sanitized.replace('..', '')

    # Only allow alphanumeric, dash, underscore, and dot
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')

    return sanitized


# Validation decorators for Pydantic models
def validate_no_html(v: str) -> str:
    """Pydantic validator to ensure no HTML in string."""
    if '<' in v or '>' in v:
        raise ValueError("HTML tags are not allowed")
    return v


def validate_no_sql(v: str) -> str:
    """Pydantic validator to check for SQL injection patterns."""
    validate_no_sql_injection(v, raise_on_suspicious=True)
    return v


def validate_safe_string(v: str) -> str:
    """Pydantic validator for comprehensive string sanitization."""
    return sanitize_string(v, check_sql_injection=True)
