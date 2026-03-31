#!/usr/bin/env pwsh
# AgentNex Service Startup Script
# Usage: .\start-services.ps1

Write-Host "🚀 Starting AgentNex services..." -ForegroundColor Green

# Get project root directory
$ProjectRoot = "$PSScriptRoot"
$AgentDir = Join-Path $ProjectRoot "agent"

Write-Host "📁 Project root: $ProjectRoot" -ForegroundColor Cyan
Write-Host "📁 Agent directory: $AgentDir" -ForegroundColor Cyan

# Check if virtual environment exists
$VenvPath = Join-Path $AgentDir "agentnex_env"
if (!(Test-Path $VenvPath)) {
    Write-Host "❌ Virtual environment not found. Please run: python -m venv agentnex_env" -ForegroundColor Red
    exit 1
}

# Start backend service
Write-Host "`n🔄 Starting backend service..." -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; $AgentDir\agentnex_env\Scripts\python.exe -m agent.main"

# Wait a few seconds for backend to start
Start-Sleep -Seconds 3

# Start frontend service
Write-Host "`n🔄 Starting frontend service..." -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; pnpm dev"

Write-Host "`n✅ Services started successfully!" -ForegroundColor Green
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend App: http://localhost:5173" -ForegroundColor Cyan
Write-Host "`n💡 Tip: To stop services, close the corresponding PowerShell windows" -ForegroundColor Gray