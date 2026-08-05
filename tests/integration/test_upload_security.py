"""
Integration tests for upload endpoint security.
"""
import io
import pytest
from fastapi.testclient import TestClient

from appaveli_codemind.web_api.codemind_api import app
from appaveli_codemind.web_api.auth import get_api_key_manager
from appaveli_codemind.web_api.rate_limiter import get_upload_rate_limiter


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    """Create valid API key for testing."""
    manager = get_api_key_manager()
    api_key = manager.generate_api_key("test-upload-security", rate_limit=1000)
    return {"X-API-Key": api_key}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests."""
    limiter = get_upload_rate_limiter()
    limiter._requests.clear()
    yield
    limiter._requests.clear()


class TestUploadSecurity:
    """Integration tests for upload security features."""

    @pytest.mark.skip(reason="Requires API keys in CI environment")
    def test_valid_upload_succeeds(self, client, auth_headers):
        """Valid uploads should succeed (skipped in CI without API keys)."""
        files = {
            "file": ("test.py", io.BytesIO(b"print('hello')"), "text/x-python")
        }
        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )
        # Should either succeed (200) or fail at analysis stage (500), not validation
        assert response.status_code in [200, 500]

    def test_oversized_file_rejected(self, client, auth_headers):
        """Files exceeding size limit should be rejected."""
        # Create 11MB file (exceeds 10MB limit)
        large_content = b"x" * (11 * 1024 * 1024)
        files = {
            "file": ("large.py", io.BytesIO(large_content), "text/x-python")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_invalid_extension_rejected(self, client, auth_headers):
        """Files with invalid extensions should be rejected."""
        files = {
            "file": ("malware.exe", io.BytesIO(b"malicious"), "application/x-msdownload")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "unsupported file type" in response.json()["detail"].lower()

    def test_path_traversal_rejected(self, client, auth_headers):
        """Path traversal attempts should be rejected."""
        files = {
            "file": ("../../etc/passwd", io.BytesIO(b"malicious"), "text/plain")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "forbidden" in response.json()["detail"].lower()

    def test_rate_limiting_enforced(self, client, auth_headers):
        """Rate limiting should be enforced per IP."""
        # Use invalid extension to fail fast at validation (before analysis)
        # This ensures we hit rate limit without needing API keys

        responses = []
        for i in range(12):  # Try more than the limit (10)
            response = client.post(
                "/analyze/upload",
                files={"file": ("test.exe", io.BytesIO(b"malicious"), "application/x-msdownload")},
                headers=auth_headers,
            )
            responses.append(response.status_code)

            if response.status_code == 429:
                # Rate limit hit
                assert "rate limit" in response.json()["detail"].lower()
                assert "Retry-After" in response.headers
                break

        # Should have gotten 400 (validation error) up to 10 times, then 429
        assert 429 in responses, "Rate limit should have been enforced"
        assert responses.count(400) <= 10, "Should not get more than 10 validation errors"

    def test_refactor_endpoint_security(self, client, auth_headers):
        """Refactor endpoint should also have security checks."""
        # Invalid extension
        files = {
            "file": ("malware.exe", io.BytesIO(b"malicious"), "application/x-msdownload")
        }

        response = client.post(
            "/refactor/upload",
            files=files,
            data={"refactor_type": "general_cleanup"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_security_scan_endpoint_security(self, client, auth_headers):
        """Security scan endpoint should also have security checks."""
        # Path traversal
        files = {
            "file": ("../../../etc/passwd", io.BytesIO(b"malicious"), "text/plain")
        }

        response = client.post(
            "/security/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.skip(reason="Requires API keys in CI environment")
    def test_zip_upload_allowed_larger_size(self, client, auth_headers):
        """ZIP files should be allowed with larger size limit (skipped in CI)."""
        import zipfile
        from io import BytesIO

        # Create a ZIP file larger than normal limit but within ZIP limit
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add a file that makes the ZIP ~15MB (exceeds normal 10MB limit)
            large_content = b"x" * (15 * 1024 * 1024)
            zipf.writestr("large_file.py", large_content)

        zip_buffer.seek(0)
        zip_size = len(zip_buffer.getvalue())

        # Should be larger than normal limit
        assert zip_size > 10 * 1024 * 1024

        files = {
            "file": ("project.zip", zip_buffer, "application/zip")
        }

        response = client.post(
            "/security/upload",
            files=files,
            headers=auth_headers,
        )

        # Should pass validation (uses larger ZIP limit)
        # May fail at analysis if no API keys, but validation should pass
        assert response.status_code in [200, 500]

    def test_no_extension_rejected(self, client, auth_headers):
        """Files without extensions should be rejected."""
        files = {
            "file": ("README", io.BytesIO(b"# README"), "text/plain")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "extension" in response.json()["detail"].lower()

    @pytest.mark.skip(reason="Requires API keys in CI environment")
    def test_sanitized_filename_in_response(self, client, auth_headers):
        """Response should use sanitized filename (skipped in CI)."""
        # Upload with spaces and special chars that get sanitized
        files = {
            "file": ("my test file.py", io.BytesIO(b"print('hello')"), "text/x-python")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        # If analysis succeeds, check filename was sanitized
        if response.status_code == 200:
            assert response.json()["file_path"] == "my_test_file.py"
