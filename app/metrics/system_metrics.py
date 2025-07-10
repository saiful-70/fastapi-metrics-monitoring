"""
System-level metrics collection for CPU, memory, and process statistics
"""
import time
import gc
import psutil
from prometheus_client import Gauge, Counter, Info, start_http_server
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
import sys


class SystemMetricsCollector:
    """Collects and exposes system-level metrics"""
    
    def __init__(self):
        # Custom application metrics (avoiding conflicts with standard process metrics)
        self.app_cpu_seconds_total = Counter(
            'app_cpu_seconds_total',
            'Total user and system CPU time spent by the application in seconds'
        )
        
        self.app_memory_resident_bytes = Gauge(
            'app_memory_resident_bytes',
            'Physical memory currently used by the application in bytes'
        )
        
        self.app_memory_virtual_bytes = Gauge(
            'app_memory_virtual_bytes',
            'Virtual memory allocated by the application in bytes'
        )
        
        self.app_start_time_seconds = Gauge(
            'app_start_time_seconds',
            'Start time of the application since unix epoch in seconds'
        )
        
        self.app_open_fds = Gauge(
            'app_open_fds',
            'Number of open file descriptors for the application'
        )
        
        # Additional CPU metrics
        self.app_cpu_usage_percent = Gauge(
            'app_cpu_usage_percent',
            'Current CPU usage percentage of the application'
        )
        
        # Additional memory metrics
        self.app_memory_usage_percent = Gauge(
            'app_memory_usage_percent',
            'Memory usage percentage of the application'
        )
        
        # Process thread metrics
        self.app_threads_total = Gauge(
            'app_threads_total',
            'Number of OS threads in the application process'
        )
        
        # Uptime metric
        self.app_uptime_seconds = Gauge(
            'app_uptime_seconds',
            'Time in seconds since the application started'
        )
        
        # Garbage Collection metrics
        self.gc_collections_total = Counter(
            'gc_collections_total',
            'Total number of garbage collections',
            ['generation']
        )
        
        self.gc_collected_objects_total = Counter(
            'gc_collected_objects_total',
            'Total number of objects collected during gc',
            ['generation']
        )
        
        self.gc_uncollectable_objects_total = Counter(
            'gc_uncollectable_objects_total',
            'Total number of uncollectable objects found',
            ['generation']
        )
        
        # Memory thresholds for alerting
        self.memory_alert_threshold_bytes = Gauge(
            'memory_alert_threshold_bytes',
            'Memory usage threshold for alerting in bytes'
        )
        
        self.cpu_alert_threshold_percent = Gauge(
            'cpu_alert_threshold_percent',
            'CPU usage threshold for alerting in percent'
        )
        
        # Process info
        self.app_info = Info(
            'app_info',
            'Application process information'
        )
        
        # Initialize process start time
        self.start_time = time.time()
        self.app_start_time_seconds.set(self.start_time)
        
        # Set default alert thresholds
        self.memory_alert_threshold_bytes.set(8 * 1024 * 1024 * 1024)  # 8GB
        self.cpu_alert_threshold_percent.set(80.0)  # 80%
        
        # Initialize GC stats tracking
        self._last_gc_stats = self._get_gc_stats()
        
        # Set process info
        process = psutil.Process()
        self.app_info.info({
            'pid': str(process.pid),
            'name': process.name(),
            'python_version': self._get_python_version(),
            'platform': sys.platform
        })
    
    def _get_python_version(self) -> str:
        """Get Python version"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_gc_stats(self) -> Dict[int, Dict[str, int]]:
        """Get garbage collection statistics"""
        stats = {}
        for i in range(len(gc.get_stats())):
            stat = gc.get_stats()[i]
            stats[i] = {
                'collections': stat.get('collections', 0),
                'collected': stat.get('collected', 0),
                'uncollectable': stat.get('uncollectable', 0)
            }
        return stats
    
    def _update_gc_metrics(self):
        """Update garbage collection metrics"""
        try:
            current_stats = self._get_gc_stats()
            
            for generation, stats in current_stats.items():
                last_stats = self._last_gc_stats.get(generation, {})
                
                # Calculate increments
                collections_inc = stats['collections'] - last_stats.get('collections', 0)
                collected_inc = stats['collected'] - last_stats.get('collected', 0)
                uncollectable_inc = stats['uncollectable'] - last_stats.get('uncollectable', 0)
                
                # Update counters if there's an increment
                if collections_inc > 0:
                    self.gc_collections_total.labels(generation=str(generation))._value._value = stats['collections']
                if collected_inc > 0:
                    self.gc_collected_objects_total.labels(generation=str(generation))._value._value = stats['collected']
                if uncollectable_inc > 0:
                    self.gc_uncollectable_objects_total.labels(generation=str(generation))._value._value = stats['uncollectable']
            
            self._last_gc_stats = current_stats
            
        except Exception as e:
            print(f"Error updating GC metrics: {e}")
    
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
            
            # Update garbage collection metrics
            self._update_gc_metrics()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'threads': process.num_threads(),
                'uptime': uptime,
                'cpu_total_seconds': cpu_total
            }
            
        except psutil.NoSuchProcess:
            return {}
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return {}
    
    def get_standard_process_metrics(self) -> Dict[str, Any]:
        """
        Get standard Prometheus process metrics that are automatically collected
        These metrics are automatically available when using prometheus_client
        """
        try:
            from prometheus_client import REGISTRY
            
            # Generate metrics to get current values
            metrics_data = generate_latest(REGISTRY)
            
            # The standard process metrics are automatically collected by prometheus_client
            # and include: process_cpu_seconds_total, process_resident_memory_bytes, etc.
            return {
                "note": "Standard process metrics are automatically collected by prometheus_client",
                "available_metrics": [
                    "process_cpu_seconds_total",
                    "process_resident_memory_bytes", 
                    "process_virtual_memory_bytes",
                    "process_start_time_seconds",
                    "process_open_fds",
                    "process_max_fds"
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of current system metrics"""
        return self.collect_metrics()
    
    def calculate_cpu_rate(self, interval: float = 5.0) -> float:
        """
        Calculate CPU usage rate over an interval
        
        Args:
            interval: Time interval in seconds
            
        Returns:
            CPU usage rate (similar to rate(process_cpu_seconds_total[5m]))
        """
        try:
            process = psutil.Process()
            initial_cpu = sum(process.cpu_times())
            time.sleep(interval)
            final_cpu = sum(process.cpu_times())
            
            cpu_rate = (final_cpu - initial_cpu) / interval
            return cpu_rate
        except Exception as e:
            print(f"Error calculating CPU rate: {e}")
            return 0.0
    
    def check_alert_thresholds(self) -> Dict[str, bool]:
        """
        Check if current metrics exceed alert thresholds
        
        Returns:
            Dictionary indicating which thresholds are exceeded
        """
        current_metrics = self.collect_metrics()
        
        alerts = {
            'high_cpu': current_metrics.get('cpu_percent', 0) > self.cpu_alert_threshold_percent._value._value,
            'high_memory': current_metrics.get('memory_rss', 0) > self.memory_alert_threshold_bytes._value._value,
            'high_memory_percent': current_metrics.get('memory_percent', 0) > 85.0
        }
        
        return alerts


# Global system metrics collector instance
system_metrics = SystemMetricsCollector()
