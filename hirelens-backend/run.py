import subprocess
import time
import os
from app import create_app
from app.database import test_connection

def check_mongodb_connection():
    """Check if MongoDB is running and accessible"""
    max_retries = 5
    retry_delay = 2  # seconds
    
    for i in range(max_retries):
        if test_connection():
            print("✅ MongoDB connection successful")
            return True
        print(f"⏳ Waiting for MongoDB to be ready... (attempt {i+1}/{max_retries})")
        time.sleep(retry_delay)
    
    print("❌ Failed to connect to MongoDB after multiple attempts")
    return False

def main():
    print("\n=== Starting HireLens Backend ===")
    print("\nPlease ensure MongoDB is running:")
    print("1. Open MongoDB Compass")
    print("2. Or run 'net start MongoDB' in an Administrator PowerShell")
    print("3. Or start MongoDB service from Windows Services\n")
    
    # Wait for MongoDB to be ready
    if not check_mongodb_connection():
        print("\n❌ MongoDB is not accessible")
        print("Please start MongoDB manually and try again")
        return
    
    # Create and run Flask app
    app = create_app()
    print("\n=== Starting Flask Server ===")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"\n❌ Error starting Flask server: {str(e)}")
        print("Please check if port 5000 is already in use")
        print("You can try running: lsof -i :5000 to check what's using the port")

if __name__ == '__main__':
    main()
