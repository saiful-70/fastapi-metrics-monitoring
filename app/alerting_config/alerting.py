"""
Alerting rules and configurations for Prometheus
This file contains example alerting rules that can be used with Prometheus AlertManager
"""

# Prometheus Alerting Rules (prometheus_alerts.yml)
PROMETHEUS_ALERTING_RULES = """
groups:
  - name: fastapi_metrics_alerts
    rules:
      # High CPU Usage Alert
      - alert: HighCPUUsage
        expr: app_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% which is above the threshold of 80%"
      
      # Critical CPU Usage Alert  
      - alert: CriticalCPUUsage
        expr: app_cpu_usage_percent > 95
        for: 2m
        labels:
          severity: critical
          service: fastapi-metrics
        annotations:
          summary: "Critical CPU usage detected"
          description: "CPU usage is {{ $value }}% which is critically high"
      
      # High Memory Usage Alert
      - alert: HighMemoryUsage
        expr: app_memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}% which is above the threshold of 85%"
      
      # Critical Memory Usage Alert
      - alert: CriticalMemoryUsage
        expr: app_memory_usage_percent > 95
        for: 2m
        labels:
          severity: critical
          service: fastapi-metrics
        annotations:
          summary: "Critical memory usage detected"
          description: "Memory usage is {{ $value }}% which is critically high"
      
      # High Error Rate Alert
      - alert: HighErrorRate
        expr: rate(http_request_errors_total[5m]) / rate(http_requests_total[5m]) * 100 > 5
        for: 3m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High HTTP error rate detected"
          description: "Error rate is {{ $value }}% which is above the threshold of 5%"
      
      # Critical Error Rate Alert
      - alert: CriticalErrorRate
        expr: rate(http_request_errors_total[5m]) / rate(http_requests_total[5m]) * 100 > 15
        for: 1m
        labels:
          severity: critical
          service: fastapi-metrics
        annotations:
          summary: "Critical HTTP error rate detected"
          description: "Error rate is {{ $value }}% which is critically high"
      
      # Slow Response Time Alert
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
        for: 5m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "Slow response times detected"
          description: "95th percentile response time is {{ $value }}s which is above 2s threshold"
      
      # Very Slow Response Time Alert
      - alert: VerySlowResponseTime
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 5
        for: 2m
        labels:
          severity: critical
          service: fastapi-metrics
        annotations:
          summary: "Very slow response times detected"
          description: "95th percentile response time is {{ $value }}s which is critically slow"
      
      # High Request Volume Alert
      - alert: HighRequestVolume
        expr: rate(http_requests_total[1m]) > 100
        for: 5m
        labels:
          severity: info
          service: fastapi-metrics
        annotations:
          summary: "High request volume detected"
          description: "Request rate is {{ $value }} requests/second"
      
      # Service Down Alert
      - alert: ServiceDown
        expr: up{job="fastapi-metrics"} == 0
        for: 1m
        labels:
          severity: critical
          service: fastapi-metrics
        annotations:
          summary: "FastAPI Metrics service is down"
          description: "The FastAPI Metrics service has been down for more than 1 minute"
      
      # High Active Requests Alert
      - alert: HighActiveRequests
        expr: http_requests_active > 100
        for: 5m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High number of active requests"
          description: "{{ $value }} active requests detected, which may indicate performance issues"
      
      # Garbage Collection Issues
      - alert: HighGCActivity
        expr: rate(gc_collections_total[5m]) > 10
        for: 3m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High garbage collection activity"
          description: "GC collections rate is {{ $value }} per second, which may impact performance"
      
      # File Descriptor Usage Alert
      - alert: HighFileDescriptorUsage
        expr: process_open_fds > 1000
        for: 5m
        labels:
          severity: warning
          service: fastapi-metrics
        annotations:
          summary: "High file descriptor usage"
          description: "{{ $value }} file descriptors are open, approaching system limits"
"""

# Grafana Dashboard JSON for comprehensive monitoring
GRAFANA_DASHBOARD = {
    "dashboard": {
        "id": None,
        "title": "FastAPI Metrics Monitoring",
        "tags": ["fastapi", "metrics", "monitoring"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total[5m])",
                        "legendFormat": "Requests/sec"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Response Time Percentiles",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                        "legendFormat": "50th percentile"
                    },
                    {
                        "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                        "legendFormat": "95th percentile"
                    },
                    {
                        "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                        "legendFormat": "99th percentile"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "CPU Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "app_cpu_usage_percent",
                        "legendFormat": "CPU %"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Memory Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "app_memory_usage_percent",
                        "legendFormat": "Memory %"
                    },
                    {
                        "expr": "process_resident_memory_bytes / 1024 / 1024",
                        "legendFormat": "RSS MB"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            },
            {
                "id": 5,
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_request_errors_total[5m]) / rate(http_requests_total[5m]) * 100",
                        "legendFormat": "Error Rate %"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
            },
            {
                "id": 6,
                "title": "Status Code Distribution",
                "type": "graph",
                "targets": [
                    {
                        "expr": "sum(rate(http_requests_total[5m])) by (status_code)",
                        "legendFormat": "{{status_code}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "5s"
    }
}

# Example alert manager configuration
ALERTMANAGER_CONFIG = """
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@example.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@example.com'
    subject: 'FastAPI Metrics Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Labels: {{ range .Labels.SortedPairs }}{{ .Name }}: {{ .Value }}{{ end }}
      {{ end }}
  
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'FastAPI Metrics Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
"""

def get_alerting_rules() -> str:
    """Get Prometheus alerting rules configuration"""
    return PROMETHEUS_ALERTING_RULES

def get_grafana_dashboard() -> dict:
    """Get Grafana dashboard configuration"""
    return GRAFANA_DASHBOARD

def get_alertmanager_config() -> str:
    """Get AlertManager configuration"""
    return ALERTMANAGER_CONFIG
