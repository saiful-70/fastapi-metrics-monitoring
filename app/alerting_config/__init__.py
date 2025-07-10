"""
Configuration module for FastAPI Metrics Monitoring System
"""

from .alerting import get_alerting_rules, get_grafana_dashboard, get_alertmanager_config

__all__ = [
    'get_alerting_rules',
    'get_grafana_dashboard', 
    'get_alertmanager_config'
]
