"""
Authentication and rate limiting middleware for CodeMind Web API
"""
from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import get_api_key_manager


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication on all protected endpoints.

    Checks for X-API-Key header and validates it against stored keys.
    Also enforces rate limiting per API key.
    """

    # Endpoints that don't require API key authentication
    # Admin endpoints use separate X-Admin-Key authentication
    PUBLIC_ENDPOINTS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api-keys/create",
        "/api-keys/list",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_ENDPOINTS:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing API key. Include X-API-Key header.",
                    "error": "unauthorized",
                },
            )

        # Validate the API key
        manager = get_api_key_manager()
        key_obj = manager.validate_key(api_key)

        if not key_obj:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid API key.",
                    "error": "unauthorized",
                },
            )

        # Check rate limit
        if not manager.check_rate_limit(key_obj):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Limit: {key_obj.rate_limit} requests per minute.",
                    "error": "rate_limit_exceeded",
                    "rate_limit": key_obj.rate_limit,
                },
            )

        # Add key info to request state for logging/tracking
        request.state.api_key_id = key_obj.key_id
        request.state.api_key_name = key_obj.name

        # Proceed with the request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(key_obj.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            key_obj.rate_limit - key_obj.request_count
        )

        return response
