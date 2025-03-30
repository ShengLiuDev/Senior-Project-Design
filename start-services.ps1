# Function to check if a command exists
function Test-Command {
    param($Command)
    try { Get-Command $Command -ErrorAction Stop; return $true }
    catch { return $false }
}

# Check if Python is installed
if (-not (Test-Command python)) {
    Write-Host "Python is not installed. Please install Python 3.x from https://www.python.org/downloads/"
    exit 1
}

# Check if Node.js is installed
if (-not (Test-Command node)) {
    Write-Host "Node.js is not installed. Please install Node.js from https://nodejs.org/"
    exit 1
}

Write-Host "Setting up HireLens environment..."

# Backend setup
Write-Host "`nSetting up backend..."
cd hirelens-backend

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..."
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Deactivate virtual environment
deactivate

# Frontend setup
Write-Host "`nSetting up frontend..."
cd ..\hirelens-frontend

# Install Node.js dependencies
Write-Host "Installing Node.js dependencies..."
npm install

cd ..

Write-Host "`nSetup complete! Starting services..."

# Start backend service with Python virtual environment
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd hirelens-backend; .\venv\Scripts\Activate.ps1; python run.py"

# Start frontend service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd hirelens-frontend; npm start"

Write-Host "`nServices started! Check the new windows for the running applications."
Write-Host "Backend should be running on http://localhost:5000"
Write-Host "Frontend should be running on http://localhost:3000" 