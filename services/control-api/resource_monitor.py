"""
Resource Monitoring Module
Collects CPU, Memory, Network metrics for Docker containers

For Publication: Proves resource efficiency (NQ1)
"""

import docker
import psutil
import time
from typing import Dict, List
from datetime import datetime

class ResourceMonitor:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Docker client not available: {e}")
            self.docker_client = None

    def get_container_stats(self, container_name: str) -> Dict:
        """
        Get resource usage for a specific container

        Returns:
            {
                'cpu_percent': float,
                'memory_mb': float,
                'memory_percent': float,
                'network_rx_mb': float,
                'network_tx_mb': float,
                'timestamp': str
            }
        """
        if not self.docker_client:
            return self._get_fallback_stats()

        try:
            container = self.docker_client.containers.get(container_name)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                        stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']

            num_cpus = stats['cpu_stats']['online_cpus']

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

            # Calculate memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_mb = memory_usage / (1024 * 1024)
            memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0

            # Calculate network I/O
            networks = stats.get('networks', {})
            total_rx = sum(net['rx_bytes'] for net in networks.values())
            total_tx = sum(net['tx_bytes'] for net in networks.values())

            return {
                'container_name': container_name,
                'cpu_percent': round(cpu_percent, 2),
                'memory_mb': round(memory_mb, 2),
                'memory_percent': round(memory_percent, 2),
                'network_rx_mb': round(total_rx / (1024 * 1024), 2),
                'network_tx_mb': round(total_tx / (1024 * 1024), 2),
                'timestamp': datetime.utcnow().isoformat()
            }

        except docker.errors.NotFound:
            return {
                'container_name': container_name,
                'error': 'Container not found',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'container_name': container_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_architecture_stats(self, architecture: str) -> Dict:
        """
        Get aggregated stats for all containers in an architecture

        Args:
            architecture: 'bpc4msa', 'synchronous', or 'monolithic'

        Returns:
            {
                'total_cpu_percent': float,
                'total_memory_mb': float,
                'containers': [...],
                'timestamp': str
            }
        """

        container_mapping = {
            'bpc4msa': [
                'bpc4msa-business-logic-1',
                'bpc4msa-compliance-service-1',
                'bpc4msa-audit-service-1',
                'bpc4msa-socket-service-1',
                'bpc4msa-kafka-bpc4msa-1',
                'bpc4msa-zookeeper-bpc4msa-1',
                'bpc4msa-postgres-bpc4msa-1'
            ],
            'synchronous': [
                'bpc4msa-soa-service-1',
                'bpc4msa-postgres-sync-1'
            ],
            'monolithic': [
                'bpc4msa-monolithic-service-1',
                'bpc4msa-postgres-mono-1'
            ]
        }

        containers = container_mapping.get(architecture, [])
        container_stats = []
        total_cpu = 0.0
        total_memory = 0.0

        for container_name in containers:
            stats = self.get_container_stats(container_name)
            container_stats.append(stats)

            if 'cpu_percent' in stats:
                total_cpu += stats['cpu_percent']
            if 'memory_mb' in stats:
                total_memory += stats['memory_mb']

        return {
            'architecture': architecture,
            'total_cpu_percent': round(total_cpu, 2),
            'total_memory_mb': round(total_memory, 2),
            'containers': container_stats,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_all_architectures_stats(self) -> Dict:
        """Get stats for all three architectures"""
        return {
            'bpc4msa': self.get_architecture_stats('bpc4msa'),
            'synchronous': self.get_architecture_stats('synchronous'),
            'monolithic': self.get_architecture_stats('monolithic'),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _get_fallback_stats(self) -> Dict:
        """Fallback to host-level stats if Docker is not available"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        network = psutil.net_io_counters()

        return {
            'cpu_percent': cpu_percent,
            'memory_mb': round(memory.used / (1024 * 1024), 2),
            'memory_percent': memory.percent,
            'network_rx_mb': round(network.bytes_recv / (1024 * 1024), 2),
            'network_tx_mb': round(network.bytes_sent / (1024 * 1024), 2),
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Host-level stats (Docker not available)'
        }

    def get_system_summary(self) -> Dict:
        """Get overall system resource usage"""
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu': {
                'count': cpu_count,
                'percent': cpu_percent,
                'per_cpu': psutil.cpu_percent(interval=1, percpu=True)
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': disk.percent
            },
            'timestamp': datetime.utcnow().isoformat()
        }

# Singleton instance
_monitor = None

def get_monitor() -> ResourceMonitor:
    """Get singleton ResourceMonitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
