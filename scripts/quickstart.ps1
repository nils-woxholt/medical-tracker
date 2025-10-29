#!/usr/bin/env pwsh
# SaaS Medical Tracker - Quickstart Script (Windows PowerShell)
# This script sets up and runs the complete development environment

param(
    [switch]$SkipBrowser = $false,
    [switch]$Verbose = $false
)

if ($Verbose) {
    $VerbosePreference = "Continue"
}

Write-Host "🚀 SaaS Medical Tracker - Quickstart Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Get script directory and root directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir

# Function to test if a command exists
function Test-Command($command) {
    try {
        if (Get-Command $command -ErrorAction SilentlyContinue) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

# Function to get version of a command
function Get-CommandVersion($command, $versionArg = "--version") {
    try {
        $output = & $command $versionArg 2>&1
        return $output
    }
    catch {
        return $null
    }
}

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue

# Check uv first (uv manages Python for us)
if (-not (Test-Command "uv")) {
    Write-Host "❌ uv is not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Please install uv from https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
    Write-Host "   Quick install: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"" -ForegroundColor Yellow
    exit 1
}

$uvVersion = Get-CommandVersion "uv"
Write-Host "✅ uv: $uvVersion" -ForegroundColor Green

# Check Python (uv can install Python if needed)
if (-not (Test-Command "python")) {
    Write-Host "⚠️ Python not found in PATH, uv will manage Python" -ForegroundColor Yellow
}
else {
    $pythonVersion = Get-CommandVersion "python"
    Write-Verbose "Python version output: $pythonVersion"

    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -eq 3 -and $minor -ge 11) {
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
        }
        elseif ($major -gt 3) {
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ Python 3.11+ recommended, found: $pythonVersion" -ForegroundColor Yellow
            Write-Host "   uv will use appropriate Python version" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "⚠️ Could not determine Python version: $pythonVersion" -ForegroundColor Yellow
        Write-Host "   uv will manage Python version" -ForegroundColor Yellow
    }
}

# Check Node.js
if (-not (Test-Command "node")) {
    Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$nodeVersion = Get-CommandVersion "node"
Write-Verbose "Node.js version output: $nodeVersion"

if ($nodeVersion -match "v(\d+)\.(\d+)\.(\d+)") {
    $major = [int]$matches[1]
    
    if ($major -ge 18) {
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Node.js 18+ is required, found: $nodeVersion" -ForegroundColor Red
        Write-Host "   Please upgrade Node.js from https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }
}
else {
    Write-Host "⚠️ Could not determine Node.js version: $nodeVersion" -ForegroundColor Yellow
    Write-Host "   Proceeding anyway..." -ForegroundColor Yellow
}

# Check Git (optional but recommended)
if (Test-Command "git") {
    $gitVersion = Get-CommandVersion "git"
    Write-Host "✅ Git: $($gitVersion.Split([Environment]::NewLine)[0])" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Git not found - required for version control" -ForegroundColor Yellow
}

Write-Host ""

# Setup Backend
Write-Host "🐍 Setting up Backend Environment..." -ForegroundColor Blue
$backendDir = Join-Path $rootDir "backend"

if (-not (Test-Path $backendDir)) {
    Write-Host "❌ Backend directory not found: $backendDir" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir
Write-Verbose "Changed to backend directory: $backendDir"

# Initialize uv project and sync dependencies (creates .venv automatically)
Write-Host "📦 Syncing Python dependencies with uv..." -ForegroundColor Yellow
# Clear any existing VIRTUAL_ENV to avoid conflicts
$env:VIRTUAL_ENV = $null
uv sync --extra dev --extra test
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to sync dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backend dependencies synced (using .venv)" -ForegroundColor Green

# Run database migrations using uv run
Write-Host "🗄️ Setting up database..." -ForegroundColor Yellow
uv run alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to run database migrations" -ForegroundColor Red
    Write-Host "   This might be normal for a fresh installation" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Database migrations completed" -ForegroundColor Green
}

# Setup Frontend
Write-Host ""
Write-Host "🌐 Setting up Frontend Environment..." -ForegroundColor Blue
$frontendDir = Join-Path $rootDir "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

Set-Location $frontendDir
Write-Verbose "Changed to frontend directory: $frontendDir"

# Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green

# Generate TypeScript types from OpenAPI schema
$contractsDir = Join-Path $rootDir "contracts"
if (Test-Path (Join-Path $contractsDir "openapi.yaml")) {
    Write-Host "🔄 Generating TypeScript types from OpenAPI schema..." -ForegroundColor Yellow
    npm run generate-types
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ TypeScript types generated" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ Failed to generate TypeScript types - continuing anyway" -ForegroundColor Yellow
    }
}

# Start Development Servers
Write-Host ""
Write-Host "🚀 Starting Development Servers..." -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
Write-Host "  📱 Frontend:      http://localhost:3000" -ForegroundColor Cyan
Write-Host "  🔧 Backend API:   http://localhost:8000/api/v1" -ForegroundColor Cyan
Write-Host "  📚 API Docs:      http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host "  ❤️ Health Check:  http://localhost:8000/api/v1/health" -ForegroundColor Cyan
Write-Host ""

# Start backend server in background
Write-Host "🔧 Starting backend server..." -ForegroundColor Yellow
Set-Location $backendDir

$backendJob = Start-Job -ScriptBlock {
    param($backendPath)
    Set-Location $backendPath
    # Clear any conflicting environment variables
    $env:VIRTUAL_ENV = $null
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} -ArgumentList $backendDir

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Test backend health
try {
    Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Backend server is running" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Backend server may not be ready yet" -ForegroundColor Yellow
}

# Start frontend server in background
Write-Host "🌐 Starting frontend server..." -ForegroundColor Yellow
Set-Location $frontendDir

$frontendJob = Start-Job -ScriptBlock {
    param($frontendPath)
    Set-Location $frontendPath
    # Set environment variables for frontend
    $env:NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1"
    $env:NODE_ENV = "development"
    npm run dev
} -ArgumentList $frontendDir

# Wait for frontend to start
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🎉 Development Environment Ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Quick Start Guide:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "  2. Create a test account or log in" -ForegroundColor White
Write-Host "  3. Try adding a medication in 'Medication Management'" -ForegroundColor White
Write-Host "  4. Log your first dose in 'Daily Logging'" -ForegroundColor White
Write-Host "  5. Explore the Health Passport features" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Open browser if not skipped
if (-not $SkipBrowser) {
    Start-Sleep -Seconds 2
    try {
        Start-Process "http://localhost:3000"
        Write-Host "🌐 Opened application in default browser" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Could not open browser automatically" -ForegroundColor Yellow
        Write-Host "   Please navigate to http://localhost:3000 manually" -ForegroundColor Yellow
    }
}

# Monitor jobs and handle cleanup
try {
    while ($true) {
        Start-Sleep -Seconds 2
        
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed") {
            Write-Host "❌ Backend server failed" -ForegroundColor Red
            Receive-Job $backendJob -ErrorAction SilentlyContinue
            break
        }
        
        if ($frontendJob.State -eq "Failed") {
            Write-Host "❌ Frontend server failed" -ForegroundColor Red
            Receive-Job $frontendJob -ErrorAction SilentlyContinue
            break
        }
        
        # Optional: Check if servers are still responding
        # This is commented out to avoid too much network noise
        # try {
        #     Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing | Out-Null
        #     Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing | Out-Null
        # }
        # catch {
        #     Write-Host "⚠️ One or more servers may have stopped responding" -ForegroundColor Yellow
        # }
    }
}
catch {
    Write-Host ""
    Write-Host "🛑 Shutting down development servers..." -ForegroundColor Yellow
}
finally {
    # Cleanup jobs
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    
    if ($frontendJob) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes on our ports
    try {
        Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*node*" } | Where-Object { 
            $_.MainWindowTitle -like "*8000*" -or $_.MainWindowTitle -like "*3000*" 
        } | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    catch {
        # Ignore errors during cleanup
    }
    
    Set-Location $rootDir
    Write-Host "✅ Development environment stopped" -ForegroundColor Green
    Write-Host ""
    Write-Host "🙏 Thank you for trying SaaS Medical Tracker!" -ForegroundColor Green
}