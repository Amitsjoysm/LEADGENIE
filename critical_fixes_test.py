#!/usr/bin/env python3
"""
Critical Fixes Test for LeadGen Pro
Tests the 3 specific fixes mentioned in the review request:
1. Credit-based Contact Reveal (atomic credit deduction)
2. Rate Limiting (fixed with fastapi-limiter)
3. Bulk Upload with Celery (Redis working)
"""

import requests
import json
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

class CriticalFixesTester:
    def __init__(self):
        self.base_url = "https://domain-relation.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        
        # Test credentials
        self.admin_creds = {
            "email": "admin@leadgen.com",
            "password": "admin123"
        }
        self.user_creds = {
            "email": "user1@example.com", 
            "password": "password123"
        }
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, files: Dict = None, params: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=data or params)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, headers=headers, data=data, files=files, params=params)
                else:
                    response = self.session.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            raise
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def setup_authentication(self):
        """Setup authentication tokens"""
        print("🔐 Setting up authentication...")
        
        # Login as admin
        response = self.make_request("POST", "/auth/login", self.admin_creds)
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            self.log_result("Admin Login", True, "Admin token obtained")
        else:
            self.log_result("Admin Login", False, f"Status: {response.status_code}")
            return False
            
        # Login as user
        response = self.make_request("POST", "/auth/login", self.user_creds)
        if response.status_code == 200:
            self.user_token = response.json()["access_token"]
            self.log_result("User Login", True, "User token obtained")
        else:
            self.log_result("User Login", False, f"Status: {response.status_code}")
            return False
            
        return True
    
    def test_rate_limiting_fix(self):
        """Test Priority 2: Rate Limiting Fix"""
        print("\n🚦 PRIORITY 2: Testing Rate Limiting Fix")
        print("-" * 50)
        
        # Test login rate limiting (10/minute)
        invalid_creds = {"email": "test@test.com", "password": "wrong"}
        
        rate_limit_hit = False
        for i in range(12):  # Exceed the 10/minute limit
            response = self.make_request("POST", "/auth/login", invalid_creds)
            if response.status_code == 429:
                rate_limit_hit = True
                self.log_result("Rate Limiting - Login", True, f"Rate limit enforced at request {i+1}")
                break
            time.sleep(0.1)
        
        if not rate_limit_hit:
            self.log_result("Rate Limiting - Login", False, "Rate limit not enforced")
            
        # Wait a bit before testing register
        time.sleep(2)
        
        # Test register rate limiting (5/minute)
        rate_limit_hit = False
        for i in range(7):  # Exceed the 5/minute limit
            test_data = {
                "email": f"ratetest{i}@example.com",
                "password": "testpass123",
                "full_name": "Rate Test User",
                "company": "Test Company"
            }
            response = self.make_request("POST", "/auth/register", test_data)
            if response.status_code == 429:
                rate_limit_hit = True
                self.log_result("Rate Limiting - Register", True, f"Rate limit enforced at request {i+1}")
                break
            time.sleep(0.1)
        
        if not rate_limit_hit:
            self.log_result("Rate Limiting - Register", False, "Rate limit not enforced")
    
    def test_bulk_upload_celery_fix(self):
        """Test Priority 3: Bulk Upload with Celery Fix"""
        print("\n📁 PRIORITY 3: Testing Bulk Upload with Celery Fix")
        print("-" * 50)
        
        if not self.admin_token:
            self.log_result("Bulk Upload Test", False, "No admin token available")
            return
            
        headers = self.get_auth_headers(self.admin_token)
        
        # Test bulk upload status endpoint with fake task ID
        fake_task_id = str(uuid.uuid4())
        response = self.make_request("GET", f"/bulk-upload/{fake_task_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["pending", "failed"]:
                self.log_result("Bulk Upload Status Endpoint", True, f"Status endpoint working: {data.get('status')}")
            else:
                self.log_result("Bulk Upload Status Endpoint", False, f"Unexpected status: {data}")
        else:
            self.log_result("Bulk Upload Status Endpoint", False, f"Status: {response.status_code}")
    
    def reveal_contact_worker(self, profile_id: str, reveal_type: str, worker_id: int):
        """Worker function for concurrent contact reveal testing"""
        headers = self.get_auth_headers(self.user_token)
        reveal_data = {"profile_id": profile_id, "reveal_type": reveal_type}
        
        try:
            response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
            return {
                "worker_id": worker_id,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "worker_id": worker_id,
                "status_code": 500,
                "response": str(e),
                "success": False
            }
    
    def test_credit_based_reveal_fix(self):
        """Test Priority 1: Credit-based Contact Reveal Fix (Atomic Credit Deduction)"""
        print("\n💳 PRIORITY 1: Testing Credit-based Contact Reveal Fix")
        print("-" * 50)
        
        if not self.user_token:
            self.log_result("Credit Reveal Test", False, "No user token available")
            return
            
        headers = self.get_auth_headers(self.user_token)
        
        # Get a profile to test with
        search_filters = {"skip": 0, "limit": 1}
        response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
        
        if response.status_code != 200:
            self.log_result("Credit Reveal Test", False, f"Could not get profiles: {response.status_code}")
            return
            
        profiles = response.json().get("profiles", [])
        if not profiles:
            self.log_result("Credit Reveal Test", False, "No profiles available for testing")
            return
            
        profile_id = profiles[0].get("id")
        
        # Get initial credits
        me_response = self.make_request("GET", "/auth/me", headers=headers)
        if me_response.status_code != 200:
            self.log_result("Credit Reveal Test", False, "Could not get user info")
            return
            
        initial_credits = me_response.json().get("credits", 0)
        print(f"Initial credits: {initial_credits}")
        
        # Test 1: Single email reveal
        reveal_data = {"profile_id": profile_id, "reveal_type": "email"}
        response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
        
        if response.status_code == 200:
            # Check credits were deducted
            me_response = self.make_request("GET", "/auth/me", headers=headers)
            if me_response.status_code == 200:
                new_credits = me_response.json().get("credits", 0)
                if new_credits == initial_credits - 1:
                    self.log_result("Credit Deduction - Email", True, f"Credits: {initial_credits} -> {new_credits}")
                else:
                    self.log_result("Credit Deduction - Email", False, f"Credits not properly deducted: {initial_credits} -> {new_credits}")
        else:
            self.log_result("Credit Deduction - Email", False, f"Email reveal failed: {response.status_code}")
            
        # Test 2: No double charging (reveal same email again)
        response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
        if response.status_code == 200:
            me_response = self.make_request("GET", "/auth/me", headers=headers)
            if me_response.status_code == 200:
                final_credits = me_response.json().get("credits", 0)
                if final_credits == new_credits:
                    self.log_result("No Double Charging", True, "Second reveal was free")
                else:
                    self.log_result("No Double Charging", False, f"Charged again: {new_credits} -> {final_credits}")
        
        # Test 3: Concurrent requests (atomic credit deduction)
        print("\nTesting atomic credit deduction with concurrent requests...")
        
        # Get a different profile for concurrent testing
        search_filters = {"skip": 1, "limit": 1}
        response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
        if response.status_code == 200:
            profiles = response.json().get("profiles", [])
            if profiles:
                concurrent_profile_id = profiles[0].get("id")
                
                # Get current credits
                me_response = self.make_request("GET", "/auth/me", headers=headers)
                concurrent_initial_credits = me_response.json().get("credits", 0)
                
                # Launch 5 concurrent email reveal requests
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for i in range(5):
                        future = executor.submit(self.reveal_contact_worker, concurrent_profile_id, "email", i)
                        futures.append(future)
                    
                    results = [future.result() for future in futures]
                
                # Check results
                successful_reveals = [r for r in results if r["success"]]
                failed_reveals = [r for r in results if not r["success"]]
                
                print(f"Concurrent requests: {len(successful_reveals)} successful, {len(failed_reveals)} failed")
                
                # Check final credits
                me_response = self.make_request("GET", "/auth/me", headers=headers)
                final_concurrent_credits = me_response.json().get("credits", 0)
                
                expected_credits = concurrent_initial_credits - 1  # Should only deduct 1 credit total
                if final_concurrent_credits == expected_credits:
                    self.log_result("Atomic Credit Deduction", True, f"Concurrent requests handled correctly: {concurrent_initial_credits} -> {final_concurrent_credits}")
                else:
                    self.log_result("Atomic Credit Deduction", False, f"Credit deduction not atomic: {concurrent_initial_credits} -> {final_concurrent_credits} (expected: {expected_credits})")
    
    def run_critical_tests(self):
        """Run all critical fix tests"""
        print("🎯 Testing LeadGen Pro Critical Fixes")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot proceed with tests")
            return
        
        # Test the 3 critical fixes
        self.test_credit_based_reveal_fix()
        self.test_rate_limiting_fix()
        self.test_bulk_upload_celery_fix()
        
        print("\n" + "=" * 60)
        print("🏁 Critical Fixes Testing Complete")
        print("=" * 60)

if __name__ == "__main__":
    tester = CriticalFixesTester()
    tester.run_critical_tests()