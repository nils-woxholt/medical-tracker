# Run full development environment
# Usage: ./scripts/run-dev.ps1

Write-Host "🚀 Starting SaaS Medical Tracker Development Environment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*Python 3.11*" -or $pythonVersion -like "*Python 3.12*") {
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Unsupported Python version: $pythonVersion"
    }
} catch {
    Write-Host "❌ Python 3.11+ is required but not found" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -like "v18.*" -or $nodeVersion -like "v19.*" -or $nodeVersion -like "v20.*") {
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Unsupported Node.js version: $nodeVersion"
    }
} catch {
    Write-Host "❌ Node.js 18+ is required but not found" -ForegroundColor Red
    exit 1
}

# Setup backend
Write-Host "🐍 Setting up backend..." -ForegroundColor Blue
$backendDir = Join-Path $rootDir "backend"
Set-Location $backendDir

# Check if virtual environment exists
if (!(Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment and install dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\activate.ps1"
pip install -e ".[dev]"

# Run database migrations
Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

# Setup frontend  
Write-Host "🌐 Setting up frontend..." -ForegroundColor Blue
$frontendDir = Join-Path $rootDir "frontend"
Set-Location $frontendDir

# Install frontend dependencies
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "📦 Updating frontend dependencies..." -ForegroundColor Yellow
    npm install
}

# Start services
Write-Host "🚀 Starting development servers..." -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Service URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Create jobs for concurrent execution
$backendJob = Start-Job -ScriptBlock {
    param($backendPath)
    Set-Location $backendPath
    & ".\venv\Scripts\activate.ps1"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} -ArgumentList $backendDir

$frontendJob = Start-Job -ScriptBlock {
    param($frontendPath)
    Set-Location $frontendPath
    npm run dev
} -ArgumentList $frontendDir

Write-Host "🎯 Development servers started!" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Monitor jobs and handle cleanup
try {
    # Wait for user interrupt
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed") {
            Write-Host "❌ Backend server failed" -ForegroundColor Red
            Receive-Job $backendJob
            break
        }
        
        if ($frontendJob.State -eq "Failed") {
            Write-Host "❌ Frontend server failed" -ForegroundColor Red
            Receive-Job $frontendJob
            break
        }
    }
} catch {
    Write-Host ""
    Write-Host "🛑 Shutting down development servers..." -ForegroundColor Yellow
} finally {
    # Cleanup jobs
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    
    Write-Host "✅ Development environment stopped" -ForegroundColor Green
}