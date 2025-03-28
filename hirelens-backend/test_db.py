from app.database import interviews, test_connection
from datetime import datetime

def test_crud():
    print("\n=== Testing MongoDB Connection ===")
    if not test_connection():
        print("❌ MongoDB connection failed!")
        return
    
    print("\n=== Testing CRUD Operations ===")
    
    # Create (Insert)
    test_interview = {
        "userId": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "date": datetime.utcnow(),
        "duration": 300,
        "scores": {
            "posture_score": 85.5,
            "smile_percentage": 60.2,
            "eye_contact_score": 75.0,
            "overall_score": 74.5,
            "total_frames": 300
        }
    }
    
    # Insert
    result = interviews.insert_one(test_interview)
    print(f"✅ Inserted document ID: {result.inserted_id}")
    
    # Read
    doc = interviews.find_one({"userId": "test_user_123"})
    print(f"✅ Found document: {doc}")
    
    # Update
    update_result = interviews.update_one(
        {"userId": "test_user_123"},
        {"$set": {"scores.overall_score": 80.0}}
    )
    print(f"✅ Updated document: {update_result.modified_count} modified")
    
    # Delete
    delete_result = interviews.delete_one({"userId": "test_user_123"})
    print(f"✅ Deleted document: {delete_result.deleted_count} deleted")
    
    print("\n=== All tests completed successfully! ===")

if __name__ == "__main__":
    test_crud() 