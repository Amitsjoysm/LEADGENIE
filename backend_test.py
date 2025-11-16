#!/usr/bin/env python3
"""
LeadGen Pro Backend API Testing Suite
Tests all critical backend endpoints with proper authentication and data validation
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

class LeadGenAPITester:
    def __init__(self):
        self.base_url = "https://leadsfinder.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = {}
        
        # Test credentials
        self.admin_creds = {
            "email": "admin@leadgen.com",
            "password": "admin123"
        }
        self.user_creds = {
            "email": "user1@example.com", 
            "password": "password123"
        }
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "response_data": response_data
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, files: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, headers=headers, data=data, files=files)
                else:
                    response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            raise
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    # ========== HEALTH CHECK TESTS ==========
    
    def test_health_check(self):
        """Test health check endpoints"""
        try:
            # Test root endpoint
            response = self.make_request("GET", "/")
            if response.status_code == 200:
                data = response.json()
                if "LeadGen Pro API" in data.get("message", ""):
                    self.log_result("Health Check - Root", True, "API is running")
                else:
                    self.log_result("Health Check - Root", False, f"Unexpected response: {data}")
            else:
                self.log_result("Health Check - Root", False, f"Status: {response.status_code}")
                
            # Test detailed health check
            response = self.make_request("GET", "/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check - Detailed", True, "All services healthy")
                else:
                    self.log_result("Health Check - Detailed", False, f"Unhealthy: {data}")
            else:
                self.log_result("Health Check - Detailed", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
    
    # ========== AUTHENTICATION TESTS ==========
    
    def test_user_registration(self):
        """Test user registration with rate limiting"""
        try:
            # Test valid registration
            unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
            user_data = {
                "email": unique_email,
                "password": "testpass123",
                "full_name": "Test User",
                "company": "Test Company"
            }
            
            response = self.make_request("POST", "/auth/register", user_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == unique_email:
                    self.log_result("User Registration", True, f"User created: {unique_email}")
                else:
                    self.log_result("User Registration", False, f"Unexpected response: {data}")
            else:
                self.log_result("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test duplicate email
            response = self.make_request("POST", "/auth/register", user_data)
            if response.status_code == 400:
                self.log_result("User Registration - Duplicate Email", True, "Correctly rejected duplicate")
            else:
                self.log_result("User Registration - Duplicate Email", False, f"Should reject duplicate, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception: {str(e)}")
    
    def test_user_login(self):
        """Test user login and token generation"""
        try:
            # Test admin login
            response = self.make_request("POST", "/auth/login", self.admin_creds)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    self.log_result("Admin Login", True, "Admin token obtained")
                else:
                    self.log_result("Admin Login", False, f"No token in response: {data}")
            else:
                self.log_result("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test regular user login
            response = self.make_request("POST", "/auth/login", self.user_creds)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.user_token = data["access_token"]
                    self.log_result("User Login", True, "User token obtained")
                else:
                    self.log_result("User Login", False, f"No token in response: {data}")
            else:
                self.log_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test invalid credentials
            invalid_creds = {"email": "invalid@test.com", "password": "wrongpass"}
            response = self.make_request("POST", "/auth/login", invalid_creds)
            if response.status_code == 401:
                self.log_result("Login - Invalid Credentials", True, "Correctly rejected invalid login")
            else:
                self.log_result("Login - Invalid Credentials", False, f"Should reject invalid, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("User Login", False, f"Exception: {str(e)}")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.admin_token:
            self.log_result("Get Current User", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.admin_creds["email"]:
                    self.log_result("Get Current User", True, f"Retrieved user: {data.get('email')}")
                else:
                    self.log_result("Get Current User", False, f"Wrong user data: {data}")
            else:
                self.log_result("Get Current User", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Get Current User", False, f"Exception: {str(e)}")
    
    def test_password_reset_flow(self):
        """Test forgot password and reset password"""
        try:
            # Test forgot password
            reset_data = {"email": self.user_creds["email"]}
            response = self.make_request("POST", "/auth/forgot-password", reset_data)
            
            if response.status_code == 200:
                data = response.json()
                if "Password reset email sent" in data.get("message", ""):
                    self.log_result("Forgot Password", True, "Reset email request processed")
                else:
                    self.log_result("Forgot Password", False, f"Unexpected message: {data}")
            else:
                self.log_result("Forgot Password", False, f"Status: {response.status_code}")
                
            # Test with non-existent email
            reset_data = {"email": "nonexistent@test.com"}
            response = self.make_request("POST", "/auth/forgot-password", reset_data)
            
            if response.status_code == 200:
                self.log_result("Forgot Password - Non-existent Email", True, "Handled gracefully")
            else:
                self.log_result("Forgot Password - Non-existent Email", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Password Reset Flow", False, f"Exception: {str(e)}")
    
    # ========== USER MANAGEMENT TESTS ==========
    
    def test_user_management(self):
        """Test user CRUD operations (super admin only)"""
        if not self.admin_token:
            self.log_result("User Management", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Test get all users
            response = self.make_request("GET", "/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    self.log_result("Get All Users", True, f"Retrieved {len(users)} users")
                    
                    # Test get specific user
                    user_id = users[0].get("id")
                    if user_id:
                        response = self.make_request("GET", f"/users/{user_id}", headers=headers)
                        if response.status_code == 200:
                            user_data = response.json()
                            self.log_result("Get User by ID", True, f"Retrieved user: {user_data.get('email')}")
                        else:
                            self.log_result("Get User by ID", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Get All Users", False, f"No users returned: {users}")
            else:
                self.log_result("Get All Users", False, f"Status: {response.status_code}")
                
            # Test with regular user token (should fail)
            if self.user_token:
                user_headers = self.get_auth_headers(self.user_token)
                response = self.make_request("GET", "/users", headers=user_headers)
                if response.status_code == 403:
                    self.log_result("User Management - Access Control", True, "Regular user correctly denied access")
                else:
                    self.log_result("User Management - Access Control", False, f"Should deny access, got: {response.status_code}")
                    
        except Exception as e:
            self.log_result("User Management", False, f"Exception: {str(e)}")
    
    def test_credit_management(self):
        """Test adding credits to users"""
        if not self.admin_token:
            self.log_result("Credit Management", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # First get a user to add credits to
            response = self.make_request("GET", "/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                if users:
                    user_id = users[0].get("id")
                    original_credits = users[0].get("credits", 0)
                    
                    # Add credits - pass credits as query parameter
                    response = self.make_request("POST", f"/users/{user_id}/credits?credits=10", 
                                               headers=headers)
                    if response.status_code == 200:
                        updated_user = response.json()
                        new_credits = updated_user.get("credits", 0)
                        if new_credits >= original_credits + 10:
                            self.log_result("Add Credits", True, f"Credits added: {original_credits} -> {new_credits}")
                        else:
                            self.log_result("Add Credits", False, f"Credits not properly added: {original_credits} -> {new_credits}")
                    else:
                        self.log_result("Add Credits", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Credit Management", False, "No users available for testing")
            else:
                self.log_result("Credit Management", False, f"Could not get users: {response.status_code}")
                
        except Exception as e:
            self.log_result("Credit Management", False, f"Exception: {str(e)}")
    
    # ========== PROFILE TESTS ==========
    
    def test_profile_search(self):
        """Test profile search with filters"""
        if not self.user_token:
            self.log_result("Profile Search", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # Test basic search
            search_filters = {
                "skip": 0,
                "limit": 10
            }
            
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                total = data.get("total", 0)
                
                if profiles and len(profiles) > 0:
                    self.log_result("Profile Search - Basic", True, f"Found {len(profiles)} profiles (total: {total})")
                    
                    # Check data masking for regular user
                    first_profile = profiles[0]
                    emails = first_profile.get("emails", [])
                    phones = first_profile.get("phones", [])
                    
                    # Check if emails/phones are masked
                    email_masked = any("***" in email for email in emails) if emails else True
                    phone_masked = any("***" in phone for phone in phones) if phones else True
                    
                    if email_masked and phone_masked:
                        self.log_result("Profile Search - Data Masking", True, f"Data properly masked: emails={emails}, phones={phones}")
                    else:
                        self.log_result("Profile Search - Data Masking", False, f"Data not masked: emails={emails}, phones={phones}")
                else:
                    self.log_result("Profile Search - Basic", False, f"No profiles found: {data}")
            else:
                self.log_result("Profile Search - Basic", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test search with filters
            filtered_search = {
                "skip": 0,
                "limit": 5,
                "industry": "Technology",
                "location": "San Francisco"
            }
            
            response = self.make_request("POST", "/profiles/search", filtered_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Filtered", True, f"Filtered search returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Filtered", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Profile Search", False, f"Exception: {str(e)}")
    
    def test_profile_reveal(self):
        """Test credit-based contact reveal (MOST IMPORTANT)"""
        if not self.user_token:
            self.log_result("Profile Reveal", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # First get a profile to reveal
            search_filters = {"skip": 0, "limit": 1}
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Reveal", False, f"Could not get profiles: {response.status_code}")
                return
                
            data = response.json()
            profiles = data.get("profiles", [])
            
            if not profiles:
                self.log_result("Profile Reveal", False, "No profiles available for testing")
                return
                
            profile_id = profiles[0].get("id")
            if not profile_id:
                self.log_result("Profile Reveal", False, "Profile has no ID")
                return
                
            # Get user's current credits
            me_response = self.make_request("GET", "/auth/me", headers=headers)
            if me_response.status_code != 200:
                self.log_result("Profile Reveal", False, "Could not get current user info")
                return
                
            original_credits = me_response.json().get("credits", 0)
            
            # Test email reveal (1 credit)
            reveal_data = {"profile_id": profile_id, "reveal_type": "email"}
            response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
            
            if response.status_code == 200:
                reveal_result = response.json()
                revealed_email = reveal_result.get("email")
                
                if revealed_email and "***" not in revealed_email:
                    self.log_result("Profile Reveal - Email", True, f"Email revealed: {revealed_email}")
                    
                    # Check credits were deducted
                    me_response = self.make_request("GET", "/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        new_credits = me_response.json().get("credits", 0)
                        if new_credits == original_credits - 1:
                            self.log_result("Profile Reveal - Credit Deduction", True, f"Credits: {original_credits} -> {new_credits}")
                        else:
                            self.log_result("Profile Reveal - Credit Deduction", False, f"Credits not properly deducted: {original_credits} -> {new_credits}")
                    
                    # Test revealing same email again (should be free)
                    response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
                    if response.status_code == 200:
                        me_response = self.make_request("GET", "/auth/me", headers=headers)
                        if me_response.status_code == 200:
                            final_credits = me_response.json().get("credits", 0)
                            if final_credits == new_credits:
                                self.log_result("Profile Reveal - No Double Charge", True, "Second reveal was free")
                            else:
                                self.log_result("Profile Reveal - No Double Charge", False, f"Charged again: {new_credits} -> {final_credits}")
                else:
                    self.log_result("Profile Reveal - Email", False, f"Email not properly revealed: {revealed_email}")
            else:
                self.log_result("Profile Reveal - Email", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test phone reveal (3 credits) if user has enough credits
            me_response = self.make_request("GET", "/auth/me", headers=headers)
            if me_response.status_code == 200:
                current_credits = me_response.json().get("credits", 0)
                if current_credits >= 3:
                    reveal_data = {"reveal_type": "phone"}
                    response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
                    
                    if response.status_code == 200:
                        reveal_result = response.json()
                        revealed_phone = reveal_result.get("phone")
                        
                        if revealed_phone and "***" not in revealed_phone:
                            self.log_result("Profile Reveal - Phone", True, f"Phone revealed: {revealed_phone}")
                        else:
                            self.log_result("Profile Reveal - Phone", False, f"Phone not properly revealed: {revealed_phone}")
                    else:
                        self.log_result("Profile Reveal - Phone", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Profile Reveal - Phone", False, f"Insufficient credits for phone reveal: {current_credits}")
                    
        except Exception as e:
            self.log_result("Profile Reveal", False, f"Exception: {str(e)}")
    
    def test_profile_get_by_id(self):
        """Test getting profile by ID"""
        if not self.user_token:
            self.log_result("Profile Get by ID", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # First get a profile ID
            search_filters = {"skip": 0, "limit": 1}
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                
                if profiles:
                    profile_id = profiles[0].get("id")
                    
                    # Get profile by ID
                    response = self.make_request("GET", f"/profiles/{profile_id}", headers=headers)
                    if response.status_code == 200:
                        profile = response.json()
                        self.log_result("Profile Get by ID", True, f"Retrieved profile: {profile.get('full_name')}")
                    else:
                        self.log_result("Profile Get by ID", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Profile Get by ID", False, "No profiles available")
            else:
                self.log_result("Profile Get by ID", False, f"Could not search profiles: {response.status_code}")
                
        except Exception as e:
            self.log_result("Profile Get by ID", False, f"Exception: {str(e)}")
    
    # ========== COMPANY TESTS ==========
    
    def test_company_search(self):
        """Test company search"""
        if not self.user_token:
            self.log_result("Company Search", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # Test basic company search
            search_filters = {
                "skip": 0,
                "limit": 10
            }
            
            response = self.make_request("POST", "/companies/search", search_filters, headers=headers)
            if response.status_code == 200:
                data = response.json()
                companies = data.get("companies", [])
                total = data.get("total", 0)
                
                if companies:
                    self.log_result("Company Search", True, f"Found {len(companies)} companies (total: {total})")
                else:
                    self.log_result("Company Search", False, f"No companies found: {data}")
            else:
                self.log_result("Company Search", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Company Search", False, f"Exception: {str(e)}")
    
    # ========== PLAN TESTS ==========
    
    def test_plans(self):
        """Test plan endpoints"""
        try:
            # Test get all plans (no auth required)
            response = self.make_request("GET", "/plans")
            if response.status_code == 200:
                plans = response.json()
                if isinstance(plans, list) and len(plans) > 0:
                    self.log_result("Get Plans", True, f"Retrieved {len(plans)} plans")
                    
                    # Test get specific plan
                    plan_id = plans[0].get("id")
                    if plan_id:
                        response = self.make_request("GET", f"/plans/{plan_id}")
                        if response.status_code == 200:
                            plan = response.json()
                            self.log_result("Get Plan by ID", True, f"Retrieved plan: {plan.get('name')}")
                        else:
                            self.log_result("Get Plan by ID", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Get Plans", False, f"No plans returned: {plans}")
            else:
                self.log_result("Get Plans", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Plans", False, f"Exception: {str(e)}")
    
    # ========== BULK UPLOAD TESTS ==========
    
    def test_bulk_upload_endpoints(self):
        """Test bulk upload endpoints (without actual file upload)"""
        if not self.admin_token:
            self.log_result("Bulk Upload", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Test getting status of non-existent task
            fake_task_id = str(uuid.uuid4())
            response = self.make_request("GET", f"/bulk-upload/{fake_task_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["pending", "failed"]:
                    self.log_result("Bulk Upload Status", True, f"Status endpoint working: {data.get('status')}")
                else:
                    self.log_result("Bulk Upload Status", False, f"Unexpected status: {data}")
            else:
                self.log_result("Bulk Upload Status", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Bulk Upload", False, f"Exception: {str(e)}")
    
    # ========== RATE LIMITING TESTS ==========
    
    def test_rate_limiting(self):
        """Test rate limiting on auth endpoints"""
        try:
            # Test login rate limiting (10/minute)
            invalid_creds = {"email": "test@test.com", "password": "wrong"}
            
            # Make multiple rapid requests
            rate_limit_hit = False
            for i in range(12):  # Exceed the 10/minute limit
                response = self.make_request("POST", "/auth/login", invalid_creds)
                if response.status_code == 429:  # Too Many Requests
                    rate_limit_hit = True
                    break
                time.sleep(0.1)  # Small delay between requests
                
            if rate_limit_hit:
                self.log_result("Rate Limiting - Login", True, "Rate limit correctly enforced")
            else:
                self.log_result("Rate Limiting - Login", False, "Rate limit not enforced")
                
        except Exception as e:
            self.log_result("Rate Limiting", False, f"Exception: {str(e)}")
    
    # ========== ADMIN DATA MASKING TESTS ==========
    
    def test_admin_data_visibility(self):
        """Test that super admin sees unmasked data"""
        if not self.admin_token:
            self.log_result("Admin Data Visibility", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Search profiles as admin
            search_filters = {"skip": 0, "limit": 1}
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                
                if profiles:
                    profile = profiles[0]
                    email = profile.get("email", "")
                    phone = profile.get("phone", "")
                    
                    # Admin should see unmasked data
                    if email and "***" not in email and "@" in email:
                        self.log_result("Admin Data Visibility", True, f"Admin sees unmasked data: {email}")
                    else:
                        self.log_result("Admin Data Visibility", False, f"Admin data still masked: {email}")
                else:
                    self.log_result("Admin Data Visibility", False, "No profiles to test")
            else:
                self.log_result("Admin Data Visibility", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Admin Data Visibility", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in order"""
        print("🚀 Starting LeadGen Pro Backend API Tests")
        print("=" * 60)
        
        # Health checks first
        self.test_health_check()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_password_reset_flow()
        
        # User management tests
        self.test_user_management()
        self.test_credit_management()
        
        # Profile tests (most important)
        self.test_profile_search()
        self.test_profile_reveal()
        self.test_profile_get_by_id()
        
        # Company tests
        self.test_company_search()
        
        # Plan tests
        self.test_plans()
        
        # Bulk upload tests
        self.test_bulk_upload_endpoints()
        
        # Admin-specific tests
        self.test_admin_data_visibility()
        
        # Rate limiting tests
        self.test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['details']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = LeadGenAPITester()
    results = tester.run_all_tests()