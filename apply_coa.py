#!/usr/bin/env python3
"""
Quick COA Application Script for ENGIE HR Hub

Usage:
    python apply_coa.py --date 2025-07-20 --in 09:32
    python apply_coa.py --date 2025-07-20 --out 17:30
    python apply_coa.py --date 2025-07-20 --in 09:32 --out 17:30
"""

import argparse
from engie_hr_login import ENGIEHRLogin
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Apply for Certificate of Attendance")
    parser.add_argument("--date", "-d", required=True, help="Date in YYYY-MM-DD format (e.g., 2025-07-20)")
    parser.add_argument("--in", "-i", dest="time_in", help="Clock-in time in HH:MM format (e.g., 09:32)")
    parser.add_argument("--out", "-o", dest="time_out", help="Clock-out time in HH:MM format (e.g., 17:30)")
    parser.add_argument("--reason", "-r", default="forgot to in/out", help="Reason for COA application")
    parser.add_argument("--type", "-t", default="forgot to in/out", help="Type description for COA")
    
    args = parser.parse_args()
    
    # Validate that at least one time is provided
    if not args.time_in and not args.time_out:
        print("❌ You must specify either --in, --out, or both")
        return 1
    
    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-07-20)")
        return 1
    
    # Initialize HR login
    hr_login = ENGIEHRLogin()
    
    # Try to load existing session
    if not hr_login.load_session('test_session.json'):
        print("❌ No valid session found. Please run test_login.py first to establish a session.")
        return 1
    
    # Test authenticated access
    if not hr_login.test_authenticated_access():
        print("❌ Session expired. Please run test_login.py to re-authenticate.")
        return 1
    
    print("🎯 Applying COA...")
    print(f"📅 Date: {args.date}")
    if args.time_in:
        print(f"📥 IN: {args.time_in}")
    if args.time_out:
        print(f"📤 OUT: {args.time_out}")
    
    # Apply COA
    result = hr_login.apply_coa(
        target_date=args.date,
        time_in=args.time_in,
        time_out=args.time_out,
        reason=args.reason,
        type_other=args.type
    )
    
    if result:
        print("🎉 COA application submitted successfully!")
        return 0
    else:
        print("❌ COA application failed")
        return 1

if __name__ == "__main__":
    exit(main())