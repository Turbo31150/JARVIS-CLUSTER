"""
JARVIS CLUSTER STARTUP SCRIPT
Demarre tous les services JARVIS sur M2
"""

import asyncio
import subprocess
import sys
import os
import json
import logging
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | JARVIS-STARTUP | %(levelname)s | %(message)s'
)
logger = logging.getLogger("JARVIS-Startup")

# Paths
JARVIS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(JARVIS_ROOT, "config", "cluster_config.json")

NODE_ID = "M2"
NODE_IP = "192.168.1.26"
MASTER_IP = "192.168.1.85"


class JarvisStartup:
    """Gestionnaire de demarrage JARVIS"""

    def __init__(self):
        self.config = self.load_config()
        self.processes = {}
        self.node_id = NODE_ID

    def load_config(self) -> dict:
        """Charger la configuration"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def check_dependencies(self) -> bool:
        """Verifier les dependances"""
        deps = ["python", "pip"]
        missing = []

        for dep in deps:
            try:
                subprocess.run([dep, "--version"], capture_output=True, check=True)
            except Exception:
                missing.append(dep)

        if missing:
            logger.error(f"Missing dependencies: {missing}")
            return False

        logger.info("All dependencies OK")
        return True

    def install_requirements(self):
        """Installer les requirements Python"""
        requirements = [
            "fastapi",
            "uvicorn",
            "websockets",
            "httpx",
            "pydantic",
            "psutil"
        ]

        logger.info("Installing Python requirements...")
        for req in requirements:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", req, "-q"],
                    check=True
                )
            except Exception:
                logger.warning(f"Failed to install {req}")

        logger.info("Requirements installed")

    def start_api_server(self):
        """Demarrer le serveur API"""
        api_path = os.path.join(JARVIS_ROOT, "api", "cluster_api.py")
        port = self.config.get("nodes", {}).get(NODE_ID, {}).get("api_port", 8765)

        logger.info(f"Starting API server on port {port}...")

        process = subprocess.Popen(
            [sys.executable, api_path],
            cwd=JARVIS_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.processes["api"] = process
        logger.info(f"API server started (PID: {process.pid})")
        return process

    def start_mcp_server(self):
        """Demarrer le serveur MCP trading"""
        mcp_path = self.config.get("mcp_servers", {}).get("trading-ai-ultimate", {}).get("path")

        if mcp_path and os.path.exists(mcp_path):
            logger.info("Starting MCP Trading server...")

            process = subprocess.Popen(
                [sys.executable, mcp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes["mcp"] = process
            logger.info(f"MCP server started (PID: {process.pid})")
            return process
        else:
            logger.warning("MCP server path not found")
            return None

    def register_with_master(self):
        """S'enregistrer aupres de M1"""
        master_ip = self.config.get("nodes", {}).get("M1", {}).get("ip", MASTER_IP)
        master_port = self.config.get("nodes", {}).get("M1", {}).get("api_port", 8765)

        logger.info(f"Registering with master M1 ({master_ip}:{master_port})...")
        logger.info("Registration will be done when M1 is available")

    def print_status(self):
        """Afficher le status"""
        print("\n" + "="*60)
        print(f"  JARVIS CLUSTER - NODE {NODE_ID} - STARTED")
        print("="*60)
        print(f"  Node ID:     {NODE_ID}")
        print(f"  IP:          {NODE_IP}")
        print(f"  Hostname:    WIN-TBOT")
        print(f"  API Port:    8765")
        print(f"  Master:      M1 ({MASTER_IP})")
        print(f"  Full Control: ENABLED")
        print("="*60)
        print("\n  Services:")
        for name, proc in self.processes.items():
            status = "RUNNING" if proc.poll() is None else "STOPPED"
            print(f"    - {name}: {status} (PID: {proc.pid})")
        print("\n  Endpoints (from M1):")
        print(f"    - REST API:  http://{NODE_IP}:8765")
        print(f"    - WebSocket: ws://{NODE_IP}:8765/ws/M1")
        print(f"    - Health:    http://{NODE_IP}:8765/health")
        print(f"    - Shell:     POST http://{NODE_IP}:8765/shell")
        print(f"    - GPU:       GET  http://{NODE_IP}:8765/gpu")
        print(f"    - Files:     POST http://{NODE_IP}:8765/file/read")
        print(f"    - LM Query:  POST http://{NODE_IP}:8765/lm/query")
        print("="*60 + "\n")

    def start_all(self):
        """Demarrer tous les services"""
        logger.info(f"Starting JARVIS on {NODE_ID}...")

        # Verifier dependencies
        if not self.check_dependencies():
            return False

        # Installer requirements
        self.install_requirements()

        # Demarrer API
        self.start_api_server()

        # S'enregistrer avec M1
        self.register_with_master()

        # Afficher status
        self.print_status()

        return True

    def stop_all(self):
        """Arreter tous les services"""
        logger.info("Stopping JARVIS services...")

        for name, proc in self.processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
                logger.info(f"Stopped {name}")
            except Exception:
                proc.kill()
                logger.warning(f"Force killed {name}")

        self.processes.clear()
        logger.info("All services stopped")


async def main():
    """Main entry point"""
    startup = JarvisStartup()

    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        startup.stop_all()
    else:
        if startup.start_all():
            logger.info(f"JARVIS {NODE_ID} is ready! Full control from M1 enabled.")
            logger.info("Press Ctrl+C to stop...")

            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                startup.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
