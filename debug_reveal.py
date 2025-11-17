#!/usr/bin/env python3
"""
Debug Credit Reveal Functionality
"""

import requests
import json

def debug_reveal():
    """Debug the credit reveal process"""
    base_url = "https://domain-relation.preview.emergentagent.com/api"
    
    # Login as user
    login_data = {"email": "user1@example.com", "password": "password123"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user info
    response = requests.get(f"{base_url}/auth/me", headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print(f"User: {user_info['email']}")
        print(f"Initial credits: {user_info['credits']}")
    else:
        print(f"Failed to get user info: {response.status_code}")
        return
    
    # Get a profile
    search_data = {"skip": 0, "limit": 1}
    response = requests.post(f"{base_url}/profiles/search", json=search_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Profile search failed: {response.status_code} - {response.text}")
        return
        
    profiles = response.json().get("profiles", [])
    if not profiles:
        print("No profiles found")
        return
        
    profile = profiles[0]
    profile_id = profile["id"]
    print(f"Profile ID: {profile_id}")
    print(f"Profile emails (masked): {profile.get('emails', [])}")
    
    # Try to reveal email
    reveal_data = {"profile_id": profile_id, "reveal_type": "email"}
    response = requests.post(f"{base_url}/profiles/{profile_id}/reveal", json=reveal_data, headers=headers)
    
    print(f"\nReveal response status: {response.status_code}")
    print(f"Reveal response: {response.text}")
    
    if response.status_code == 200:
        reveal_result = response.json()
        print(f"Revealed emails: {reveal_result.get('emails', [])}")
        print(f"Credits used: {reveal_result.get('credits_used', 0)}")
        print(f"Credits remaining: {reveal_result.get('credits_remaining', 0)}")
        print(f"Already revealed: {reveal_result.get('already_revealed', False)}")
    
    # Check user credits after reveal
    response = requests.get(f"{base_url}/auth/me", headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print(f"Final credits: {user_info['credits']}")
    else:
        print(f"Failed to get final user info: {response.status_code}")

if __name__ == "__main__":
    debug_reveal()