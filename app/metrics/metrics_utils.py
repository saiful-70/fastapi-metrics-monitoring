"""
Metrics utilities and helper functions for advanced metrics operations
"""
import time
from typing import Dict, Any, List, Optional
from prometheus_client import REGISTRY
from .system_metrics import system_metrics
from .http_metrics import http_metrics


class MetricsAnalyzer:
    """Advanced metrics analysis and utility functions"""
    
    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_p95': 2.0,  # seconds
            'error_rate_percent': 5.0,
            'active_requests': 100
        }
    
    def get_prometheus_rate_examples(self) -> Dict[str, str]:
        """
        Get example Prometheus queries for rate calculations
        
        Returns:
            Dictionary of example PromQL queries
        """
        return {
            "cpu_rate_5m": "rate(process_cpu_seconds_total[5m])",
            "request_rate_5m": "rate(http_requests_total[5m])",
            "error_rate_5m": "rate(http_request_errors_total[5m]) / rate(http_requests_total[5m])",
            "p95_response_time": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "p99_response_time": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "memory_usage_mb": "process_resident_memory_bytes / 1024 / 1024",
            "request_throughput_per_minute": "rate(http_requests_total[1m]) * 60",
            "slow_requests_rate": "rate(http_slow_requests_total[5m])",
            "status_code_distribution": "sum(rate(http_requests_total[5m])) by (status_code)",
            "cpu_utilization_percent": "rate(process_cpu_seconds_total[5m]) * 100"
        }
    
    def calculate_system_health_score(self) -> Dict[str, Any]:
        """
        Calculate an overall system health score based on multiple metrics
        
        Returns:
            Health score and component details
        """
        system_summary = system_metrics.get_system_summary()
        http_summary = http_metrics.get_metrics_summary()
        
        # Component scores (0-100, where 100 is perfect)
        scores = {}
        
        # CPU Score
        cpu_percent = system_summary.get('cpu_percent', 0)
        scores['cpu'] = max(0, 100 - (cpu_percent / self.alert_thresholds['cpu_percent']) * 100)
        
        # Memory Score
        memory_percent = system_summary.get('memory_percent', 0)
        scores['memory'] = max(0, 100 - (memory_percent / self.alert_thresholds['memory_percent']) * 100)
        
        # HTTP Error Rate Score
        error_rate = http_summary.get('error_rate_percent', 0)
        scores['error_rate'] = max(0, 100 - (error_rate / self.alert_thresholds['error_rate_percent']) * 100)
        
        # Active Requests Score
        active_requests = http_summary.get('active_requests', 0)
        scores['load'] = max(0, 100 - (active_requests / self.alert_thresholds['active_requests']) * 100)
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine health status
        if overall_score >= 90:
            status = "excellent"
        elif overall_score >= 75:
            status = "good"
        elif overall_score >= 60:
            status = "fair"
        elif overall_score >= 40:
            status = "poor"
        else:
            status = "critical"
        
        return {
            'overall_score': round(overall_score, 2),
            'status': status,
            'component_scores': scores,
            'timestamp': time.time()
        }
    
    def get_alert_conditions(self) -> Dict[str, Any]:
        """
        Check current metrics against alert thresholds
        
        Returns:
            Alert conditions and current values
        """
        system_summary = system_metrics.get_system_summary()
        http_summary = http_metrics.get_metrics_summary()
        
        alerts = {
            'active': [],
            'warnings': [],
            'info': []
        }
        
        current_values = {}
        
        # CPU Alert
        cpu_percent = system_summary.get('cpu_percent', 0)
        current_values['cpu_percent'] = cpu_percent
        if cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts['active'].append({
                'type': 'high_cpu',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent'],
                'message': f"CPU usage ({cpu_percent:.1f}%) exceeds threshold ({self.alert_thresholds['cpu_percent']}%)"
            })
        elif cpu_percent > self.alert_thresholds['cpu_percent'] * 0.8:
            alerts['warnings'].append({
                'type': 'cpu_warning',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent'] * 0.8,
                'message': f"CPU usage ({cpu_percent:.1f}%) approaching threshold"
            })
        
        # Memory Alert
        memory_percent = system_summary.get('memory_percent', 0)
        current_values['memory_percent'] = memory_percent
        if memory_percent > self.alert_thresholds['memory_percent']:
            alerts['active'].append({
                'type': 'high_memory',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_percent'],
                'message': f"Memory usage ({memory_percent:.1f}%) exceeds threshold ({self.alert_thresholds['memory_percent']}%)"
            })
        elif memory_percent > self.alert_thresholds['memory_percent'] * 0.8:
            alerts['warnings'].append({
                'type': 'memory_warning',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_percent'] * 0.8,
                'message': f"Memory usage ({memory_percent:.1f}%) approaching threshold"
            })
        
        # Error Rate Alert
        error_rate = http_summary.get('error_rate_percent', 0)
        current_values['error_rate_percent'] = error_rate
        if error_rate > self.alert_thresholds['error_rate_percent']:
            alerts['active'].append({
                'type': 'high_error_rate',
                'value': error_rate,
                'threshold': self.alert_thresholds['error_rate_percent'],
                'message': f"Error rate ({error_rate:.1f}%) exceeds threshold ({self.alert_thresholds['error_rate_percent']}%)"
            })
        
        # Active Requests Alert
        active_requests = http_summary.get('active_requests', 0)
        current_values['active_requests'] = active_requests
        if active_requests > self.alert_thresholds['active_requests']:
            alerts['active'].append({
                'type': 'high_load',
                'value': active_requests,
                'threshold': self.alert_thresholds['active_requests'],
                'message': f"Active requests ({active_requests}) exceeds threshold ({self.alert_thresholds['active_requests']})"
            })
        
        return {
            'alerts': alerts,
            'current_values': current_values,
            'thresholds': self.alert_thresholds,
            'timestamp': time.time()
        }
    
    def get_performance_trends(self, window_minutes: int = 5) -> Dict[str, Any]:
        """
        Analyze performance trends over a time window
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            Performance trend analysis
        """
        # This would typically require historical data storage
        # For now, we'll provide current snapshot and rate calculations
        
        window_seconds = window_minutes * 60
        request_rate = http_metrics.calculate_request_rate(window_seconds)
        error_rate = http_metrics.get_error_rate(window_seconds)
        
        return {
            'window_minutes': window_minutes,
            'request_rate_per_second': request_rate,
            'error_rate_percent': error_rate,
            'current_active_requests': http_metrics.http_requests_active._value._value,
            'recommendations': self._generate_recommendations(request_rate, error_rate),
            'timestamp': time.time()
        }
    
    def _generate_recommendations(self, request_rate: float, error_rate: float) -> List[str]:
        """Generate performance recommendations based on current metrics"""
        recommendations = []
        
        if request_rate > 100:  # High traffic
            recommendations.append("Consider implementing request rate limiting")
            recommendations.append("Monitor for potential DDoS attacks")
        
        if error_rate > 5:  # High error rate
            recommendations.append("Investigate high error rate - check application logs")
            recommendations.append("Consider implementing circuit breaker pattern")
        
        if request_rate > 50 and error_rate > 2:
            recommendations.append("High traffic with elevated errors - scale horizontally")
        
        if not recommendations:
            recommendations.append("System operating within normal parameters")
        
        return recommendations
    
    def export_metrics_summary(self) -> Dict[str, Any]:
        """
        Export comprehensive metrics summary for external monitoring systems
        
        Returns:
            Complete metrics summary
        """
        system_summary = system_metrics.get_system_summary()
        http_summary = http_metrics.get_metrics_summary()
        health_score = self.calculate_system_health_score()
        alerts = self.get_alert_conditions()
        
        return {
            'timestamp': time.time(),
            'system_metrics': system_summary,
            'http_metrics': http_summary,
            'health_score': health_score,
            'alerts': alerts,
            'prometheus_queries': self.get_prometheus_rate_examples(),
            'uptime_seconds': time.time() - system_metrics.start_time
        }


# Global metrics analyzer instance
metrics_analyzer = MetricsAnalyzer()
