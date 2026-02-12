import hashlib
import io
import logging
import mimetypes
import os
import re
import secrets
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, List, Set, Dict, Any, BinaryIO
import uuid

try:
    import magic
except ImportError:
    magic = None

try:
    import boto3
    from botocore.exceptions import ClientError
    from boto3.s3.transfer import TransferConfig
except ImportError:
    boto3 = None
    ClientError = Exception
    TransferConfig = None

try:
    from PIL import Image
except ImportError:
    Image = None


logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class FileSizeError(Exception):
    """Raised when file exceeds size limit."""
    pass


class MalwareDetectedError(Exception):
    """Raised when malware signature is detected."""
    pass


class ValidationError(Exception):
    """Raised when file validation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class StorageError(Exception):
    """Raised when storage operation fails."""
    pass


@dataclass
class UploadResult:
    """Result of file upload operation."""
    success: bool
    url: Optional[str] = None
    size: Optional[int] = None
    content_type: Optional[str] = None
    key: Optional[str] = None
    would_succeed: Optional[bool] = None


class FileUploadHandler:
    """Handles secure file uploads with validation and malware scanning."""
    
    BLOCKED_EXTENSIONS: Set[str] = {
        '.exe', '.bat', '.sh', '.cmd', '.com', 
        '.ps1', '.scr', '.msi', '.dll'
    }
    
    BLOCKED_MIMES: Set[str] = {
        'application/x-executable',
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-sh',
        'application/x-shellscript'
    }
    
    EICAR_SIGNATURE: bytes = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    
    MALWARE_SIGNATURES: List[bytes] = [
        EICAR_SIGNATURE,
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR',
    ]
    
    SCRIPT_PATTERNS: List[re.Pattern] = [
        re.compile(rb'<script[\s>]', re.IGNORECASE),
        re.compile(rb'on\w+\s*=', re.IGNORECASE),
        re.compile(rb'javascript:', re.IGNORECASE),
        re.compile(rb'/JavaScript', re.IGNORECASE),
        re.compile(rb'/JS', re.IGNORECASE),
    ]
    
    MAX_FILENAME_LENGTH: int = 255
    CHUNK_SIZE: int = 65536
    MULTIPART_THRESHOLD: int = 100 * 1024 * 1024
    MALWARE_SCAN_TIMEOUT: float = 5.0
    MAX_COMPRESSION_RATIO: float = 100.0
    
    def __init__(
        self,
        allowed_types: Optional[List[str]] = None,
        size_limit: Union[int, str] = '100MB',
        s3_access_key: Optional[str] = None,
        s3_secret_key: Optional[str] = None,
        s3_endpoint: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        s3_region: Optional[str] = 'us-east-1',
        user_id: Optional[str] = None
    ):
        """Initialize file upload handler with configuration.
        
        Args:
            allowed_types: List of allowed MIME types (whitelist)
            size_limit: Maximum file size (e.g., '100MB' or bytes as int)
            s3_access_key: S3 access key
            s3_secret_key: S3 secret key
            s3_endpoint: S3 endpoint URL
            s3_bucket: S3 bucket name
            s3_region: S3 region
            user_id: User identifier for audit logging
        """
        if not allowed_types:
            raise ConfigurationError('allowed_types must be configured')
        
        if not s3_access_key or not s3_secret_key:
            raise ConfigurationError('S3 credentials (s3_access_key and s3_secret_key) must be configured')
        
        if not s3_bucket:
            raise ConfigurationError('s3_bucket must be configured')
        
        self.allowed_types: Set[str] = set(allowed_types)
        self.size_limit: int = self._parse_size_limit(size_limit)
        self.s3_access_key: str = s3_access_key
        self.s3_secret_key: str = s3_secret_key
        self.s3_endpoint: Optional[str] = s3_endpoint
        self.s3_bucket: str = s3_bucket
        self.s3_region: str = s3_region
        self.user_id: Optional[str] = user_id
        
        if not boto3:
            raise ConfigurationError('boto3 library is required for S3 operations')
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint,
            region_name=s3_region
        )
    
    def _parse_size_limit(self, limit: Union[int, str]) -> int:
        """Parse size limit from string or int to bytes.
        
        Args:
            limit: Size limit as string ('10MB', '1GB') or integer bytes
            
        Returns:
            Size limit in bytes
        """
        if isinstance(limit, int):
            return limit
        
        match = re.match(r'^(\d+)(KB|MB|GB)$', limit.upper())
        if not match:
            raise ValidationError(f'Invalid size limit format: {limit}')
        
        value = int(match.group(1))
        unit = match.group(2)
        
        multipliers = {
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        return value * multipliers[unit]
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename or not filename.strip():
            raise ValidationError('invalid filename: cannot be empty or whitespace-only')
        
        filename = filename.strip()
        
        if len(filename) > self.MAX_FILENAME_LENGTH:
            raise ValidationError(f'filename exceeds maximum length of {self.MAX_FILENAME_LENGTH} characters')
        
        filename = os.path.basename(filename)
        filename = filename.replace('..', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        
        try:
            filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        except Exception:
            pass
        
        if not filename or not filename.strip():
            raise ValidationError('invalid filename after sanitization')
        
        return filename
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename.
        
        Args:
            filename: Filename
            
        Returns:
            File extension (lowercase, including dot)
        """
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[-1].lower()
        return ''
    
    def _check_double_extension(self, filename: str) -> None:
        """Check for dangerous double extensions.
        
        Args:
            filename: Filename to check
            
        Raises:
            SecurityError: If double extension detected
        """
        filename_lower = filename.lower()
        
        for blocked_ext in self.BLOCKED_EXTENSIONS:
            if blocked_ext in filename_lower and not filename_lower.endswith(blocked_ext):
                parts = filename_lower.split('.')
                if len(parts) > 2:
                    for i in range(len(parts) - 1):
                        potential_ext = '.' + parts[i + 1]
                        if potential_ext in self.BLOCKED_EXTENSIONS:
                            raise SecurityError(f'dangerous double extension detected: {filename}')
    
    def _validate_extension(self, filename: str) -> None:
        """Validate file extension against blacklist.
        
        Args:
            filename: Filename to validate
            
        Raises:
            SecurityError: If extension is blocked
        """
        extension = self._get_file_extension(filename)
        
        if extension in self.BLOCKED_EXTENSIONS:
            raise SecurityError(f'executable file type not allowed: {extension}')
    
    def _detect_mime_type(self, content: bytes, filename: str) -> str:
        """Detect MIME type from file content.
        
        Args:
            content: File content
            filename: Original filename
            
        Returns:
            Detected MIME type
        """
        if magic:
            try:
                mime_type = magic.from_buffer(content, mime=True)
                return mime_type
            except Exception as e:
                logger.warning(f'Failed to detect MIME type with magic: {e}')
        
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _validate_mime_type(self, mime_type: str, content: bytes, filename: str) -> None:
        """Validate MIME type against whitelist and blacklist.
        
        Args:
            mime_type: Detected MIME type
            content: File content
            filename: Original filename
            
        Raises:
            SecurityError: If MIME type is blocked
            ValidationError: If MIME type not in whitelist or mismatched
        """
        if mime_type in self.BLOCKED_MIMES:
            raise SecurityError(f'blocked MIME type: {mime_type}')
        
        if mime_type not in self.allowed_types:
            raise ValidationError(f'MIME type not allowed: {mime_type}')
        
        guessed_mime, _ = mimetypes.guess_type(filename)
        if guessed_mime and guessed_mime != mime_type:
            logger.warning(f'MIME type mismatch: detected={mime_type}, expected={guessed_mime}')
    
    def _scan_for_malware(self, content: bytes, filename: str) -> None:
        """Scan file content for malware signatures.
        
        Args:
            content: File content
            filename: Original filename
            
        Raises:
            MalwareDetectedError: If malware signature detected
        """
        for signature in self.MALWARE_SIGNATURES:
            if signature in content:
                self._log_security_event(
                    'malware_detected',
                    filename=filename,
                    reason='EICAR signature detected'
                )
                raise MalwareDetectedError('EICAR signature detected')
    
    def _check_embedded_scripts(self, content: bytes, mime_type: str, filename: str) -> None:
        """Check for embedded scripts in document files.
        
        Args:
            content: File content
            mime_type: MIME type
            filename: Original filename
            
        Raises:
            SecurityError: If embedded script detected
        """
        if mime_type in ['image/svg+xml', 'text/html', 'application/pdf']:
            for pattern in self.SCRIPT_PATTERNS:
                if pattern.search(content):
                    self._log_security_event(
                        'embedded_script_detected',
                        filename=filename,
                        reason=f'embedded script detected in {mime_type}'
                    )
                    raise SecurityError('embedded script detected')
    
    def _check_zip_bomb(self, content: bytes, mime_type: str, filename: str) -> None:
        """Check for ZIP bomb attacks.
        
        Args:
            content: File content
            mime_type: MIME type
            filename: Original filename
            
        Raises:
            MalwareDetectedError: If suspicious compression ratio detected
        """
        if mime_type in ['application/zip', 'application/x-zip-compressed', 
                         'application/gzip', 'application/x-gzip']:
            compressed_size = len(content)
            
            try:
                import zipfile
                import gzip
                
                if mime_type.startswith('application/zip'):
                    with io.BytesIO(content) as f:
                        with zipfile.ZipFile(f) as zf:
                            uncompressed_size = sum(info.file_size for info in zf.infolist())
                            
                            if compressed_size > 0:
                                ratio = uncompressed_size / compressed_size
                                if ratio > self.MAX_COMPRESSION_RATIO:
                                    self._log_security_event(
                                        'zip_bomb_detected',
                                        filename=filename,
                                        reason=f'suspicious compression ratio: {ratio:.1f}:1'
                                    )
                                    raise MalwareDetectedError('suspicious compression ratio detected')
                
            except (zipfile.BadZipFile, OSError, RuntimeError) as e:
                logger.warning(f'Failed to analyze archive: {e}')
    
    def _strip_exif_metadata(self, content: bytes, mime_type: str) -> bytes:
        """Strip EXIF metadata from images.
        
        Args:
            content: Image content
            mime_type: MIME type
            
        Returns:
            Image content without EXIF data
        """
        if not Image:
            return content
        
        if mime_type.startswith('image/'):
            try:
                with io.BytesIO(content) as f:
                    img = Image.open(f)
                    
                    data = list(img.getdata())
                    img_clean = Image.new(img.mode, img.size)
                    img_clean.putdata(data)
                    
                    output = io.BytesIO()
                    img_clean.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
            except Exception as e:
                logger.warning(f'Failed to strip EXIF data: {e}')
                return content
        
        return content
    
    def _generate_storage_key(self, filename: str) -> str:
        """Generate unique storage key.
        
        Args:
            filename: Original filename
            
        Returns:
            Unique storage key
        """
        extension = self._get_file_extension(filename)
        safe_extension = extension if extension else ''
        
        unique_id = uuid.uuid4().hex
        storage_key = f'{unique_id}{safe_extension}'
        
        return storage_key
    
    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of content.
        
        Args:
            content: File content
            
        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(content).hexdigest()
    
    def _read_file_content(
        self,
        file: Union[str, bytes, BinaryIO],
        filename: Optional[str] = None
    ) -> tuple[bytes, str]:
        """Read file content with size validation.
        
        Args:
            file: File path, bytes, or file-like object
            filename: Original filename (if file is bytes or file-like)
            
        Returns:
            Tuple of (content, filename)
            
        Raises:
            FileSizeError: If file exceeds size limit
            ValidationError: If file is empty
        """
        content = b''
        cumulative_size = 0
        
        if isinstance(file, bytes):
            content = file
            cumulative_size = len(content)
            if not filename:
                filename = 'uploaded_file'
        
        elif hasattr(file, 'read'):
            chunks = []
            while True:
                chunk = file.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                
                cumulative_size += len(chunk)
                if cumulative_size > self.size_limit:
                    raise FileSizeError(f'file size exceeds limit of {self.size_limit} bytes')
                
                chunks.append(chunk)
            
            content = b''.join(chunks)
            
            if hasattr(file, 'name') and not filename:
                filename = os.path.basename(file.name)
            elif not filename:
                filename = 'uploaded_file'
        
        elif isinstance(file, (str, Path)):
            file_path = Path(file)
            
            if not file_path.exists():
                raise ValidationError(f'file does not exist: {file_path}')
            
            if not file_path.is_file():
                raise ValidationError(f'not a file: {file_path}')
            
            file_size = file_path.stat().st_size
            
            if file_size > self.size_limit:
                raise FileSizeError(f'file size exceeds limit of {self.size_limit} bytes')
            
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except (OSError, IOError) as e:
                raise ValidationError(f'failed to read file: {e}')
            
            filename = file_path.name
        
        else:
            raise ValidationError(f'unsupported file type: {type(file)}')
        
        if cumulative_size == 0 or len(content) == 0:
            raise ValidationError('file is empty (0 bytes)')
        
        if cumulative_size <= self.size_limit:
            pass
        else:
            raise FileSizeError(f'file size exceeds limit of {self.size_limit} bytes')
        
        return content, filename
    
    def _upload_to_s3(
        self,
        content: bytes,
        storage_key: str,
        mime_type: str,
        filename: str
    ) -> str:
        """Upload file to S3.
        
        Args:
            content: File content
            storage_key: Storage key
            mime_type: MIME type
            filename: Original filename
            
        Returns:
            S3 URL
            
        Raises:
            StorageError: If upload fails
        """
        try:
            file_obj = io.BytesIO(content)
            
            extra_args = {
                'ContentType': mime_type,
                'ContentDisposition': f'attachment; filename="{filename}"'
            }
            
            if len(content) > self.MULTIPART_THRESHOLD:
                transfer_config = TransferConfig(
                    multipart_threshold=self.MULTIPART_THRESHOLD,
                    multipart_chunksize=8 * 1024 * 1024
                )
                
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.s3_bucket,
                    storage_key,
                    ExtraArgs=extra_args,
                    Config=transfer_config
                )
            else:
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.s3_bucket,
                    storage_key,
                    ExtraArgs=extra_args
                )
            
            if self.s3_endpoint:
                url = f'{self.s3_endpoint}/{self.s3_bucket}/{storage_key}'
            else:
                url = f'https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{storage_key}'
            
            return url
            
        except ClientError as e:
            logger.error(f'S3 upload failed: {e}')
            raise StorageError('Storage service unavailable') from e
        except Exception as e:
            logger.error(f'Unexpected error during upload: {e}')
            raise StorageError('Storage operation failed') from e
    
    def _log_security_event(
        self,
        event_type: str,
        filename: str,
        reason: str
    ) -> None:
        """Log security-relevant events for audit trail.
        
        Args:
            event_type: Type of security event
            filename: Original filename
            reason: Reason for event
        """
        from datetime import datetime, timezone
        
        logger.warning(
            f'Security: {event_type}',
            extra={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'filename': filename,
                'reason': reason,
                'user_id': self.user_id,
                'event_type': event_type
            }
        )
    
    def upload_file(
        self,
        file: Union[str, bytes, BinaryIO, None],
        filename: Optional[str] = None,
        dry_run: bool = False
    ) -> UploadResult:
        """Upload file with validation and malware scanning.
        
        Args:
            file: File to upload (path, bytes, or file-like object)
            filename: Original filename (optional if file is path or has .name)
            dry_run: If True, validate but don't actually upload
            
        Returns:
            UploadResult with upload details
            
        Raises:
            ValueError: If file is None
            SecurityError: If security validation fails
            ValidationError: If file validation fails
            FileSizeError: If file exceeds size limit
            MalwareDetectedError: If malware detected
            StorageError: If storage operation fails
        """
        temp_file = None
        
        try:
            if file is None:
                raise ValueError('file cannot be None')
            
            content, detected_filename = self._read_file_content(file, filename)
            
            filename = filename or detected_filename
            sanitized_filename = self._sanitize_filename(filename)
            
            self._validate_extension(sanitized_filename)
            self._check_double_extension(sanitized_filename)
            
            mime_type = self._detect_mime_type(content, sanitized_filename)
            
            self._validate_mime_type(mime_type, content, sanitized_filename)
            
            self._scan_for_malware(content, sanitized_filename)
            
            self._check_embedded_scripts(content, mime_type, sanitized_filename)
            
            self._check_zip_bomb(content, mime_type, sanitized_filename)
            
            content = self._strip_exif_metadata(content, mime_type)
            
            original_hash = self._compute_hash(content)
            
            if dry_run:
                return UploadResult(
                    success=False,
                    would_succeed=True,
                    url=None,
                    size=len(content),
                    content_type=mime_type,
                    key=None
                )
            
            storage_key = self._generate_storage_key(sanitized_filename)
            
            url = self._upload_to_s3(content, storage_key, mime_type, sanitized_filename)
            
            return UploadResult(
                success=True,
                url=url,
                size=len(content),
                content_type=mime_type,
                key=storage_key
            )
            
        except (SecurityError, ValidationError, FileSizeError, MalwareDetectedError, 
                StorageError, ConfigurationError, ValueError) as e:
            if filename:
                self._log_security_event(
                    'file_rejected',
                    filename=filename or 'unknown',
                    reason=str(e)
                )
            raise
            
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f'Failed to cleanup temp file: {e}')


def upload_file(
    file: Union[str, bytes, BinaryIO, None],
    allowed_types: Optional[List[str]] = None,
    size_limit: Union[int, str] = '100MB',
    s3_access_key: Optional[str] = None,
    s3_secret_key: Optional[str] = None,
    s3_endpoint: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    s3_region: str = 'us-east-1',
    filename: Optional[str] = None,
    dry_run: bool = False,
    user_id: Optional[str] = None
) -> UploadResult:
    """Upload file with validation and malware scanning.
    
    Args:
        file: File to upload (path, bytes, or file-like object)
        allowed_types: List of allowed MIME types
        size_limit: Maximum file size (e.g., '100MB' or bytes as int)
        s3_access_key: S3 access key
        s3_secret_key: S3 secret key
        s3_endpoint: S3 endpoint URL
        s3_bucket: S3 bucket name
        s3_region: S3 region
        filename: Original filename (optional)
        dry_run: If True, validate but don't actually upload
        user_id: User identifier for audit logging
        
    Returns:
        UploadResult with upload details
    """
    handler = FileUploadHandler(
        allowed_types=allowed_types,
        size_limit=size_limit,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key,
        s3_endpoint=s3_endpoint,
        s3_bucket=s3_bucket,
        s3_region=s3_region,
        user_id=user_id
    )
    
    return handler.upload_file(file, filename=filename, dry_run=dry_run)