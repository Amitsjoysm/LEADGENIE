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
        self.base_url = "https://domain-relation.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = {}
        
        # Test credentials from review request
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
                "first_name": "Test",
                "last_name": "User"
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
                    
                    # Add credits - pass amount in request body
                    credit_data = {"amount": 10}
                    response = self.make_request("POST", f"/users/{user_id}/credits", 
                                               credit_data, headers=headers)
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
                "page": 1,
                "page_size": 10
            }
            
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                total = data.get("total", 0)
                
                if profiles and len(profiles) > 0 and total >= 5000:
                    self.log_result("Profile Search - 5000 Profiles", True, f"Found {len(profiles)} profiles (total: {total})")
                    
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
                elif profiles and total < 5000:
                    self.log_result("Profile Search - 5000 Profiles", False, f"Expected 5000+ profiles, got {total}")
                else:
                    self.log_result("Profile Search - 5000 Profiles", False, f"No profiles found: {data}")
            else:
                self.log_result("Profile Search - Basic", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test search with traditional filters
            filtered_search = {
                "page": 1,
                "page_size": 5,
                "industry": "Technology",
                "location": "San Francisco"
            }
            
            response = self.make_request("POST", "/profiles/search", filtered_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Traditional Filters", True, f"Filtered search returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Traditional Filters", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Profile Search", False, f"Exception: {str(e)}")
    
    def test_profile_search_new_filters(self):
        """Test profile search with new enhanced filters"""
        if not self.user_token:
            self.log_result("Profile Search New Filters", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # Test experience years filter
            experience_search = {
                "page": 1,
                "page_size": 10,
                "experience_years_min": 5,
                "experience_years_max": 15
            }
            
            response = self.make_request("POST", "/profiles/search", experience_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Experience Years Filter", True, 
                              f"Experience filter returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Experience Years Filter", False, 
                              f"Status: {response.status_code}")
            
            # Test company size filter
            company_size_search = {
                "page": 1,
                "page_size": 10,
                "company_size": "100-500"
            }
            
            response = self.make_request("POST", "/profiles/search", company_size_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Company Size Filter", True, 
                              f"Company size filter returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Company Size Filter", False, 
                              f"Status: {response.status_code}")
            
            # Test revenue range filter
            revenue_search = {
                "page": 1,
                "page_size": 10,
                "revenue_range": "$10M-$50M"
            }
            
            response = self.make_request("POST", "/profiles/search", revenue_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Revenue Range Filter", True, 
                              f"Revenue filter returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Revenue Range Filter", False, 
                              f"Status: {response.status_code}")
            
            # Test skills filter
            skills_search = {
                "page": 1,
                "page_size": 10,
                "skills": "Leadership,Strategy"
            }
            
            response = self.make_request("POST", "/profiles/search", skills_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Skills Filter", True, 
                              f"Skills filter returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Skills Filter", False, 
                              f"Status: {response.status_code}")
            
            # Test combined new filters
            combined_search = {
                "page": 1,
                "page_size": 5,
                "experience_years_min": 3,
                "experience_years_max": 20,
                "company_size": "100-500",
                "skills": "Leadership"
            }
            
            response = self.make_request("POST", "/profiles/search", combined_search, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                self.log_result("Profile Search - Combined New Filters", True, 
                              f"Combined filters returned {len(profiles)} profiles")
            else:
                self.log_result("Profile Search - Combined New Filters", False, 
                              f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Profile Search New Filters", False, f"Exception: {str(e)}")
    
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
                revealed_emails = reveal_result.get("emails", [])
                
                if revealed_emails and any("***" not in email for email in revealed_emails):
                    self.log_result("Profile Reveal - Email", True, f"Email revealed: {revealed_emails}")
                    
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
                    self.log_result("Profile Reveal - Email", False, f"Email not properly revealed: {revealed_emails}")
            else:
                self.log_result("Profile Reveal - Email", False, f"Status: {response.status_code}, Response: {response.text}")
                
            # Test phone reveal (3 credits) if user has enough credits
            me_response = self.make_request("GET", "/auth/me", headers=headers)
            if me_response.status_code == 200:
                current_credits = me_response.json().get("credits", 0)
                if current_credits >= 3:
                    reveal_data = {"profile_id": profile_id, "reveal_type": "phone"}
                    response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
                    
                    if response.status_code == 200:
                        reveal_result = response.json()
                        revealed_phones = reveal_result.get("phones", [])
                        
                        if revealed_phones and any("***" not in phone for phone in revealed_phones):
                            self.log_result("Profile Reveal - Phone", True, f"Phone revealed: {revealed_phones}")
                        else:
                            self.log_result("Profile Reveal - Phone", False, f"Phone not properly revealed: {revealed_phones}")
                    else:
                        self.log_result("Profile Reveal - Phone", False, f"Status: {response.status_code}")
                else:
                    self.log_result("Profile Reveal - Phone", False, f"Insufficient credits for phone reveal: {current_credits}")
                    
        except Exception as e:
            self.log_result("Profile Reveal", False, f"Exception: {str(e)}")
    
    def test_profile_get_by_id(self):
        """Test getting profile by ID (super admin only)"""
        if not self.admin_token:
            self.log_result("Profile Get by ID", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
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
        """Test company search with 1000 companies"""
        if not self.user_token:
            self.log_result("Company Search", False, "No user token available")
            return
            
        try:
            headers = self.get_auth_headers(self.user_token)
            
            # Test basic company search
            search_filters = {
                "page": 1,
                "page_size": 10
            }
            
            response = self.make_request("POST", "/companies/search", search_filters, headers=headers)
            if response.status_code == 200:
                data = response.json()
                companies = data.get("companies", [])
                total = data.get("total", 0)
                
                if companies and total >= 1000:
                    self.log_result("Company Search - 1000 Companies", True, f"Found {len(companies)} companies (total: {total})")
                elif companies:
                    self.log_result("Company Search - 1000 Companies", False, f"Expected 1000+ companies, got {total}")
                else:
                    self.log_result("Company Search - 1000 Companies", False, f"No companies found: {data}")
                    
                # Test with name filter
                filtered_search = {
                    "page": 1,
                    "page_size": 5,
                    "name": "Tech"
                }
                
                response = self.make_request("POST", "/companies/search", filtered_search, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    companies = data.get("companies", [])
                    self.log_result("Company Search - Name Filter", True, f"Name filter returned {len(companies)} companies")
                else:
                    self.log_result("Company Search - Name Filter", False, f"Status: {response.status_code}")
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
    
    def test_bulk_upload_template_downloads(self):
        """Test bulk upload template download endpoints"""
        if not self.admin_token:
            self.log_result("Template Downloads", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Expected template structures
            expected_templates = {
                "profiles": [
                    "first_name", "last_name", "job_title", "company_name", "industry",
                    "emails", "phones", "city", "state", "country", "linkedin_url",
                    "experience_years", "skills"
                ],
                "companies": [
                    "name", "industry", "size", "revenue", "website", "description",
                    "city", "state", "country", "founded_year"
                ],
                "combined": [
                    "type", "first_name", "last_name", "job_title", "company_name", 
                    "industry", "emails", "phones", "city", "state", "country", 
                    "linkedin_url", "experience_years", "skills", "size", "revenue", 
                    "website", "description", "founded_year"
                ]
            }
            
            # Test each template type
            for template_type, expected_fields in expected_templates.items():
                response = self.make_request("GET", f"/bulk-upload/templates/{template_type}", headers=headers)
                
                if response.status_code == 200:
                    # Check if response is CSV
                    content_type = response.headers.get('content-type', '')
                    if 'text/csv' in content_type:
                        # Parse CSV content
                        csv_content = response.text
                        lines = csv_content.strip().split('\n')
                        if lines:
                            header_line = lines[0]
                            actual_fields = [field.strip('"') for field in header_line.split(',')]
                            
                            # Check if all expected fields are present
                            missing_fields = set(expected_fields) - set(actual_fields)
                            extra_fields = set(actual_fields) - set(expected_fields)
                            
                            if not missing_fields and not extra_fields:
                                self.log_result(f"Template Download - {template_type.title()}", True, 
                                              f"Template structure correct: {len(actual_fields)} fields")
                            else:
                                error_msg = ""
                                if missing_fields:
                                    error_msg += f"Missing: {missing_fields} "
                                if extra_fields:
                                    error_msg += f"Extra: {extra_fields}"
                                self.log_result(f"Template Download - {template_type.title()}", False, 
                                              f"Template structure incorrect: {error_msg}")
                        else:
                            self.log_result(f"Template Download - {template_type.title()}", False, "Empty CSV content")
                    else:
                        self.log_result(f"Template Download - {template_type.title()}", False, 
                                      f"Wrong content type: {content_type}")
                else:
                    self.log_result(f"Template Download - {template_type.title()}", False, 
                                  f"Status: {response.status_code}")
            
            # Test authentication requirement - try with regular user token
            if self.user_token:
                user_headers = self.get_auth_headers(self.user_token)
                response = self.make_request("GET", "/bulk-upload/templates/profiles", headers=user_headers)
                if response.status_code == 403:
                    self.log_result("Template Downloads - Access Control", True, 
                                  "Regular user correctly denied access")
                else:
                    self.log_result("Template Downloads - Access Control", False, 
                                  f"Should deny access, got: {response.status_code}")
            
            # Test invalid template type
            response = self.make_request("GET", "/bulk-upload/templates/invalid", headers=headers)
            if response.status_code == 400:
                self.log_result("Template Downloads - Invalid Type", True, 
                              "Invalid template type correctly rejected")
            else:
                self.log_result("Template Downloads - Invalid Type", False, 
                              f"Should reject invalid type, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("Template Downloads", False, f"Exception: {str(e)}")
    
    def test_bulk_upload_endpoints(self):
        """Test bulk upload endpoints (without actual file upload)"""
        if not self.admin_token:
            self.log_result("Bulk Upload", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Test the specific endpoint mentioned in review request
            test_task_id = "test-task-id"
            response = self.make_request("GET", f"/bulk-upload/{test_task_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["pending", "processing", "completed", "failed"]:
                    self.log_result("Bulk Upload Status - Test Task", True, f"Status endpoint working: {data.get('status')}")
                else:
                    self.log_result("Bulk Upload Status - Test Task", False, f"Unexpected status: {data}")
            else:
                self.log_result("Bulk Upload Status - Test Task", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test getting status of non-existent task
            fake_task_id = str(uuid.uuid4())
            response = self.make_request("GET", f"/bulk-upload/{fake_task_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["pending", "failed"]:
                    self.log_result("Bulk Upload Status - Random Task", True, f"Status endpoint working: {data.get('status')}")
                else:
                    self.log_result("Bulk Upload Status - Random Task", False, f"Unexpected status: {data}")
            else:
                self.log_result("Bulk Upload Status - Random Task", False, f"Status: {response.status_code}")
                
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
            responses = []
            for i in range(15):  # Exceed the 10/minute limit
                response = self.make_request("POST", "/auth/login", invalid_creds)
                responses.append(response.status_code)
                if response.status_code == 429:  # Too Many Requests
                    rate_limit_hit = True
                    break
                # No delay to test rapid requests
                
            if rate_limit_hit:
                self.log_result("Rate Limiting - Login", True, f"Rate limit correctly enforced after {len(responses)} requests")
            else:
                self.log_result("Rate Limiting - Login", False, f"Rate limit not enforced. Status codes: {responses}")
                
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
                    emails = profile.get("emails", [])
                    phones = profile.get("phones", [])
                    
                    # Admin should see unmasked data
                    if emails and any("@" in email and "***" not in email for email in emails):
                        self.log_result("Admin Data Visibility", True, f"Admin sees unmasked data: {emails}")
                    else:
                        self.log_result("Admin Data Visibility", False, f"Admin data still masked: {emails}")
                else:
                    self.log_result("Admin Data Visibility", False, "No profiles to test")
            else:
                self.log_result("Admin Data Visibility", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Admin Data Visibility", False, f"Exception: {str(e)}")
    
    # ========== HIERARCHICAL RELATIONSHIPS & UNIQUENESS TESTS ==========
    
    def test_profile_company_hierarchical_relationship(self):
        """Test Profile-Company hierarchical relationship"""
        if not self.admin_token:
            self.log_result("Profile-Company Hierarchical Relationship", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # First get a profile to verify it has company_id
            search_filters = {"page": 1, "page_size": 1}
            response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                
                if profiles:
                    profile = profiles[0]
                    profile_id = profile.get("id")
                    company_id = profile.get("company_id")
                    company_name = profile.get("company_name")
                    company_domain = profile.get("company_domain")
                    
                    if company_id:
                        self.log_result("Profile Has Company ID", True, f"Profile {profile_id} has company_id: {company_id}")
                        
                        # Now fetch the company using company_id
                        response = self.make_request("GET", f"/companies/{company_id}", headers=headers)
                        if response.status_code == 200:
                            company = response.json()
                            company_fetched_name = company.get("name")
                            company_fetched_domain = company.get("domain")
                            
                            # Verify company data matches profile data
                            if (company_fetched_name == company_name and 
                                company_fetched_domain == company_domain):
                                self.log_result("Profile-Company Data Match", True, 
                                              f"Company data matches: name={company_name}, domain={company_domain}")
                            else:
                                self.log_result("Profile-Company Data Match", False, 
                                              f"Data mismatch - Profile: {company_name}/{company_domain}, Company: {company_fetched_name}/{company_fetched_domain}")
                        else:
                            self.log_result("Fetch Company by ID", False, f"Could not fetch company {company_id}: {response.status_code}")
                    else:
                        self.log_result("Profile Has Company ID", False, "Profile missing company_id field")
                else:
                    self.log_result("Profile-Company Hierarchical Relationship", False, "No profiles available for testing")
            else:
                self.log_result("Profile-Company Hierarchical Relationship", False, f"Could not search profiles: {response.status_code}")
                
        except Exception as e:
            self.log_result("Profile-Company Hierarchical Relationship", False, f"Exception: {str(e)}")
    
    def test_email_uniqueness_constraint(self):
        """Test email uniqueness constraint"""
        if not self.admin_token:
            self.log_result("Email Uniqueness Constraint", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Create a profile with unique email
            unique_email = f"unique_{uuid.uuid4().hex[:8]}@testcompany.com"
            profile_data = {
                "first_name": "Test",
                "last_name": "User",
                "job_title": "Software Engineer",
                "company_name": "Test Company",
                "company_domain": f"testcompany{uuid.uuid4().hex[:8]}.com",
                "emails": [unique_email],
                "phones": ["+1-555-123-4567"],
                "city": "San Francisco",
                "state": "CA",
                "country": "USA"
            }
            
            response = self.make_request("POST", "/profiles", profile_data, headers=headers)
            if response.status_code == 200:
                created_profile = response.json()
                self.log_result("Create Profile with Unique Email", True, f"Profile created with email: {unique_email}")
                
                # Now try to create another profile with the same email (should fail)
                duplicate_profile_data = {
                    "first_name": "Another",
                    "last_name": "User", 
                    "job_title": "Manager",
                    "company_name": "Another Company",
                    "company_domain": f"anothercompany{uuid.uuid4().hex[:8]}.com",
                    "emails": [unique_email],  # Same email
                    "phones": ["+1-555-987-6543"],
                    "city": "New York",
                    "state": "NY",
                    "country": "USA"
                }
                
                response = self.make_request("POST", "/profiles", duplicate_profile_data, headers=headers)
                if response.status_code == 400:
                    error_message = response.json().get("detail", "")
                    if "already registered" in error_message.lower():
                        self.log_result("Email Uniqueness Constraint", True, f"Duplicate email correctly rejected: {error_message}")
                    else:
                        self.log_result("Email Uniqueness Constraint", False, f"Wrong error message: {error_message}")
                else:
                    self.log_result("Email Uniqueness Constraint", False, f"Should reject duplicate email, got: {response.status_code}")
            else:
                self.log_result("Email Uniqueness Constraint", False, f"Could not create initial profile: {response.status_code}, {response.text}")
                
        except Exception as e:
            self.log_result("Email Uniqueness Constraint", False, f"Exception: {str(e)}")
    
    def test_company_domain_uniqueness_constraint(self):
        """Test company domain uniqueness constraint"""
        if not self.admin_token:
            self.log_result("Company Domain Uniqueness Constraint", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Create a company with unique domain
            unique_domain = f"uniquecompany{uuid.uuid4().hex[:8]}.com"
            company_data = {
                "name": "Unique Test Company",
                "domain": unique_domain,
                "industry": "Technology",
                "employee_size": "100-500",
                "revenue": "$10M-$50M",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA"
            }
            
            response = self.make_request("POST", "/companies", company_data, headers=headers)
            if response.status_code == 200:
                created_company = response.json()
                self.log_result("Create Company with Unique Domain", True, f"Company created with domain: {unique_domain}")
                
                # Now try to create another company with the same domain (should fail)
                duplicate_company_data = {
                    "name": "Another Test Company",
                    "domain": unique_domain,  # Same domain
                    "industry": "Finance",
                    "employee_size": "50-100",
                    "revenue": "$5M-$10M",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA"
                }
                
                response = self.make_request("POST", "/companies", duplicate_company_data, headers=headers)
                if response.status_code == 400:
                    error_message = response.json().get("detail", "")
                    if "already exists" in error_message.lower():
                        self.log_result("Company Domain Uniqueness Constraint", True, f"Duplicate domain correctly rejected: {error_message}")
                    else:
                        self.log_result("Company Domain Uniqueness Constraint", False, f"Wrong error message: {error_message}")
                else:
                    self.log_result("Company Domain Uniqueness Constraint", False, f"Should reject duplicate domain, got: {response.status_code}")
            else:
                self.log_result("Company Domain Uniqueness Constraint", False, f"Could not create initial company: {response.status_code}, {response.text}")
                
        except Exception as e:
            self.log_result("Company Domain Uniqueness Constraint", False, f"Exception: {str(e)}")
    
    def test_auto_company_creation_from_profile(self):
        """Test auto company creation when creating profile with new domain"""
        if not self.admin_token:
            self.log_result("Auto Company Creation from Profile", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # Create profile with a completely new company domain
            new_domain = f"newcompany{uuid.uuid4().hex[:8]}.com"
            new_company_name = "Auto Created Company"
            
            profile_data = {
                "first_name": "Auto",
                "last_name": "Test",
                "job_title": "CEO",
                "company_name": new_company_name,
                "company_domain": new_domain,
                "emails": [f"auto.test{uuid.uuid4().hex[:8]}@{new_domain}"],
                "phones": ["+1-555-111-2222"],
                "city": "Austin",
                "state": "TX",
                "country": "USA"
            }
            
            response = self.make_request("POST", "/profiles", profile_data, headers=headers)
            if response.status_code == 200:
                created_profile = response.json()
                company_id = created_profile.get("company_id")
                
                if company_id:
                    self.log_result("Profile Created with Auto Company", True, f"Profile created with auto-generated company_id: {company_id}")
                    
                    # Verify the company was actually created
                    response = self.make_request("GET", f"/companies/{company_id}", headers=headers)
                    if response.status_code == 200:
                        auto_created_company = response.json()
                        if (auto_created_company.get("name") == new_company_name and 
                            auto_created_company.get("domain") == new_domain):
                            self.log_result("Auto Company Creation from Profile", True, 
                                          f"Company auto-created successfully: {new_company_name} ({new_domain})")
                        else:
                            self.log_result("Auto Company Creation from Profile", False, 
                                          f"Auto-created company data mismatch: {auto_created_company}")
                    else:
                        self.log_result("Auto Company Creation from Profile", False, 
                                      f"Auto-created company not found: {response.status_code}")
                else:
                    self.log_result("Auto Company Creation from Profile", False, "Profile created without company_id")
            else:
                self.log_result("Auto Company Creation from Profile", False, 
                              f"Could not create profile: {response.status_code}, {response.text}")
                
        except Exception as e:
            self.log_result("Auto Company Creation from Profile", False, f"Exception: {str(e)}")
    
    def test_existing_company_linkage(self):
        """Test profile linking to existing company by domain"""
        if not self.admin_token:
            self.log_result("Existing Company Linkage", False, "No admin token available")
            return
            
        try:
            headers = self.get_auth_headers(self.admin_token)
            
            # First, get an existing company domain from the database
            search_filters = {"page": 1, "page_size": 1}
            response = self.make_request("POST", "/companies/search", search_filters, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                companies = data.get("companies", [])
                
                if companies:
                    existing_company = companies[0]
                    existing_domain = existing_company.get("domain")
                    existing_company_id = existing_company.get("id")
                    existing_company_name = existing_company.get("name")
                    
                    # Create a new profile with the existing company domain
                    profile_data = {
                        "first_name": "Existing",
                        "last_name": "Company",
                        "job_title": "Developer",
                        "company_name": existing_company_name,
                        "company_domain": existing_domain,  # Use existing domain
                        "emails": [f"existing.company{uuid.uuid4().hex[:8]}@{existing_domain}"],
                        "phones": ["+1-555-333-4444"],
                        "city": "Seattle",
                        "state": "WA",
                        "country": "USA"
                    }
                    
                    response = self.make_request("POST", "/profiles", profile_data, headers=headers)
                    if response.status_code == 200:
                        created_profile = response.json()
                        profile_company_id = created_profile.get("company_id")
                        
                        if profile_company_id == existing_company_id:
                            self.log_result("Existing Company Linkage", True, 
                                          f"Profile correctly linked to existing company: {existing_company_id}")
                            
                            # Verify multiple profiles can belong to same company
                            # Create another profile with same domain
                            profile_data2 = {
                                "first_name": "Another",
                                "last_name": "Employee",
                                "job_title": "Manager",
                                "company_name": existing_company_name,
                                "company_domain": existing_domain,
                                "emails": [f"another.employee{uuid.uuid4().hex[:8]}@{existing_domain}"],
                                "phones": ["+1-555-555-6666"],
                                "city": "Portland",
                                "state": "OR",
                                "country": "USA"
                            }
                            
                            response = self.make_request("POST", "/profiles", profile_data2, headers=headers)
                            if response.status_code == 200:
                                created_profile2 = response.json()
                                profile2_company_id = created_profile2.get("company_id")
                                
                                if profile2_company_id == existing_company_id:
                                    self.log_result("Multiple Profiles Same Company", True, 
                                                  f"Multiple profiles linked to same company: {existing_company_id}")
                                else:
                                    self.log_result("Multiple Profiles Same Company", False, 
                                                  f"Second profile linked to different company: {profile2_company_id}")
                            else:
                                self.log_result("Multiple Profiles Same Company", False, 
                                              f"Could not create second profile: {response.status_code}")
                        else:
                            self.log_result("Existing Company Linkage", False, 
                                          f"Profile linked to wrong company: expected {existing_company_id}, got {profile_company_id}")
                    else:
                        self.log_result("Existing Company Linkage", False, 
                                      f"Could not create profile: {response.status_code}, {response.text}")
                else:
                    self.log_result("Existing Company Linkage", False, "No existing companies found for testing")
            else:
                self.log_result("Existing Company Linkage", False, f"Could not search companies: {response.status_code}")
                
        except Exception as e:
            self.log_result("Existing Company Linkage", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests in order"""
        print("🚀 Starting LeadGen Pro Backend API Tests - HIERARCHICAL RELATIONSHIPS & UNIQUENESS")
        print("=" * 80)
        
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
        
        # NEW: Hierarchical Relationships & Uniqueness Tests
        print("\n🔗 TESTING HIERARCHICAL RELATIONSHIPS & UNIQUENESS CONSTRAINTS")
        print("-" * 80)
        self.test_profile_company_hierarchical_relationship()
        self.test_email_uniqueness_constraint()
        self.test_company_domain_uniqueness_constraint()
        self.test_auto_company_creation_from_profile()
        self.test_existing_company_linkage()
        
        # Profile tests (most important)
        self.test_profile_search()
        self.test_profile_search_new_filters()
        self.test_profile_reveal()
        self.test_profile_get_by_id()
        
        # Company tests
        self.test_company_search()
        
        # Plan tests
        self.test_plans()
        
        # Bulk upload tests
        self.test_bulk_upload_template_downloads()
        self.test_bulk_upload_endpoints()
        
        # Admin-specific tests
        self.test_admin_data_visibility()
        
        # Rate limiting tests
        self.test_rate_limiting()
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
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