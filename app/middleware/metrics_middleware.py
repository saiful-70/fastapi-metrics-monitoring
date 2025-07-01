"""
FastAPI middleware for HTTP metrics collection
"""
import time
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..metrics.http_metrics import http_metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics automatically
    """
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        """
        Initialize metrics middleware
        
        Args:
            app: ASGI application
            exclude_paths: List of paths to exclude from metrics collection
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/metrics']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each HTTP request and collect metrics
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from the application
        """
        # Skip metrics collection for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract request information
        method = request.method
        path = request.url.path
        
        # Get request size
        request_size = None
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length:
                try:
                    request_size = int(content_length)
                except ValueError:
                    pass
        
        # Start tracking the request
        request_id = http_metrics.start_request(
            method=method,
            path=path,
            request_size=request_size
        )
        
        # Initialize response variables
        status_code = 500
        response_size = None
        error_type = None
        
        try:
            # Process the request
            start_time = time.time()
            response = await call_next(request)
            
            # Extract response information
            status_code = response.status_code
            
            # Get response size if available
            if hasattr(response, 'headers'):
                content_length = response.headers.get('content-length')
                if content_length:
                    try:
                        response_size = int(content_length)
                    except ValueError:
                        pass
                elif hasattr(response, 'body'):
                    # For responses with body, calculate size
                    if isinstance(response.body, bytes):
                        response_size = len(response.body)
                    elif isinstance(response.body, str):
                        response_size = len(response.body.encode('utf-8'))
            
            # For streaming responses, we can't easily get the size
            if isinstance(response, StreamingResponse):
                response_size = None
            
            return response
            
        except Exception as e:
            # Classify error type
            error_type = type(e).__name__
            status_code = 500
            raise
            
        finally:
            # Always finish tracking the request
            http_metrics.finish_request(
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                response_size=response_size,
                error_type=error_type
            )


def create_metrics_middleware(exclude_paths: Optional[list] = None):
    """
    Factory function to create metrics middleware with configuration
    
    Args:
        exclude_paths: List of paths to exclude from metrics collection
        
    Returns:
        Configured MetricsMiddleware factory function
    """
    def middleware_factory(app: ASGIApp) -> MetricsMiddleware:
        return MetricsMiddleware(app, exclude_paths=exclude_paths)
    
    return middleware_factory
