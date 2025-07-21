#!/usr/bin/env python3
"""
Test script for ENGIE HR Login functionality

Usage:
    python test_login.py --username your_username --password your_password
    
Or run interactively:
    python test_login.py
"""

import argparse
import getpass
from engie_hr_login import ENGIEHRLogin


def test_login_flow(username: str, password: str, verbose: bool = True):
    """
    Test the complete login flow and return success status.
    
    Args:
        username: Login username
        password: Login password  
        verbose: Whether to print detailed output
        
    Returns:
        bool: True if login and authentication test successful
    """
    if verbose:
        print("🧪 Testing ENGIE HR Login Flow")
        print("=" * 35)
    
    try:
        # Initialize login handler
        hr_login = ENGIEHRLogin()
        
        # Step 1: Get authentication parameters
        if verbose:
            print("1️⃣  Testing authentication parameter extraction...")
        
        if not hr_login.get_initial_auth_params():
            if verbose:
                print("❌ Failed to get authentication parameters")
            return False
        
        if verbose:
            print("✅ Authentication parameters extracted successfully")
        
        # Step 2: Perform login
        if verbose:
            print("2️⃣  Testing login submission...")
        
        if not hr_login.perform_login(username, password):
            if verbose:
                print("❌ Login failed")
            return False
        
        if verbose:
            print("✅ Login successful")
        
        # Step 3: Test authenticated access
        if verbose:
            print("3️⃣  Testing authenticated access...")
        
        if not hr_login.test_authenticated_access():
            if verbose:
                print("❌ Authenticated access test failed")
            return False
        
        if verbose:
            print("✅ Authenticated access verified")
        
        # Step 4: Extract and display user info
        if verbose:
            print("4️⃣  Extracting user information...")
        
        user_info = hr_login.get_user_info()
        
        if verbose:
            if user_info.get('recent_attendance'):
                print("📅 Recent Attendance Found:")
                for entry in user_info['recent_attendance'][:3]:
                    print(f"   {entry['date']} - {entry['status']} at {entry['time']}")
            
            if user_info.get('leave_credits'):
                print("🏖️  Leave Credits Found:")
                for leave_type, balance in user_info['leave_credits'].items():
                    print(f"   {leave_type}: {balance}")
        
        # Step 5: Test session persistence
        if verbose:
            print("5️⃣  Testing session persistence...")
        
        if hr_login.save_session("test_session.json"):
            if verbose:
                print("✅ Session saved successfully")
        
        if verbose:
            print("\n🎉 All tests passed!")
            print("🔐 Login flow is working correctly")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Test failed with error: {e}")
        return False


def interactive_test():
    """Run interactive test with user input."""
    print("🔐 ENGIE HR Login Interactive Test")
    print("=" * 35)
    
    username = input("👤 Enter username: ").strip()
    if not username:
        print("❌ Username is required")
        return False
    
    password = getpass.getpass("🔑 Enter password: ").strip()
    if not password:
        print("❌ Password is required")
        return False
    
    return test_login_flow(username, password)


def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description="Test ENGIE HR login functionality")
    parser.add_argument("--username", "-u", help="Login username")
    parser.add_argument("--password", "-p", help="Login password")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (minimal output)")
    
    args = parser.parse_args()
    
    if args.username and args.password:
        # Use provided credentials
        success = test_login_flow(args.username, args.password, verbose=not args.quiet)
    else:
        # Use default credentials if no arguments provided
        default_username = "bperalta"
        default_password = "KKrm7MpdNQijfSM@"
        
        if args.quiet:
            success = test_login_flow(default_username, default_password, verbose=False)
        else:
            print("🔐 Using default credentials...")
            success = test_login_flow(default_username, default_password, verbose=True)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())