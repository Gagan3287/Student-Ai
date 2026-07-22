"""
Scratch script to verify Phase 1 Auth logic.
Runs unit tests on user creation, password verification, and JWT issuance
using an in-memory SQLite database (avoiding pgvector/postgres requirement for tests).
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models.user import User
from app.services.auth_service import create_user, authenticate_user, create_access_token, decode_access_token

def test_auth_flow():
    print("Initializing in-memory database for testing...")
    engine = create_engine("sqlite:///:memory:")
    SessionClass = sessionmaker(bind=engine)
    
    # Create the users table (SQLite doesn't support vector or extensions,
    # but that's fine since we are only testing the User model)
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    db = SessionClass()
    
    print("Testing signup...")
    email = "test@university.edu"
    password = "supersecurepassword123"
    name = "Test Student"
    
    user = create_user(db, email, password, name)
    assert user.email == email
    assert user.full_name == name
    assert user.password_hash != password  # verify it's hashed
    print("[OK] User successfully created with hashed password.")
    
    print("Testing duplicate email protection...")
    try:
        create_user(db, email, "anotherpassword", "Duplicate User")
        assert False, "Should have raised duplicate email error"
    except ValueError as exc:
        print(f"[OK] Correctly rejected duplicate registration: '{exc}'")
        
    print("Testing login authentication (success case)...")
    auth_user = authenticate_user(db, email, password)
    assert auth_user is not None
    assert auth_user.id == user.id
    print("[OK] Login authentication succeeded.")
    
    print("Testing login authentication (failure cases)...")
    assert authenticate_user(db, email, "wrongpassword") is None
    assert authenticate_user(db, "nonexistent@university.edu", password) is None
    print("[OK] Login authentication correctly rejected invalid credentials.")
    
    print("Testing JWT token generation and decoding...")
    token, expires_in = create_access_token(str(user.id))
    assert token is not None
    assert expires_in > 0
    print(f"[OK] Token successfully generated. Expiry: {expires_in} seconds.")
    
    decoded_user_id = decode_access_token(token)
    assert decoded_user_id == str(user.id)
    print("[OK] Token successfully verified and decoded back to user ID.")
    
    print("\nALL PHASE 1 AUTH VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_flow()
