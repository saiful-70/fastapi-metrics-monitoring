# FastAPI Metrics Monitoring System

A comprehensive FastAPI application that implements both system-level and application-level metrics monitoring using Prometheus metrics format. The application provides detailed performance metrics for monitoring infrastructure health and application behavior.

## 🚀 Quick Start

```bash
# Navigate to the project directory
cd fastapi-metrics-monitoring

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 main.py
```

The application will be available at:
- **Main API**: http://localhost:8000
- **Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## Features

- **System Metrics**: CPU usage, memory consumption, process statistics
- **HTTP Metrics**: Request volume, performance, error tracking
- **Prometheus Integration**: Standard metrics exposition format
- **Health Checks**: Comprehensive health monitoring endpoints
- **RESTful API**: Sample data management endpoints with full CRUD operations
- **Production Ready**: Built with scalability and monitoring in mind

## Project Structure

```
fastapi-metrics-monitoring/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── system_metrics.py  # CPU, memory metrics
│   │   └── http_metrics.py    # HTTP request metrics
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── metrics_middleware.py
│   └── routers/
│       ├── __init__.py
│       ├── api.py             # Business logic endpoints
│       └── health.py          # Health check endpoints
├── main.py                     # Direct runner script (python3 main.py)
├── requirements.txt
├── README.md
├── docker-compose.yml
├── prometheus.yml
└── Dockerfile
```

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Setup

1. **Clone or create the project directory:**
   ```bash
   cd fastapi-metrics-monitoring
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Required packages:
   - `fastapi==0.104.1`
   - `uvicorn[standard]==0.24.0`
   - `prometheus-client==0.19.0`
   - `psutil==5.9.6`
   - `python-multipart==0.0.6`
   - `pydantic==2.5.0`
   - `pydantic-settings==2.1.0`

## Configuration

The application can be configured through environment variables. Create a `.env` file in the project root:

```env
FASTAPI_METRICS_DEBUG=false
FASTAPI_METRICS_HOST=localhost
FASTAPI_METRICS_PORT=8000
FASTAPI_METRICS_METRICS_COLLECTION_INTERVAL=5
FASTAPI_METRICS_SYSTEM_METRICS_INTERVAL=10
FASTAPI_METRICS_ENABLE_SYSTEM_METRICS=true
```

## Running the Application

### Quick Start (Recommended)

The easiest way to run the application:

```bash
# Navigate to project directory
cd fastapi-metrics-monitoring

# Run the application directly
python3 main.py
```

The application will start on `http://localhost:8000`

### Development Mode

```bash
# Using Python module
python3 -m app.main

# Using uvicorn with auto-reload
uvicorn app.main:app --reload --host localhost --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host localhost --port 8000 --workers 4
```

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with application information
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check with system metrics
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/ready` - Kubernetes readiness probe
- `GET /metrics` - Prometheus metrics exposition
- `GET /metrics/summary` - Human-readable metrics summary

### Data Management API

- `GET /api/v1/data` - List data items with pagination and filtering
- `POST /api/v1/data` - Create a new data item
- `GET /api/v1/data/{id}` - Get specific data item
- `PUT /api/v1/data/{id}` - Update data item
- `DELETE /api/v1/data/{id}` - Delete data item
- `POST /api/v1/data/bulk` - Create multiple data items
- `GET /api/v1/data/stats/summary` - Get data statistics

## Metrics Reference

### System Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `app_cpu_seconds_total` | Counter | Total CPU time consumed by the application |
| `app_cpu_usage_percent` | Gauge | Current CPU usage percentage |
| `app_memory_resident_bytes` | Gauge | Physical memory currently used |
| `app_memory_virtual_bytes` | Gauge | Virtual memory allocated |
| `app_memory_usage_percent` | Gauge | Memory usage percentage |
| `app_start_time_seconds` | Gauge | Application start time since unix epoch |
| `app_open_fds` | Gauge | Number of open file descriptors |
| `app_threads_total` | Gauge | Number of OS threads |
| `app_uptime_seconds` | Gauge | Time since application started |
| `app_info` | Info | Application process information |

### HTTP Metrics

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests | method, endpoint, status_code |
| `http_request_duration_seconds` | Histogram | Request duration | method, endpoint |
| `http_request_size_bytes` | Histogram | Request size | method, endpoint |
| `http_response_size_bytes` | Histogram | Response size | method, endpoint, status_code |
| `http_requests_active` | Gauge | Active requests | - |
| `http_request_errors_total` | Counter | Request errors | method, endpoint, error_type |

## Monitoring Queries

### Prometheus Query Examples

**Request Rate (requests per second):**
```promql
rate(http_requests_total[5m])
```

**95th Percentile Response Time:**
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

**Error Rate:**
```promql
rate(http_request_errors_total[5m]) / rate(http_requests_total[5m])
```

**CPU Usage Rate:**
```promql
rate(app_cpu_seconds_total[5m])
```

## Docker Deployment

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  fastapi-metrics:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTAPI_METRICS_HOST=0.0.0.0
      - FASTAPI_METRICS_PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi-metrics'
    static_configs:
      - targets: ['fastapi-metrics:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Running with Docker Compose

```bash
docker-compose up -d
```

Access the services:
- FastAPI Application: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Performance Considerations

### Metrics Collection Impact

- **System Metrics**: Collected every 10 seconds by default (configurable)
- **HTTP Metrics**: Collected on every request with minimal overhead
- **Memory Usage**: Metrics are stored in memory; consider retention policies for long-running applications

### Scaling Recommendations

1. **Production Deployment**: Use multiple worker processes
2. **Metrics Storage**: External Prometheus server for metrics storage
3. **Load Balancing**: Distribute traffic across multiple instances
4. **Monitoring**: Set up alerts for high resource usage

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Reduce metrics collection frequency or implement retention policies
2. **Permission Errors**: Ensure proper file descriptor access permissions
3. **Port Conflicts**: Change default port in configuration

### Health Check Failures

Check the detailed health endpoint for specific issues:
```bash
curl http://localhost:8000/health/detailed
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Install development dependencies
pip install black flake8 mypy

# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Use the health check endpoints for debugging
4. Open an issue in the project repository
