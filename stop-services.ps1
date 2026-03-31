#!/usr/bin/env pwsh
# AgentNex Service Stop Script
# Usage: .\stop-services.ps1

Write-Host "🛑 Stopping AgentNex services..." -ForegroundColor Red

# Stop Python processes (backend service)
$PythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($PythonProcesses) {
    Write-Host "⏹️  Stopping backend service (Python)..." -ForegroundColor Yellow
    Stop-Process -Name python -Force
    Write-Host "✅ Backend service stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No backend service processes found" -ForegroundColor Gray
}

# Stop Node.js processes (frontend service)
$NodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue
if ($NodeProcesses) {
    Write-Host "⏹️  Stopping frontend service (Node.js)..." -ForegroundColor Yellow
    Stop-Process -Name node -Force
    Write-Host "✅ Frontend service stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No frontend service processes found" -ForegroundColor Gray
}

Write-Host "`n✅ All services stopped!" -ForegroundColor Green