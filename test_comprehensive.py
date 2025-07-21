#!/usr/bin/env python3
"""
Comprehensive Test Suite for ENGIE HR Login and COA Functionality

This test suite covers:
1. Login edge cases and robustness testing
2. COA input validation and error handling
3. Session management scenarios
4. Network error simulation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
from engie_hr_login import ENGIEHRLogin
import json
import tempfile
import os
from datetime import datetime, timedelta


class TestLoginRobustness(unittest.TestCase):
    """Test login functionality edge cases and error handling."""
    
    def setUp(self):
        self.hr_login = ENGIEHRLogin()
    
    def test_network_failure_initial_request(self):
        """Test handling of network failures during initial auth params."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            result = self.hr_login.get_initial_auth_params()
            self.assertFalse(result)
    
    def test_http_error_initial_request(self):
        """Test handling of HTTP errors during initial auth params."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            result = self.hr_login.get_initial_auth_params()
            self.assertFalse(result)
    
    def test_invalid_redirect_chain(self):
        """Test handling of invalid redirect chains."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://invalid-domain.com/login"
            mock_get.return_value = mock_response
            result = self.hr_login.get_initial_auth_params()
            self.assertFalse(result)
    
    def test_missing_login_form(self):
        """Test handling of missing login form in SSO page."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://sso.sprout.ph/realms/engie/auth"
            mock_response.text = "<html><body>No form here</body></html>"
            mock_get.return_value = mock_response
            result = self.hr_login.get_initial_auth_params()
            self.assertFalse(result)
    
    def test_malformed_login_form(self):
        """Test handling of login form without action attribute."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://sso.sprout.ph/realms/engie/auth"
            mock_response.text = '<html><body><form id="kc-form-login">No action</form></body></html>'
            mock_get.return_value = mock_response
            result = self.hr_login.get_initial_auth_params()
            self.assertFalse(result)
    
    def test_login_network_error(self):
        """Test login network error handling."""
        self.hr_login.login_action_url = "https://test.com/login"
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Network error")
            result = self.hr_login.perform_login("test", "test")
            self.assertFalse(result)
    
    def test_login_http_error(self):
        """Test login HTTP error handling."""
        self.hr_login.login_action_url = "https://test.com/login"
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            result = self.hr_login.perform_login("test", "test")
            self.assertFalse(result)
    
    def test_invalid_credentials_error_message(self):
        """Test handling of invalid credentials with error message."""
        self.hr_login.login_action_url = "https://test.com/login"
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '''
            <html><body>
                <span class="kc-feedback-text">Invalid username or password.</span>
            </body></html>
            '''
            mock_post.return_value = mock_response
            result = self.hr_login.perform_login("invalid", "invalid")
            self.assertFalse(result)
    
    def test_missing_form_post_response(self):
        """Test handling of missing form_post in successful login."""
        self.hr_login.login_action_url = "https://test.com/login"
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>No form here</body></html>"
            mock_post.return_value = mock_response
            result = self.hr_login.perform_login("test", "test")
            self.assertFalse(result)
    
    def test_successful_login_flow(self):
        """Test complete successful login flow."""
        self.hr_login.login_action_url = "https://test.com/login"
        
        # Mock login response with form_post
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = '''
        <html><body>
            <form action="https://engie.hrhub.ph/">
                <input name="code" value="test-code"/>
                <input name="id_token" value="test-token"/>
                <input name="state" value="test-state"/>
            </form>
        </body></html>
        '''
        
        # Mock final redirect to dashboard
        final_response = Mock()
        final_response.status_code = 200
        final_response.url = "https://engie.hrhub.ph/EmployeeDashboard.aspx"
        
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_post.side_effect = [login_response, final_response]
            result = self.hr_login.perform_login("valid", "valid")
            self.assertTrue(result)


class TestSessionManagement(unittest.TestCase):
    """Test session persistence and management."""
    
    def setUp(self):
        self.hr_login = ENGIEHRLogin()
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = os.path.join(self.temp_dir, "test_session.json")
    
    def tearDown(self):
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
        os.rmdir(self.temp_dir)
    
    def test_save_session_success(self):
        """Test successful session saving."""
        self.hr_login.session.cookies.set('test_cookie', 'test_value')
        result = self.hr_login.save_session(self.session_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.session_file))
    
    def test_save_session_permission_error(self):
        """Test session saving with permission errors."""
        invalid_path = "/root/cannot_write_here.json"
        result = self.hr_login.save_session(invalid_path)
        self.assertFalse(result)
    
    def test_load_session_success(self):
        """Test successful session loading."""
        # Create test session file
        session_data = {
            "cookies": {"test_cookie": "test_value"},
            "headers": {"User-Agent": "test"}
        }
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)
        
        result = self.hr_login.load_session(self.session_file)
        self.assertTrue(result)
        self.assertEqual(self.hr_login.session.cookies.get('test_cookie'), 'test_value')
    
    def test_load_session_file_not_found(self):
        """Test loading non-existent session file."""
        result = self.hr_login.load_session("nonexistent.json")
        self.assertFalse(result)
    
    def test_load_session_invalid_json(self):
        """Test loading corrupted session file."""
        with open(self.session_file, 'w') as f:
            f.write("invalid json content")
        
        result = self.hr_login.load_session(self.session_file)
        self.assertFalse(result)
    
    def test_authenticated_access_success(self):
        """Test successful authenticated access check."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>Employee Dashboard</body></html>"
            mock_get.return_value = mock_response
            result = self.hr_login.test_authenticated_access()
            self.assertTrue(result)
    
    def test_authenticated_access_failure(self):
        """Test failed authenticated access check."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response
            result = self.hr_login.test_authenticated_access()
            self.assertFalse(result)


class TestCOAValidation(unittest.TestCase):
    """Test COA input validation and error handling without actual API calls."""
    
    def setUp(self):
        self.hr_login = ENGIEHRLogin()
        # Mock authenticated session
        self.hr_login.dashboard_cookies = {"session": "test"}
    
    def test_coa_no_time_provided(self):
        """Test COA with neither IN nor OUT time provided."""
        result = self.hr_login.apply_coa("2025-07-20")
        self.assertFalse(result)
    
    def test_coa_invalid_date_format(self):
        """Test COA with invalid date formats."""
        invalid_dates = ["07-20-2025", "2025/07/20", "20-07-2025", "invalid"]
        for date in invalid_dates:
            with self.subTest(date=date):
                result = self.hr_login.apply_coa(date, time_in="09:00")
                self.assertFalse(result)
    
    def test_coa_valid_date_formats(self):
        """Test COA with valid date format."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=None):
            # This should pass date validation but fail on employee ID
            result = self.hr_login.apply_coa("2025-07-20", time_in="09:00")
            self.assertFalse(result)
    
    def test_coa_in_time_only(self):
        """Test COA with only IN time."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                # Mock validation response
                validation_response = Mock()
                validation_response.status_code = 200
                # Mock submit response  
                submit_response = Mock()
                submit_response.status_code = 200
                submit_response.json.return_value = {'d': {'IsSuccess': True, 'ID': 123}}
                mock_post.side_effect = [validation_response, submit_response]
                
                result = self.hr_login.apply_coa("2025-07-20", time_in="09:32")
                self.assertTrue(result)
    
    def test_coa_out_time_only(self):
        """Test COA with only OUT time."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                validation_response = Mock()
                validation_response.status_code = 200
                submit_response = Mock()
                submit_response.status_code = 200
                submit_response.json.return_value = {'d': {'IsSuccess': True, 'ID': 123}}
                mock_post.side_effect = [validation_response, submit_response]
                
                result = self.hr_login.apply_coa("2025-07-20", time_out="17:30")
                self.assertTrue(result)
    
    def test_coa_both_times(self):
        """Test COA with both IN and OUT times."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                validation_response = Mock()
                validation_response.status_code = 200
                submit_response = Mock()
                submit_response.status_code = 200
                submit_response.json.return_value = {'d': {'IsSuccess': True, 'ID': 123}}
                mock_post.side_effect = [validation_response, submit_response]
                
                result = self.hr_login.apply_coa("2025-07-20", time_in="09:32", time_out="17:30")
                self.assertTrue(result)
    
    def test_coa_validation_failure(self):
        """Test COA validation step failure."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                validation_response = Mock()
                validation_response.status_code = 400
                validation_response.text = "Validation failed"
                mock_post.return_value = validation_response
                
                result = self.hr_login.apply_coa("2025-07-20", time_in="09:32")
                self.assertFalse(result)
    
    def test_coa_submission_failure(self):
        """Test COA submission step failure."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                validation_response = Mock()
                validation_response.status_code = 200
                submission_response = Mock()
                submission_response.status_code = 500
                submission_response.text = "Submission failed"
                mock_post.side_effect = [validation_response, submission_response]
                
                result = self.hr_login.apply_coa("2025-07-20", time_in="09:32")
                self.assertFalse(result)
    
    def test_coa_network_error_validation(self):
        """Test COA network error during validation."""
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                mock_post.side_effect = requests.ConnectionError("Network error")
                
                result = self.hr_login.apply_coa("2025-07-20", time_in="09:32")
                self.assertFalse(result)


class TestEmployeeIDExtraction(unittest.TestCase):
    """Test employee ID extraction robustness."""
    
    def setUp(self):
        self.hr_login = ENGIEHRLogin()
    
    def test_employee_id_from_javascript(self):
        """Test extracting employee ID from JavaScript variables."""
        html_content = '''
        <html><body>
            <script>
                var EmployeeID = 6033;
                var userInfo = {name: "Test"};
            </script>
        </body></html>
        '''
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            employee_id = self.hr_login._get_employee_id()
            self.assertEqual(employee_id, 6033)
    
    def test_employee_id_from_hidden_input(self):
        """Test extracting employee ID from hidden input fields."""
        html_content = '''
        <html><body>
            <input type="hidden" name="employee_id" value="6033"/>
            <input type="hidden" name="other" value="test"/>
        </body></html>
        '''
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            employee_id = self.hr_login._get_employee_id()
            self.assertEqual(employee_id, 6033)
    
    def test_employee_id_from_data_attribute(self):
        """Test extracting employee ID from data attributes."""
        html_content = '''
        <html><body>
            <div data-employee-id="6033" class="user-info">User Info</div>
        </body></html>
        '''
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            employee_id = self.hr_login._get_employee_id()
            self.assertEqual(employee_id, 6033)
    
    def test_employee_id_not_found(self):
        """Test when employee ID cannot be found."""
        html_content = '''
        <html><body>
            <div>No employee ID here</div>
        </body></html>
        '''
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            employee_id = self.hr_login._get_employee_id()
            self.assertIsNone(employee_id)
    
    def test_employee_id_network_error(self):
        """Test employee ID extraction with network error."""
        with patch.object(self.hr_login.session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            employee_id = self.hr_login._get_employee_id()
            self.assertIsNone(employee_id)


class TestEdgeCases(unittest.TestCase):
    """Test various edge cases and boundary conditions."""
    
    def setUp(self):
        self.hr_login = ENGIEHRLogin()
    
    def test_empty_credentials(self):
        """Test login with empty credentials."""
        self.hr_login.login_action_url = "https://test.com/login"
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<span class="kc-feedback-text">Username is required</span>'
            mock_post.return_value = mock_response
            
            result = self.hr_login.perform_login("", "")
            self.assertFalse(result)
    
    def test_special_characters_in_credentials(self):
        """Test login with special characters in credentials."""
        self.hr_login.login_action_url = "https://test.com/login"
        
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = '''
        <form action="https://engie.hrhub.ph/">
            <input name="code" value="test"/>
        </form>
        '''
        
        final_response = Mock()
        final_response.status_code = 200
        final_response.url = "https://engie.hrhub.ph/EmployeeDashboard.aspx"
        
        with patch.object(self.hr_login.session, 'post') as mock_post:
            mock_post.side_effect = [login_response, final_response]
            result = self.hr_login.perform_login("user@domain.com", "P@ssw0rd!@#")
            self.assertTrue(result)
    
    def test_coa_boundary_dates(self):
        """Test COA with boundary dates (past/future)."""
        past_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        with patch.object(self.hr_login, '_get_employee_id', return_value=6033):
            with patch.object(self.hr_login.session, 'post') as mock_post:
                validation_response = Mock()
                validation_response.status_code = 200
                submit_response = Mock()
                submit_response.status_code = 200
                submit_response.json.return_value = {'d': {'IsSuccess': True, 'ID': 123}}
                mock_post.side_effect = [validation_response, submit_response]
                
                # Test past date
                result_past = self.hr_login.apply_coa(past_date, time_in="09:00")
                self.assertTrue(result_past)
                
                # Reset mocks for future date test
                mock_post.side_effect = [validation_response, submit_response]
                result_future = self.hr_login.apply_coa(future_date, time_in="09:00")
                self.assertTrue(result_future)


def run_comprehensive_tests():
    """Run all comprehensive tests and return results."""
    print("🧪 Running Comprehensive Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestLoginRobustness,
        TestSessionManagement,
        TestCOAValidation,
        TestEmployeeIDExtraction,
        TestEdgeCases
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].strip()}")
    
    if result.errors:
        print("\n⚠️  Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error: ')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures + result.errors)} tests failed")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)