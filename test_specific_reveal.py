#!/usr/bin/env python3
"""
Test Credit Reveal with Specific Unrevealed Profile
"""

import requests
import json

def test_specific_reveal():
    """Test credit reveal with a specific profile that hasn't been revealed yet"""
    base_url = "https://endpoint-verify-1.preview.emergentagent.com/api"
    
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
        initial_credits = user_info['credits']
    else:
        print(f"Failed to get user info: {response.status_code}")
        return
    
    # Use the specific unrevealed profile ID
    profile_id = "d8291991-eda5-4248-99c0-e56546b8a9a1"
    print(f"Testing with profile ID: {profile_id}")
    
    # Get profile details first
    response = requests.get(f"{base_url}/profiles/{profile_id}", headers=headers)
    if response.status_code == 200:
        profile = response.json()
        print(f"Profile: {profile.get('first_name')} {profile.get('last_name')}")
        print(f"Profile emails (masked): {profile.get('emails', [])}")
    else:
        print(f"Failed to get profile: {response.status_code} - {response.text}")
        return
    
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
        
        # Check if credits were actually deducted
        expected_credits = initial_credits - reveal_result.get('credits_used', 0)
        actual_credits = reveal_result.get('credits_remaining', 0)
        
        if actual_credits == expected_credits and reveal_result.get('credits_used', 0) > 0:
            print(f"✅ Credit deduction working: {initial_credits} -> {actual_credits}")
        else:
            print(f"❌ Credit deduction issue: Expected {expected_credits}, got {actual_credits}")
    else:
        print(f"❌ Reveal failed: {response.status_code} - {response.text}")
    
    # Check user credits after reveal
    response = requests.get(f"{base_url}/auth/me", headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print(f"Final credits from /auth/me: {user_info['credits']}")
    else:
        print(f"Failed to get final user info: {response.status_code}")

if __name__ == "__main__":
    test_specific_reveal()