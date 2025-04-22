#!/bin/bash

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "$1 is not installed. Please install $1"
        exit 1
    fi
}

# Check if required commands are installed
check_command python3
check_command node
check_command mongod

echo "Setting up HireLens environment..."

# Kill any existing processes on ports 3000 and 5000
echo "Checking for existing processes..."
if lsof -ti:3000 > /dev/null; then
    echo "Killing process on port 3000..."
    lsof -ti:3000 | xargs kill -9
fi

if lsof -ti:5000 > /dev/null; then
    echo "Killing process on port 5000..."
    lsof -ti:5000 | xargs kill -9
fi

# Start MongoDB if not running
if ! pgrep -x "mongod" > /dev/null; then
    echo "Starting MongoDB..."
    mongod --config /usr/local/etc/mongod.conf &
    sleep 5  # Give MongoDB time to start
fi

# Verify MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "Error: MongoDB failed to start. Please start it manually."
    echo "Try: brew services start mongodb-community"
    exit 1
fi

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
# Install missing dependencies for sentiment analysis
pip install transformers torch accelerate

# Frontend setup
echo -e "\nSetting up frontend..."
cd ../hirelens-frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo -e "\nSetup complete! Starting services..."

# Start backend in a new terminal window
echo "Starting backend server..."
osascript <<END
tell application "Terminal"
    do script "cd $(pwd)/hirelens-backend && source venv/bin/activate && python3 run.py"
end tell
END

# Wait a moment for backend to start
sleep 3

# Verify backend is starting
echo "Verifying backend is starting..."
for i in {1..10}; do
    if curl -s http://localhost:5000 > /dev/null; then
        echo "✅ Backend is running"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️ Warning: Could not verify backend started. Check terminal window."
    else
        echo "Waiting for backend to start... ($i/10)"
        sleep 2
    fi
done

# Start frontend in a new terminal window
echo "Starting frontend server..."
osascript <<END
tell application "Terminal"
    do script "cd $(pwd)/hirelens-frontend && npm start"
end tell
END

echo -e "\nServices started!"
echo "Backend running on http://localhost:5000"
echo "Frontend running on http://localhost:3000"