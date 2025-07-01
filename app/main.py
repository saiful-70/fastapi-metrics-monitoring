"""
FastAPI Metrics Monitoring System - Main Application
"""
import asyncio
import time
import sys
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import based on execution context
if __name__ == "__main__":
    # Direct execution - use absolute imports
    from app.config import settings
    from app.metrics.system_metrics import system_metrics
    from app.metrics.http_metrics import http_metrics
    from app.middleware.metrics_middleware import MetricsMiddleware
    from app.routers import api, health
else:
    # Module import - use relative imports
    from .config import settings
    from .metrics.system_metrics import system_metrics
    from .metrics.http_metrics import http_metrics
    from .middleware.metrics_middleware import MetricsMiddleware
    from .routers import api, health


# Background task for system metrics collection
async def collect_system_metrics():
    """Background task to periodically collect system metrics"""
    while True:
        try:
            system_metrics.collect_metrics()
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
        
        await asyncio.sleep(settings.system_metrics_interval)


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Start background task for system metrics collection
    metrics_task = None
    if settings.enable_system_metrics:
        metrics_task = asyncio.create_task(collect_system_metrics())
        print("System metrics collection started")
    
    # Collect initial metrics
    system_metrics.collect_metrics()
    
    yield
    
    # Shutdown
    if settings.enable_system_metrics and metrics_task:
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass
        print("System metrics collection stopped")
    
    print(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A comprehensive FastAPI application with built-in metrics monitoring using Prometheus",
    lifespan=lifespan,
    debug=settings.debug
)

# Add metrics middleware
app.add_middleware(
    MetricsMiddleware,
    exclude_paths=[settings.metrics_path, "/docs", "/redoc", "/openapi.json"]
)

# Include routers
app.include_router(health.router)
app.include_router(api.router)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with application information
    
    Returns:
        Application information and status
    """
    uptime = time.time() - system_metrics.start_time
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "FastAPI application with comprehensive metrics monitoring",
        "status": "running",
        "uptime_seconds": uptime,
        "metrics_endpoint": settings.metrics_path,
        "health_endpoint": "/health",
        "api_docs": "/docs",
        "features": [
            "System metrics (CPU, memory, process statistics)",
            "HTTP request metrics (volume, performance, errors)",
            "Prometheus metrics exposition",
            "Health checks with detailed system information",
            "RESTful API with data management endpoints"
        ]
    }


@app.get(settings.metrics_path, response_class=PlainTextResponse)
async def metrics_endpoint() -> Response:
    """
    Prometheus metrics exposition endpoint
    
    Returns:
        Prometheus formatted metrics
    """
    # Collect latest system metrics before exposing
    system_metrics.collect_metrics()
    
    # Generate Prometheus metrics
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data.decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/metrics/summary")
async def metrics_summary() -> Dict[str, Any]:
    """
    Human-readable metrics summary endpoint
    
    Returns:
        Summary of current metrics in JSON format
    """
    # Collect latest metrics
    system_summary = system_metrics.get_system_summary()
    http_summary = http_metrics.get_metrics_summary()
    
    return {
        "timestamp": time.time(),
        "system": system_summary,
        "http": http_summary,
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "uptime_seconds": time.time() - system_metrics.start_time
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Custom 500 handler"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "path": str(request.url.path),
            "method": request.method
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
