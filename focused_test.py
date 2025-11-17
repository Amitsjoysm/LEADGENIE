#!/usr/bin/env python3
"""
Focused test for new bulk upload template downloads and profile search filters
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

class FocusedTester:
    def __init__(self):
        self.base_url = "https://advanced-filters.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = {}
        
        # Test credentials
        self.admin_creds = {
            "email": "admin@leadgenpro.com",
            "password": "Admin123!"
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
    
    def login_admin(self):
        """Login as admin and get token"""
        try:
            response = self.make_request("POST", "/auth/login", self.admin_creds)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    self.log_result("Admin Login", True, "Admin token obtained")
                    return True
                else:
                    self.log_result("Admin Login", False, f"No token in response: {data}")
            else:
                self.log_result("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
        return False
    
    def login_user(self):
        """Login as regular user and get token"""
        try:
            response = self.make_request("POST", "/auth/login", self.user_creds)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.user_token = data["access_token"]
                    self.log_result("User Login", True, "User token obtained")
                    return True
                else:
                    self.log_result("User Login", False, f"No token in response: {data}")
            else:
                self.log_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("User Login", False, f"Exception: {str(e)}")
        return False
    
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
    
    def run_focused_tests(self):
        """Run focused tests for new functionality"""
        print("🚀 Starting Focused Tests for New Functionality")
        print("=" * 60)
        
        # Login first
        admin_login_success = self.login_admin()
        user_login_success = self.login_user()
        
        if admin_login_success:
            # Test template downloads
            self.test_bulk_upload_template_downloads()
        
        if user_login_success:
            # Test new profile search filters
            self.test_profile_search_new_filters()
        
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
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
    tester = FocusedTester()
    results = tester.run_focused_tests()