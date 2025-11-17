#!/usr/bin/env python3
"""
Production Readiness Test for Credit System & Payment-Related Endpoints
Focused test based on the specific review request requirements
"""

import requests
import json
import time
from typing import Dict, Any

class ProductionReadinessTest:
    def __init__(self):
        self.base_url = "https://endpoint-verify-1.preview.emergentagent.com/api"
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
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.test_results[test_name] = {
            "success": success,
            "details": details
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        if method.upper() == "GET":
            response = self.session.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = self.session.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return response
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_authentication_flow(self):
        """Test authentication flow for both user types"""
        print("\n🔐 TESTING AUTHENTICATION FLOW")
        print("-" * 50)
        
        # Test super admin login
        response = self.make_request("POST", "/auth/login", self.admin_creds)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.admin_token = data["access_token"]
                self.log_result("Super Admin Login", True, "Admin token obtained successfully")
            else:
                self.log_result("Super Admin Login", False, f"No token in response: {data}")
        else:
            self.log_result("Super Admin Login", False, f"Status: {response.status_code}")
            
        # Test regular user login
        response = self.make_request("POST", "/auth/login", self.user_creds)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.user_token = data["access_token"]
                self.log_result("Regular User Login", True, "User token obtained successfully")
            else:
                self.log_result("Regular User Login", False, f"No token in response: {data}")
        else:
            self.log_result("Regular User Login", False, f"Status: {response.status_code}")
            
        # Test JWT token validation
        if self.admin_token:
            headers = self.get_auth_headers(self.admin_token)
            response = self.make_request("GET", "/auth/me", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.admin_creds["email"] and data.get("credits") == 1000:
                    self.log_result("JWT Token Validation", True, f"Admin has 1000 credits as expected")
                else:
                    self.log_result("JWT Token Validation", False, f"Unexpected user data: {data}")
            else:
                self.log_result("JWT Token Validation", False, f"Status: {response.status_code}")
    
    def test_credit_management_endpoints(self):
        """Test credit management endpoints (core payment features)"""
        print("\n💳 TESTING CREDIT MANAGEMENT ENDPOINTS")
        print("-" * 50)
        
        if not self.admin_token:
            self.log_result("Credit Management", False, "No admin token available")
            return
            
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET /api/users (super admin - view all users and their credits)
        response = self.make_request("GET", "/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            if isinstance(users, list) and len(users) > 0:
                admin_user = next((u for u in users if u.get("email") == "admin@leadgen.com"), None)
                regular_user = next((u for u in users if u.get("email") == "user1@example.com"), None)
                
                if admin_user and admin_user.get("credits") == 1000:
                    self.log_result("View All Users - Admin Credits", True, "Super admin has 1000 credits")
                else:
                    self.log_result("View All Users - Admin Credits", False, f"Admin credits: {admin_user.get('credits') if admin_user else 'User not found'}")
                    
                if regular_user and regular_user.get("credits") == 50:
                    self.log_result("View All Users - User Credits", True, "Regular user has 50 credits")
                    user_id = regular_user.get("id")
                else:
                    self.log_result("View All Users - User Credits", False, f"User credits: {regular_user.get('credits') if regular_user else 'User not found'}")
                    user_id = users[0].get("id")  # Use first user as fallback
            else:
                self.log_result("View All Users", False, f"No users returned: {users}")
                return
        else:
            self.log_result("View All Users", False, f"Status: {response.status_code}")
            return
            
        # Test GET /api/users/{user_id} (super admin - view specific user's credit balance)
        if user_id:
            response = self.make_request("GET", f"/users/{user_id}", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                self.log_result("View Specific User", True, f"Retrieved user: {user_data.get('email')} with {user_data.get('credits')} credits")
            else:
                self.log_result("View Specific User", False, f"Status: {response.status_code}")
                
        # Test POST /api/users/{user_id}/credits (super admin - add credits)
        if user_id:
            original_credits = regular_user.get("credits", 0) if regular_user else 0
            credit_data = {"amount": 100}
            response = self.make_request("POST", f"/users/{user_id}/credits", credit_data, headers=headers)
            if response.status_code == 200:
                updated_user = response.json()
                new_credits = updated_user.get("credits", 0)
                if new_credits == original_credits + 100:
                    self.log_result("Add Credits (+100)", True, f"Credits: {original_credits} -> {new_credits}")
                else:
                    self.log_result("Add Credits (+100)", False, f"Credits not properly added: {original_credits} -> {new_credits}")
            else:
                self.log_result("Add Credits (+100)", False, f"Status: {response.status_code}")
                
            # Test deducting credits
            credit_data = {"amount": -50}
            response = self.make_request("POST", f"/users/{user_id}/credits", credit_data, headers=headers)
            if response.status_code == 200:
                updated_user = response.json()
                final_credits = updated_user.get("credits", 0)
                expected_credits = original_credits + 100 - 50
                if final_credits == expected_credits:
                    self.log_result("Deduct Credits (-50)", True, f"Credits: {new_credits} -> {final_credits}")
                else:
                    self.log_result("Deduct Credits (-50)", False, f"Credits not properly deducted: {new_credits} -> {final_credits}")
            else:
                self.log_result("Deduct Credits (-50)", False, f"Status: {response.status_code}")
    
    def test_credit_based_reveal_system(self):
        """Test credit-based reveal system (payment transaction)"""
        print("\n🔍 TESTING CREDIT-BASED REVEAL SYSTEM")
        print("-" * 50)
        
        if not self.user_token:
            self.log_result("Credit Reveal System", False, "No user token available")
            return
            
        headers = self.get_auth_headers(self.user_token)
        
        # Get some profiles first
        search_filters = {"page": 1, "page_size": 5}
        response = self.make_request("POST", "/profiles/search", search_filters, headers=headers)
        if response.status_code != 200:
            self.log_result("Get Profiles for Reveal", False, f"Status: {response.status_code}")
            return
            
        data = response.json()
        profiles = data.get("profiles", [])
        if not profiles:
            self.log_result("Get Profiles for Reveal", False, "No profiles available")
            return
            
        profile_id = profiles[0].get("id")
        self.log_result("Get Profiles for Reveal", True, f"Found {len(profiles)} profiles for testing")
        
        # Get user's current credits
        me_response = self.make_request("GET", "/auth/me", headers=headers)
        if me_response.status_code != 200:
            self.log_result("Get Current Credits", False, "Could not get current user info")
            return
            
        original_credits = me_response.json().get("credits", 0)
        self.log_result("Get Current Credits", True, f"User has {original_credits} credits")
        
        # Test email reveal (costs 1 credit)
        reveal_data = {"profile_id": profile_id, "reveal_type": "email"}
        response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
        
        if response.status_code == 200:
            reveal_result = response.json()
            revealed_emails = reveal_result.get("emails", [])
            credits_used = reveal_result.get("credits_used", 0)
            
            if revealed_emails and any("***" not in email for email in revealed_emails):
                self.log_result("Email Reveal - Data Unmasked", True, f"Email revealed: {revealed_emails}")
                
                if credits_used == 1:
                    self.log_result("Email Reveal - Cost 1 Credit", True, f"Correctly charged 1 credit")
                    
                    # Verify credit deduction
                    me_response = self.make_request("GET", "/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        new_credits = me_response.json().get("credits", 0)
                        if new_credits == original_credits - 1:
                            self.log_result("Email Reveal - Credit Deduction", True, f"Credits: {original_credits} -> {new_credits}")
                        else:
                            self.log_result("Email Reveal - Credit Deduction", False, f"Credits not properly deducted: {original_credits} -> {new_credits}")
                else:
                    self.log_result("Email Reveal - Cost 1 Credit", False, f"Wrong credit cost: {credits_used}")
            else:
                self.log_result("Email Reveal - Data Unmasked", False, f"Email not properly revealed: {revealed_emails}")
        else:
            self.log_result("Email Reveal", False, f"Status: {response.status_code}")
            return
            
        # Test phone reveal (costs 3 credits)
        me_response = self.make_request("GET", "/auth/me", headers=headers)
        current_credits = me_response.json().get("credits", 0)
        
        if current_credits >= 3:
            reveal_data = {"reveal_type": "phone"}
            response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
            
            if response.status_code == 200:
                reveal_result = response.json()
                revealed_phones = reveal_result.get("phones", [])
                credits_used = reveal_result.get("credits_used", 0)
                
                if revealed_phones and any("***" not in phone for phone in revealed_phones):
                    self.log_result("Phone Reveal - Data Unmasked", True, f"Phone revealed: {revealed_phones}")
                    
                    if credits_used == 3:
                        self.log_result("Phone Reveal - Cost 3 Credits", True, f"Correctly charged 3 credits")
                        
                        # Verify credit deduction
                        me_response = self.make_request("GET", "/auth/me", headers=headers)
                        if me_response.status_code == 200:
                            final_credits = me_response.json().get("credits", 0)
                            if final_credits == current_credits - 3:
                                self.log_result("Phone Reveal - Credit Deduction", True, f"Credits: {current_credits} -> {final_credits}")
                            else:
                                self.log_result("Phone Reveal - Credit Deduction", False, f"Credits not properly deducted: {current_credits} -> {final_credits}")
                    else:
                        self.log_result("Phone Reveal - Cost 3 Credits", False, f"Wrong credit cost: {credits_used}")
                else:
                    self.log_result("Phone Reveal - Data Unmasked", False, f"Phone not properly revealed: {revealed_phones}")
            else:
                self.log_result("Phone Reveal", False, f"Status: {response.status_code}")
        else:
            self.log_result("Phone Reveal - Insufficient Credits", True, f"User has {current_credits} credits (need 3)")
            
        # Test revealing same contact again (should be free - no double charging)
        reveal_data = {"reveal_type": "email"}
        response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=headers)
        
        if response.status_code == 200:
            reveal_result = response.json()
            already_revealed = reveal_result.get("already_revealed", False)
            credits_used = reveal_result.get("credits_used", 0)
            
            if already_revealed and credits_used == 0:
                self.log_result("No Double Charging", True, "Already revealed contact returned free")
            else:
                self.log_result("No Double Charging", False, f"Double charged: already_revealed={already_revealed}, credits_used={credits_used}")
        else:
            self.log_result("No Double Charging", False, f"Status: {response.status_code}")
    
    def test_insufficient_credits_handling(self):
        """Test insufficient credits handling"""
        print("\n⚠️  TESTING INSUFFICIENT CREDITS HANDLING")
        print("-" * 50)
        
        if not self.admin_token:
            self.log_result("Insufficient Credits Test", False, "No admin token available")
            return
            
        # First, find a user and reduce their credits to 0
        admin_headers = self.get_auth_headers(self.admin_token)
        response = self.make_request("GET", "/users", headers=admin_headers)
        
        if response.status_code == 200:
            users = response.json()
            test_user = next((u for u in users if u.get("email") != "admin@leadgen.com"), None)
            
            if test_user:
                user_id = test_user.get("id")
                current_credits = test_user.get("credits", 0)
                
                # Deduct all credits
                credit_data = {"amount": -current_credits}
                response = self.make_request("POST", f"/users/{user_id}/credits", credit_data, headers=admin_headers)
                
                if response.status_code == 200:
                    self.log_result("Set User Credits to 0", True, f"Reduced credits from {current_credits} to 0")
                    
                    # Now try to reveal with insufficient credits using user token
                    if self.user_token:
                        user_headers = self.get_auth_headers(self.user_token)
                        
                        # Get a profile to reveal
                        search_filters = {"page": 1, "page_size": 1}
                        response = self.make_request("POST", "/profiles/search", search_filters, headers=user_headers)
                        
                        if response.status_code == 200:
                            profiles = response.json().get("profiles", [])
                            if profiles:
                                profile_id = profiles[0].get("id")
                                
                                # Try to reveal phone (costs 3 credits) with 0 credits
                                reveal_data = {"reveal_type": "phone"}
                                response = self.make_request("POST", f"/profiles/{profile_id}/reveal", reveal_data, headers=user_headers)
                                
                                if response.status_code == 400:
                                    error_detail = response.json().get("detail", "")
                                    if "insufficient" in error_detail.lower() or "credit" in error_detail.lower():
                                        self.log_result("Insufficient Credits Error", True, f"Proper error returned: {error_detail}")
                                    else:
                                        self.log_result("Insufficient Credits Error", False, f"Wrong error message: {error_detail}")
                                else:
                                    self.log_result("Insufficient Credits Error", False, f"Should return 400, got: {response.status_code}")
                            else:
                                self.log_result("Insufficient Credits Test", False, "No profiles available for testing")
                        else:
                            self.log_result("Insufficient Credits Test", False, "Could not get profiles")
                else:
                    self.log_result("Set User Credits to 0", False, f"Status: {response.status_code}")
            else:
                self.log_result("Insufficient Credits Test", False, "No test user found")
        else:
            self.log_result("Insufficient Credits Test", False, f"Could not get users: {response.status_code}")
    
    def test_plan_management(self):
        """Test plan management (subscription plans)"""
        print("\n📋 TESTING PLAN MANAGEMENT")
        print("-" * 50)
        
        # Test GET /api/plans (get all available plans)
        response = self.make_request("GET", "/plans")
        if response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list) and len(plans) >= 3:
                self.log_result("Get All Plans", True, f"Retrieved {len(plans)} plans")
                
                # Test GET /api/plans/{plan_id} (get specific plan details)
                plan_id = plans[0].get("id")
                if plan_id:
                    response = self.make_request("GET", f"/plans/{plan_id}")
                    if response.status_code == 200:
                        plan = response.json()
                        plan_name = plan.get("name")
                        plan_price = plan.get("price")
                        plan_credits = plan.get("credits_included")
                        
                        self.log_result("Get Plan Details", True, f"Plan: {plan_name}, Price: ${plan_price}, Credits: {plan_credits}")
                        
                        # Verify plan has pricing and credits
                        if plan_price and plan_credits:
                            self.log_result("Plan Pricing & Credits", True, f"Plan has proper pricing structure")
                        else:
                            self.log_result("Plan Pricing & Credits", False, f"Missing pricing or credits: price={plan_price}, credits={plan_credits}")
                    else:
                        self.log_result("Get Plan Details", False, f"Status: {response.status_code}")
            else:
                self.log_result("Get All Plans", False, f"Expected 3+ plans, got: {len(plans) if isinstance(plans, list) else 'invalid response'}")
        else:
            self.log_result("Get All Plans", False, f"Status: {response.status_code}")
    
    def test_health_check(self):
        """Test health check (verify Redis connected)"""
        print("\n🏥 TESTING HEALTH CHECK")
        print("-" * 50)
        
        response = self.make_request("GET", "/health")
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            database = data.get("database")
            redis = data.get("redis")
            
            if status == "healthy" and database == "connected" and redis == "connected":
                self.log_result("Health Check", True, "All services connected (Redis, MongoDB)")
            else:
                self.log_result("Health Check", False, f"Services not healthy: status={status}, db={database}, redis={redis}")
        else:
            self.log_result("Health Check", False, f"Status: {response.status_code}")
    
    def run_production_readiness_tests(self):
        """Run all production readiness tests"""
        print("🎯 PRODUCTION READINESS CHECK - Credit System & Payment Endpoints")
        print("=" * 80)
        
        # Run all test categories
        self.test_health_check()
        self.test_authentication_flow()
        self.test_credit_management_endpoints()
        self.test_credit_based_reveal_system()
        self.test_insufficient_credits_handling()
        self.test_plan_management()
        
        print("\n" + "=" * 80)
        print("📊 PRODUCTION READINESS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results.values() if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Check critical requirements
        critical_tests = [
            "Super Admin Login",
            "Regular User Login", 
            "JWT Token Validation",
            "View All Users - Admin Credits",
            "View All Users - User Credits",
            "Add Credits (+100)",
            "Email Reveal - Cost 1 Credit",
            "Phone Reveal - Cost 3 Credits",
            "No Double Charging",
            "Get All Plans",
            "Health Check"
        ]
        
        critical_passed = sum(1 for test in critical_tests if self.test_results.get(test, {}).get("success", False))
        
        print(f"\n🎯 CRITICAL REQUIREMENTS: {critical_passed}/{len(critical_tests)} PASSED")
        
        if critical_passed == len(critical_tests):
            print("✅ PRODUCTION READY - All critical payment system requirements met!")
        else:
            print("❌ NOT PRODUCTION READY - Critical requirements failed")
            
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['details']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = ProductionReadinessTest()
    results = tester.run_production_readiness_tests()