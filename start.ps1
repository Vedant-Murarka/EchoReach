# EchoReach PowerShell Launch Script
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Starting EchoReach Backend Server (FastAPI)       " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
}

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
