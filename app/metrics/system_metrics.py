"""
System-level metrics collection for CPU, memory, and process statistics
"""
import time
import psutil
from prometheus_client import Gauge, Counter, Info
from typing import Dict, Any


class SystemMetricsCollector:
    """Collects and exposes system-level metrics"""
    
    def __init__(self):
        # CPU metrics (using custom names to avoid conflicts)
        self.app_cpu_seconds_total = Counter(
            'app_cpu_seconds_total',
            'Total user and system CPU time spent by the application in seconds'
        )
        
        self.app_cpu_usage_percent = Gauge(
            'app_cpu_usage_percent',
            'Current CPU usage percentage of the application'
        )
        
        # Memory metrics (using custom names to avoid conflicts)
        self.app_memory_resident_bytes = Gauge(
            'app_memory_resident_bytes',
            'Physical memory currently used by the application in bytes'
        )
        
        self.app_memory_virtual_bytes = Gauge(
            'app_memory_virtual_bytes',
            'Virtual memory allocated by the application in bytes'
        )
        
        self.app_memory_usage_percent = Gauge(
            'app_memory_usage_percent',
            'Memory usage percentage of the application'
        )
        
        # Process metrics (using custom names to avoid conflicts)
        self.app_start_time_seconds = Gauge(
            'app_start_time_seconds',
            'Start time of the application since unix epoch in seconds'
        )
        
        self.app_open_fds = Gauge(
            'app_open_fds',
            'Number of open file descriptors for the application'
        )
        
        self.app_threads_total = Gauge(
            'app_threads_total',
            'Number of OS threads in the application process'
        )
        
        # Uptime metric
        self.app_uptime_seconds = Gauge(
            'app_uptime_seconds',
            'Time in seconds since the application started'
        )
        
        # Process info
        self.app_info = Info(
            'app_info',
            'Application process information'
        )
        
        # Initialize process start time
        self.start_time = time.time()
        self.app_start_time_seconds.set(self.start_time)
        
        # Set process info
        process = psutil.Process()
        self.app_info.info({
            'pid': str(process.pid),
            'name': process.name(),
            'python_version': self._get_python_version()
        })
    
    def _get_python_version(self) -> str:
        """Get Python version"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics and update gauges"""
        try:
            process = psutil.Process()
            
            # CPU metrics
            cpu_times = process.cpu_times()
            cpu_total = cpu_times.user + cpu_times.system
            self.app_cpu_seconds_total._value._value = cpu_total
            
            cpu_percent = process.cpu_percent()
            self.app_cpu_usage_percent.set(cpu_percent)
            
            # Memory metrics
            memory_info = process.memory_info()
            self.app_memory_resident_bytes.set(memory_info.rss)
            self.app_memory_virtual_bytes.set(memory_info.vms)
            
            memory_percent = process.memory_percent()
            self.app_memory_usage_percent.set(memory_percent)
            
            # Process metrics
            try:
                self.app_open_fds.set(process.num_fds())
            except (AttributeError, psutil.AccessDenied):
                # Windows doesn't support num_fds()
                pass
            
            self.app_threads_total.set(process.num_threads())
            
            # Uptime
            current_time = time.time()
            uptime = current_time - self.start_time
            self.app_uptime_seconds.set(uptime)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'threads': process.num_threads(),
                'uptime': uptime
            }
            
        except psutil.NoSuchProcess:
            return {}
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return {}
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of current system metrics"""
        return self.collect_metrics()


# Global system metrics collector instance
system_metrics = SystemMetricsCollector()
