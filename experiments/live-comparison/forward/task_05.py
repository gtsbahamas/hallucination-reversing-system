import hashlib
import logging
import mimetypes
import os
import re
import struct
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


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
        self.signatures.update([
            b'<?php eval(',
            b'<script>alert(',
            b'javascript:',
            b'vbscript:',
            b'\x00\x00\x00\x20ftypmp42',
            b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE',
        ])
    
    def add_signature(self, signature: bytes) -> None:
        """
        Add a new malware signature.
        
        Args:
            signature: Byte signature to add
        """
        self.signatures.add(signature)
    
    def scan(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Scan file content for malware signatures.
        
        Args:
            file_content: File content to scan
            
        Returns:
            Tuple of (is_clean, detected_signature)
        """
        # Check for PE executables
        is_pe, pe_reason = self._check_pe_executable(file_content)
        if is_pe:
            logger.warning(f"PE executable detected: {pe_reason}")
            return False, pe_reason
        
        # Check static signatures
        for signature in self.signatures:
            if signature in file_content:
                logger.warning(f"Malware signature detected: {signature.hex()}")
                return False, signature.hex()
        
        # Check for EICAR with variations
        normalized = re.sub(rb'\s+', b'', file_content)
        if b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' in normalized:
            logger.warning("EICAR test file detected")
            return False, "eicar_test_file"
        
        # Additional heuristic checks
        suspicious, reason = self._check_suspicious_patterns(file_content)
        if suspicious:
            logger.warning(f"Suspicious pattern detected: {reason}")
            return False, reason
        
        return True, None
    
    def _check_pe_executable(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Check if content is a PE executable.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (is_pe, reason)
        """
        if len(content) < 64:
            return False, None
            
        if not content.startswith(b'MZ'):
            return False, None
        
        try:
            pe_offset = struct.unpack('<I', content[0x3C:0x40])[0]
            if pe_offset < len(content) - 4:
                if content[pe_offset:pe_offset + 4] == b'PE\x00\x00':
                    return True, "pe_executable"
        except (struct.error, IndexError):
            pass
        
        return False, None
    
    def _check_suspicious_patterns(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Check for suspicious patterns using heuristics.
        
        Args:
            content: File content to check
            
        Returns:
            Tuple of (is_suspicious, reason)
        """
        suspicious_patterns = [
            rb'<\s*iframe',
            rb'<\s*object',
            rb'<\s*embed',
            rb'eval\s*\(',
            rb'exec\s*\(',
            rb'system\s*\(',
            rb'base64_decode\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, f"suspicious_pattern_{pattern.decode('utf-8', errors='ignore')}"
        
        return False, None


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
        'jar', 'msi', 'dll', 'sh', 'py', 'rb', 'pl', 'php', 'asp',
        'ps1', 'psm1', 'application', 'appref-ms', 'hta', 'cpl',
        'wsf', 'wsh', 'lnk', 'inf', 'reg'
    }
    
    MAGIC_BYTES_MAP: Dict[bytes, str] = {
        b'\xFF\xD8\xFF': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF-': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'\x00\x00\x00\x18ftypmp4': 'video/mp4',
        b'\x00\x00\x00\x20ftypmp42': 'video/mp4',
        b'ID3': 'audio/mpeg',
        b'\xFF\xFB': 'audio/mpeg',
        b'\xFF\xF3': 'audio/mpeg',
        b'\xFF\xF2': 'audio/mpeg',
        b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'application/msword',
        b'PK\x03\x04': 'application/vnd.openxmlformats-officedocument',
    }
    
    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,
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
        self.allowed_extensions = allowed_extensions or self.ALLOWED_EXTENSIONS.copy()
        self.allowed_mimetypes = allowed_mimetypes or self.ALLOWED_MIMETYPES.copy()
        self.dangerous_extensions = self.DANGEROUS_EXTENSIONS.copy()
    
    def add_dangerous_extension(self, extension: str) -> None:
        """Add a dangerous extension at runtime."""
        self.dangerous_extensions.add(extension.lower().lstrip('.'))
    
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
            logger.warning(f"File size exceeded: {file_size} > {self.max_file_size}")
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds maximum allowed size {self.max_file_size} bytes"
            )
        
        if file_size == 0:
            logger.warning("Empty file uploaded")
            raise FileValidationError("File is empty")
    
    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security issues."""
        if not filename or filename.strip() == '':
            raise FileValidationError("Filename is empty")
        
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Path traversal attempt in filename: {filename}")
            raise FileValidationError("Filename contains invalid path characters")
        
        if '\x00' in filename:
            logger.warning(f"Null byte in filename: {filename}")
            raise FileValidationError("Filename contains null bytes")
        
        if len(filename) > 255:
            logger.warning(f"Filename too long: {len(filename)} characters")
            raise FileValidationError("Filename is too long")
    
    def _validate_extension(self, filename: str) -> None:
        """Validate file extension including double extensions."""
        parts = filename.split('.')
        
        if len(parts) < 2:
            raise FileTypeNotAllowedError("File has no extension")
        
        # Check all extensions for dangerous ones
        extensions = [part.lower() for part in parts[1:]]
        
        for ext in extensions:
            if ext in self.dangerous_extensions:
                logger.warning(f"Dangerous extension detected: {ext} in {filename}")
                raise FileTypeNotAllowedError(
                    f"File extension .{ext} is not allowed for security reasons"
                )
        
        # Check final extension is allowed
        final_extension = extensions[-1]
        if final_extension not in self.allowed_extensions:
            logger.warning(f"Extension not allowed: {final_extension}")
            raise FileTypeNotAllowedError(f"File extension .{final_extension} is not allowed")
    
    def _validate_mimetype(self, content_type: str) -> None:
        """Validate MIME type."""
        if not content_type:
            raise FileValidationError("Content type is missing")
        
        base_type = content_type.split(';')[0].strip()
        
        is_allowed = False
        for allowed in self.allowed_mimetypes:
            if base_type == allowed or base_type.startswith(allowed.split('/')[0] + '/'):
                is_allowed = True
                break
        
        if not is_allowed:
            logger.warning(f"MIME type not allowed: {content_type}")
            raise FileTypeNotAllowedError(f"MIME type {content_type} is not allowed")
    
    def _validate_content_matches_type(self, filename: str, content_type: str, file_content: bytes) -> None:
        """
        Validate that file content matches declared type.
        
        Args:
            filename: Original filename
            content_type: Declared MIME type
            file_content: Actual file content
        """
        if len(file_content) < 16:
            return
        
        detected_type = None
        
        for magic, expected_type in self.MAGIC_BYTES_MAP.items():
            if file_content.startswith(magic):
                detected_type = expected_type
                break
        
        if detected_type:
            base_content_type = content_type.split(';')[0].strip()
            base_detected = detected_type.split(';')[0].strip()
            
            if base_detected.startswith('application/vnd.openxmlformats'):
                if not (base_content_type.startswith('application/vnd.openxmlformats') or 
                        base_content_type == 'application/zip'):
                    logger.warning(
                        f"Content type mismatch: declared {content_type}, detected {detected_type}"
                    )
                    raise FileValidationError(
                        f"File content type mismatch: declared as {content_type} but appears to be Office document"
                    )
            elif base_content_type != base_detected:
                content_category = base_content_type.split('/')[0]
                detected_category = base_detected.split('/')[0]
                
                if content_category != detected_category and detected_category != 'application':
                    logger.warning(
                        f"Content type mismatch: declared {content_type}, detected {detected_type}"
                    )
                    raise FileValidationError(
                        f"File content type mismatch: declared as {content_type} but appears to be {detected_type}"
                    )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing potentially dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        filename = os.path.basename(filename)
        
        filename = re.sub(r'[^\w\s\-\.]', '_', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = re.sub(r'\.{2,}', '.', filename)
        filename = filename.strip('._')
        
        if not filename:
            filename = 'unnamed_file'
        
        if '..' in filename or filename.startswith('.'):
            filename = 'safe_' + filename.lstrip('.')
        
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
        self.region_name = region_name
        self.storage_prefix = storage_prefix.rstrip('/') + '/'
        
        session_kwargs: Dict[str, Any] = {
            'region_name': region_name
        }
        
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = aws_access_key_id
            session_kwargs['aws_secret_access_key'] = aws_secret_access_key
        
        self.s3_client = boto3.client('s3', endpoint_url=endpoint_url, **session_kwargs)
        
        self.validator = FileValidator(
            max_file_size=max_file_size,
            allowed_extensions=allowed_extensions,
            allowed_mimetypes=allowed_mimetypes
        )
        self.malware_scanner = MalwareScanner()
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} is accessible")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                try:
                    if self.region_name != 'us-east-1':
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region_name}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise RuntimeError(f"Failed to create bucket: {create_error}")
            else:
                logger.error(f"Bucket not accessible: {e}")
                raise RuntimeError(f"Bucket not accessible: {e}")
    
    def _read_file_safely(self, file_obj: BinaryIO, max_size: int) -> bytes:
        """
        Read file in chunks to prevent memory exhaustion.
        
        Args:
            file_obj: File object to read
            max_size: Maximum allowed size
            
        Returns:
            File content as bytes
            
        Raises:
            FileSizeExceededError: If file exceeds max size
        """
        chunks = []
        total_size = 0
        chunk_size = 8192
        
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            
            total_size += len(chunk)
            if total_size > max_size:
                logger.warning(f"File size exceeded during read: {total_size} > {max_size}")
                raise FileSizeExceededError(
                    f"File size exceeds maximum allowed size {max_size} bytes"
                )
            
            chunks.append(chunk)
        
        return b''.join(chunks)
    
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
        if not hasattr(file_obj, 'read') or not callable(file_obj.read):
            raise TypeError('file_obj must be a file-like object with read() method')
        
        status = UploadStatus.VALIDATING
        file_content = None
        
        try:
            logger.info(f"Starting upload for file: {filename}")
            
            file_content = self._read_file_safely(file_obj, self.validator.max_file_size)
            file_size = len(file_content)
            
            if not content_type:
                guessed_type = mimetypes.guess_type(filename)[0]
                if guessed_type and guessed_type in self.validator.allowed_mimetypes:
                    content_type = guessed_type
                else:
                    content_type = 'application/octet-stream'
            
            self.validator.validate(filename, file_size, content_type, file_content)
            logger.info(f"File validation passed: {filename}")
            
            status = UploadStatus.SCANNING
            is_clean, detected_signature = self.malware_scanner.scan(file_content)
            if not is_clean:
                logger.error(f"Malware detected in {filename}: {detected_signature}")
                raise MalwareDetectedError(
                    f"Malware detected in file: signature {detected_signature}"
                )
            logger.info(f"Malware scan passed: {filename}")
            
            file_id = str(uuid4())
            sanitized_filename = self.validator.sanitize_filename(filename)
            
            checksum = hashlib.sha256(file_content).hexdigest()
            
            timestamp = datetime.utcnow()
            date_prefix = timestamp.strftime('%Y/%m/%d')
            s3_key = f"{self.storage_prefix}{date_prefix}/{file_id}_{sanitized_filename}"
            
            status = UploadStatus.UPLOADING
            
            upload_metadata = metadata or {}
            upload_metadata.update({
                'original-filename': filename,
                'file-id': file_id,
                'checksum': checksum,
                'upload-timestamp': timestamp.isoformat()
            })
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata=upload_metadata
            )
            
            logger.info(f"File uploaded successfully: {s3_key}")
            status = UploadStatus.COMPLETED
            
            return FileMetadata(
                file_id=file_id,
                original_filename=filename,
                sanitized_filename=sanitized_filename,
                content_type=content_type,
                file_size=file_size,
                checksum=checksum,
                upload_timestamp=timestamp,
                s3_key=s3_key,
                s3_bucket=self.bucket_name,
                status=status
            )
            
        except (FileValidationError, MalwareDetectedError, FileSizeExceededError, 
                FileTypeNotAllowedError) as e:
            logger.error(f"Upload failed for {filename}: {e}")
            status = UploadStatus.FAILED
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upload of {filename}: {e}")
            status = UploadStatus.FAILED
            raise
        finally:
            try:
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
            except Exception:
                pass