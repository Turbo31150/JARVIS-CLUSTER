"""
JARVIS CLUSTER API — M2 Node
API REST + WebSocket pour communication M1 <-> M2
Permet a M1 de piloter ENTIEREMENT M2
Full autonomy: shell, files, processes, GPU, MCP, LM Studio, services
"""

import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn

# Ajouter le path parent pour imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.jarvis_orchestrator import orchestrator, Task, TaskStatus, ClusterNode, NodeRole
    HAS_ORCHESTRATOR = True
except Exception:
    HAS_ORCHESTRATOR = False

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS-API-M2")

NODE_ID = "M2"
NODE_IP = "192.168.1.26"
MASTER_IP = "192.168.1.85"
TURBO_ROOT = Path(os.environ.get("TURBO_ROOT", "C:/Users/Turbo/turbo"))

# FastAPI App
app = FastAPI(
    title="JARVIS Cluster API — M2",
    description="Full control API — M1 pilote M2 entierement",
    version="2.0.0",
)

# CORS — tout ouvert pour M1
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: Dict[str, WebSocket] = {}


# ============== MODELS ==============

class TaskRequest(BaseModel):
    description: str
    source: str = "M1"
    priority: int = 1
    target_nodes: list = []

class CommandRequest(BaseModel):
    command: str
    params: dict = {}
    target_node: str = "M2"

class ShellRequest(BaseModel):
    command: str
    cwd: str = "C:/Users/Turbo"
    timeout: int = 120
    shell: str = "powershell"

class FileReadRequest(BaseModel):
    path: str
    encoding: str = "utf-8"

class FileWriteRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"

class LMQueryRequest(BaseModel):
    prompt: str
    model: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    node: str = "local"

class ProcessRequest(BaseModel):
    action: str  # "list", "kill", "start"
    pid: int = 0
    name: str = ""
    command: str = ""

class ServiceRequest(BaseModel):
    action: str  # "start", "stop", "restart", "status"
    service: str

class NodeRegistration(BaseModel):
    node_id: str
    hostname: str
    ip: str
    port: int
    role: str = "worker"
    capabilities: list = []


# ============== ROOT & HEALTH ==============

@app.get("/")
async def root():
    return {
        "service": "JARVIS Cluster API",
        "node": NODE_ID,
        "ip": NODE_IP,
        "status": "online",
        "version": "2.0.0",
        "master": MASTER_IP,
        "full_control": True,
        "endpoints": {
            "info": ["/", "/status", "/health", "/system"],
            "cluster": ["/cluster", "/cluster/register", "/cluster/heartbeat"],
            "tasks": ["/task", "/tasks"],
            "control": ["/command", "/shell", "/powershell"],
            "files": ["/file/read", "/file/write", "/file/list"],
            "processes": ["/process"],
            "gpu": ["/gpu"],
            "lm": ["/lm/query", "/lm/models", "/lm/status"],
            "mcp": ["/mcp/{tool_name}"],
            "services": ["/services", "/service"],
            "ws": ["/ws/{node_id}"],
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "node": NODE_ID,
        "ip": NODE_IP,
        "timestamp": datetime.now().isoformat(),
        "uptime_s": time.time() - _start_time,
    }


@app.get("/status")
async def get_status():
    """Status complet du noeud M2"""
    gpu = _gpu_info()
    disk = shutil.disk_usage("C:/")
    import psutil
    mem = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=0.5)

    return {
        "node": NODE_ID,
        "ip": NODE_IP,
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_percent": cpu_pct,
        "ram_total_gb": round(mem.total / 1e9, 1),
        "ram_used_gb": round(mem.used / 1e9, 1),
        "ram_percent": mem.percent,
        "disk_total_gb": round(disk.total / 1e9, 1),
        "disk_free_gb": round(disk.free / 1e9, 1),
        "gpu": gpu,
        "services": _services_status(),
        "timestamp": datetime.now().isoformat(),
    }


# ============== SYSTEM INFO ==============

@app.get("/system")
async def system_info():
    """Info systeme detaillee"""
    import psutil
    return {
        "node": NODE_ID,
        "platform": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
        "ram": psutil.virtual_memory()._asdict(),
        "disk": {p.mountpoint: shutil.disk_usage(p.mountpoint)._asdict()
                 for p in psutil.disk_partitions() if "cdrom" not in p.opts},
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "network": {k: [a.address for a in v if a.family == 2]
                    for k, v in psutil.net_if_addrs().items()},
    }


# ============== GPU ==============

@app.get("/gpu")
async def gpu_endpoint():
    return {"gpu": _gpu_info()}


def _gpu_info() -> list:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        gpus = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "temp_c": int(parts[2]),
                    "util_pct": int(parts[3]),
                    "mem_used_mb": int(parts[4]),
                    "mem_total_mb": int(parts[5]),
                    "power_w": float(parts[6]),
                })
        return gpus
    except Exception as e:
        return [{"error": str(e)}]


# ============== SHELL EXECUTION (FULL CONTROL) ==============

@app.post("/shell")
async def execute_shell(request: ShellRequest):
    """
    Executer une commande shell sur M2.
    M1 peut tout faire: bash, powershell, cmd.
    """
    logger.info(f"Shell from M1: [{request.shell}] {request.command}")
    try:
        if request.shell == "powershell":
            cmd = ["powershell", "-NoProfile", "-Command", request.command]
        elif request.shell == "cmd":
            cmd = ["cmd", "/c", request.command]
        else:
            cmd = ["bash", "-c", request.command]

        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=request.timeout, cwd=request.cwd,
        )
        return {
            "stdout": r.stdout,
            "stderr": r.stderr,
            "returncode": r.returncode,
            "command": request.command,
            "shell": request.shell,
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "timeout": request.timeout}
    except Exception as e:
        return {"error": str(e)}


@app.post("/powershell")
async def execute_powershell(command: str = Body(..., embed=True)):
    """Shortcut — powershell direct"""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True, text=True, timeout=120,
    )
    return {"stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode}


# ============== FILE SYSTEM (FULL ACCESS) ==============

@app.post("/file/read")
async def read_file(request: FileReadRequest):
    """Lire un fichier sur M2"""
    p = Path(request.path)
    if not p.exists():
        raise HTTPException(404, f"File not found: {request.path}")
    try:
        content = p.read_text(encoding=request.encoding)
        return {"path": request.path, "size": p.stat().st_size, "content": content}
    except Exception as e:
        return {"error": str(e)}


@app.post("/file/write")
async def write_file(request: FileWriteRequest):
    """Ecrire un fichier sur M2"""
    p = Path(request.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(request.content, encoding=request.encoding)
    return {"path": request.path, "size": p.stat().st_size, "status": "written"}


@app.post("/file/list")
async def list_files(path: str = Body("C:/Users/Turbo", embed=True)):
    """Lister un repertoire sur M2"""
    p = Path(path)
    if not p.is_dir():
        raise HTTPException(404, f"Directory not found: {path}")
    items = []
    for item in sorted(p.iterdir()):
        items.append({
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else 0,
        })
    return {"path": path, "items": items, "count": len(items)}


@app.post("/file/delete")
async def delete_file(path: str = Body(..., embed=True)):
    """Supprimer un fichier/dossier sur M2"""
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, f"Not found: {path}")
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return {"path": path, "status": "deleted"}


# ============== PROCESS MANAGEMENT ==============

@app.post("/process")
async def process_control(request: ProcessRequest):
    """Gerer les processus sur M2"""
    import psutil

    if request.action == "list":
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = p.info
                if request.name and request.name.lower() not in info["name"].lower():
                    continue
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu": info["cpu_percent"],
                    "mem_mb": round(info["memory_info"].rss / 1e6, 1) if info["memory_info"] else 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return {"processes": procs[:100], "total": len(procs)}

    elif request.action == "kill":
        try:
            p = psutil.Process(request.pid)
            p.terminate()
            return {"pid": request.pid, "status": "terminated"}
        except Exception as e:
            return {"error": str(e)}

    elif request.action == "start":
        proc = subprocess.Popen(
            request.command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return {"pid": proc.pid, "command": request.command, "status": "started"}

    raise HTTPException(400, f"Unknown action: {request.action}")


# ============== LM STUDIO PROXY ==============

@app.get("/lm/models")
async def lm_models():
    """Lister les modeles LM Studio sur M2"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:1234/v1/models")
            return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/lm/status")
async def lm_status():
    """Status LM Studio"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:1234/v1/models")
            data = r.json()
            models = [m.get("id", "?") for m in data.get("data", [])]
            return {"status": "online", "models": models, "count": len(models)}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


@app.post("/lm/query")
async def lm_query(request: LMQueryRequest):
    """
    Query LM Studio sur M2 (ou autre noeud).
    M1 peut utiliser les modeles de M2 directement.
    """
    import httpx

    nodes = {
        "local": "http://127.0.0.1:1234",
        "M2": "http://127.0.0.1:1234",
        "M1": "http://192.168.1.85:1234",
        "M3": "http://192.168.1.113:1234",
    }
    base_url = nodes.get(request.node, "http://127.0.0.1:1234")

    payload = {
        "messages": [{"role": "user", "content": request.prompt}],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "stream": False,
    }
    if request.model:
        payload["model"] = request.model

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{base_url}/v1/chat/completions", json=payload)
            return r.json()
    except Exception as e:
        return {"error": str(e)}


# ============== SERVICES M2 ==============

@app.get("/services")
async def list_services():
    """Status de tous les services JARVIS sur M2"""
    return {"services": _services_status()}


def _services_status() -> dict:
    """Check all JARVIS services"""
    import httpx

    services = {}
    checks = {
        "lm_studio": ("http://127.0.0.1:1234/v1/models", 1234),
        "dashboard": ("http://127.0.0.1:8080/api/cluster", 8080),
        "mcp_sse": ("http://127.0.0.1:8901/mcp/", 8901),
        "fastapi_ws": ("http://127.0.0.1:9742/health", 9742),
        "canvas_proxy": ("http://127.0.0.1:18800/", 18800),
    }
    for name, (url, port) in checks.items():
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=2)
            services[name] = {"status": "online", "port": port}
        except Exception:
            services[name] = {"status": "offline", "port": port}
    return services


@app.post("/service")
async def service_control(request: ServiceRequest):
    """Demarrer/arreter un service JARVIS sur M2"""
    launchers = {
        "dashboard": "uv run python dashboard/server.py",
        "mcp_sse": "uv run python -m src.mcp_server_sse --port 8901",
        "fastapi": "uv run python -m src.fastapi_ws",
        "canvas": "node canvas/direct-proxy.js",
        "autonomous": "uv run python -m src.autonomous_loop",
    }
    if request.service not in launchers and request.action == "start":
        raise HTTPException(400, f"Unknown service: {request.service}")

    if request.action == "start":
        cmd = launchers[request.service]
        proc = subprocess.Popen(
            cmd, shell=True, cwd=str(TURBO_ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return {"service": request.service, "pid": proc.pid, "status": "started"}

    elif request.action == "stop":
        # Kill by name pattern
        r = subprocess.run(
            ["powershell", "-Command",
             f"Get-Process | Where-Object {{$_.CommandLine -like '*{request.service}*'}} | Stop-Process -Force"],
            capture_output=True, text=True,
        )
        return {"service": request.service, "status": "stopped"}

    elif request.action == "status":
        return {"services": _services_status()}

    raise HTTPException(400, f"Unknown action: {request.action}")


# ============== TASK MANAGEMENT ==============

@app.post("/task")
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Creer et executer une tache JARVIS — appele par M1"""
    logger.info(f"Task from {request.source}: {request.description}")

    if HAS_ORCHESTRATOR:
        async def run_task():
            result = await orchestrator.process_task(
                description=request.description,
                source=request.source,
            )
            if "M1" in active_connections:
                await active_connections["M1"].send_json({
                    "type": "task_complete", "result": result,
                })
            return result

        background_tasks.add_task(run_task)

    return {
        "status": "accepted",
        "message": "Task queued for execution",
        "source": request.source,
        "node": NODE_ID,
    }


@app.get("/tasks")
async def list_tasks():
    if HAS_ORCHESTRATOR:
        return {
            "tasks": [t.to_dict() for t in orchestrator.tasks.values()],
            "total": len(orchestrator.tasks),
        }
    return {"tasks": [], "total": 0}


# ============== CLUSTER MANAGEMENT ==============

@app.get("/cluster")
async def get_cluster_info():
    result = {
        "master": "M1",
        "this_node": NODE_ID,
        "this_ip": NODE_IP,
        "connected_ws": list(active_connections.keys()),
    }
    if HAS_ORCHESTRATOR:
        result["nodes"] = {nid: n.to_dict() for nid, n in orchestrator.cluster_nodes.items()}
        result["total_nodes"] = len(orchestrator.cluster_nodes)
    return result


@app.post("/cluster/register")
async def register_node(node: NodeRegistration):
    if not HAS_ORCHESTRATOR:
        return {"status": "no orchestrator", "node": node.node_id}
    cluster_node = ClusterNode(
        node_id=node.node_id, hostname=node.hostname,
        ip=node.ip, port=node.port,
        role=NodeRole(node.role), capabilities=node.capabilities,
    )
    orchestrator.register_node(cluster_node)
    await broadcast({"type": "node_registered", "node": cluster_node.to_dict()})
    return {"status": "registered", "node": cluster_node.to_dict()}


@app.post("/cluster/heartbeat")
async def heartbeat(node_id: str = Body(..., embed=True)):
    if HAS_ORCHESTRATOR and node_id in orchestrator.cluster_nodes:
        orchestrator.cluster_nodes[node_id].last_heartbeat = datetime.now()
        orchestrator.cluster_nodes[node_id].status = "online"
    return {"status": "ok", "node": node_id, "timestamp": datetime.now().isoformat()}


# ============== COMMAND EXECUTION ==============

@app.post("/command")
async def execute_command(request: CommandRequest):
    """Executer une commande JARVIS sur M2"""
    command = request.command
    params = request.params
    logger.info(f"Command: {command} params={params}")

    commands = {
        "scan_mexc": lambda: {"action": "scan_mexc", "status": "triggered"},
        "get_positions": lambda: {"action": "get_positions", "status": "triggered"},
        "consensus": lambda: {"action": "multi_ia_consensus", "status": "triggered"},
        "status": lambda: {"node": NODE_ID, "services": _services_status()},
        "gpu": lambda: {"gpu": _gpu_info()},
        "restart": lambda: {"action": "restart", "status": "scheduled"},
        "stop": lambda: {"action": "stop", "status": "scheduled"},
        "list_models": lambda: _sync_lm_models(),
    }

    if command in commands:
        result = commands[command]()
        return {"command": command, "result": result, "node": NODE_ID}

    raise HTTPException(400, f"Unknown command: {command}")


def _sync_lm_models():
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=3) as r:
            data = json.loads(r.read())
            return {"models": [m.get("id") for m in data.get("data", [])]}
    except Exception as e:
        return {"error": str(e)}


# ============== MCP TOOLS PROXY ==============

@app.post("/mcp/{tool_name}")
async def call_mcp_tool(tool_name: str, params: dict = Body(default={})):
    """Proxy MCP tools — M1 utilise les outils MCP de M2"""
    logger.info(f"MCP: {tool_name}")

    mcp_tools = {
        "scan_mexc": "mcp__trading-ai-ultimate__scan_mexc",
        "get_positions": "mcp__trading-ai-ultimate__get_mexc_positions",
        "check_margins": "mcp__trading-ai-ultimate__check_critical_margins",
        "consensus": "mcp__trading-ai-ultimate__parallel_consensus",
        "send_telegram": "mcp__trading-ai-ultimate__send_telegram",
        "ohlcv": "mcp__trading-ai-ultimate__get_ohlcv_ccxt",
    }

    if tool_name in mcp_tools:
        return {
            "tool": tool_name,
            "mcp_tool": mcp_tools[tool_name],
            "params": params,
            "status": "executed",
            "node": NODE_ID,
        }

    raise HTTPException(404, f"MCP tool not found: {tool_name}")


# ============== WEBSOCKET (FULL CONTROL) ==============

@app.websocket("/ws/{node_id}")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    """WebSocket temps reel — M1 controle M2"""
    await websocket.accept()
    active_connections[node_id] = websocket
    logger.info(f"WS connected: {node_id}")

    await websocket.send_json({
        "type": "connected",
        "node": NODE_ID,
        "ip": NODE_IP,
        "full_control": True,
        "timestamp": datetime.now().isoformat(),
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })

            elif msg_type == "task":
                if HAS_ORCHESTRATOR:
                    result = await orchestrator.process_task(
                        description=data.get("description", ""),
                        source=node_id,
                    )
                else:
                    result = {"status": "no orchestrator"}
                await websocket.send_json({"type": "task_result", "result": result})

            elif msg_type == "shell":
                # Execute shell command via WS
                cmd = data.get("command", "")
                shell = data.get("shell", "powershell")
                try:
                    if shell == "powershell":
                        proc_cmd = ["powershell", "-NoProfile", "-Command", cmd]
                    else:
                        proc_cmd = ["bash", "-c", cmd]
                    r = subprocess.run(
                        proc_cmd, capture_output=True, text=True, timeout=60,
                    )
                    await websocket.send_json({
                        "type": "shell_result",
                        "stdout": r.stdout,
                        "stderr": r.stderr,
                        "returncode": r.returncode,
                    })
                except Exception as e:
                    await websocket.send_json({"type": "shell_error", "error": str(e)})

            elif msg_type == "command":
                command = data.get("command", "")
                await websocket.send_json({
                    "type": "command_result",
                    "command": command,
                    "result": "executed",
                    "node": NODE_ID,
                })

            elif msg_type == "status":
                import psutil
                mem = psutil.virtual_memory()
                await websocket.send_json({
                    "type": "status",
                    "node": NODE_ID,
                    "cpu_pct": psutil.cpu_percent(),
                    "ram_pct": mem.percent,
                    "gpu": _gpu_info(),
                    "services": _services_status(),
                    "timestamp": datetime.now().isoformat(),
                })

            elif msg_type == "broadcast":
                await broadcast(data.get("message", {}), exclude=node_id)

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {node_id}")
        if node_id in active_connections:
            del active_connections[node_id]


async def broadcast(message: dict, exclude: str = None):
    for node_id, ws in list(active_connections.items()):
        if node_id != exclude:
            try:
                await ws.send_json(message)
            except Exception:
                pass


# ============== STARTUP/SHUTDOWN ==============

_start_time = time.time()


@app.on_event("startup")
async def startup():
    if HAS_ORCHESTRATOR:
        await orchestrator.start()
    logger.info(f"JARVIS Cluster API started on {NODE_ID} ({NODE_IP}:8765) — FULL CONTROL ENABLED")


@app.on_event("shutdown")
async def shutdown():
    if HAS_ORCHESTRATOR:
        await orchestrator.stop()
    logger.info(f"JARVIS Cluster API stopped on {NODE_ID}")


# ============== MAIN ==============

def run_api(host: str = "0.0.0.0", port: int = 8765):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api()
