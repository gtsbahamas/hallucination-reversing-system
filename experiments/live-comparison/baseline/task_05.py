import hashlib
import mimetypes
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


class MalwareDetectedError(Exception):
    """Raised when malware signature is detected."""
    pass


class FileSizeExceededError(Exception):
    """Raised when file size exceeds limit."""
    pass


class FileTypeNotAllowedError(Exception):
    """Raised when file type is not allowed."""
    pass


class UploadStatus(Enum):
    """Status of file upload operation."""
    PENDING = "pending"
    VALIDATING = "validating"
    SCANNING = "scanning"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileMetadata:
    """Metadata for uploaded file."""
    file_id: str
    original_filename: str
    sanitized_filename: str
    content_type: str
    file_size: int
    checksum: str
    upload_timestamp: datetime
    s3_key: str
    s3_bucket: str
    status: UploadStatus


class MalwareScanner:
    """Simple signature-based malware scanner."""
    
    def __init__(self, signatures: Optional[List[bytes]] = None):
        """
        Initialize malware scanner with known malicious signatures.
        
        Args:
            signatures: List of byte signatures to scan for
        """
        self.signatures: Set[bytes] = set(signatures) if signatures else set()
        self._load_default_signatures()
    
    def _load_default_signatures(self) -> None:
        """Load default malicious file signatures."""
        # Common malware signatures (simplified examples)
        self.signatures.update([
            b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff',  # PE executable header
            b'<?php eval(',  # Suspicious PHP code
            b'<script>alert(',  # XSS patterns
            b'javascript:',  # JavaScript protocol
            b'vbscript:',  # VBScript protocol
            b'\x00\x00\x00\x20ftypmp42',  # Suspicious video formats
            b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE',  # EICAR test signature
        ])
    
    def add_signature(self, signature: bytes) -> None:
        """
        Add a new malware signature.
        
        Args:
            signature: Byte signature to add
        """
        self.signatures.add(signature)
    
    def scan(self, file_content: bytes, chunk_size: int = 8192) -> Tuple[bool, Optional[str]]:
        """
        Scan file content for malware signatures.
        
        Args:
            file_content: File content to scan
            chunk_size: Size of chunks to scan
            
        Returns:
            Tuple of (is_clean, detected_signature)
        """
        for signature in self.signatures:
            if signature in file_content:
                return False, signature.hex()
        
        # Additional heuristic checks
        if self._check_suspicious_patterns(file_content):
            return False, "suspicious_pattern_detected"
        
        return True, None
    
    def _check_suspicious_patterns(self, content: bytes) -> bool:
        """
        Check for suspicious patterns using heuristics.
        
        Args:
            content: File content to check
            
        Returns:
            True if suspicious patterns found
        """
        # Check for high entropy (potential encryption/obfuscation)
        if len(content) > 1024:
            sample = content[:1024]
            unique_bytes = len(set(sample))
            if unique_bytes > 200:  # High entropy threshold
                return True
        
        # Check for embedded executables
        suspicious_patterns = [
            rb'<\s*iframe',
            rb'<\s*object',
            rb'<\s*embed',
            rb'eval\s*\(',
            rb'exec\s*\(',
            rb'system\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False


class FileValidator:
    """Validates uploaded files against security policies."""
    
    ALLOWED_EXTENSIONS: Set[str] = {
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx',
        'xls', 'xlsx', 'txt', 'csv', 'zip', 'mp4', 'mp3'
    }
    
    ALLOWED_MIMETYPES: Set[str] = {
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain', 'text/csv',
        'application/zip',
        'video/mp4', 'audio/mpeg'
    }
    
    DANGEROUS_EXTENSIONS: Set[str] = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js',
        'jar', 'msi', 'dll', 'sh', 'py', 'rb', 'pl', 'php', 'asp'
    }
    
    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
        allowed_extensions: Optional[Set[str]] = None,
        allowed_mimetypes: Optional[Set[str]] = None
    ):
        """
        Initialize file validator.
        
        Args:
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: Set of allowed file extensions
            allowed_mimetypes: Set of allowed MIME types
        """
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or self.ALLOWED_EXTENSIONS
        self.allowed_mimetypes = allowed_mimetypes or self.ALLOWED_MIMETYPES
    
    def validate(self, filename: str, file_size: int, content_type: str, file_content: bytes) -> None:
        """
        Validate file against all security policies.
        
        Args:
            filename: Original filename
            file_size: Size of file in bytes
            content_type: MIME type of file
            file_content: File content for deep inspection
            
        Raises:
            FileSizeExceededError: If file size exceeds limit
            FileTypeNotAllowedError: If file type is not allowed
            FileValidationError: If file fails validation
        """
        self._validate_size(file_size)
        self._validate_filename(filename)
        self._validate_extension(filename)
        self._validate_mimetype(content_type)
        self._validate_content_matches_type(filename, content_type, file_content)
    
    def _validate_size(self, file_size: int) -> None:
        """Validate file size."""
        if file_size > self.max_file_size:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds maximum allowed size {self.max_file_size} bytes"
            )
        
        if file_size == 0:
            raise FileValidationError("File is empty")
    
    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security issues."""
        if not filename or filename.strip() == '':
            raise FileValidationError("Filename is empty")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise FileValidationError("Filename contains invalid path characters")
        
        # Check for null bytes
        if '\x00' in filename:
            raise FileValidationError("Filename contains null bytes")
        
        # Check for excessively long filenames
        if len(filename) > 255:
            raise FileValidationError("Filename is too long")
    
    def _validate_extension(self, filename: str) -> None:
        """Validate file extension."""
        extension = Path(filename).suffix.lower().lstrip('.')
        
        if not extension:
            raise FileTypeNotAllowedError("File has no extension")
        
        if extension in self.DANGEROUS_EXTENSIONS:
            raise FileTypeNotAllowedError(f"File extension .{extension} is not allowed for security reasons")
        
        if extension not in self.allowed_extensions:
            raise FileTypeNotAllowedError(f"File extension .{extension} is not allowed")
    
    def _validate_mimetype(self, content_type: str) -> None:
        """Validate MIME type."""
        if not content_type:
            raise FileValidationError("Content type is missing")
        
        if content_type not in self.allowed_mimetypes:
            raise FileTypeNotAllowedError(f"MIME type {content_type} is not allowed")
    
    def _validate_content_matches_type(self, filename: str, content_type: str, file_content: bytes) -> None:
        """
        Validate that file content matches declared type.
        
        Args:
            filename: Original filename
            content_type: Declared MIME type
            file_content: Actual file content
        """
        # Check magic bytes for common file types
        magic_bytes_map = {
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'%PDF-': 'application/pdf',
            b'PK\x03\x04': 'application/zip',
        }
        
        for magic, expected_type in magic_bytes_map.items():
            if file_content.startswith(magic):
                if content_type != expected_type and not content_type.startswith(expected_type.split('/')[0]):
                    raise FileValidationError(
                        f"File content type mismatch: declared as {content_type} but appears to be {expected_type}"
                    )
                return
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing potentially dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Get filename without path
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '_', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = filename.strip('._')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_file'
        
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]
        
        return f"{name}{ext}"


class S3FileUploadHandler:
    """Handles secure file uploads to S3-compatible storage."""
    
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: str = 'us-east-1',
        max_file_size: int = 10 * 1024 * 1024,
        allowed_extensions: Optional[Set[str]] = None,
        allowed_mimetypes: Optional[Set[str]] = None,
        storage_prefix: str = 'uploads/'
    ):
        """
        Initialize S3 file upload handler.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            endpoint_url: S3-compatible endpoint URL (for non-AWS providers)
            region_name: AWS region name
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: Set of allowed file extensions
            allowed_mimetypes: Set of allowed MIME types
            storage_prefix: Prefix for S3 object keys
        """
        self.bucket_name = bucket_name
        self.storage_prefix = storage_prefix.rstrip('/') + '/'
        
        # Initialize S3 client
        session_kwargs: Dict[str, Any] = {
            'region_name': region_name
        }
        
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = aws_access_key_id
            session_kwargs['aws_secret_access_key'] = aws_secret_access_key
        
        self.s3_client = boto3.client('s3', endpoint_url=endpoint_url, **session_kwargs)
        
        # Initialize validator and scanner
        self.validator = FileValidator(
            max_file_size=max_file_size,
            allowed_extensions=allowed_extensions,
            allowed_mimetypes=allowed_mimetypes
        )
        self.malware_scanner = MalwareScanner()
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                except ClientError as create_error:
                    raise RuntimeError(f"Failed to create bucket: {create_error}")
            else:
                raise RuntimeError(f"Bucket not accessible: {e}")
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> FileMetadata:
        """
        Upload file with validation, malware scanning, and storage.
        
        Args:
            file_obj: File object to upload
            filename: Original filename
            content_type: MIME type of file
            metadata: Additional metadata to store with file
            
        Returns:
            FileMetadata object containing upload information
            
        Raises:
            FileValidationError: If file validation fails
            MalwareDetectedError: If malware is detected
            FileSizeExceededError: If file size exceeds limit
            FileTypeNotAllowedError: If file type is not allowed
        """
        # Read file content
        file_content = file_obj.read()
        file_size = len(file_content)
        
        # Detect content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Validate file
        self.validator.