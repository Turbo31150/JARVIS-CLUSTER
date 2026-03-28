"""
JARVIS ORCHESTRATOR - Core System
Machine M2 - Cluster Node
Pilotable par M1 via API/WebSocket

Architecture inspiree de microsoft/JARVIS (HuggingGPT)
+ sukeesh/Jarvis (plugin system)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import os

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("JARVIS-M2")


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    SELECTING = "selecting"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeRole(Enum):
    MASTER = "master"      # M1
    WORKER = "worker"      # M2, M3, autres
    HYBRID = "hybrid"      # Peut etre les deux


@dataclass
class ClusterNode:
    """Representation d'un noeud du cluster"""
    node_id: str
    hostname: str
    ip: str
    port: int
    role: NodeRole
    capabilities: List[str] = field(default_factory=list)
    status: str = "online"
    last_heartbeat: datetime = field(default_factory=datetime.now)
    load: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "ip": self.ip,
            "port": self.port,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "load": self.load
        }


@dataclass
class Task:
    """Tache JARVIS avec workflow 4 etapes"""
    task_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    source_node: str = "M2"
    target_nodes: List[str] = field(default_factory=list)
    subtasks: List[Dict] = field(default_factory=list)
    selected_models: List[str] = field(default_factory=list)
    results: Dict = field(default_factory=dict)
    consensus_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)  # DAG

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "source_node": self.source_node,
            "target_nodes": self.target_nodes,
            "subtasks": self.subtasks,
            "selected_models": self.selected_models,
            "results": self.results,
            "consensus_score": self.consensus_score,
            "dependencies": self.dependencies
        }


class JarvisOrchestrator:
    """
    Orchestrateur JARVIS principal
    Workflow: Planning -> Selection -> Execution -> Synthesis
    """

    def __init__(self, node_id: str = "M2"):
        self.node_id = node_id
        self.node_role = NodeRole.WORKER
        self.cluster_nodes: Dict[str, ClusterNode] = {}
        self.tasks: Dict[str, Task] = {}
        self.agents: Dict[str, Any] = {}
        self.models: Dict[str, Dict] = {}
        self.running = False

        # Configuration M2
        self.config = {
            "node_id": "M2",
            "hostname": "WIN-TBOT",
            "master_node": "M1",
            "api_port": 8765,
            "websocket_port": 8766,
            "heartbeat_interval": 30,
            "consensus_threshold": 0.70,
            "max_parallel_tasks": 10
        }

        # Modeles IA disponibles
        self.models = {
            "qwen3-30b": {"type": "local", "endpoint": "http://192.168.1.85:1234", "weight": 0.30, "specialty": "technical"},
            "perplexity": {"type": "cloud", "endpoint": "api.perplexity.ai", "weight": 0.20, "specialty": "sentiment"},
            "claude": {"type": "cloud", "endpoint": "api.anthropic.com", "weight": 0.25, "specialty": "strategy"},
            "gemini": {"type": "cloud", "endpoint": "gemini-cli", "weight": 0.15, "specialty": "vision"},
            "nemotron": {"type": "local", "endpoint": "http://127.0.0.1:1234", "weight": 0.10, "specialty": "fast"}
        }

        logger.info(f"JARVIS Orchestrator initialized - Node {self.node_id}")

    def register_node(self, node: ClusterNode) -> bool:
        """Enregistrer un noeud dans le cluster"""
        self.cluster_nodes[node.node_id] = node
        logger.info(f"Node registered: {node.node_id} ({node.hostname})")
        return True

    def register_self(self) -> ClusterNode:
        """Enregistrer ce noeud (M2)"""
        self_node = ClusterNode(
            node_id="M2",
            hostname="WIN-TBOT",
            ip="192.168.1.26",
            port=8765,
            role=NodeRole.WORKER,
            capabilities=[
                "trading", "mcp", "lm-studio", "n8n",
                "telegram", "mexc", "multi-ia", "gpu",
                "shell", "file-access", "process-mgmt"
            ]
        )
        self.cluster_nodes["M2"] = self_node
        return self_node

    async def stage_1_planning(self, task: Task) -> List[Dict]:
        """
        STAGE 1: Task Planning
        Decompose la tache en sous-taches (DAG)
        """
        task.status = TaskStatus.PLANNING
        logger.info(f"[STAGE 1] Planning task: {task.task_id}")

        # Analyse de la tache et decomposition
        subtasks = []

        # Detection du type de tache
        description_lower = task.description.lower()

        if any(kw in description_lower for kw in ["scan", "analyse", "trading", "mexc"]):
            subtasks = [
                {"id": 0, "type": "data_collection", "action": "scan_mexc", "dep": []},
                {"id": 1, "type": "technical_analysis", "action": "analyze_technicals", "dep": [0]},
                {"id": 2, "type": "sentiment_analysis", "action": "analyze_sentiment", "dep": [0]},
                {"id": 3, "type": "risk_assessment", "action": "assess_risk", "dep": [1, 2]},
                {"id": 4, "type": "consensus", "action": "multi_ia_consensus", "dep": [1, 2, 3]},
                {"id": 5, "type": "decision", "action": "make_decision", "dep": [4]},
                {"id": 6, "type": "execution", "action": "execute_or_alert", "dep": [5]}
            ]
        elif any(kw in description_lower for kw in ["cluster", "node", "status"]):
            subtasks = [
                {"id": 0, "type": "cluster_scan", "action": "scan_nodes", "dep": []},
                {"id": 1, "type": "health_check", "action": "check_health", "dep": [0]},
                {"id": 2, "type": "report", "action": "generate_report", "dep": [1]}
            ]
        else:
            # Tache generique
            subtasks = [
                {"id": 0, "type": "analyze", "action": "analyze_request", "dep": []},
                {"id": 1, "type": "execute", "action": "execute_action", "dep": [0]},
                {"id": 2, "type": "report", "action": "report_result", "dep": [1]}
            ]

        task.subtasks = subtasks
        logger.info(f"[STAGE 1] Planned {len(subtasks)} subtasks")
        return subtasks

    async def stage_2_selection(self, task: Task) -> List[str]:
        """
        STAGE 2: Model Selection
        Selectionne les modeles experts pour chaque sous-tache
        """
        task.status = TaskStatus.SELECTING
        logger.info(f"[STAGE 2] Selecting models for task: {task.task_id}")

        selected = []

        for subtask in task.subtasks:
            subtask_type = subtask.get("type", "")

            # Mapping type -> modele optimal
            model_mapping = {
                "technical_analysis": "qwen3-30b",
                "sentiment_analysis": "perplexity",
                "risk_assessment": "claude",
                "consensus": "claude",
                "decision": "claude",
                "data_collection": "nemotron",
                "cluster_scan": "nemotron",
                "health_check": "nemotron",
                "analyze": "qwen3-30b",
                "execute": "local",
                "report": "claude"
            }

            model = model_mapping.get(subtask_type, "qwen3-30b")
            subtask["assigned_model"] = model
            if model not in selected:
                selected.append(model)

        task.selected_models = selected
        logger.info(f"[STAGE 2] Selected models: {selected}")
        return selected

    async def stage_3_execution(self, task: Task) -> Dict:
        """
        STAGE 3: Task Execution
        Execute les sous-taches en respectant le DAG
        """
        task.status = TaskStatus.EXECUTING
        logger.info(f"[STAGE 3] Executing task: {task.task_id}")

        results = {}
        completed_ids = set()

        # Execution en respectant les dependances (DAG)
        while len(completed_ids) < len(task.subtasks):
            # Trouver les taches executables (deps satisfaites)
            executable = []
            for subtask in task.subtasks:
                sid = subtask["id"]
                if sid not in completed_ids:
                    deps = subtask.get("dep", [])
                    if all(d in completed_ids for d in deps):
                        executable.append(subtask)

            if not executable:
                logger.warning("No executable subtasks found - possible circular dependency")
                break

            # Executer en parallele les taches sans deps mutuelles
            exec_tasks = []
            for subtask in executable:
                exec_tasks.append(self._execute_subtask(subtask, results))

            subtask_results = await asyncio.gather(*exec_tasks, return_exceptions=True)

            for subtask, result in zip(executable, subtask_results):
                sid = subtask["id"]
                if isinstance(result, Exception):
                    results[sid] = {"error": str(result)}
                else:
                    results[sid] = result
                completed_ids.add(sid)

        task.results = results
        logger.info(f"[STAGE 3] Execution complete: {len(results)} subtasks")
        return results

    async def _execute_subtask(self, subtask: Dict, previous_results: Dict) -> Dict:
        """Execute une sous-tache individuelle"""
        action = subtask.get("action", "")
        model = subtask.get("assigned_model", "local")

        logger.info(f"  Executing subtask {subtask['id']}: {action} with {model}")

        # Simulation d'execution (a remplacer par vraie logique)
        await asyncio.sleep(0.1)

        return {
            "subtask_id": subtask["id"],
            "action": action,
            "model": model,
            "status": "success",
            "output": f"Result of {action}",
            "timestamp": datetime.now().isoformat()
        }

    async def stage_4_synthesis(self, task: Task) -> Dict:
        """
        STAGE 4: Response Synthesis
        Synthetise les resultats et calcule le consensus
        """
        logger.info(f"[STAGE 4] Synthesizing results for: {task.task_id}")

        # Calcul du consensus
        successful = sum(1 for r in task.results.values() if r.get("status") == "success")
        total = len(task.results)
        consensus_score = successful / total if total > 0 else 0

        task.consensus_score = consensus_score
        task.status = TaskStatus.COMPLETED

        synthesis = {
            "task_id": task.task_id,
            "status": "completed",
            "consensus_score": consensus_score,
            "consensus_reached": consensus_score >= self.config["consensus_threshold"],
            "subtasks_total": total,
            "subtasks_successful": successful,
            "results_summary": task.results,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"[STAGE 4] Synthesis complete - Consensus: {consensus_score:.2%}")
        return synthesis

    async def process_task(self, description: str, source: str = "local") -> Dict:
        """
        Pipeline complet JARVIS (4 stages)
        """
        # Creer la tache
        task_id = hashlib.md5(f"{description}{datetime.now()}".encode()).hexdigest()[:12]
        task = Task(
            task_id=task_id,
            description=description,
            source_node=source
        )
        self.tasks[task_id] = task

        logger.info(f"Processing task: {task_id}")
        logger.info(f"Description: {description}")

        try:
            # Stage 1: Planning
            await self.stage_1_planning(task)

            # Stage 2: Model Selection
            await self.stage_2_selection(task)

            # Stage 3: Execution
            await self.stage_3_execution(task)

            # Stage 4: Synthesis
            result = await self.stage_4_synthesis(task)

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"Task failed: {e}")
            return {"error": str(e), "task_id": task_id}

    def get_status(self) -> Dict:
        """Retourne le status du noeud M2"""
        return {
            "node_id": self.node_id,
            "role": self.node_role.value,
            "status": "online" if self.running else "standby",
            "tasks_pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "tasks_running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.EXECUTING),
            "tasks_completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "cluster_nodes": len(self.cluster_nodes),
            "models_available": list(self.models.keys()),
            "config": self.config
        }

    async def start(self):
        """Demarrer l'orchestrateur"""
        self.running = True
        self.register_self()
        logger.info(f"JARVIS Orchestrator started on node {self.node_id}")

    async def stop(self):
        """Arreter l'orchestrateur"""
        self.running = False
        logger.info(f"JARVIS Orchestrator stopped on node {self.node_id}")


# Instance globale
orchestrator = JarvisOrchestrator(node_id="M2")


async def main():
    """Test de l'orchestrateur"""
    await orchestrator.start()

    # Test avec une tache trading
    result = await orchestrator.process_task(
        "Analyser BTC/USDT pour opportunite LONG sur MEXC Futures"
    )

    print(json.dumps(result, indent=2))
    print("\nStatus:", json.dumps(orchestrator.get_status(), indent=2))

    await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
