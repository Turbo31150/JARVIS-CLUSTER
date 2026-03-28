@echo off
title JARVIS CLUSTER - M2 NODE
color 0A

echo.
echo  ============================================
echo       JARVIS CLUSTER - NODE M2
echo       Trading AI Ultimate System
echo       FULL CONTROL FROM M1 ENABLED
echo  ============================================
echo.

cd /d C:\Users\Turbo\JARVIS-CLUSTER

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo [2/4] Installing dependencies...
pip install fastapi uvicorn websockets httpx pydantic psutil -q

echo.
echo [3/4] Starting JARVIS API Server...
start "JARVIS-API-M2" cmd /k "python api\cluster_api.py"

echo.
echo [4/4] Starting Cluster Monitor...
timeout /t 3 /nobreak > nul
start "JARVIS-Monitor-M2" cmd /k "python monitoring\cluster_monitor.py"

echo.
echo  ============================================
echo       JARVIS M2 STARTED! (FULL CONTROL)
echo  ============================================
echo.
echo  API Server:    http://192.168.1.26:8765
echo  WebSocket:     ws://192.168.1.26:8765/ws/M1
echo  Status:        http://192.168.1.26:8765/status
echo  Shell:         POST http://192.168.1.26:8765/shell
echo  GPU:           GET  http://192.168.1.26:8765/gpu
echo  Files:         POST http://192.168.1.26:8765/file/read
echo  LM Studio:     POST http://192.168.1.26:8765/lm/query
echo.
echo  M1 can now fully control this node.
echo.
echo  Press any key to open API status page...
pause > nul

start http://127.0.0.1:8765/status
