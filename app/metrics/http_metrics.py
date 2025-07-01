"""
HTTP request metrics collection for request patterns and performance monitoring
"""
import time
from typing import Dict, List, Optional, Any
from prometheus_client import Counter, Histogram, Gauge
from ..config import settings


class HTTPMetricsCollector:
    """Collects and exposes HTTP request metrics"""
    
    def __init__(self):
        # Request volume metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        # Request performance metrics
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=settings.request_duration_buckets
        )
        
        # Request size metrics
        self.http_request_size_bytes = Histogram(
            'http_request_size_bytes',
            'HTTP request size in bytes',
            ['method', 'endpoint'],
            buckets=[1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
        )
        
        # Response size metrics
        self.http_response_size_bytes = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint', 'status_code'],
            buckets=[1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
        )
        
        # Active requests gauge
        self.http_requests_active = Gauge(
            'http_requests_active',
            'Number of HTTP requests currently being processed'
        )
        
        # Request errors
        self.http_request_errors_total = Counter(
            'http_request_errors_total',
            'Total HTTP request errors',
            ['method', 'endpoint', 'error_type']
        )
        
        # Store active requests for tracking
        self.active_requests: Dict[str, float] = {}
    
    def start_request(self, method: str, path: str, request_size: Optional[int] = None) -> str:
        """
        Start tracking a new HTTP request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path/endpoint
            request_size: Size of request body in bytes
            
        Returns:
            Request ID for tracking
        """
        request_id = f"{method}_{path}_{time.time()}_{id(self)}"
        start_time = time.time()
        
        # Increment active requests
        self.http_requests_active.inc()
        
        # Store request start time
        self.active_requests[request_id] = start_time
        
        # Record request size if provided
        if request_size is not None:
            self.http_request_size_bytes.labels(
                method=method,
                endpoint=self._normalize_endpoint(path)
            ).observe(request_size)
        
        return request_id
    
    def finish_request(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        response_size: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """
        Finish tracking an HTTP request
        
        Args:
            request_id: Request ID from start_request
            method: HTTP method
            path: Request path/endpoint
            status_code: HTTP response status code
            response_size: Size of response body in bytes
            error_type: Type of error if request failed
        """
        if request_id not in self.active_requests:
            return
        
        start_time = self.active_requests.pop(request_id)
        duration = time.time() - start_time
        
        # Decrement active requests
        self.http_requests_active.dec()
        
        # Normalize endpoint for consistent labeling
        endpoint = self._normalize_endpoint(path)
        
        # Record request completion
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        # Record request duration
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Record response size if provided
        if response_size is not None:
            self.http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).observe(response_size)
        
        # Record error if present
        if error_type:
            self.http_request_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type
            ).inc()
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for consistent metrics labeling
        
        Args:
            path: Original request path
            
        Returns:
            Normalized endpoint path
        """
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Replace path parameters with placeholders
        # This is a simple implementation - in production, you might want
        # to use FastAPI's route matching for more accurate normalization
        parts = path.split('/')
        normalized_parts = []
        
        for part in parts:
            if part.isdigit():
                normalized_parts.append('{id}')
            elif len(part) > 0 and part[0] == '{' and part[-1] == '}':
                normalized_parts.append(part)
            else:
                normalized_parts.append(part)
        
        return '/'.join(normalized_parts)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current HTTP metrics"""
        return {
            'active_requests': self.http_requests_active._value._value,
            'total_requests': sum(self.http_requests_total._metrics.values()),
            'error_requests': sum(self.http_request_errors_total._metrics.values())
        }


# Global HTTP metrics collector instance
http_metrics = HTTPMetricsCollector()
