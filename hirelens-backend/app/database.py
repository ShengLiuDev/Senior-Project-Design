from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment variable or use default
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['hirelens']

# Collections
interviews = db['interviews']

# Create indexes
interviews.create_index([("userId", 1)])
interviews.create_index([("date", -1)])

def test_connection():
    try:
        # The ismaster command is cheap and does not require auth
        client.admin.command('ismaster')
        print("MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False