"""API middleware components."""

import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/response logging middleware.
    
    Logs all API requests with timing and correlation IDs.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("robin.api")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Log request
        start_time = time.time()
        
        self.logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        self.logger.info(
            f"Request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{round(duration * 1000, 2)}ms"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Limits requests per client IP to prevent abuse.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._request_counts = {}  # IP -> (count, window_start)
        self.logger = logging.getLogger("robin.api.ratelimit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Get or create rate limit entry
        if client_ip not in self._request_counts:
            self._request_counts[client_ip] = (1, current_time)
        else:
            count, window_start = self._request_counts[client_ip]
            
            # Check if we're in a new window
            if current_time - window_start > 60:
                self._request_counts[client_ip] = (1, current_time)
            else:
                # Check rate limit
                if count >= self.requests_per_minute:
                    self.logger.warning(f"Rate limit exceeded for {client_ip}")
                    return Response(
                        content='{"error": "Rate limit exceeded"}',
                        status_code=429,
                        media_type="application/json",
                        headers={
                            "Retry-After": str(int(60 - (current_time - window_start))),
                            "X-RateLimit-Limit": str(self.requests_per_minute),
                            "X-RateLimit-Remaining": "0",
                        }
                    )
                
                self._request_counts[client_ip] = (count + 1, window_start)
        
        # Add rate limit headers
        response = await call_next(request)
        
        count, _ = self._request_counts.get(client_ip, (0, 0))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - count))
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    API key authentication middleware.
    
    Validates API keys for protected endpoints.
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}
    
    def __init__(self, app, api_keys: set = None):
        super().__init__(app)
        self.api_keys = api_keys or set()
        self.logger = logging.getLogger("robin.api.auth")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip if no API keys configured (development mode)
        if not self.api_keys:
            return await call_next(request)
        
        # Check API key
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return Response(
                content='{"error": "API key required"}',
                status_code=401,
                media_type="application/json",
            )
        
        if api_key not in self.api_keys:
            self.logger.warning(f"Invalid API key attempt from {request.client.host}")
            return Response(
                content='{"error": "Invalid API key"}',
                status_code=403,
                media_type="application/json",
            )
        
        return await call_next(request)
