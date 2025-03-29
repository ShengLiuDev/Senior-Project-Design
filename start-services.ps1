# Start both frontend and backend services
Write-Host "Starting HireLens services..."

# Start backend service with Python virtual environment
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd hirelens-backend; .\venv\Scripts\Activate.ps1; python run.py"

# Start frontend service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd hirelens-frontend; npm start"

Write-Host "Services started! Check the new windows for the running applications."
Write-Host "Backend should be running on http://localhost:5000"
Write-Host "Frontend should be running on http://localhost:3000" 