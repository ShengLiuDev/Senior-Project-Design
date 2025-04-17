#!/bin/bash

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "$1 is not installed. Please install $1"
        exit 1
    fi
}

# Check if Python is installed
check_command python3

# Check if Node.js is installed
check_command node

echo "Setting up HireLens environment..."

# Backend setup
echo -e "\nSetting up backend..."
cd hirelens-backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Deactivate virtual environment
deactivate

# Frontend setup
echo -e "\nSetting up frontend..."
cd ../hirelens-frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo -e "\nSetup complete! Starting services..."

# Start backend service with Python virtual environment
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"'/hirelens-backend && source venv/bin/activate && python3 run.py"'

# Start frontend service
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"'/hirelens-frontend && npm start"'

echo -e "\nServices started! Check the new Terminal windows for the running applications."
echo "Backend should be running on http://localhost:5000"
echo "Frontend should be running on http://localhost:3000" 