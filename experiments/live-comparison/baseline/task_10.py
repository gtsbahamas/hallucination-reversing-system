import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import unicodedata


class InputSanitizer:
    """
    Comprehensive input sanitization library that prevents XSS, SQL injection,
    and path traversal attacks while preserving legitimate content.
    """

    # XSS-related patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>',
        r'<applet[^>]*>.*?</applet>',
        r'<meta[^>]*>',
        r'<link[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'vbscript:',
        r'data:text/html',
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)',
        r'(--|#|/\*|\*/)',
        r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*)",
        r"(;\s*(DROP|DELETE|UPDATE|INSERT))",
        r'(\bxp_\w+\b)',
        r'(\bsp_\w+\b)',
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.',
        r'%2e%2e',
        r'\.%2e',
        r'%2e\.',
        r'%252e',
    ]

    # Allowed HTML tags for rich content
    ALLOWED_HTML_TAGS = {
        'p', 'br', 'strong', 'em', 'u', 'i', 'b',
        'ul', 'ol', 'li', 'a', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre'
    }

    # Allowed HTML attributes
    ALLOWED_HTML_ATTRIBUTES = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'span': ['class'],
        'div': ['class'],
    }

    def __init__(
        self,
        strict_mode: bool = False,
        allow_html: bool = False,
        custom_allowed_tags: Optional[List[str]] = None
    ):
        """
        Initialize the input sanitizer.

        Args:
            strict_mode: If True, applies more aggressive sanitization
            allow_html: If True, allows whitelisted HTML tags
            custom_allowed_tags: Custom list of allowed HTML tags
        """
        self.strict_mode = strict_mode
        self.allow_html = allow_html

        if custom_allowed_tags:
            self.allowed_tags = set(custom_allowed_tags)
        else:
            self.allowed_tags = self.ALLOWED_HTML_TAGS.copy()

        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self.xss_regex = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.XSS_PATTERNS
        ]
        self.sql_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SQL_PATTERNS
        ]
        self.path_traversal_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.PATH_TRAVERSAL_PATTERNS
        ]

    def sanitize(
        self,
        data: Any,
        context: str = 'general'
    ) -> Any:
        """
        Main sanitization method that dispatches to specific sanitizers.

        Args:
            data: Input data to sanitize
            context: Context of sanitization ('general', 'html', 'sql', 'path', 'url')

        Returns:
            Sanitized data
        """
        if data is None:
            return None

        if isinstance(data, (list, tuple)):
            return [self.sanitize(item, context) for item in data]

        if isinstance(data, dict):
            return {
                key: self.sanitize(value, context)
                for key, value in data.items()
            }

        if not isinstance(data, str):
            return data

        context_methods = {
            'general': self._sanitize_general,
            'html': self._sanitize_html,
            'sql': self._sanitize_sql,
            'path': self._sanitize_path,
            'url': self._sanitize_url,
            'email': self._sanitize_email,
        }

        method = context_methods.get(context, self._sanitize_general)
        return method(data)

    def _sanitize_general(self, text: str) -> str:
        """
        General purpose sanitization covering all attack vectors.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text
        """
        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Apply all sanitization methods
        text = self._remove_xss(text)
        text = self._sanitize_sql_input(text)
        text = self._remove_path_traversal(text)

        # Trim whitespace
        text = text.strip()

        return text

    def _sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content, removing dangerous tags while preserving safe ones.

        Args:
            html_content: HTML content to sanitize

        Returns:
            Sanitized HTML
        """
        if not self.allow_html:
            return html.escape(html_content)

        # First pass: remove obvious XSS patterns
        for pattern in self.xss_regex:
            html_content = pattern.sub('', html_content)

        # Parse and whitelist tags
        html_content = self._whitelist_html_tags(html_content)

        return html_content

    def _whitelist_html_tags(self, html_content: str) -> str:
        """
        Remove non-whitelisted HTML tags and attributes.

        Args:
            html_content: HTML content

        Returns:
            HTML with only whitelisted tags
        """
        # Simple tag parser that preserves whitelisted tags
        tag_pattern = re.compile(
            r'<(/?)(\w+)([^>]*)>',
            re.IGNORECASE | re.DOTALL
        )

        def replace_tag(match: re.Match) -> str:
            closing = match.group(1)
            tag_name = match.group(2).lower()
            attributes = match.group(3)

            if tag_name not in self.allowed_tags:
                return ''

            if closing:
                return f'</{tag_name}>'

            # Sanitize attributes
            clean_attrs = self._sanitize_attributes(tag_name, attributes)
            if clean_attrs:
                return f'<{tag_name} {clean_attrs}>'
            return f'<{tag_name}>'

        return tag_pattern.sub(replace_tag, html_content)

    def _sanitize_attributes(self, tag_name: str, attributes: str) -> str:
        """
        Sanitize HTML tag attributes.

        Args:
            tag_name: HTML tag name
            attributes: Attribute string

        Returns:
            Sanitized attributes
        """
        allowed_attrs = self.ALLOWED_HTML_ATTRIBUTES.get(tag_name, [])
        if not allowed_attrs:
            return ''

        attr_pattern = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']')
        matches = attr_pattern.findall(attributes)

        clean_attrs = []
        for attr_name, attr_value in matches:
            if attr_name.lower() in allowed_attrs:
                # Check for XSS in attribute values
                if not any(pattern.search(attr_value) for pattern in self.xss_regex):
                    clean_value = html.escape(attr_value, quote=True)
                    clean_attrs.append(f'{attr_name}="{clean_value}"')

        return ' '.join(clean_attrs)

    def _remove_xss(self, text: str) -> str:
        """
        Remove XSS attack patterns from text.

        Args:
            text: Input text

        Returns:
            Text with XSS patterns removed
        """
        for pattern in self.xss_regex:
            text = pattern.sub('', text)

        # Encode remaining HTML entities
        if not self.allow_html:
            text = html.escape(text)

        return text

    def _sanitize_sql_input(self, text: str) -> str:
        """
        Sanitize input to prevent SQL injection.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        if self.strict_mode:
            # In strict mode, remove SQL keywords entirely
            for pattern in self.sql_regex:
                text = pattern.sub('', text)
        else:
            # Escape single quotes
            text = text.replace("'", "''")

        return text

    def _sanitize_sql(self, value: str) -> str:
        """
        SQL-specific sanitization with escaping.

        Args:
            value: SQL parameter value

        Returns:
            Sanitized SQL parameter
        """
        # Remove SQL injection patterns
        value = self._sanitize_sql_input(value)

        # Additional SQL-specific escaping
        value = value.replace('\\', '\\\\')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')

        return value

    def _remove_path_traversal(self, path: str) -> str:
        """
        Remove path traversal patterns.

        Args:
            path: Path string

        Returns:
            Sanitized path
        """
        for pattern in self.path_traversal_regex:
            path = pattern.sub('', path)

        return path

    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize file path to prevent path traversal attacks.

        Args:
            path: File path

        Returns:
            Sanitized path
        """
        # Remove path traversal patterns
        path = self._remove_path_traversal(path)

        # URL decode to catch encoded traversal attempts
        path = urllib.parse.unquote(path)
        path = self._remove_path_traversal(path)

        # Normalize path
        try:
            normalized = Path(path).resolve()
            # Only return the filename component
            return normalized.name
        except (ValueError, OSError):
            return ''

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL to prevent XSS and injection attacks.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
        url_lower = url.lower().strip()

        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                return ''

        # Parse and validate URL
        try:
            parsed = urllib.parse.urlparse(url)

            # Only allow http, https, and relative URLs
            if parsed.scheme and parsed.scheme not in ['http', 'https', '']:
                return ''

            # Reconstruct URL with encoding
            safe_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                urllib.parse.quote(parsed.path, safe='/'),
                parsed.params,
                urllib.parse.quote(parsed.query, safe='&='),
                urllib.parse.quote(parsed.fragment, safe='')
            ))

            return safe_url
        except Exception:
            return ''

    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize email address.

        Args:
            email: Email address

        Returns:
            Sanitized email or empty string if invalid
        """
        # Basic email validation pattern
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

        email = email.strip().lower()

        if email_pattern.match(email):
            return email

        return ''

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        context_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Sanitize dictionary with field-specific contexts.

        Args:
            data: Dictionary to sanitize
            context_map: Mapping of field names to sanitization contexts

        Returns:
            Sanitized dictionary
        """
        context_map = context_map or {}
        result = {}

        for key, value in data.items():
            context = context_map.get(key, 'general')
            result[key] = self.sanitize(value, context)

        return result

    def is_safe(
        self,
        text: str,
        check_xss: bool = True,
        check_sql: bool = True,
        check_path: bool = True
    ) -> bool:
        """
        Check if text contains potential security threats.

        Args:
            text: Text to check
            check_xss: Check for XSS patterns
            check_sql: Check for SQL injection patterns
            check_path: Check for path traversal patterns

        Returns:
            True if text is safe, False otherwise
        """
        if not isinstance(text, str):
            return True

        if check_xss:
            if any(pattern.search(text) for pattern in self.xss_regex):
                return False

        if check_sql:
            if any(pattern.search(text) for pattern in self.sql_regex):
                return False

        if check_path:
            if any(pattern.search(text) for pattern in self.path_traversal_regex):
                return False

        return True

    def validate_and_sanitize(
        self,
        data: Any,
        context: str = 'general',
        raise_on_unsafe: bool = False
    ) -> tuple[bool, Any]:
        """
        Validate input safety and return sanitized version.

        Args:
            data: Input data
            context: Sanitization context
            raise_on_unsafe: Raise exception if input is unsafe

        Returns:
            Tuple of (is_safe, sanitized_data)

        Raises:
            ValueError: If raise_on_unsafe is True and input is unsafe
        """
        if isinstance(data, str):
            is_safe = self.is_safe(data)

            if not is_safe and raise_on_unsafe:
                raise ValueError("Input contains potentially dangerous content")

            sanitized = self.sanitize(data, context)
            return is_safe, sanitized

        sanitized = self.sanitize(data, context)
        return True, sanitized


def create_sanitizer(
    strict_mode: bool = False,
    allow_html: bool = False,
    custom_allowed_tags: Optional[List[str]] = None
) -> InputSanitizer:
    """
    Factory function to create an InputSanitizer instance.

    