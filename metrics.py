import time
import functools
import psutil
import logging
from datetime import datetime

# Configuración del logging
logging.basicConfig(
    filename=f'metrics_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
metrics_logger = logging.getLogger('metrics')

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            'endpoint_latency': {},
            'memory_usage': {},
            'function_timing': {},
            'db_operations': {}
        }
    
    def track_endpoint(self, endpoint_name):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                result = func(*args, **kwargs)
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                execution_time = round(end_time - start_time, 3)
                memory_used = round(end_memory - start_memory, 2)
                
                metrics_logger.info(
                    f"[MÉTRICA] Endpoint: {endpoint_name} | "
                    f"Tiempo de ejecución: {execution_time}s | "
                    f"Memoria utilizada: {memory_used}MB | "
                    f"Timestamp: {datetime.now().isoformat()}"
                )
                
                # Almacenar métricas
                if endpoint_name not in self.metrics['endpoint_latency']:
                    self.metrics['endpoint_latency'][endpoint_name] = []
                self.metrics['endpoint_latency'][endpoint_name].append(execution_time)
                
                if endpoint_name not in self.metrics['memory_usage']:
                    self.metrics['memory_usage'][endpoint_name] = []
                self.metrics['memory_usage'][endpoint_name].append(memory_used)
                
                return result
            return wrapper
        return decorator
    
    def track_db_operation(self, operation_name):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                result = func(*args, **kwargs)
                
                execution_time = round(time.time() - start_time, 3)
                
                metrics_logger.info(
                    f"[MÉTRICA-DB] Operación: {operation_name} | "
                    f"Tiempo de ejecución: {execution_time}s | "
                    f"Timestamp: {datetime.now().isoformat()}"
                )
                
                if operation_name not in self.metrics['db_operations']:
                    self.metrics['db_operations'][operation_name] = []
                self.metrics['db_operations'][operation_name].append(execution_time)
                
                return result
            return wrapper
        return decorator

# Instancia global del recolector de métricas
metrics = MetricsCollector()

def get_system_metrics():
    """Obtiene métricas del sistema."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used_gb': round(memory.used / (1024**3), 2),
        'disk_percent': disk.percent,
        'disk_used_gb': round(disk.used / (1024**3), 2)
    }
    
    # Log de métricas del sistema
    metrics_logger.info(
        f"[SISTEMA] CPU: {cpu_percent}% | "
        f"Memoria: {memory.percent}% ({metrics['memory_used_gb']} GB) | "
        f"Disco: {disk.percent}% ({metrics['disk_used_gb']} GB) | "
        f"Timestamp: {datetime.now().isoformat()}"
    )
    
    return metrics