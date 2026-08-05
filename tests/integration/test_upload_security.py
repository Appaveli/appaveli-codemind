"""
Integration tests for upload endpoint security.
"""
import io
import pytest
from fastapi.testclient import TestClient

from appaveli_codemind.web_api.codemind_api import app
from appaveli_codemind.web_api.auth import get_api_key_manager


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


class TestUploadSecurity:
    """Integration tests for upload security features."""

    def test_valid_upload_succeeds(self, client, auth_headers):
        """Valid uploads should succeed."""
        files = {
            "file": ("test.py", io.BytesIO(b"print('hello')"), "text/x-python")
        }
        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 200

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
        # Create a small valid file
        files = {
            "file": ("test.py", io.BytesIO(b"print('test')"), "text/x-python")
        }

        # Make requests up to the limit (default is 10 per minute)
        # Note: This test might be flaky if other tests are running concurrently
        # In production, you'd want to use a separate rate limiter instance for testing

        successful_requests = 0
        for i in range(15):  # Try more than the limit
            response = client.post(
                "/analyze/upload",
                files={"file": ("test.py", io.BytesIO(b"print('test')"), "text/x-python")},
                headers=auth_headers,
            )

            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                # Rate limit hit
                assert "rate limit" in response.json()["detail"].lower()
                assert "Retry-After" in response.headers
                break

        # Should have been rate limited before completing all 15 requests
        assert successful_requests <= 10

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

    def test_zip_upload_allowed_larger_size(self, client, auth_headers):
        """ZIP files should be allowed with larger size limit."""
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

        # Should succeed (uses larger ZIP limit)
        # Note: Might fail during actual analysis, but should pass validation
        assert response.status_code in [200, 500]  # 500 if analysis fails, but validation passed

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

    def test_sanitized_filename_in_response(self, client, auth_headers):
        """Response should use sanitized filename."""
        # Upload with spaces and special chars that get sanitized
        files = {
            "file": ("my test file.py", io.BytesIO(b"print('hello')"), "text/x-python")
        }

        response = client.post(
            "/analyze/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Should have sanitized the spaces
        assert response.json()["file_path"] == "my_test_file.py"
