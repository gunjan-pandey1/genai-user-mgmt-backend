import sys
try:
    from app.models import UserCreate, UserResponse
    from bson import ObjectId
    print("Imports successful")
    
    # Test UserCreate
    user_data = {"name": "Test", "email": "test@example.com"}
    user = UserCreate(**user_data)
    print("UserCreate successful")
    
    # Test UserResponse with ObjectId
    db_data = {"_id": ObjectId(), "name": "Test", "email": "test@example.com", "role": "user"}
    response = UserResponse(**db_data)
    print("UserResponse successful")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
