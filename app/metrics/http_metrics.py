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
        
        # Request errors with detailed classification
        self.http_request_errors_total = Counter(
            'http_request_errors_total',
            'Total HTTP request errors',
            ['method', 'endpoint', 'error_type', 'status_code']
        )
        
        # Status code distribution
        self.http_requests_by_status = Counter(
            'http_requests_by_status_total',
            'Total HTTP requests by status code class',
            ['status_class', 'method']
        )
        
        # Request rate tracking
        self.http_request_rate_per_second = Gauge(
            'http_request_rate_per_second',
            'HTTP request rate per second (calculated over last minute)'
        )
        
        # Slow requests counter
        self.http_slow_requests_total = Counter(
            'http_slow_requests_total',
            'Total number of slow HTTP requests (>1s)',
            ['method', 'endpoint']
        )
        
        # Store active requests for tracking
        self.active_requests: Dict[str, float] = {}
        
        # Store request history for rate calculations
        self.request_history: List[float] = []
    
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
        
        # Add to request history for rate calculation
        current_time = time.time()
        self.request_history.append(current_time)
        if len(self.request_history) > 1000:  # Keep last 1000 requests
            self.request_history.pop(0)
        
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
        
        # Record status code distribution
        status_class = self._get_status_class(status_code)
        self.http_requests_by_status.labels(
            status_class=status_class,
            method=method
        ).inc()
        
        # Record slow requests (>1 second)
        if duration > 1.0:
            self.http_slow_requests_total.labels(
                method=method,
                endpoint=endpoint
            ).inc()
        
        # Record error if present
        if error_type or status_code >= 400:
            self.http_request_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type or self._classify_error_by_status(status_code),
                status_code=str(status_code)
            ).inc()
        
        # Update request rate
        self._update_request_rate()
    
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
    
    def _get_status_class(self, status_code: int) -> str:
        """Get status code class (1xx, 2xx, 3xx, 4xx, 5xx)"""
        if 100 <= status_code < 200:
            return "1xx"
        elif 200 <= status_code < 300:
            return "2xx"
        elif 300 <= status_code < 400:
            return "3xx"
        elif 400 <= status_code < 500:
            return "4xx"
        elif 500 <= status_code < 600:
            return "5xx"
        else:
            return "unknown"
    
    def _classify_error_by_status(self, status_code: int) -> str:
        """Classify error type by status code"""
        if status_code == 400:
            return "bad_request"
        elif status_code == 401:
            return "unauthorized"
        elif status_code == 403:
            return "forbidden"
        elif status_code == 404:
            return "not_found"
        elif status_code == 405:
            return "method_not_allowed"
        elif status_code == 422:
            return "validation_error"
        elif status_code == 429:
            return "rate_limited"
        elif 400 <= status_code < 500:
            return "client_error"
        elif status_code == 500:
            return "internal_server_error"
        elif status_code == 502:
            return "bad_gateway"
        elif status_code == 503:
            return "service_unavailable"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "unknown_error"
    
    def _update_request_rate(self):
        """Update request rate metrics"""
        current_time = time.time()
        
        # Calculate requests in last minute
        minute_ago = current_time - 60
        recent_requests = [t for t in self.request_history if t > minute_ago]
        
        # Calculate requests per second (last minute average)
        if recent_requests:
            self.http_request_rate_per_second.set(len(recent_requests) / 60.0)
        else:
            self.http_request_rate_per_second.set(0.0)
    
    def calculate_request_rate(self, time_window: int = 300) -> float:
        """
        Calculate request rate over a time window (similar to Prometheus rate function)
        
        Args:
            time_window: Time window in seconds (default 5 minutes)
            
        Returns:
            Requests per second over the time window
        """
        current_time = time.time()
        window_start = current_time - time_window
        
        requests_in_window = [t for t in self.request_history if t > window_start]
        if requests_in_window and time_window > 0:
            return len(requests_in_window) / time_window
        return 0.0
    
    def get_error_rate(self, time_window: int = 300) -> float:
        """
        Calculate error rate over a time window
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Error rate as a percentage
        """
        total = self.calculate_request_rate(time_window) * time_window
        errors = sum(counter._value._value for counter in self.http_request_errors_total._metrics.values())
        
        if total > 0:
            return (errors / total) * 100
        return 0.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current HTTP metrics"""
        total_requests = sum(counter._value._value for counter in self.http_requests_total._metrics.values())
        error_requests = sum(counter._value._value for counter in self.http_request_errors_total._metrics.values())
        
        return {
            'active_requests': self.http_requests_active._value._value,
            'total_requests': total_requests,
            'error_requests': error_requests,
            'request_rate_per_second': self.http_request_rate_per_second._value._value,
            'error_rate_percent': (error_requests / max(total_requests, 1)) * 100
        }
        

# Global HTTP metrics collector instance
http_metrics = HTTPMetricsCollector()
