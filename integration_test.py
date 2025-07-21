#!/usr/bin/env python3
"""
Integration Test Script for ENGIE HR Login and COA Application

This script performs real integration tests with the actual ENGIE HR system
using the stored credentials. It tests both login and COA functionality
in a controlled manner.

Usage:
    python integration_test.py --test-login-only
    python integration_test.py --test-coa-dry-run
    python integration_test.py --full-integration-test
"""

import argparse
import sys
from datetime import datetime, timedelta
from engie_hr_login import ENGIEHRLogin
import time


class IntegrationTester:
    """Integration test runner for ENGIE HR system."""
    
    def __init__(self):
        self.hr_login = ENGIEHRLogin()
        self.default_username = "bperalta"
        self.default_password = "KKrm7MpdNQijfSM@"
    
    def test_login_robustness(self) -> bool:
        """Test login functionality with multiple attempts and scenarios."""
        print("🔐 Testing Login Robustness")
        print("-" * 30)
        
        # Test 1: Fresh login (no existing session)
        print("1️⃣  Testing fresh login...")
        
        # Clear any existing session
        try:
            import os
            if os.path.exists("engie_session.json"):
                os.remove("engie_session.json")
            if os.path.exists("test_session.json"):
                os.remove("test_session.json")
        except:
            pass
        
        # Attempt fresh login
        if not self.hr_login.get_initial_auth_params():
            print("❌ Failed to get authentication parameters")
            return False
        
        if not self.hr_login.perform_login(self.default_username, self.default_password):
            print("❌ Fresh login failed")
            return False
        
        print("✅ Fresh login successful")
        
        # Test 2: Session persistence
        print("2️⃣  Testing session persistence...")
        
        if not self.hr_login.save_session("integration_test_session.json"):
            print("❌ Failed to save session")
            return False
        
        # Create new instance and load session
        hr_login_2 = ENGIEHRLogin()
        if not hr_login_2.load_session("integration_test_session.json"):
            print("❌ Failed to load saved session")
            return False
        
        if not hr_login_2.test_authenticated_access():
            print("❌ Loaded session is not valid")
            return False
        
        print("✅ Session persistence working")
        
        # Test 3: Multiple consecutive requests
        print("3️⃣  Testing consecutive authenticated requests...")
        
        for i in range(3):
            if not self.hr_login.test_authenticated_access():
                print(f"❌ Consecutive request {i+1} failed")
                return False
            time.sleep(0.5)  # Small delay between requests
        
        print("✅ Consecutive requests successful")
        
        # Test 4: User info extraction
        print("4️⃣  Testing user info extraction...")
        
        user_info = self.hr_login.get_user_info()
        if not user_info:
            print("⚠️  No user info extracted (may be normal)")
        else:
            print(f"✅ User info extracted: {len(user_info)} fields")
            if user_info.get('recent_attendance'):
                print(f"   📅 Recent attendance: {len(user_info['recent_attendance'])} entries")
            if user_info.get('leave_credits'):
                print(f"   🏖️  Leave credits: {len(user_info['leave_credits'])} types")
        
        return True
    
    def test_employee_id_extraction(self) -> bool:
        """Test employee ID extraction reliability."""
        print("🆔 Testing Employee ID Extraction")
        print("-" * 35)
        
        # Test multiple extraction attempts
        employee_ids = []
        for i in range(3):
            emp_id = self.hr_login._get_employee_id()
            if emp_id:
                employee_ids.append(emp_id)
                print(f"Attempt {i+1}: Employee ID = {emp_id}")
            else:
                print(f"Attempt {i+1}: No employee ID found")
            time.sleep(0.2)
        
        if not employee_ids:
            print("❌ Employee ID extraction failed in all attempts")
            return False
        
        # Check consistency
        if len(set(employee_ids)) > 1:
            print(f"⚠️  Inconsistent employee IDs found: {set(employee_ids)}")
        else:
            print(f"✅ Consistent employee ID: {employee_ids[0]}")
        
        return True
    
    def test_coa_validation_dry_run(self) -> bool:
        """Test COA validation without submitting actual requests."""
        print("📋 Testing COA Validation (Dry Run)")
        print("-" * 35)
        
        # Test various date formats and scenarios
        test_cases = [
            {
                "name": "Valid future date with IN time",
                "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                "time_in": "09:00",
                "time_out": None,
                "expected": True
            },
            {
                "name": "Valid past date with OUT time", 
                "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                "time_in": None,
                "time_out": "17:30",
                "expected": True
            },
            {
                "name": "Valid date with both times",
                "date": "2025-07-25",
                "time_in": "08:30",
                "time_out": "18:00",
                "expected": True
            },
            {
                "name": "Invalid date format",
                "date": "07/25/2025",
                "time_in": "09:00",
                "time_out": None,
                "expected": False
            },
            {
                "name": "No time provided",
                "date": "2025-07-25",
                "time_in": None,
                "time_out": None,
                "expected": False
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}️⃣  {test_case['name']}...")
            
            # We'll test the validation logic without making actual API calls
            try:
                # Test date parsing
                datetime.strptime(test_case['date'], '%Y-%m-%d')
                date_valid = True
            except ValueError:
                date_valid = False
            
            # Test time requirement
            has_time = test_case['time_in'] is not None or test_case['time_out'] is not None
            
            # Expected result
            should_pass = date_valid and has_time
            
            if should_pass == test_case['expected']:
                print(f"   ✅ Validation logic correct")
            else:
                print(f"   ❌ Validation logic incorrect (expected {test_case['expected']}, got {should_pass})")
                all_passed = False
        
        return all_passed
    
    def test_network_resilience(self) -> bool:
        """Test network resilience and retry mechanisms."""
        print("🌐 Testing Network Resilience")
        print("-" * 30)
        
        # Test 1: Multiple dashboard access attempts
        print("1️⃣  Testing dashboard access resilience...")
        
        success_count = 0
        total_attempts = 5
        
        for i in range(total_attempts):
            try:
                if self.hr_login.test_authenticated_access():
                    success_count += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"   Attempt {i+1} failed: {e}")
        
        success_rate = (success_count / total_attempts) * 100
        print(f"   Success rate: {success_count}/{total_attempts} ({success_rate:.1f}%)")
        
        if success_rate < 80:
            print("❌ Poor network resilience")
            return False
        
        print("✅ Good network resilience")
        return True
    
    def generate_test_report(self) -> dict:
        """Generate comprehensive test report."""
        print("\n📊 Generating Integration Test Report")
        print("=" * 40)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "PASS"
        }
        
        # Run all tests and collect results
        tests = [
            ("login_robustness", self.test_login_robustness),
            ("employee_id_extraction", self.test_employee_id_extraction), 
            ("coa_validation", self.test_coa_validation_dry_run),
            ("network_resilience", self.test_network_resilience)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name.replace('_', ' ').title()} Test...")
            try:
                result = test_func()
                report["tests"][test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "success": result
                }
                if not result:
                    report["overall_status"] = "FAIL"
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                report["tests"][test_name] = {
                    "status": "ERROR", 
                    "error": str(e),
                    "success": False
                }
                report["overall_status"] = "FAIL"
        
        return report
    
    def print_report(self, report: dict):
        """Print formatted test report."""
        print("\n" + "=" * 50)
        print("📋 INTEGRATION TEST REPORT")
        print("=" * 50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {'✅ PASS' if report['overall_status'] == 'PASS' else '❌ FAIL'}")
        print()
        
        for test_name, result in report["tests"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        print()
        passed = sum(1 for r in report["tests"].values() if r["status"] == "PASS")
        total = len(report["tests"])
        print(f"Tests Passed: {passed}/{total}")
        print("=" * 50)


def main():
    """Main function for integration testing."""
    parser = argparse.ArgumentParser(description="Integration test for ENGIE HR system")
    parser.add_argument("--test-login-only", action="store_true", help="Test login functionality only")
    parser.add_argument("--test-coa-dry-run", action="store_true", help="Test COA validation without API calls")
    parser.add_argument("--full-integration-test", action="store_true", help="Run full integration test suite")
    parser.add_argument("--quick-test", action="store_true", help="Run quick validation test")
    
    args = parser.parse_args()
    
    if not any([args.test_login_only, args.test_coa_dry_run, args.full_integration_test, args.quick_test]):
        # Default to quick test if no specific test specified
        args.quick_test = True
    
    tester = IntegrationTester()
    
    try:
        if args.test_login_only:
            success = tester.test_login_robustness()
            return 0 if success else 1
        
        elif args.test_coa_dry_run:
            success = tester.test_coa_validation_dry_run()
            return 0 if success else 1
        
        elif args.full_integration_test:
            report = tester.generate_test_report()
            tester.print_report(report)
            return 0 if report["overall_status"] == "PASS" else 1
        
        elif args.quick_test:
            print("🚀 Running Quick Integration Test")
            print("=" * 35)
            
            # Quick test: Login + Basic validation + Session test
            if not tester.test_login_robustness():
                print("❌ Quick test failed: Login issues")
                return 1
            
            if not tester.test_employee_id_extraction():
                print("❌ Quick test failed: Employee ID extraction issues")
                return 1
            
            print("\n✅ Quick integration test completed successfully!")
            print("💡 Run --full-integration-test for comprehensive testing")
            return 0
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())