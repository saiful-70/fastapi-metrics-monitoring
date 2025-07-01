"""
Configuration management for FastAPI Metrics Monitoring System
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application settings
    app_name: str = "FastAPI Metrics Monitoring System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "localhost"
    port: int = 8000
    
    # Metrics settings
    metrics_path: str = "/metrics"
    metrics_collection_interval: int = 5  # seconds
    
    # Histogram bucket settings for request duration
    request_duration_buckets: List[float] = [
        0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0
    ]
    
    # System metrics settings
    enable_system_metrics: bool = True
    system_metrics_interval: int = 10  # seconds
    
    class Config:
        env_file = ".env"
        env_prefix = "FASTAPI_METRICS_"


# Global settings instance
settings = Settings()
