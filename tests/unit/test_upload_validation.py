"""
Unit tests for upload validation.
"""
import io
import pytest
from fastapi import HTTPException, UploadFile

from appaveli_codemind.web_api.upload_validation import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
    validate_upload,
)

# Configure pytest-anyio for async tests (asyncio backend only)
pytestmark = pytest.mark.anyio


def create_upload_file(filename: str, content: bytes, content_type: str = "text/plain") -> UploadFile:
    """Helper to create an UploadFile with content_type."""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers={"content-type": content_type} if content_type else None,
    )


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_valid_filename(self):
        """Valid filenames should pass through."""
        assert sanitize_filename("test.py") == "test.py"
        assert sanitize_filename("my_file-v2.java") == "my_file-v2.java"

    def test_path_traversal_rejected(self):
        """Path traversal attempts should be rejected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_filename("../etc/passwd")
        assert exc.value.status_code == 400
        assert "forbidden characters" in exc.value.detail.lower()

    def test_absolute_path_rejected(self):
        """Absolute paths should be rejected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_filename("/etc/passwd")
        assert exc.value.status_code == 400

    def test_backslash_rejected(self):
        """Backslashes should be rejected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_filename("folder\\file.py")
        assert exc.value.status_code == 400

    def test_windows_forbidden_chars_rejected(self):
        """Windows forbidden characters should be rejected."""
        for char in '<>:"|?*':
            with pytest.raises(HTTPException):
                sanitize_filename(f"file{char}.py")

    def test_only_dots_rejected(self):
        """Filenames with only dots should be rejected."""
        with pytest.raises(HTTPException):
            sanitize_filename("...")


class TestValidateFileExtension:
    """Tests for file extension validation."""

    def test_allowed_extensions(self):
        """Allowed extensions should pass."""
        for ext in [".py", ".java", ".js", ".ts", ".cpp"]:
            filename = f"test{ext}"
            assert validate_file_extension(filename) == ext

    def test_case_insensitive(self):
        """Extension check should be case-insensitive."""
        assert validate_file_extension("test.PY") == ".py"
        assert validate_file_extension("test.Java") == ".java"

    def test_no_extension_rejected(self):
        """Files without extensions should be rejected."""
        with pytest.raises(HTTPException) as exc:
            validate_file_extension("readme")
        assert exc.value.status_code == 400
        assert "must have an extension" in exc.value.detail.lower()

    def test_unsupported_extension_rejected(self):
        """Unsupported extensions should be rejected."""
        with pytest.raises(HTTPException) as exc:
            validate_file_extension("malware.exe")
        assert exc.value.status_code == 400
        assert "unsupported file type" in exc.value.detail.lower()
        assert ".exe" in exc.value.detail

    def test_custom_allowed_extensions(self):
        """Custom extension list should be respected."""
        custom = {".txt", ".md"}
        assert validate_file_extension("readme.txt", custom) == ".txt"

        with pytest.raises(HTTPException):
            validate_file_extension("code.py", custom)


class TestValidateMimeType:
    """Tests for MIME type validation."""

    def test_allowed_mime_types(self):
        """Allowed MIME types should pass."""
        validate_mime_type("text/plain")
        validate_mime_type("text/x-python")
        validate_mime_type("application/zip")

    def test_mime_type_with_charset(self):
        """MIME types with charset should be accepted."""
        validate_mime_type("text/plain; charset=utf-8")

    def test_missing_content_type(self):
        """Missing content type should not raise (logs warning)."""
        validate_mime_type(None)

    def test_unsupported_mime_type_rejected(self):
        """Unsupported MIME types should be rejected."""
        with pytest.raises(HTTPException) as exc:
            validate_mime_type("application/x-msdownload")
        assert exc.value.status_code == 400
        assert "invalid content type" in exc.value.detail.lower()


class TestValidateFileSize:
    """Tests for file size validation."""

    async def test_small_file_accepted(self):
        """Small files should be accepted."""
        content = b"print('hello')"
        file = UploadFile(filename="test.py", file=io.BytesIO(content))

        size = await validate_file_size(file)
        assert size == len(content)

    @pytest.mark.asyncio
    async def test_large_file_rejected(self):
        """Files exceeding size limit should be rejected."""
        # Create content larger than MAX_FILE_SIZE
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        file = UploadFile(filename="huge.py", file=io.BytesIO(large_content))

        with pytest.raises(HTTPException) as exc:
            await validate_file_size(file)

        assert exc.value.status_code == 413
        assert "file too large" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_custom_size_limit(self):
        """Custom size limits should be respected."""
        content = b"x" * 1000
        file = UploadFile(filename="test.py", file=io.BytesIO(content))

        # Should pass with large custom limit
        size = await validate_file_size(file, max_size=2000)
        assert size == 1000

        # Should fail with small custom limit
        file.file.seek(0)  # Reset
        with pytest.raises(HTTPException):
            await validate_file_size(file, max_size=500)

    @pytest.mark.asyncio
    async def test_file_position_reset(self):
        """File position should be reset after validation."""
        content = b"test content"
        file = UploadFile(filename="test.py", file=io.BytesIO(content))

        await validate_file_size(file)

        # Should be able to read from start
        assert file.file.read() == content


class TestValidateUpload:
    """Integration tests for complete upload validation."""

    async def test_valid_upload(self):
        """Valid uploads should pass all checks."""
        content = b"print('hello')"
        file = create_upload_file("test.py", content, "text/x-python")

        safe_name, size = await validate_upload(file)

        assert safe_name == "test.py"
        assert size == len(content)

    async def test_dangerous_filename_rejected(self):
        """Uploads with dangerous filenames should be rejected."""
        content = b"malicious"
        file = create_upload_file("../../../etc/passwd", content, "text/plain")

        with pytest.raises(HTTPException) as exc:
            await validate_upload(file)

        assert exc.value.status_code == 400

    async def test_invalid_extension_rejected(self):
        """Uploads with invalid extensions should be rejected."""
        content = b"malicious"
        file = create_upload_file("malware.exe", content, "application/x-msdownload")

        with pytest.raises(HTTPException) as exc:
            await validate_upload(file)

        assert exc.value.status_code == 400

    async def test_oversized_file_rejected(self):
        """Oversized uploads should be rejected."""
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        file = create_upload_file("huge.py", large_content, "text/x-python")

        with pytest.raises(HTTPException) as exc:
            await validate_upload(file)

        assert exc.value.status_code == 413

    async def test_zip_file_larger_limit(self):
        """ZIP files should use larger size limit."""
        # Create a ZIP-sized file that would exceed normal limit
        # but is within ZIP limit
        from appaveli_codemind.web_api.upload_validation import MAX_ZIP_SIZE

        zip_content = b"x" * (MAX_FILE_SIZE + 1000)  # Larger than normal limit
        assert len(zip_content) < MAX_ZIP_SIZE  # But within ZIP limit

        file = create_upload_file("project.zip", zip_content, "application/zip")

        # Should succeed (uses larger ZIP limit)
        safe_name, size = await validate_upload(file)
        assert safe_name == "project.zip"
        assert size == len(zip_content)
