"""
Unit tests for upload rate limiting.
"""
import time
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock

from appaveli_codemind.web_api.rate_limiter import UploadRateLimiter


class TestUploadRateLimiter:
    """Tests for the upload rate limiter."""

    def create_mock_request(self, ip: str = "127.0.0.1"):
        """Create a mock FastAPI request with the given IP."""
        request = Mock()
        request.client = Mock()
        request.client.host = ip
        request.headers = {}
        return request

    def test_allow_within_limit(self):
        """Requests within limit should be allowed."""
        limiter = UploadRateLimiter(max_requests=5, window_seconds=60)
        request = self.create_mock_request()

        # Should allow up to max_requests
        for _ in range(5):
            limiter.check_rate_limit(request)  # Should not raise

    def test_reject_over_limit(self):
        """Requests exceeding limit should be rejected."""
        limiter = UploadRateLimiter(max_requests=3, window_seconds=60)
        request = self.create_mock_request()

        # Use up the limit
        for _ in range(3):
            limiter.check_rate_limit(request)

        # Next request should be rejected
        with pytest.raises(HTTPException) as exc:
            limiter.check_rate_limit(request)

        assert exc.value.status_code == 429
        assert "rate limit exceeded" in exc.value.detail.lower()
        assert "Retry-After" in exc.value.headers

    def test_different_ips_independent(self):
        """Different IPs should have independent rate limits."""
        limiter = UploadRateLimiter(max_requests=2, window_seconds=60)

        ip1_request = self.create_mock_request("192.168.1.1")
        ip2_request = self.create_mock_request("192.168.1.2")

        # IP1 uses its limit
        limiter.check_rate_limit(ip1_request)
        limiter.check_rate_limit(ip1_request)

        # IP2 should still be able to make requests
        limiter.check_rate_limit(ip2_request)
        limiter.check_rate_limit(ip2_request)

        # Both should now be at limit
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(ip1_request)

        with pytest.raises(HTTPException):
            limiter.check_rate_limit(ip2_request)

    def test_window_expiration(self):
        """Requests should be allowed again after window expires."""
        # Use very short window for testing
        limiter = UploadRateLimiter(max_requests=2, window_seconds=1)
        request = self.create_mock_request()

        # Use up the limit
        limiter.check_rate_limit(request)
        limiter.check_rate_limit(request)

        # Should be rejected immediately
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request)

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        limiter.check_rate_limit(request)  # Should not raise

    def test_x_forwarded_for_header(self):
        """Should use X-Forwarded-For header when present."""
        limiter = UploadRateLimiter(max_requests=2, window_seconds=60)

        # Request with X-Forwarded-For header
        request = Mock()
        request.client = Mock()
        request.client.host = "10.0.0.1"  # Internal proxy IP
        request.headers = {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"}

        # Should use the first IP from X-Forwarded-For
        limiter.check_rate_limit(request)
        limiter.check_rate_limit(request)

        # Should be limited based on forwarded IP, not proxy IP
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request)

        # Request from proxy IP directly should still work
        direct_request = self.create_mock_request("10.0.0.1")
        limiter.check_rate_limit(direct_request)  # Should not raise

    def test_no_client_ip(self):
        """Should handle requests without client IP gracefully."""
        limiter = UploadRateLimiter(max_requests=2, window_seconds=60)

        request = Mock()
        request.client = None
        request.headers = {}

        # Should use "unknown" as IP and still rate limit
        limiter.check_rate_limit(request)
        limiter.check_rate_limit(request)

        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request)

    def test_cleanup_old_requests(self):
        """Old requests should be cleaned up automatically."""
        limiter = UploadRateLimiter(max_requests=2, window_seconds=1)
        request = self.create_mock_request()

        # Make requests
        limiter.check_rate_limit(request)
        limiter.check_rate_limit(request)

        # At limit
        assert len(limiter._requests["127.0.0.1"]) == 2

        # Wait for expiration
        time.sleep(1.1)

        # Next check should clean up old requests
        limiter.check_rate_limit(request)

        # Should only have the new request
        assert len(limiter._requests["127.0.0.1"]) == 1
