"""
Rate limiting for file uploads to prevent abuse.
"""
import logging
import time
from collections import defaultdict
from typing import DefaultDict, Tuple

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Rate limit configuration
UPLOAD_RATE_LIMIT_PER_IP = 10  # Max uploads per window
UPLOAD_RATE_WINDOW_SECONDS = 60  # Time window in seconds


class UploadRateLimiter:
    """
    Simple in-memory rate limiter for file uploads.

    Tracks upload counts per IP address within a time window.
    For production, consider Redis-based rate limiting.
    """

    def __init__(
        self,
        max_requests: int = UPLOAD_RATE_LIMIT_PER_IP,
        window_seconds: int = UPLOAD_RATE_WINDOW_SECONDS,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # ip_address -> list of (timestamp, count) tuples
        self._requests: DefaultDict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        # Check X-Forwarded-For header first (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (client)
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    def _clean_old_requests(self, ip: str) -> None:
        """Remove requests outside the current time window."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Keep only requests within the window
        self._requests[ip] = [
            timestamp for timestamp in self._requests[ip]
            if timestamp > cutoff
        ]

    def check_rate_limit(self, request: Request) -> None:
        """
        Check if request is within rate limits.

        Args:
            request: The FastAPI request

        Raises:
            HTTPException: If rate limit exceeded
        """
        ip = self._get_client_ip(request)

        # Clean old requests
        self._clean_old_requests(ip)

        # Check current count
        current_count = len(self._requests[ip])

        if current_count >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for IP {ip}: {current_count} requests "
                f"in {self.window_seconds}s window"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded: maximum {self.max_requests} uploads "
                    f"per {self.window_seconds} seconds. Please try again later."
                ),
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record this request
        self._requests[ip].append(time.time())

        logger.debug(
            f"Rate limit check passed for IP {ip}: {current_count + 1}/{self.max_requests}"
        )


# Global rate limiter instance
_rate_limiter: UploadRateLimiter | None = None


def get_upload_rate_limiter() -> UploadRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = UploadRateLimiter()
    return _rate_limiter
