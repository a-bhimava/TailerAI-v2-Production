#!/usr/bin/env python3
"""
Test script for authentication system.
Tests registration, login, and protected endpoints.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v2"

def test_registration():
    """Test user registration."""
    print("🔐 Testing User Registration...")
    
    registration_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_login():
    """Test user login."""
    print("\n🔑 Testing User Login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            return data.get("access_token")
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_protected_endpoint(access_token):
    """Test protected endpoint access."""
    print("\n🛡️ Testing Protected Endpoint...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful!")
            return True
        else:
            print("❌ Protected endpoint access failed!")
            return False
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False

def test_master_dataset_endpoint(access_token):
    """Test master dataset endpoint access."""
    print("\n📊 Testing Master Dataset Endpoint...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/master-dataset/profile",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Master dataset endpoint access successful!")
            return True
        else:
            print("❌ Master dataset endpoint access failed!")
            return False
            
    except Exception as e:
        print(f"❌ Master dataset endpoint error: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("🧪 TailerAI v2.0 Authentication System Test")
    print("=" * 50)
    
    # Test 1: Registration
    if not test_registration():
        print("\n❌ Registration test failed. Stopping tests.")
        return
    
    # Small delay to ensure user is created
    time.sleep(1)
    
    # Test 2: Login
    access_token = test_login()
    if not access_token:
        print("\n❌ Login test failed. Stopping tests.")
        return
    
    # Test 3: Protected endpoint
    if not test_protected_endpoint(access_token):
        print("\n❌ Protected endpoint test failed.")
    
    # Test 4: Master dataset endpoint
    if not test_master_dataset_endpoint(access_token):
        print("\n❌ Master dataset endpoint test failed.")
    
    print("\n🎉 Authentication system tests completed!")

if __name__ == "__main__":
    main()