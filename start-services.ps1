# HireLens Startup Script
# This script starts both the frontend and backend services

# Function to check if a command exists
function Test-Command {
    param($Command)
    try { Get-Command $Command -ErrorAction Stop; return $true }
    catch { return $false }
}

# Function to check if a port is in use (service running)
function Test-Port {
    param($Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    }
    catch { return $false }
}

# Get the script's directory (where start-services.ps1 is located)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       HireLens Startup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
if (-not (Test-Command python)) {
    Write-Host "ERROR: Python is not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.x from https://www.python.org/downloads/"
    exit 1
}

# Check if Node.js is installed
if (-not (Test-Command node)) {
    Write-Host "ERROR: Node.js is not installed." -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/"
    exit 1
}

Write-Host "[OK] Python found: $(python --version)" -ForegroundColor Green
Write-Host "[OK] Node.js found: $(node --version)" -ForegroundColor Green
Write-Host ""

# Check MongoDB status
Write-Host "Checking MongoDB status..." -ForegroundColor Yellow
$mongoRunning = Test-Port 27017

if (-not $mongoRunning) {
    Write-Host ""
    Write-Host "WARNING: MongoDB is not running on localhost:27017" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options to fix this:" -ForegroundColor Cyan
    Write-Host "  1. Start MongoDB locally:"
    Write-Host "     - If installed as a service: " -NoNewline
    Write-Host "net start MongoDB" -ForegroundColor White
    Write-Host "     - Or run: " -NoNewline
    Write-Host "mongod" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. Use MongoDB Atlas (cloud database):"
    Write-Host "     - Create a .env file in hirelens-backend/ with:"
    Write-Host "       MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/"
    Write-Host ""
    Write-Host "  3. Install MongoDB:"
    Write-Host "     - Download from: https://www.mongodb.com/try/download/community"
    Write-Host ""
    
    $response = Read-Host "Do you want to continue anyway? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Exiting. Please start MongoDB first." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "[OK] MongoDB is running on localhost:27017" -ForegroundColor Green
    Write-Host ""
}

# Backend setup
Write-Host "Setting up backend..." -ForegroundColor Cyan
Push-Location hirelens-backend

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "  Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment and install dependencies
Write-Host "  Installing Python dependencies (this may take a moment)..."
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Deactivate virtual environment
deactivate
Pop-Location

Write-Host "[OK] Backend setup complete" -ForegroundColor Green
Write-Host ""

# Frontend setup
Write-Host "Setting up frontend..." -ForegroundColor Cyan
Push-Location hirelens-frontend

# Install Node.js dependencies if node_modules doesn't exist or package.json changed
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing Node.js dependencies (this may take a moment)..."
    npm install --silent
} else {
    Write-Host "  Node modules already installed, skipping npm install"
}

Pop-Location
Write-Host "[OK] Frontend setup complete" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "         Starting Services" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Start backend service with Python virtual environment
Write-Host "Starting backend server..." -ForegroundColor Yellow
$backendPath = Join-Path $ScriptDir "hirelens-backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; .\venv\Scripts\Activate.ps1; Write-Host 'Backend server starting...' -ForegroundColor Green; python run.py"

# Give backend a moment to start
Start-Sleep -Seconds 2

# Start frontend service
Write-Host "Starting frontend server..." -ForegroundColor Yellow
$frontendPath = Join-Path $ScriptDir "hirelens-frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; Write-Host 'Frontend server starting...' -ForegroundColor Green; npm start"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "         Services Started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Two new PowerShell windows have been opened."
Write-Host "Close those windows to stop the services."
Write-Host ""
