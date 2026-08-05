"""
File upload validation utilities for security hardening.
Implements comprehensive checks for file size, type, and content.
"""
import logging
import os
import re
from pathlib import Path
from typing import Optional, Set

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB default
MAX_ZIP_SIZE = int(os.getenv("MAX_ZIP_SIZE", 50 * 1024 * 1024))  # 50MB for project zips

# Allowed file extensions for code files
ALLOWED_EXTENSIONS: Set[str] = {
    ".java", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".swift", ".kt", ".kts", ".php", ".cpp", ".c",
    ".h", ".hpp", ".cs", ".go", ".rs", ".rb",
    ".pl", ".sh", ".bash", ".zsh", ".sql",
    ".zip",  # For project uploads
}

# Allowed MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    "text/plain",
    "text/x-python",
    "text/x-java",
    "text/javascript",
    "application/javascript",
    "text/x-c",
    "text/x-c++",
    "text/x-php",
    "text/x-ruby",
    "text/x-go",
    "text/x-rust",
    "text/x-swift",
    "application/zip",
    "application/x-zip-compressed",
    # Generic types that might be sent by browsers
    "application/octet-stream",  # Many browsers use this for unknown text files
}

# Dangerous filename patterns to reject
DANGEROUS_PATTERNS = [
    r"\.\.",  # Path traversal
    r"[<>:\"|?*]",  # Windows forbidden chars
    r"^/",  # Absolute paths
    r"\\",  # Backslashes
    r"^\.+$",  # Only dots
]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename from upload

    Returns:
        Sanitized filename safe for filesystem operations

    Raises:
        HTTPException: If filename contains dangerous patterns
    """
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, filename):
            logger.warning(f"Rejected dangerous filename pattern: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: contains forbidden characters or patterns",
            )

    # Extract just the filename (no path components)
    safe_name = Path(filename).name

    # Additional safety: replace any remaining suspicious chars
    safe_name = re.sub(r'[^\w\-\.]', '_', safe_name)

    # Ensure it's not empty after sanitization
    if not safe_name or safe_name == '_':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: no valid characters remaining after sanitization",
        )

    return safe_name


def validate_file_extension(filename: str, allowed_extensions: Optional[Set[str]] = None) -> str:
    """
    Validate file extension against allowlist.

    Args:
        filename: Filename to validate
        allowed_extensions: Optional custom set of allowed extensions

    Returns:
        The validated extension (lowercase)

    Raises:
        HTTPException: If extension is not allowed
    """
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    ext = Path(filename).suffix.lower()

    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension",
        )

    if ext not in extensions:
        logger.warning(f"Rejected file with unsupported extension: {ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(extensions))}",
        )

    return ext


def validate_mime_type(content_type: Optional[str]) -> None:
    """
    Validate MIME type against allowlist.

    Args:
        content_type: MIME type from upload

    Raises:
        HTTPException: If MIME type is not allowed
    """
    if not content_type:
        # Some clients don't send content type; we'll rely on extension validation
        logger.warning("Upload received without Content-Type header")
        return

    # Extract base type (ignore charset, etc.)
    base_type = content_type.split(';')[0].strip().lower()

    if base_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Rejected file with unsupported MIME type: {base_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {base_type}",
        )


async def validate_file_size(file: UploadFile, max_size: Optional[int] = None) -> int:
    """
    Validate file size by reading it.

    Args:
        file: The uploaded file
        max_size: Optional custom max size (bytes)

    Returns:
        The actual file size in bytes

    Raises:
        HTTPException: If file exceeds size limit
    """
    limit = max_size or MAX_FILE_SIZE

    # Try to get size from file object
    size = 0
    chunk_size = 8192

    # Read in chunks to avoid loading entire file into memory
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)

        if size > limit:
            logger.warning(f"Rejected oversized file: {size} bytes (limit: {limit})")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {size} bytes exceeds limit of {limit} bytes ({limit // (1024*1024)}MB)",
            )

    # Reset file position for subsequent processing
    await file.seek(0)

    logger.info(f"Validated file size: {size} bytes")
    return size


async def validate_upload(
    file: UploadFile,
    max_size: Optional[int] = None,
    allowed_extensions: Optional[Set[str]] = None,
) -> tuple[str, int]:
    """
    Comprehensive upload validation.

    Validates:
    - Filename safety (no path traversal, dangerous chars)
    - File extension against allowlist
    - MIME type against allowlist
    - File size limits

    Args:
        file: The uploaded file
        max_size: Optional custom max size
        allowed_extensions: Optional custom allowed extensions

    Returns:
        Tuple of (sanitized_filename, file_size_bytes)

    Raises:
        HTTPException: If any validation check fails
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # 1. Sanitize filename (checks for path traversal, etc.)
    safe_filename = sanitize_filename(file.filename)

    # 2. Validate extension
    ext = validate_file_extension(safe_filename, allowed_extensions)

    # 3. Validate MIME type
    validate_mime_type(file.content_type)

    # 4. Validate file size (use larger limit for zips)
    size_limit = MAX_ZIP_SIZE if ext == ".zip" else max_size
    file_size = await validate_file_size(file, size_limit)

    logger.info(
        f"Upload validated: filename={safe_filename}, size={file_size}, "
        f"type={file.content_type}, ext={ext}"
    )

    return safe_filename, file_size
