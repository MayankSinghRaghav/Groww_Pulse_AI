"""
Test script for Gmail OAuth 2.0 integration
Run this to test the complete OAuth flow
"""

import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_server_running():
    """Check if the backend server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Backend server is running")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Backend server is not running!")
        print("\nStart the server with:")
        print("  cd backend")
        print("  python mcp_server.py")
        return False

def test_oauth_status():
    """Check current OAuth authentication status"""
    print_section("Step 1: Check OAuth Status")
    
    response = requests.get(f"{BASE_URL}/oauth/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get("authenticated", False)

def test_authorization_url():
    """Get the OAuth authorization URL"""
    print_section("Step 2: Get Authorization URL")
    
    print("\n⚠️  IMPORTANT: You need to complete authorization in your browser")
    print("\nCopy and paste this URL into your browser:")
    print(f"\n{BASE_URL}/oauth/authorize\n")
    
    print("Or click this link (if your terminal supports it):")
    print(f"\n👉  {BASE_URL}/oauth/authorize  👈\n")
    
    print("After you grant permission, you'll be redirected to the callback URL.")
    print("The server will handle the token exchange automatically.\n")
    
    response = input("Have you completed the authorization? (yes/no): ").strip().lower()
    return response == 'yes'

def test_oauth_status_after_auth():
    """Check OAuth status after authorization"""
    print_section("Step 3: Verify Authorization")
    
    response = requests.get(f"{BASE_URL}/oauth/status")
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get("authenticated"):
        print("\n✓ OAuth authorization successful!")
        print(f"✓ Authenticated as: {data['user']['email']}")
        return True
    else:
        print("\n✗ Authorization not complete or failed")
        return False

def test_send_email():
    """Send a test email"""
    print_section("Step 4: Send Test Email")
    
    response = requests.post(f"{BASE_URL}/oauth/test-email")
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("status") == "success":
            print("\n✓ Test email sent successfully!")
            print("✓ Check your inbox for the test email")
            return True
        else:
            print(f"\n✗ Test email failed: {data.get('message')}")
            return False
    except:
        print(f"Response: {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("  Kuvera Weekly Pulse - Gmail OAuth 2.0 Test")
    print("="*60)
    
    # Step 0: Check server
    if not check_server_running():
        return
    
    # Step 1: Check current status
    is_authenticated = test_oauth_status()
    
    if is_authenticated:
        print("\n✓ You already have valid OAuth credentials!")
        response = input("Do you want to send a test email? (yes/no): ").strip().lower()
        if response == 'yes':
            test_send_email()
        return
    
    # Step 2: Get authorization
    print("\nYou need to complete OAuth authorization.")
    authorized = test_authorization_url()
    
    if not authorized:
        print("\n✗ Authorization not completed. Please run this script again after authorizing.")
        return
    
    # Step 3: Verify authorization
    if not test_oauth_status_after_auth():
        print("\n✗ Authorization verification failed.")
        print("Please check the server logs for details.")
        return
    
    # Step 4: Send test email
    test_send_email()
    
    # Summary
    print_section("Summary")
    print("✅ OAuth 2.0 integration is working correctly!")
    print("\nYou can now:")
    print("  1. Run the weekly pulse to generate reports")
    print("  2. Send stakeholder emails with PDF attachments")
    print("  3. Use the frontend dashboard to manage emails")
    print("\nOAuth Endpoints:")
    print(f"  • Check Status:  {BASE_URL}/oauth/status")
    print(f"  • Authorize:     {BASE_URL}/oauth/authorize")
    print(f"  • Logout:        {BASE_URL}/oauth/logout (POST)")
    print(f"  • Test Email:    {BASE_URL}/oauth/test-email (POST)")
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
