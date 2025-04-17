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
    app.run(debug=True)

if __name__ == '__main__':
    main()
