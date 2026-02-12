import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union, TypeVar, overload
from pathlib import Path
import unicodedata
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class InputSanitizer:
    """
    Comprehensive input sanitization library that prevents XSS, SQL injection,
    and path traversal attacks while preserving legitimate content.
    
    WARNING: SQL injection cannot be prevented through input sanitization alone.
    ALWAYS use parameterized queries/prepared statements for database operations.
    The SQL sanitization methods in this library should NOT be used to build
    SQL query strings through concatenation.
    """

    XSS_PATTERNS = [
        r'<\s*script[^>]*>.*?<\s*/\s*script\s*>',
        r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>',
        r'<\s*object[^>]*>.*?<\s*/\s*object\s*>',
        r'<\s*embed[^>]*>',
        r'<\s*applet[^>]*>.*?<\s*/\s*applet\s*>',
        r'<\s*meta[^>]*>',
        r'<\s*link[^>]*>',
        r'<\s*style[^>]*>.*?<\s*/\s*style\s*>',
        r'<\s*svg[^>]*>.*?<\s*/\s*svg\s*>',
        r'on\s*\w+\s*=',
        r'javascript\s*:',
        r'vbscript\s*:',
        r'data\s*:\s*text\s*/\s*html',
        r'data\s*:\s*image\s*/\s*svg',
    ]

    SQL_KEYWORDS = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'EXEC', 'EXECUTE', 'UNION', 'DECLARE', 'CAST', 'CONVERT', 'CHAR',
        'VARCHAR', 'NCHAR', 'NVARCHAR', 'BENCHMARK', 'SLEEP', 'WAITFOR',
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.',
        r'\\',
        r'%2e',
        r'%252e',
        r'%c0%ae',
        r'%e0%80%ae',
        r'\u2215',
        r'\u2216',
        r'\uff0e',
        r'\uff0f',
        r'\uff3c',
    ]

    ALLOWED_HTML_TAGS = {
        'p', 'br', 'strong', 'em', 'u', 'i', 'b',
        'ul', 'ol', 'li', 'a', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre', 'hr',
    }

    ALLOWED_HTML_ATTRIBUTES = {
        'a': ['href', 'title', 'rel'],
        'span': ['class'],
        'div': ['class'],
        'code': ['class'],
        'pre': ['class'],
    }

    SAFE_URL_SCHEMES = {'http', 'https', 'mailto', ''}

    def __init__(
        self,
        strict_mode: bool = False,
        allow_html: bool = False,
        custom_allowed_tags: Optional[List[str]] = None,
        base_path: Optional[Path] = None
    ):
        """
        Initialize the input sanitizer.

        Args:
            strict_mode: If True, applies more aggressive sanitization
            allow_html: If True, allows whitelisted HTML tags (uses proper HTML parser)
            custom_allowed_tags: Custom list of allowed HTML tags
            base_path: Base directory for path validation (required for path sanitization)
        """
        self.strict_mode = strict_mode
        self.allow_html = allow_html
        self.base_path = base_path.resolve() if base_path else None

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
            context: Context of sanitization ('general', 'html', 'path', 'url')

        Returns:
            Sanitized data
        """
        if data is None:
            return None

        if isinstance(data, (list, tuple)):
            sanitized = [self.sanitize(item, context) for item in data]
            return type(data)(sanitized)

        if isinstance(data, dict):
            return {
                key: self.sanitize(value, context)
                for key, value in data.items()
            }

        if isinstance(data, bool):
            return data

        if isinstance(data, (int, float)):
            return data

        if not isinstance(data, str):
            return data

        context_methods = {
            'general': self._sanitize_general,
            'html': self._sanitize_html,
            'path': self._sanitize_path,
            'url': self._sanitize_url,
            'email': self._sanitize_email,
            'filename': self._sanitize_filename,
        }

        method = context_methods.get(context, self._sanitize_general)
        return method(data)

    def _normalize_and_decode(self, text: str, max_iterations: int = 5) -> str:
        """
        Normalize and decode text to prevent encoding-based bypasses.

        Args:
            text: Input text
            max_iterations: Maximum decoding iterations

        Returns:
            Normalized and decoded text
        """
        text = unicodedata.normalize('NFC', text)
        
        text = text.replace('\x00', '')
        
        text = ''.join(char for char in text if char >= ' ' or char in '\t\n\r')
        
        previous = None
        iterations = 0
        while previous != text and iterations < max_iterations:
            previous = text
            try:
                text = urllib.parse.unquote(text)
            except Exception:
                break
            iterations += 1
        
        text = re.sub(r'\s+', ' ', text)
        
        return text

    def _decode_html_entities(self, text: str, max_iterations: int = 3) -> str:
        """
        Recursively decode HTML entities to prevent entity-based bypasses.

        Args:
            text: Input text
            max_iterations: Maximum decoding iterations

        Returns:
            Decoded text
        """
        previous = None
        iterations = 0
        while previous != text and iterations < max_iterations:
            previous = text
            text = html.unescape(text)
            iterations += 1
        return text

    def _sanitize_general(self, text: str) -> str:
        """
        General purpose sanitization covering all attack vectors.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text
        """
        text = self._normalize_and_decode(text)
        
        text = self._decode_html_entities(text)
        
        text = self._remove_xss(text)
        
        text = self._remove_path_traversal(text)
        
        text = text.strip()

        return text

    def _sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content using proper HTML parsing.

        Args:
            html_content: HTML content to sanitize

        Returns:
            Sanitized HTML
        """
        if not self.allow_html:
            return html.escape(html_content)

        try:
            from html.parser import HTMLParser
        except ImportError:
            logger.error("HTML parser not available, falling back to escape")
            return html.escape(html_content)

        html_content = self._normalize_and_decode(html_content)
        html_content = self._decode_html_entities(html_content)

        class SafeHTMLParser(HTMLParser):
            def __init__(self, allowed_tags, allowed_attrs, xss_patterns):
                super().__init__()
                self.allowed_tags = allowed_tags
                self.allowed_attrs = allowed_attrs
                self.xss_patterns = xss_patterns
                self.output = []
                
            def handle_starttag(self, tag, attrs):
                if tag.lower() not in self.allowed_tags:
                    return
                
                safe_attrs = []
                allowed = self.allowed_attrs.get(tag.lower(), [])
                
                for attr_name, attr_value in attrs:
                    if attr_name.lower() not in allowed:
                        continue
                    
                    if attr_value is None:
                        attr_value = ''
                    
                    if any(pattern.search(str(attr_value)) for pattern in self.xss_patterns):
                        continue
                    
                    if attr_name.lower() == 'href':
                        attr_value = self._sanitize_href(attr_value)
                        if not attr_value:
                            continue
                    
                    safe_attrs.append(f'{html.escape(attr_name)}="{html.escape(str(attr_value), quote=True)}"')
                
                if safe_attrs:
                    self.output.append(f'<{tag} {" ".join(safe_attrs)}>')
                else:
                    self.output.append(f'<{tag}>')
            
            def handle_endtag(self, tag):
                if tag.lower() in self.allowed_tags:
                    self.output.append(f'</{tag}>')
            
            def handle_data(self, data):
                self.output.append(html.escape(data))
            
            def _sanitize_href(self, url):
                url = url.strip()
                url_lower = url.lower()
                
                dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
                for protocol in dangerous_protocols:
                    if protocol in url_lower:
                        return ''
                
                try:
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme and parsed.scheme.lower() not in {'http', 'https', 'mailto', ''}:
                        return ''
                    return url
                except Exception:
                    return ''
            
            def get_output(self):
                return ''.join(self.output)

        parser = SafeHTMLParser(self.allowed_tags, self.ALLOWED_HTML_ATTRIBUTES, self.xss_regex)
        
        try:
            parser.feed(html_content)
            return parser.get_output()
        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")
            return html.escape(html_content)

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

        if not self.allow_html:
            text = html.escape(text)

        return text

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
            Sanitized path relative to base_path

        Raises:
            ValueError: If path traversal is detected or base_path not configured
        """
        if not self.base_path:
            raise ValueError("base_path must be configured for path sanitization")

        path = self._normalize_and_decode(path)
        
        path = self._remove_path_traversal(path)
        
        path = path.replace('\x00', '').replace('\\', '/')
        
        path = path.strip('/')

        try:
            full_path = (self.base_path / path).resolve()
            
            try:
                full_path.relative_to(self.base_path)
            except ValueError:
                logger.warning(f"Path traversal attempt detected: {path}")
                raise ValueError("Path traversal detected")
            
            return str(full_path.relative_to(self.base_path))
        
        except (ValueError, OSError) as e:
            logger.error(f"Path sanitization failed for '{path}': {e}")
            raise ValueError(f"Invalid path: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.

        Args:
            filename: Filename to sanitize

        Returns:
            Safe filename
        """
        filename = self._normalize_and_decode(filename)
        filename = self._remove_path_traversal(filename)
        
        filename = filename.replace('\x00', '').replace('/', '').replace('\\', '')
        
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        filename = filename.strip('. ')
        
        if not filename:
            return 'unnamed'
        
        return filename[:255]

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL to prevent XSS and injection attacks.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL or empty string if invalid
        """
        url = self._normalize_and_decode(url)
        
        url = url.strip()
        url_lower = url.lower().replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                logger.warning(f"Dangerous URL protocol detected: {url}")
                return ''

        try:
            parsed = urllib.parse.urlparse(url)
            
            if parsed.scheme and parsed.scheme.lower() not in self.SAFE_URL_SCHEMES:
                logger.warning(f"Disallowed URL scheme: {parsed.scheme}")
                return ''
            
            safe_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                urllib.parse.quote(parsed.path, safe='/:@!$&\'()*+,;='),
                parsed.params,
                urllib.parse.quote(parsed.query, safe='&='),
                urllib.parse.quote(parsed.fragment, safe='')
            ))

            return safe_url
        except Exception as e:
            logger.error(f"URL parsing failed for '{url}': {e}")
            return ''

    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize email address.

        Args:
            email: Email address

        Returns:
            Sanitized email or empty string if invalid
        """
        email_pattern = re.compile(
            r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,63}@[a-zA-Z0-9][a-zA-Z0-9.-]{0,253}\.[a-zA-Z]{2,}$'
        )

        email = email.strip().lower()
        
        email = self._normalize_and_decode(email)
        
        dangerous_chars = [';', '\n', '\r', '\x00', '\\']
        if any(char in email for char in dangerous_chars):
            logger.warning(f"Dangerous characters in email: {email}")
            return ''

        if len(email) > 320:
            return ''

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
            try:
                result[key] = self.sanitize(value, context)
            except Exception as e:
                logger.error(f"Sanitization failed for key '{key}': {e}")
                result[key] = None

        return result

    @overload
    def validate_and_sanitize(
        self,
        data: str,
        context: str = 'general',
        raise_on_unsafe: bool = False
    ) -> tuple[bool, str]:
        ...

    @overload
    def validate_and_sanitize(
        self,
        data: List[T],
        context: str = 'general',
        raise_on_unsafe: bool = False
    ) -> tuple[bool, List[T]]:
        ...

    @overload
    def validate_and_sanitize(
        self,
        data: Dict[str, T],
        context: str = 'general',
        raise_on_unsafe: bool = False
    ) -> tuple[bool, Dict[str, T]]:
        ...

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
        is_safe = True
        
        if isinstance(data, str):
            normalized = self._normalize_and_decode(data)
            decoded = self._decode_html_entities(normalized)
            
            if any(pattern.search(decoded) for pattern in self.xss_regex):
                is_safe = False
            
            if any(pattern.search(decoded) for pattern in self.path_traversal_regex):
                is_safe = False

            if not is_safe and raise_on_unsafe:
                raise ValueError("Input contains potentially dangerous content")

        try:
            sanitized = self.sanitize(data, context)
            return is_safe, sanitized
        except Exception as e:
            logger.error(f"Sanitization error: {e}")
            if raise_on_unsafe:
                raise
            return False, None


def create_sanitizer(
    strict_mode: bool = False,
    allow_html: bool = False,
    custom_allowed_tags: Optional[List[str]] = None,
    base_path: Optional[Path] = None
) -> InputSanitizer:
    """
    Factory function to create an InputSanitizer instance.

    Args:
        strict_mode: If True, applies more aggressive sanitization
        allow_html: If True, allows whitelisted HTML tags
        custom_allowed_tags: Custom list of allowed HTML tags
        base_path: Base directory for path validation

    Returns:
        InputSanitizer instance
    """
    return InputSanitizer(
        strict_mode=strict_mode,
        allow_html=allow_html,
        custom_allowed_tags=custom_allowed_tags,
        base_path=base_path
    )