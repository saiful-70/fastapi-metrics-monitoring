"""
Health check endpoints for monitoring application health
"""
import time
from typing import Dict, Any
from fastapi import APIRouter
from datetime import datetime, timedelta

from ..metrics.system_metrics import system_metrics
from ..metrics.http_metrics import http_metrics

# Create health router
router = APIRouter(tags=["health"])

# Application start time
app_start_time = time.time()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - app_start_time,
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with system metrics
    
    Returns:
        Comprehensive health status including system metrics
    """
    # Get system metrics
    system_summary = system_metrics.get_system_summary()
    
    # Get HTTP metrics summary
    http_summary = http_metrics.get_metrics_summary()
    
    # Calculate uptime
    uptime_seconds = time.time() - app_start_time
    uptime_readable = str(timedelta(seconds=int(uptime_seconds)))
    
    # Determine health status based on metrics
    status = "healthy"
    issues = []
    
    # Check CPU usage
    cpu_percent = system_summary.get('cpu_percent', 0)
    if cpu_percent > 80:
        status = "warning"
        issues.append(f"High CPU usage: {cpu_percent:.1f}%")
    
    # Check memory usage
    memory_percent = system_summary.get('memory_percent', 0)
    if memory_percent > 85:
        status = "warning" if status == "healthy" else "critical"
        issues.append(f"High memory usage: {memory_percent:.1f}%")
    
    # Check for active requests overload
    active_requests = http_summary.get('active_requests', 0)
    if active_requests > 100:
        status = "warning" if status == "healthy" else status
        issues.append(f"High number of active requests: {active_requests}")
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": {
            "seconds": uptime_seconds,
            "readable": uptime_readable
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_rss_mb": system_summary.get('memory_rss', 0) / 1024 / 1024,
            "threads": system_summary.get('threads', 0)
        },
        "http": {
            "active_requests": active_requests,
            "total_requests": http_summary.get('total_requests', 0),
            "error_requests": http_summary.get('error_requests', 0)
        },
        "issues": issues,
        "version": "1.0.0"
    }


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint
    
    Returns:
        Simple alive status
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint
    
    Returns:
        Readiness status with basic checks
    """
    # Perform basic readiness checks
    ready = True
    checks = {}
    
    try:
        # Check if metrics collection is working
        system_summary = system_metrics.get_system_summary()
        checks["metrics_collection"] = "pass" if system_summary else "fail"
        if not system_summary:
            ready = False
    except Exception as e:
        checks["metrics_collection"] = f"fail: {str(e)}"
        ready = False
    
    try:
        # Check if HTTP metrics are working
        http_summary = http_metrics.get_metrics_summary()
        checks["http_metrics"] = "pass" if http_summary is not None else "fail"
        if http_summary is None:
            ready = False
    except Exception as e:
        checks["http_metrics"] = f"fail: {str(e)}"
        ready = False
    
    # Check uptime (should be ready after 5 seconds)
    uptime = time.time() - app_start_time
    checks["uptime"] = "pass" if uptime > 5 else "fail"
    if uptime <= 5:
        ready = False
    
    return {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
