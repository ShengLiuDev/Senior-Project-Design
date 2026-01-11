from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment variable or use default
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# MongoDB Atlas connection settings
# - serverSelectionTimeoutMS: How long to wait for server selection
# - connectTimeoutMS: How long to wait for initial connection
# - retryWrites: Enable retryable writes (recommended for Atlas)
client = None
db = None
interviews = None

def get_client():
    """Get or create MongoDB client with proper Atlas settings"""
    global client
    if client is None:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            connectTimeoutMS=10000,
            retryWrites=True,
            w='majority'
        )
    return client

def get_db():
    """Get the database instance"""
    global db
    if db is None:
        db = get_client()['hirelens']
    return db

def get_interviews_collection():
    """Get the interviews collection"""
    global interviews
    if interviews is None:
        interviews = get_db()['interviews']
    return interviews

def init_indexes():
    """Initialize database indexes - call this after connection is verified"""
    try:
        collection = get_interviews_collection()
        collection.create_index([("userId", 1)])
        collection.create_index([("date", -1)])
        print("Database indexes created successfully")
        return True
    except Exception as e:
        print(f"Warning: Could not create indexes: {e}")
        return False

def test_connection():
    """Test MongoDB connection"""
    try:
        # The ping command is lightweight and works with Atlas
        get_client().admin.command('ping')
        print("MongoDB connection successful!")
        return True
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"MongoDB server selection timeout: {e}")
        print("Check your MONGODB_URI in .env file and network/firewall settings")
        return False
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return False