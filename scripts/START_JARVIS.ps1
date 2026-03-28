# JARVIS CLUSTER STARTUP - PowerShell
# Node M2 - Full Control Startup

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "JARVIS CLUSTER - M2"

$NODE_ID = "M2"
$NODE_IP = "192.168.1.26"
$MASTER_IP = "192.168.1.85"

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "       JARVIS CLUSTER - NODE $NODE_ID" -ForegroundColor Yellow
Write-Host "       Trading AI Ultimate System" -ForegroundColor Yellow
Write-Host "       FULL CONTROL FROM M1 ENABLED" -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

$JARVIS_ROOT = "C:\Users\Turbo\JARVIS-CLUSTER"
Set-Location $JARVIS_ROOT

# Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Green
try {
    $pythonVersion = python --version
    Write-Host "       $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Green
pip install fastapi uvicorn websockets httpx pydantic psutil --quiet 2>$null

# Start API Server
Write-Host "[3/5] Starting JARVIS API Server..." -ForegroundColor Green
$apiProcess = Start-Process -FilePath "python" -ArgumentList "api\cluster_api.py" -WorkingDirectory $JARVIS_ROOT -PassThru -WindowStyle Minimized
Write-Host "       API Server PID: $($apiProcess.Id)" -ForegroundColor Gray

Start-Sleep -Seconds 2

# Start Monitor
Write-Host "[4/5] Starting Cluster Monitor..." -ForegroundColor Green
$monitorProcess = Start-Process -FilePath "python" -ArgumentList "monitoring\cluster_monitor.py" -WorkingDirectory $JARVIS_ROOT -PassThru -WindowStyle Minimized
Write-Host "       Monitor PID: $($monitorProcess.Id)" -ForegroundColor Gray

# Register with M1 (if available)
Write-Host "[5/5] Registering with M1 master..." -ForegroundColor Green
try {
    $registration = @{
        node_id = $NODE_ID
        hostname = $env:COMPUTERNAME
        ip = $NODE_IP
        port = 8765
        role = "worker"
        capabilities = @("trading", "mcp", "lm-studio", "n8n", "telegram", "mexc", "multi-ia", "gpu", "shell", "file-access", "process-mgmt")
    } | ConvertTo-Json

    Write-Host "       Registration queued (M1 will discover on connect)" -ForegroundColor Gray
} catch {
    Write-Host "       M1 not available, will register on connection" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "       JARVIS $NODE_ID STARTED! (FULL CONTROL)" -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services Running:" -ForegroundColor White
Write-Host "    - API Server:  http://${NODE_IP}:8765" -ForegroundColor Gray
Write-Host "    - WebSocket:   ws://${NODE_IP}:8765/ws/M1" -ForegroundColor Gray
Write-Host "    - Health:      http://${NODE_IP}:8765/health" -ForegroundColor Gray
Write-Host ""
Write-Host "  Full Control Endpoints (from M1):" -ForegroundColor White
Write-Host "    - GET  /status        - Node status + GPU + RAM" -ForegroundColor Gray
Write-Host "    - POST /shell         - Execute any command" -ForegroundColor Gray
Write-Host "    - POST /file/read     - Read any file" -ForegroundColor Gray
Write-Host "    - POST /file/write    - Write any file" -ForegroundColor Gray
Write-Host "    - POST /process       - List/kill/start processes" -ForegroundColor Gray
Write-Host "    - GET  /gpu           - GPU stats" -ForegroundColor Gray
Write-Host "    - POST /lm/query      - Query LM Studio" -ForegroundColor Gray
Write-Host "    - GET  /lm/models     - List loaded models" -ForegroundColor Gray
Write-Host "    - POST /task          - Send JARVIS task" -ForegroundColor Gray
Write-Host "    - POST /command       - JARVIS command" -ForegroundColor Gray
Write-Host "    - POST /mcp/{tool}    - Call MCP tool" -ForegroundColor Gray
Write-Host "    - POST /service       - Start/stop services" -ForegroundColor Gray
Write-Host ""
Write-Host "  Process IDs:" -ForegroundColor White
Write-Host "    - API: $($apiProcess.Id)  Monitor: $($monitorProcess.Id)" -ForegroundColor Gray
Write-Host ""

# Keep script running
Write-Host "Press Ctrl+C to stop JARVIS..." -ForegroundColor Yellow
try {
    while ($true) {
        Start-Sleep -Seconds 60

        # Health check — auto-restart API if crashed
        if ($apiProcess.HasExited) {
            Write-Host "WARNING: API Server stopped! Restarting..." -ForegroundColor Red
            $apiProcess = Start-Process -FilePath "python" -ArgumentList "api\cluster_api.py" -WorkingDirectory $JARVIS_ROOT -PassThru -WindowStyle Minimized
        }
    }
} finally {
    Write-Host "Stopping JARVIS services..." -ForegroundColor Yellow
    Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "JARVIS stopped." -ForegroundColor Red
}
