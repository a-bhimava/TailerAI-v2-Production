#!/usr/bin/env python3
"""
Debug script to test user registration directly without API.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.auth_service import auth_service
from app.services.database_service import initialize_database

async def test_direct_registration():
    """Test user registration directly through service."""
    print("🔧 Debug: Testing direct user registration...")
    
    try:
        # Initialize database
        initialize_database()
        
        # Test registration
        user = await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            full_name="Test User"
        )
        
        print(f"✅ User created successfully:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Verified: {user.is_verified}")
        
        return user
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    await test_direct_registration()

if __name__ == "__main__":
    asyncio.run(main())