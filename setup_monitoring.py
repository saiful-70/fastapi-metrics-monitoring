#!/usr/bin/env python3
"""
Monitoring setup script for FastAPI Metrics application
This script helps set up comprehensive monitoring with Prometheus, Grafana, and AlertManager
"""

import os
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any

def create_prometheus_config(target_host: str = "localhost", target_port: int = 8000) -> str:
    """Create Prometheus configuration with alerting rules"""
    config = {
        'global': {
            'scrape_interval': '15s',
            'evaluation_interval': '15s'
        },
        'rule_files': [
            'alerts.yml'
        ],
        'scrape_configs': [
            {
                'job_name': 'fastapi-metrics',
                'static_configs': [
                    {'targets': [f'{target_host}:{target_port}']}
                ],
                'metrics_path': '/metrics',
                'scrape_interval': '5s'
            },
            {
                'job_name': 'prometheus',
                'static_configs': [
                    {'targets': ['localhost:9090']}
                ]
            }
        ],
        'alerting': {
            'alertmanagers': [
                {
                    'static_configs': [
                        {'targets': ['localhost:9093']}
                    ]
                }
            ]
        }
    }
    return yaml.dump(config, default_flow_style=False)

def create_alerting_rules() -> str:
    """Create Prometheus alerting rules"""
    return """
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
"""

def create_grafana_dashboard() -> Dict[str, Any]:
    """Create Grafana dashboard configuration"""
    return {
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

def create_alertmanager_config(email: str = "admin@example.com") -> str:
    """Create AlertManager configuration"""
    return f"""
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
  - to: '{email}'
    subject: 'FastAPI Metrics Alert: {{{{ .GroupLabels.alertname }}}}'
    body: |
      {{{{ range .Alerts }}}}
      Alert: {{{{ .Annotations.summary }}}}
      Description: {{{{ .Annotations.description }}}}
      Labels: {{{{ range .Labels.SortedPairs }}}}{{{{ .Name }}}}: {{{{ .Value }}}}{{{{ end }}}}
      {{{{ end }}}}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
"""

def setup_monitoring(output_dir: str = "monitoring_config", target_host: str = "localhost", 
                    target_port: int = 8000, email: str = "admin@example.com"):
    """Set up monitoring configuration files"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create Prometheus config
    prometheus_config = create_prometheus_config(target_host, target_port)
    with open(output_path / "prometheus.yml", "w") as f:
        f.write(prometheus_config)
    
    # Create alerting rules
    alerting_rules = create_alerting_rules()
    with open(output_path / "alerts.yml", "w") as f:
        f.write(alerting_rules)
    
    # Create Grafana dashboard
    grafana_dashboard = create_grafana_dashboard()
    with open(output_path / "grafana_dashboard.json", "w") as f:
        json.dump(grafana_dashboard, f, indent=2)
    
    # Create AlertManager config
    alertmanager_config = create_alertmanager_config(email)
    with open(output_path / "alertmanager.yml", "w") as f:
        f.write(alertmanager_config)
    
    # Create Docker Compose file
    docker_compose = f"""
version: '3.8'

services:
  fastapi-metrics:
    build: .
    ports:
      - "{target_port}:{target_port}"
    environment:
      - FASTAPI_METRICS_HOST=0.0.0.0
      - FASTAPI_METRICS_PORT={target_port}
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana_dashboard.json:/var/lib/grafana/dashboards/dashboard.json
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
"""
    
    with open(output_path / "docker-compose.monitoring.yml", "w") as f:
        f.write(docker_compose)
    
    # Create setup instructions
    instructions = f"""
# FastAPI Metrics Monitoring Setup

This directory contains configuration files for comprehensive monitoring of the FastAPI Metrics application.

## Files Generated:
- `prometheus.yml` - Prometheus configuration with scraping and alerting
- `alerts.yml` - Prometheus alerting rules
- `grafana_dashboard.json` - Grafana dashboard configuration
- `alertmanager.yml` - AlertManager configuration for notifications
- `docker-compose.monitoring.yml` - Complete monitoring stack

## Quick Start:

1. Start the monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. Access the services:
   - FastAPI Application: http://localhost:{target_port}
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - AlertManager: http://localhost:9093

3. Import Grafana dashboard:
   - Go to Grafana -> Dashboards -> Import
   - Upload the `grafana_dashboard.json` file

## Manual Setup:

### Prometheus:
1. Copy `prometheus.yml` to your Prometheus config directory
2. Copy `alerts.yml` to your Prometheus rules directory
3. Restart Prometheus

### Grafana:
1. Import `grafana_dashboard.json` via Grafana UI
2. Configure Prometheus as data source (http://localhost:9090)

### AlertManager:
1. Copy `alertmanager.yml` to AlertManager config directory
2. Update email settings in the config file
3. Restart AlertManager

## Monitoring Queries:

Key Prometheus queries for monitoring:
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `rate(http_request_errors_total[5m]) / rate(http_requests_total[5m]) * 100`
- Response time 95th percentile: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
- CPU usage: `app_cpu_usage_percent`
- Memory usage: `app_memory_usage_percent`

## Alert Configuration:

The following alerts are configured:
- High CPU usage (>80% for 5 minutes)
- Critical CPU usage (>95% for 2 minutes)
- High memory usage (>85% for 5 minutes)
- High error rate (>5% for 3 minutes)
- Slow response times (>2s 95th percentile for 5 minutes)
- Service down (>1 minute)

## Customization:

Edit the configuration files to customize:
- Alert thresholds in `alerts.yml`
- Scrape intervals in `prometheus.yml`
- Email settings in `alertmanager.yml`
- Dashboard panels in `grafana_dashboard.json`
"""
    
    with open(output_path / "README.md", "w") as f:
        f.write(instructions)
    
    print(f"✅ Monitoring configuration created in '{output_dir}' directory")
    print(f"📁 Files created:")
    print(f"   - prometheus.yml")
    print(f"   - alerts.yml")
    print(f"   - grafana_dashboard.json")
    print(f"   - alertmanager.yml")
    print(f"   - docker-compose.monitoring.yml")
    print(f"   - README.md")
    print(f"\n🚀 Quick start: cd {output_dir} && docker-compose -f docker-compose.monitoring.yml up -d")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Setup monitoring for FastAPI Metrics application")
    parser.add_argument("--output-dir", default="monitoring_config", help="Output directory for config files")
    parser.add_argument("--target-host", default="localhost", help="Target host for FastAPI application")
    parser.add_argument("--target-port", type=int, default=8000, help="Target port for FastAPI application")
    parser.add_argument("--email", default="admin@example.com", help="Email for alerts")
    
    args = parser.parse_args()
    
    setup_monitoring(args.output_dir, args.target_host, args.target_port, args.email)

if __name__ == "__main__":
    main()
