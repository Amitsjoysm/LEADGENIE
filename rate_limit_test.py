#!/usr/bin/env python3
"""
Focused Rate Limiting Test for LeadGen Pro
Tests rate limiting on specific endpoints with detailed debugging
"""

import requests
import time
import json

def test_rate_limiting():
    """Test rate limiting with detailed debugging"""
    base_url = "https://domain-relation.preview.emergentagent.com/api"
    
    print("🔍 Testing Rate Limiting on Auth Endpoints")
    print("=" * 60)
    
    # Test data
    invalid_creds = {"email": "test@test.com", "password": "wrong"}
    register_data = {
        "email": "ratetest@example.com",
        "password": "testpass123",
        "full_name": "Rate Test User",
        "company": "Test Company"
    }
    forgot_data = {"email": "test@example.com"}
    
    # Test 1: Login Rate Limiting (10/minute)
    print("\n1. Testing Login Rate Limiting (10/minute limit)")
    print("-" * 40)
    
    login_responses = []
    for i in range(15):  # Exceed the 10/minute limit
        try:
            response = requests.post(f"{base_url}/auth/login", json=invalid_creds, timeout=5)
            login_responses.append({
                "request": i+1,
                "status": response.status_code,
                "headers": dict(response.headers),
                "response": response.text[:200] if response.text else ""
            })
            
            print(f"Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ Rate limit hit at request {i+1}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                break
                
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
            
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    # Check if rate limiting worked
    rate_limited = any(r["status"] == 429 for r in login_responses)
    if rate_limited:
        print("✅ Login rate limiting is working")
    else:
        print("❌ Login rate limiting is NOT working")
        print("All responses:")
        for r in login_responses:
            print(f"  Request {r['request']}: {r['status']} - {r['response'][:50]}")
    
    # Wait a bit before next test
    print("\nWaiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 2: Register Rate Limiting (5/minute)
    print("\n2. Testing Register Rate Limiting (5/minute limit)")
    print("-" * 40)
    
    register_responses = []
    for i in range(8):  # Exceed the 5/minute limit
        try:
            # Use unique email for each attempt
            test_data = register_data.copy()
            test_data["email"] = f"ratetest{i}@example.com"
            
            response = requests.post(f"{base_url}/auth/register", json=test_data, timeout=5)
            register_responses.append({
                "request": i+1,
                "status": response.status_code,
                "headers": dict(response.headers),
                "response": response.text[:200] if response.text else ""
            })
            
            print(f"Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ Rate limit hit at request {i+1}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                break
                
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
            
        time.sleep(0.1)
    
    # Check if rate limiting worked
    rate_limited = any(r["status"] == 429 for r in register_responses)
    if rate_limited:
        print("✅ Register rate limiting is working")
    else:
        print("❌ Register rate limiting is NOT working")
        print("All responses:")
        for r in register_responses:
            print(f"  Request {r['request']}: {r['status']} - {r['response'][:50]}")
    
    # Wait a bit before next test
    print("\nWaiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 3: Forgot Password Rate Limiting (3/minute)
    print("\n3. Testing Forgot Password Rate Limiting (3/minute limit)")
    print("-" * 40)
    
    forgot_responses = []
    for i in range(6):  # Exceed the 3/minute limit
        try:
            response = requests.post(f"{base_url}/auth/forgot-password", json=forgot_data, timeout=5)
            forgot_responses.append({
                "request": i+1,
                "status": response.status_code,
                "headers": dict(response.headers),
                "response": response.text[:200] if response.text else ""
            })
            
            print(f"Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ Rate limit hit at request {i+1}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                break
                
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
            
        time.sleep(0.1)
    
    # Check if rate limiting worked
    rate_limited = any(r["status"] == 429 for r in forgot_responses)
    if rate_limited:
        print("✅ Forgot Password rate limiting is working")
    else:
        print("❌ Forgot Password rate limiting is NOT working")
        print("All responses:")
        for r in forgot_responses:
            print(f"  Request {r['request']}: {r['status']} - {r['response'][:50]}")
    
    print("\n" + "=" * 60)
    print("Rate Limiting Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_rate_limiting()