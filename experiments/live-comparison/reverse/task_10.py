import re
import html
import urllib.parse
import unicodedata
import os
from typing import Optional, Dict, Tuple, Set, List, Union
from html.parser import HTMLParser


class SecurityError(ValueError):
    """Raised when malicious input is detected"""
    pass


# Compile regex patterns at module level for performance
SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
DANGEROUS_PROTOCOLS = re.compile(r'^(javascript|data|vbscript|file):', re.IGNORECASE)
SQL_COMMENT_PATTERN = re.compile(r'(--|/\*|\*/)', re.IGNORECASE)
SQL_STACKED_QUERY = re.compile(r';\s*\w+', re.IGNORECASE)
SQL_UNION_PATTERN = re.compile(r'\bunion\b.*\bselect\b', re.IGNORECASE | re.DOTALL)
SQL_DROP_PATTERN = re.compile(r'\bdrop\b\s+\btable\b', re.IGNORECASE)
TEMPLATE_EXPR = re.compile(r'(\{\{|\}\}|\$\{)')
EVENT_HANDLER = re.compile(r'\bon\w+\s*=', re.IGNORECASE)
META_REFRESH = re.compile(r'<meta[^>]*http-equiv\s*=\s*["\']?refresh', re.IGNORECASE)
HEX_NUMERIC = re.compile(r'0x[0-9a-f]+', re.IGNORECASE)
DANGEROUS_CSS = ['expression', 'behavior', '-moz-binding', 'javascript:', 'import', 'url(javascript:']
INVISIBLE_CHARS = ['\ufeff', '\u200b', '\u200c', '\u200d', '\u202e']

# HTML sanitization configuration
DANGEROUS_TAGS = {
    'script', 'object', 'embed', 'iframe', 'frame', 'frameset',
    'base', 'applet', 'style', 'link', 'meta'
}

ALLOWED_TAGS = {
    'p', 'div', 'span', 'strong', 'em', 'b', 'i', 'u', 's', 'strike',
    'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'a', 'img', 'blockquote', 'pre', 'code', 'sup', 'sub'
}

ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
    '*': ['class', 'id', 'title']
}

SAFE_URI_SCHEMES = {'http', 'https', 'mailto', ''}

MAX_INPUT_LENGTH = 10_000_000
MAX_NESTING_DEPTH = 100


class SafeHTMLParser(HTMLParser):
    """HTML parser that sanitizes malicious content"""
    
    def __init__(self, allowed_tags: Set[str], allowed_attrs: Dict[str, List[str]], 
                 strict: bool = False):
        super().__init__()
        self.allowed_tags = allowed_tags
        self.allowed_attrs = allowed_attrs
        self.strict = strict
        self.result = []
        self.nesting_depth = 0
        self.report = {'removed_tags': [], 'removed_attrs': [], 'blocked_content': []}
        
    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        
        if self.nesting_depth >= MAX_NESTING_DEPTH:
            if self.strict:
                raise SecurityError('Maximum nesting depth exceeded')
            return
            
        if tag_lower in DANGEROUS_TAGS:
            self.report['removed_tags'].append(tag_lower)
            if self.strict:
                raise SecurityError(f'Dangerous tag detected: {tag_lower}')
            return
        
        if tag_lower == 'svg':
            self.report['removed_tags'].append('svg')
            if self.strict:
                raise SecurityError('SVG tags are blocked')
            return
            
        if tag_lower not in self.allowed_tags:
            self.report['removed_tags'].append(tag_lower)
            return
        
        self.nesting_depth += 1
        
        # Sanitize attributes
        safe_attrs = []
        tag_allowed_attrs = self.allowed_attrs.get(tag_lower, [])
        global_allowed_attrs = self.allowed_attrs.get('*', [])
        
        for attr_name, attr_value in attrs:
            attr_lower = attr_name.lower()
            
            # Check for event handlers
            if attr_lower.startswith('on'):
                self.report['removed_attrs'].append(f'{tag_lower}.{attr_lower}')
                if self.strict:
                    raise SecurityError(f'Event handler detected: {attr_lower}')
                continue
            
            # Check for style attribute
            if attr_lower == 'style':
                if not self._is_safe_style(attr_value):
                    self.report['removed_attrs'].append(f'{tag_lower}.style')
                    if self.strict:
                        raise SecurityError('Dangerous CSS detected in style attribute')
                    continue
            
            # Check for data attributes (allow safe ones)
            if attr_lower.startswith('data-'):
                if self._is_safe_data_attr(attr_value):
                    safe_attrs.append((attr_name, attr_value))
                else:
                    self.report['removed_attrs'].append(f'{tag_lower}.{attr_lower}')
                continue
            
            # Check if attribute is allowed for this tag
            if attr_lower not in tag_allowed_attrs and attr_lower not in global_allowed_attrs:
                self.report['removed_attrs'].append(f'{tag_lower}.{attr_lower}')
                continue
            
            # Special validation for href and src
            if attr_lower in ('href', 'src'):
                sanitized_url = self._sanitize_url(attr_value)
                if sanitized_url is None:
                    self.report['removed_attrs'].append(f'{tag_lower}.{attr_lower}')
                    if self.strict:
                        raise SecurityError(f'Dangerous URL scheme in {attr_lower}')
                    continue
                safe_attrs.append((attr_name, sanitized_url))
            else:
                safe_attrs.append((attr_name, attr_value))
        
        # Build tag
        if safe_attrs:
            attrs_str = ' ' + ' '.join(f'{name}="{html.escape(value)}"' 
                                       for name, value in safe_attrs)
        else:
            attrs_str = ''
        
        self.result.append(f'<{tag}{attrs_str}>')
    
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.allowed_tags and tag_lower not in DANGEROUS_TAGS:
            if self.nesting_depth > 0:
                self.nesting_depth -= 1
            self.result.append(f'</{tag}>')
    
    def handle_data(self, data):
        self.result.append(html.escape(data))
    
    def handle_entityref(self, name):
        # Preserve HTML entities
        self.result.append(f'&{name};')
    
    def handle_charref(self, name):
        # Preserve character references
        self.result.append(f'&#{name};')
    
    def _sanitize_url(self, url: str) -> Optional[str]:
        """Validate and sanitize URLs"""
        if not url:
            return url
        
        try:
            parsed = urllib.parse.urlparse(url)
            scheme = parsed.scheme.lower()
            
            if scheme not in SAFE_URI_SCHEMES:
                return None
            
            # Check for encoded javascript/data URIs
            decoded_url = urllib.parse.unquote(url)
            if DANGEROUS_PROTOCOLS.match(decoded_url):
                return None
            
            return url
        except Exception:
            return None
    
    def _is_safe_style(self, style: str) -> bool:
        """Check if CSS style is safe"""
        style_lower = style.lower()
        for danger in DANGEROUS_CSS:
            if danger in style_lower:
                return False
        return True
    
    def _is_safe_data_attr(self, value: str) -> bool:
        """Check if data attribute value is safe"""
        value_lower = value.lower()
        if DANGEROUS_PROTOCOLS.match(value_lower):
            return False
        if '<script' in value_lower or 'javascript:' in value_lower:
            return False
        return True
    
    def get_sanitized_html(self) -> str:
        return ''.join(self.result)


def _normalize_input(text: str) -> str:
    """Normalize input by decoding and removing invisible characters"""
    # Remove invisible Unicode characters
    for char in INVISIBLE_CHARS:
        text = text.replace(char, '')
    
    # Normalize Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Decode URL encoding
    try:
        text = urllib.parse.unquote(text)
    except Exception:
        pass
    
    # Decode HTML entities
    text = html.unescape(text)
    
    return text


def sanitize_html(html_input: Union[str, bytes], 
                  allowed_tags: Optional[Set[str]] = None,
                  allowed_attrs: Optional[Dict[str, List[str]]] = None,
                  strict: bool = False,
                  return_report: bool = False) -> Union[str, Tuple[str, Dict]]:
    """
    Sanitize HTML input to prevent XSS attacks.
    
    Args:
        html_input: HTML string or bytes to sanitize
        allowed_tags: Set of allowed HTML tags (defaults to ALLOWED_TAGS)
        allowed_attrs: Dict of allowed attributes per tag (defaults to ALLOWED_ATTRS)
        strict: If True, raises SecurityError instead of sanitizing
        return_report: If True, returns tuple of (sanitized, report)
    
    Returns:
        Sanitized HTML string, or tuple of (sanitized, report) if return_report=True
    
    Raises:
        TypeError: If input is None
        ValueError: If input is too long
        SecurityError: If strict=True and malicious content is detected
    """
    if html_input is None:
        raise TypeError('expected str, got NoneType')
    
    # Handle bytes input
    if isinstance(html_input, bytes):
        html_input = html_input.decode('utf-8', errors='replace')
    
    # Handle empty string
    if html_input == '':
        if return_report:
            return '', {}
        return ''
    
    # Check length limit
    if len(html_input) > MAX_INPUT_LENGTH:
        raise ValueError(f'Input too long: {len(html_input)} > {MAX_INPUT_LENGTH}')
    
    # Detect null bytes
    if '\x00' in html_input:
        if strict:
            raise SecurityError('Null byte injection detected')
        html_input = html_input.replace('\x00', '')
    
    # Normalize input
    normalized = _normalize_input(html_input)
    
    # Check for dangerous patterns after normalization
    if SCRIPT_PATTERN.search(normalized):
        if strict:
            raise SecurityError('XSS attempt detected: script tag found')
    
    if META_REFRESH.search(normalized):
        if strict:
            raise SecurityError('Meta refresh redirect detected')
    
    if TEMPLATE_EXPR.search(normalized):
        if strict:
            raise SecurityError('Template expression detected')
        # Escape template expressions
        normalized = normalized.replace('{{', '&#123;&#123;')
        normalized = normalized.replace('}}', '&#125;&#125;')
        normalized = normalized.replace('${', '&#36;&#123;')
    
    # Use default allowed tags/attrs if not provided
    if allowed_tags is None:
        allowed_tags = ALLOWED_TAGS
    if allowed_attrs is None:
        allowed_attrs = ALLOWED_ATTRS
    
    # Parse and sanitize HTML
    parser = SafeHTMLParser(allowed_tags, allowed_attrs, strict)
    
    try:
        parser.feed(normalized)
    except Exception as e:
        if strict:
            raise
        # Fallback to conservative sanitization on parse error
        result = html.escape(html_input)
        if return_report:
            return result, {'error': str(e), 'fallback': True}
        return result
    
    sanitized = parser.get_sanitized_html()
    
    if return_report:
        return sanitized, parser.report
    
    return sanitized


def sanitize_sql(sql_input: Union[str, bytes], detect_only: bool = False) -> str:
    """
    Sanitize SQL input to prevent SQL injection attacks.
    
    NOTE: This should NOT be used as a replacement for parameterized queries.
    Always use parameterized queries when possible. This is for sanitizing
    individual string values that will be used in SQL contexts.
    
    Args:
        sql_input: SQL string or bytes to sanitize
        detect_only: If True, only detects attacks without sanitizing
    
    Returns:
        Sanitized SQL string with escaped quotes
    
    Raises:
        TypeError: If input is None
        SecurityError: If SQL injection patterns are detected and detect_only=True
    """
    if sql_input is None:
        raise TypeError('expected str, got NoneType')
    
    # Handle bytes input
    if isinstance(sql_input, bytes):
        sql_input = sql_input.decode('utf-8', errors='replace')
    
    # Handle empty string
    if sql_input == '':
        return ''
    
    # Detect null bytes
    if '\x00' in sql_input:
        raise SecurityError('Null byte injection detected in SQL input')
    
    # Strip CRLF characters
    sanitized = sql_input.replace('\r', '').replace('\n', ' ')
    
    # Normalize input
    normalized = _normalize_input(sanitized)
    
    # Check for SQL injection patterns
    attacks_detected = []
    
    if SQL_COMMENT_PATTERN.search(normalized):
        attacks_detected.append('SQL comment marker (-- or /* */)')
    
    if SQL_STACKED_QUERY.search(normalized):
        attacks_detected.append('stacked query (semicolon)')
    
    if SQL_UNION_PATTERN.search(normalized):
        attacks_detected.append('UNION-based injection')
    
    if SQL_DROP_PATTERN.search(normalized):
        attacks_detected.append('DROP TABLE statement')
    
    # Check for hex-encoded bypasses
    if HEX_NUMERIC.search(normalized):
        attacks_detected.append('hexadecimal numeric encoding')
    
    # Check for quote-based injection
    if "'" in normalized and (' or ' in normalized.lower() or ' and ' in normalized.lower()):
        # Check for patterns like: ' OR '1'='1
        if re.search(r"'\s*(or|and)\s*'", normalized, re.IGNORECASE):
            attacks_detected.append('quote-based boolean injection')
    
    if attacks_detected:
        if detect_only:
            raise SecurityError(f'SQL injection detected: {", ".join(attacks_detected)}')
    
    # Escape single quotes
    sanitized = sanitized.replace("'", "\\'")
    
    # Escape double quotes
    sanitized = sanitized.replace('"', '\\"')
    
    return sanitized


def sanitize_path(path_input: Union[str, bytes], 
                  base_dir: Optional[str] = None,
                  allow_absolute: bool = False) -> str:
    """
    Sanitize file path input to prevent path traversal attacks.
    
    Args:
        path_input: Path string or bytes to sanitize
        base_dir: Base directory to validate against (optional)
        allow_absolute: If True, allows absolute paths
    
    Returns:
        Sanitized and normalized path
    
    Raises:
        TypeError: If input is None
        SecurityError: If path traversal or invalid path is detected
    """
    if path_input is None:
        raise TypeError('expected str, got NoneType')
    
    # Handle bytes input
    if isinstance(path_input, bytes):
        path_input = path_input.decode('utf-8', errors='replace')
    
    # Handle empty string
    if path_input == '':
        return ''
    
    # Detect null bytes
    if '\x00' in path_input:
        raise SecurityError('Null byte injection detected in path')
    
    # Normalize Unicode (handles fullwidth slashes etc.)
    path = unicodedata.normalize('NFKC', path_input)
    
    # Normalize Windows paths to Unix style
    path = path.replace('\\', '/')
    
    # Check for UNC paths
    if path.startswith('//'):
        raise SecurityError('UNC path detected')
    
    # Check for absolute paths
    if os.path.isabs(path) and not allow_absolute:
        raise SecurityError('Absolute path not allowed')
    
    # Normalize the path
    path = os.path.normpath(path)
    
    # Convert back to forward slashes for consistency
    path = path.replace('\\', '/')
    
    # Check for path traversal after normalization
    if '..' in path:
        raise SecurityError('Path traversal detected: .. component in path')
    
    # If base_dir is provided, validate the path stays within it
    if base_dir is not None:
        base = os.path.abspath(base_dir)
        
        # Handle relative paths by joining with base
        if not os.path.isabs(path):
            full_path = os.path.abspath(os.path.join(base, path))
        else:
            full_path = os.path.abspath(path)
        
        # Ensure the resolved path is within base directory
        if not full_path.startswith(base + os.sep) and full_path != base:
            raise SecurityError('Path traversal: resolved path outside base directory')
        
        return full_path
    
    return path


# Type hints for static analysis
__all__ = [
    'sanitize_html',
    'sanitize_sql', 
    'sanitize_path',
    'SecurityError'
]