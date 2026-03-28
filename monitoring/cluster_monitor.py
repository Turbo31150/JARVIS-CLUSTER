"""
JARVIS CLUSTER MONITOR
Monitoring temps reel du cluster
Dashboard et alertes
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, field
import psutil

logger = logging.getLogger("JARVIS-Monitor")
logging.basicConfig(level=logging.INFO)


@dataclass
class NodeMetrics:
    """Metriques d'un noeud"""
    node_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    gpu_memory_percent: float = 0.0
    network_in: float = 0.0
    network_out: float = 0.0
    tasks_pending: int = 0
    tasks_running: int = 0
    tasks_completed: int = 0
    status: str = "unknown"
    latency_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "gpu_memory_percent": self.gpu_memory_percent,
            "network_in": self.network_in,
            "network_out": self.network_out,
            "tasks_pending": self.tasks_pending,
            "tasks_running": self.tasks_running,
            "tasks_completed": self.tasks_completed,
            "status": self.status,
            "latency_ms": self.latency_ms
        }


@dataclass
class Alert:
    """Alerte du cluster"""
    alert_id: str
    node_id: str
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "node_id": self.node_id,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }


class ClusterMonitor:
    """
    Moniteur de cluster JARVIS
    Collecte metriques, genere alertes, dashboard
    """

    def __init__(self):
        self.nodes: Dict[str, Dict] = {
            "M2": {"ip": "192.168.1.26", "port": 8765},
            "M1": {"ip": "192.168.1.85", "port": 8765},
            "M3": {"ip": "192.168.1.113", "port": 1234},
        }
        self.metrics_history: Dict[str, List[NodeMetrics]] = {}
        self.alerts: List[Alert] = []
        self.alert_rules = {
            "cpu_high": {"threshold": 90, "severity": "warning"},
            "memory_high": {"threshold": 85, "severity": "warning"},
            "disk_high": {"threshold": 90, "severity": "critical"},
            "node_offline": {"severity": "critical"},
            "latency_high": {"threshold": 1000, "severity": "warning"}
        }
        self.running = False
        self.check_interval = 30  # seconds

    async def collect_local_metrics(self) -> NodeMetrics:
        """Collecter les metriques locales (M2)"""
        metrics = NodeMetrics(node_id="M2")

        try:
            # CPU
            metrics.cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            mem = psutil.virtual_memory()
            metrics.memory_percent = mem.percent

            # Disk
            disk = psutil.disk_usage('/')
            metrics.disk_percent = disk.percent

            # Network
            net = psutil.net_io_counters()
            metrics.network_in = net.bytes_recv / 1024 / 1024  # MB
            metrics.network_out = net.bytes_sent / 1024 / 1024  # MB

            metrics.status = "online"

        except Exception as e:
            logger.error(f"Error collecting local metrics: {e}")
            metrics.status = "error"

        return metrics

    async def collect_remote_metrics(self, node_id: str, ip: str, port: int) -> NodeMetrics:
        """Collecter les metriques d'un noeud distant"""
        metrics = NodeMetrics(node_id=node_id)

        try:
            start_time = datetime.now()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip}:{port}/status",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Calculer latence
                        latency = (datetime.now() - start_time).total_seconds() * 1000
                        metrics.latency_ms = latency

                        # Parser les donnees
                        metrics.tasks_pending = data.get("tasks_pending", 0)
                        metrics.tasks_running = data.get("tasks_running", 0)
                        metrics.tasks_completed = data.get("tasks_completed", 0)
                        metrics.status = "online"
                    else:
                        metrics.status = "error"

        except asyncio.TimeoutError:
            metrics.status = "timeout"
            metrics.latency_ms = 5000
        except Exception as e:
            logger.error(f"Error collecting metrics from {node_id}: {e}")
            metrics.status = "offline"

        return metrics

    def check_alerts(self, metrics: NodeMetrics):
        """Verifier les regles d'alerte"""
        node_id = metrics.node_id

        # CPU high
        if metrics.cpu_percent > self.alert_rules["cpu_high"]["threshold"]:
            self.create_alert(
                node_id,
                self.alert_rules["cpu_high"]["severity"],
                f"CPU usage high: {metrics.cpu_percent}%"
            )

        # Memory high
        if metrics.memory_percent > self.alert_rules["memory_high"]["threshold"]:
            self.create_alert(
                node_id,
                self.alert_rules["memory_high"]["severity"],
                f"Memory usage high: {metrics.memory_percent}%"
            )

        # Disk high
        if metrics.disk_percent > self.alert_rules["disk_high"]["threshold"]:
            self.create_alert(
                node_id,
                self.alert_rules["disk_high"]["severity"],
                f"Disk usage critical: {metrics.disk_percent}%"
            )

        # Node offline
        if metrics.status == "offline":
            self.create_alert(
                node_id,
                self.alert_rules["node_offline"]["severity"],
                f"Node {node_id} is OFFLINE"
            )

        # Latency high
        if metrics.latency_ms > self.alert_rules["latency_high"]["threshold"]:
            self.create_alert(
                node_id,
                self.alert_rules["latency_high"]["severity"],
                f"High latency to {node_id}: {metrics.latency_ms}ms"
            )

    def create_alert(self, node_id: str, severity: str, message: str):
        """Creer une nouvelle alerte"""
        alert_id = f"{node_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Eviter les doublons recents
        recent_alerts = [a for a in self.alerts
                        if a.node_id == node_id
                        and a.message == message
                        and (datetime.now() - a.timestamp) < timedelta(minutes=5)]

        if not recent_alerts:
            alert = Alert(
                alert_id=alert_id,
                node_id=node_id,
                severity=severity,
                message=message
            )
            self.alerts.append(alert)
            logger.warning(f"ALERT [{severity}] {node_id}: {message}")

            # Garder seulement les 100 dernieres alertes
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

    def store_metrics(self, metrics: NodeMetrics):
        """Stocker les metriques dans l'historique"""
        node_id = metrics.node_id

        if node_id not in self.metrics_history:
            self.metrics_history[node_id] = []

        self.metrics_history[node_id].append(metrics)

        # Garder 1h d'historique (120 points a 30s)
        if len(self.metrics_history[node_id]) > 120:
            self.metrics_history[node_id] = self.metrics_history[node_id][-120:]

    async def collect_all_metrics(self) -> Dict[str, NodeMetrics]:
        """Collecter les metriques de tous les noeuds"""
        all_metrics = {}

        # Metriques locales (M3)
        local_metrics = await self.collect_local_metrics()
        all_metrics["M2"] = local_metrics
        self.store_metrics(local_metrics)
        self.check_alerts(local_metrics)

        # Metriques des autres noeuds
        for node_id, config in self.nodes.items():
            if node_id != "M2":  # Pas soi-meme
                metrics = await self.collect_remote_metrics(
                    node_id, config["ip"], config["port"]
                )
                all_metrics[node_id] = metrics
                self.store_metrics(metrics)
                self.check_alerts(metrics)

        return all_metrics

    def get_dashboard(self) -> Dict:
        """Generer le dashboard"""
        latest_metrics = {}
        for node_id, history in self.metrics_history.items():
            if history:
                latest_metrics[node_id] = history[-1].to_dict()

        active_alerts = [a.to_dict() for a in self.alerts if not a.acknowledged]

        return {
            "timestamp": datetime.now().isoformat(),
            "cluster_status": "healthy" if not active_alerts else "degraded",
            "nodes": latest_metrics,
            "alerts": active_alerts[:10],  # 10 dernieres
            "total_alerts": len(active_alerts)
        }

    async def start_monitoring(self):
        """Demarrer le monitoring continu"""
        self.running = True
        logger.info("Cluster monitoring started")

        while self.running:
            try:
                metrics = await self.collect_all_metrics()
                logger.info(f"Collected metrics for {len(metrics)} nodes")

                # Afficher dashboard compact
                dashboard = self.get_dashboard()
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cluster Status: {dashboard['cluster_status']}")
                for node_id, m in dashboard['nodes'].items():
                    print(f"  {node_id}: CPU={m['cpu_percent']:.1f}% MEM={m['memory_percent']:.1f}% STATUS={m['status']}")

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            await asyncio.sleep(self.check_interval)

    async def stop_monitoring(self):
        """Arreter le monitoring"""
        self.running = False
        logger.info("Cluster monitoring stopped")


# Instance globale
monitor = ClusterMonitor()


async def main():
    """Test du monitoring"""
    print("Starting JARVIS Cluster Monitor...")
    print("Press Ctrl+C to stop\n")

    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        await monitor.stop_monitoring()
        print("\nMonitoring stopped")


if __name__ == "__main__":
    asyncio.run(main())
