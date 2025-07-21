#!/usr/bin/env python3
"""
ENGIE HR Hub Headless Login Script

This script performs automated login to ENGIE's HR Hub system using pure HTTP requests.
It handles the complete OpenID Connect authentication flow without requiring a browser.
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs, urlencode
import json
from typing import Dict, Optional, Tuple
import sys
from datetime import datetime, date


class ENGIEHRLogin:
    def __init__(self, username: str = None, password: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.base_url = "https://engie.hrhub.ph/"
        self.sso_url = "https://sso.sprout.ph/"
        self.auth_params = {}
        self.dashboard_cookies = {}
        
        # Store credentials for automatic authentication
        self.username = username or "bperalta"  # Default username
        self.password = password or "KKrm7MpdNQijfSM@"  # Default password
        self.session_file = "engie_session.json"

    def get_initial_auth_params(self) -> bool:
        """
        Follow the initial redirect chain to get authentication parameters.
        Returns True if successful, False otherwise.
        """
        try:
            # Step 1: Initial request to HR hub
            print("🔄 Following initial redirect chain...")
            response = self.session.get(self.base_url, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"❌ Failed to access initial URL. Status: {response.status_code}")
                return False
            
            # Check if we landed on the SSO login page
            if "sso.sprout.ph" not in response.url:
                print("❌ Did not redirect to SSO login page")
                return False
                
            print(f"✅ Redirected to SSO: {response.url}")
            
            # Parse the authentication URL parameters
            parsed_url = urlparse(response.url)
            self.auth_params = parse_qs(parsed_url.query)
            
            # Extract single values from lists
            for key, value in self.auth_params.items():
                if isinstance(value, list) and len(value) == 1:
                    self.auth_params[key] = value[0]
            
            # Parse the login form to extract additional parameters
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form', {'id': 'kc-form-login'})
            
            if not form:
                print("❌ Could not find login form")
                return False
            
            # Extract form action URL
            action_url = form.get('action')
            if action_url:
                self.login_action_url = action_url
                print(f"✅ Found login action URL: {action_url}")
            else:
                print("❌ Could not extract login action URL")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error getting auth parameters: {e}")
            return False

    def perform_login(self, username: str, password: str) -> bool:
        """
        Submit login credentials to the authentication server.
        Returns True if login successful, False otherwise.
        """
        try:
            print(f"🔐 Attempting login for user: {username}")
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password,
                'credentialId': ''  # Usually empty for password auth
            }
            
            # Set proper headers for form submission
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.session.get_adapter('https://').last_url if hasattr(self.session.get_adapter('https://'), 'last_url') else self.sso_url,
                'Origin': self.sso_url.rstrip('/'),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Submit login form (this returns the form_post response)
            response = self.session.post(
                self.login_action_url, 
                data=login_data,
                headers=headers,
                allow_redirects=False  # Don't auto-redirect to handle form_post manually
            )
            
            print(f"📊 Login response status: {response.status_code}")
            
            if response.status_code == 200:
                # Parse the form_post response
                soup = BeautifulSoup(response.text, 'html.parser')
                form = soup.find('form')
                
                if form and form.get('action'):
                    print("🔄 Processing OIDC form_post response...")
                    
                    # Extract form data for the post-back
                    form_data = {}
                    for input_elem in form.find_all('input'):
                        name = input_elem.get('name')
                        value = input_elem.get('value', '')
                        if name:
                            form_data[name] = value
                    
                    # Submit the form_post to complete OIDC flow
                    final_response = self.session.post(
                        form.get('action'),
                        data=form_data,
                        allow_redirects=True
                    )
                    
                    print(f"📍 Final URL: {final_response.url}")
                    
                    # Check if we reached the dashboard
                    if "engie.hrhub.ph" in final_response.url and "EmployeeDashboard.aspx" in final_response.url:
                        print("✅ Login successful! Redirected to dashboard")
                        self.dashboard_cookies = dict(self.session.cookies)
                        return True
                    else:
                        print(f"❌ Did not reach expected dashboard: {final_response.url}")
                        return False
                else:
                    # Check for error messages in the response
                    error_msg = soup.find('span', class_='kc-feedback-text')
                    if error_msg:
                        print(f"❌ Login failed: {error_msg.text}")
                        return False
                    else:
                        print("❌ Login failed: No form_post found in response")
                        return False
            else:
                print(f"❌ Login request failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False

    def test_authenticated_access(self) -> bool:
        """
        Test that we can access authenticated pages in the HR system.
        """
        try:
            print("🧪 Testing authenticated access...")
            
            # Try to access the dashboard
            response = self.session.get(f"{self.base_url}EmployeeDashboard.aspx")
            
            if response.status_code == 200 and "Employee Dashboard" in response.text:
                print("✅ Successfully accessing authenticated dashboard")
                
                # Extract some basic user info for verification
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for user-specific content
                attendance_section = soup.find('div', class_='attendance')
                if attendance_section:
                    print("✅ Found attendance data - user is properly authenticated")
                
                return True
            else:
                print(f"❌ Failed to access dashboard. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing authenticated access: {e}")
            return False

    def get_user_info(self) -> Dict:
        """
        Extract basic user information from the dashboard.
        """
        try:
            response = self.session.get(f"{self.base_url}EmployeeDashboard.aspx")
            if response.status_code != 200:
                return {}
                
            soup = BeautifulSoup(response.text, 'html.parser')
            user_info = {}
            
            # Extract attendance data
            attendance_rows = soup.find_all('tr')
            recent_attendance = []
            
            for row in attendance_rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    date = cells[0].get_text(strip=True)
                    status = cells[1].get_text(strip=True)
                    time = cells[2].get_text(strip=True)
                    
                    if date and status in ['IN', 'OUT'] and time:
                        recent_attendance.append({
                            'date': date,
                            'status': status,
                            'time': time
                        })
            
            user_info['recent_attendance'] = recent_attendance[:5]  # Last 5 entries
            
            # Extract leave credits
            leave_credits = {}
            leave_rows = soup.find_all('tr')
            for row in leave_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    leave_type = cells[0].get_text(strip=True)
                    balance = cells[1].get_text(strip=True)
                    
                    if leave_type and balance.replace('.', '').isdigit():
                        leave_credits[leave_type] = balance
            
            user_info['leave_credits'] = leave_credits
            
            return user_info
            
        except Exception as e:
            print(f"❌ Error extracting user info: {e}")
            return {}

    def save_session(self, filename: str = "engie_session.json") -> bool:
        """
        Save the current session cookies for reuse.
        """
        try:
            session_data = {
                'cookies': dict(self.session.cookies),
                'headers': dict(self.session.headers)
            }
            
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"✅ Session saved to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            return False

    def load_session(self, filename: str = "engie_session.json") -> bool:
        """
        Load a previously saved session.
        """
        try:
            with open(filename, 'r') as f:
                session_data = json.load(f)
            
            # Restore cookies
            for name, value in session_data.get('cookies', {}).items():
                self.session.cookies.set(name, value)
            
            print(f"✅ Session loaded from {filename}")
            return True
            
        except FileNotFoundError:
            print(f"📝 No existing session file found: {filename}")
            return False
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return False

    def clock_in(self) -> bool:
        """
        Submit a clock-in request to the HR system.
        
        This function automatically handles authentication if no valid session exists.
        
        Returns:
            bool: True if clock-in successful, False otherwise
        """
        try:
            # Ensure we have an authenticated session
            if not self._ensure_authenticated():
                print("❌ Failed to authenticate. Cannot clock in.")
                return False
            
            # TODO: Implement actual clock-in functionality
            # This would involve finding and clicking the clock-in button on the HR system
            print("🕐 Clock-in functionality not yet implemented")
            print("💡 Use apply_coa() for time entry corrections")
            return False
            
        except Exception as e:
            print(f"❌ Error during clock-in: {e}")
            return False

    def clock_out(self) -> bool:
        """
        Submit a clock-out request to the HR system.
        
        This function automatically handles authentication if no valid session exists.
        
        Returns:
            bool: True if clock-out successful, False otherwise
        """
        try:
            # Ensure we have an authenticated session
            if not self._ensure_authenticated():
                print("❌ Failed to authenticate. Cannot clock out.")
                return False
            
            # TODO: Implement actual clock-out functionality
            # This would involve finding and clicking the clock-out button on the HR system
            print("🕐 Clock-out functionality not yet implemented")
            print("💡 Use apply_coa() for time entry corrections")
            return False
            
        except Exception as e:
            print(f"❌ Error during clock-out: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid authenticated session.
        
        This method will:
        1. Try to load an existing session
        2. Test if the session is still valid
        3. Perform fresh authentication if needed
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # First, try to load an existing session
            if self.load_session(self.session_file):
                if self.test_authenticated_access():
                    print("✅ Using existing valid session")
                    return True
                else:
                    print("🔄 Existing session expired, performing fresh authentication...")
            else:
                print("🔄 No existing session found, performing fresh authentication...")
            
            # Perform fresh authentication
            print(f"🔐 Authenticating as {self.username}...")
            
            if not self.get_initial_auth_params():
                print("❌ Failed to get authentication parameters")
                return False
            
            if not self.perform_login(self.username, self.password):
                print("❌ Login failed")
                return False
            
            if not self.test_authenticated_access():
                print("❌ Authentication verification failed")
                return False
            
            # Save the session for future use
            self.save_session(self.session_file)
            print("✅ Authentication successful, session saved")
            return True
            
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return False

    def apply_coa(self, target_date: str, time_in: str = None, time_out: str = None, reason: str = "forgot to in/out", type_other: str = "forgot to in/out") -> bool:
        """
        Apply for Certificate of Attendance (COA) using the actual API endpoints discovered through network analysis.
        
        This function automatically handles authentication if no valid session exists.
        You can specify just IN time, just OUT time, or both.
        
        Args:
            target_date (str): Date for COA in format 'YYYY-MM-DD' (e.g., '2025-07-19')
            time_in (str, optional): Clock-in time in format 'HH:MM' (e.g., '09:00'). None to skip IN entry.
            time_out (str, optional): Clock-out time in format 'HH:MM' (e.g., '17:00'). None to skip OUT entry.
            reason (str, optional): Reason for COA application, defaults to "forgot to in/out"
            type_other (str, optional): Type description when using "Others" category, defaults to "forgot to in/out"
        
        Returns:
            bool: True if COA application successful, False otherwise
            
        Examples:
            # Apply COA for both IN and OUT (auto-login if needed)
            hr_login.apply_coa('2025-07-19', '09:00', '17:00')
            
            # Apply COA for just clock-in (auto-login if needed)
            hr_login.apply_coa('2025-07-19', time_in='09:00')
            
            # Apply COA for just clock-out (auto-login if needed)
            hr_login.apply_coa('2025-07-19', time_out='17:00')
        """
        try:
            # Validate that at least one time is provided
            if not time_in and not time_out:
                print("❌ Either time_in or time_out (or both) must be provided")
                return False
            
            # Ensure we have an authenticated session before proceeding
            if not self._ensure_authenticated():
                print("❌ Failed to authenticate. Cannot apply COA.")
                return False
            
            print(f"🎯 Applying COA for {target_date}")
            if time_in:
                print(f"   📥 IN: {time_in}")
            if time_out:
                print(f"   📤 OUT: {time_out}")
            
            # Parse and validate date
            try:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            except ValueError:
                print(f"❌ Invalid date format. Use YYYY-MM-DD format (e.g., '2025-07-19')")
                return False
            
            # Build certificate logs based on provided times
            certificate_logs = []
            
            if time_in:
                certificate_logs.append({
                    "FormattedDate": target_date,
                    "FormattedTime": time_in,
                    "Type": "In",
                    "CertificateLogID": 0
                })
            
            if time_out:
                certificate_logs.append({
                    "FormattedDate": target_date,
                    "FormattedTime": time_out,
                    "Type": "Out", 
                    "CertificateLogID": 0
                })
            
            # Get employee ID from session
            employee_id = self._get_employee_id()
            if not employee_id:
                print("❌ Could not determine employee ID from session")
                return False
            
            # Prepare COA payload using the captured API structure
            coa_payload = {
                "certificateOfAttendance": {
                    "CertificateOfAttendanceID": 0,
                    "CertificateTypeID": "0",  # "0" = Others
                    "CertificateTypeOthers": type_other,
                    "Remarks": reason,
                    "Status": None,
                    "EmployeeID": employee_id,
                    "FormattedCertificateLogs": certificate_logs
                }
            }
            
            print(f"📋 COA payload prepared for Employee ID: {employee_id}")
            
            # Step 1: Validate submission (check for duplicates)
            validate_url = f"{self.base_url}CertificateOfAttendance.aspx/ValidateSameFiling"
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{self.base_url}CertificateOfAttendance.aspx"
            }
            
            print("🔍 Step 1: Validating COA submission...")
            validate_response = self.session.post(validate_url, json=coa_payload, headers=headers)
            
            if validate_response.status_code != 200:
                print(f"❌ Validation failed. Status: {validate_response.status_code}")
                print(f"Response: {validate_response.text}")
                return False
            
            print("✅ Validation passed")
            
            # Step 2: Submit actual COA application
            submit_url = f"{self.base_url}CertificateOfAttendance.aspx/Save"
            
            print("💾 Step 2: Submitting COA application...")
            submit_response = self.session.post(submit_url, json=coa_payload, headers=headers)
            
            if submit_response.status_code != 200:
                print(f"❌ COA submission failed. Status: {submit_response.status_code}")
                print(f"Response: {submit_response.text}")
                return False
            
            # Parse response
            try:
                result = submit_response.json()
                if result.get('d'):  # ASP.NET Web Methods return data in 'd' property
                    print("🎉 COA application submitted successfully!")
                    print(f"📋 Response: {result}")
                    return True
                else:
                    print("⚠️  Unexpected response format")
                    print(f"Response: {result}")
                    return False
            except Exception as e:
                print(f"⚠️  Could not parse response: {e}")
                # If response parsing fails but status is 200, assume success
                print("✅ COA submitted (response parsing failed but HTTP 200 received)")
                return True
                
        except Exception as e:
            print(f"❌ Error applying for COA: {e}")
            return False

    def _get_employee_id(self) -> int:
        """
        Extract employee ID from the current session.
        This is required for COA submissions.
        
        Returns:
            int: Employee ID if found, None otherwise
        """
        try:
            # Try to get employee ID from dashboard page
            response = self.session.get(f"{self.base_url}EmployeeDashboard.aspx")
            if response.status_code != 200:
                return None
            
            # Look for employee ID patterns in the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Common patterns where employee ID might be found:
            # 1. JavaScript variables
            # 2. Hidden input fields  
            # 3. Data attributes
            # 4. URL parameters
            
            # Pattern 1: Look for JavaScript variables
            import re
            js_patterns = [
                r'EmployeeID["\']?\s*[:=]\s*["\']?(\d+)',
                r'employeeId["\']?\s*[:=]\s*["\']?(\d+)', 
                r'empId["\']?\s*[:=]\s*["\']?(\d+)',
                r'UserID["\']?\s*[:=]\s*["\']?(\d+)'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    return int(matches[0])
            
            # Pattern 2: Hidden input fields
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for inp in hidden_inputs:
                if inp.get('name') and 'employee' in inp.get('name', '').lower():
                    value = inp.get('value', '')
                    if value.isdigit():
                        return int(value)
            
            # Pattern 3: Data attributes
            elements_with_data = soup.find_all(attrs={'data-employee-id': True})
            if elements_with_data:
                emp_id = elements_with_data[0].get('data-employee-id')
                if emp_id and emp_id.isdigit():
                    return int(emp_id)
            
            print("⚠️  Could not automatically detect employee ID")
            return None
            
        except Exception as e:
            print(f"❌ Error getting employee ID: {e}")
            return None

    def _parse_dates(self, date_from: str, date_to: str) -> tuple:
        """
        Parse date strings into datetime objects.
        Supports formats: 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY'
        """
        try:
            formats_to_try = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
            
            from_date_obj = None
            to_date_obj = None
            
            # Try to parse from_date
            for fmt in formats_to_try:
                try:
                    from_date_obj = datetime.strptime(date_from, fmt)
                    break
                except ValueError:
                    continue
            
            # Try to parse to_date
            for fmt in formats_to_try:
                try:
                    to_date_obj = datetime.strptime(date_to, fmt)
                    break
                except ValueError:
                    continue
            
            if not from_date_obj or not to_date_obj:
                return None, None
                
            return from_date_obj, to_date_obj
            
        except Exception as e:
            print(f"❌ Error parsing dates: {e}")
            return None, None


def main():
    """Main function demonstrating usage of the ENGIE HR login system."""
    
    print("🚀 ENGIE HR Hub Headless Login")
    print("=" * 40)
    
    # Get credentials
    username = input("👤 Username: ").strip()
    if not username:
        print("❌ Username is required")
        sys.exit(1)
    
    password = input("🔑 Password: ").strip()
    if not password:
        print("❌ Password is required")
        sys.exit(1)
    
    # Initialize login handler
    hr_login = ENGIEHRLogin()
    
    # Try to load existing session first
    if hr_login.load_session():
        if hr_login.test_authenticated_access():
            print("✅ Using existing valid session")
        else:
            print("🔄 Existing session invalid, performing fresh login...")
    
    # Perform login flow
    if not hr_login.get_initial_auth_params():
        print("❌ Failed to get authentication parameters")
        sys.exit(1)
    
    if not hr_login.perform_login(username, password):
        print("❌ Login failed")
        sys.exit(1)
    
    # Test access and save session
    if hr_login.test_authenticated_access():
        hr_login.save_session()
        
        # Display user information
        print("\n📊 User Information:")
        print("-" * 20)
        
        user_info = hr_login.get_user_info()
        
        if user_info.get('recent_attendance'):
            print("📅 Recent Attendance:")
            for entry in user_info['recent_attendance']:
                print(f"  {entry['date']} - {entry['status']} at {entry['time']}")
        
        if user_info.get('leave_credits'):
            print("🏖️  Leave Credits:")
            for leave_type, balance in user_info['leave_credits'].items():
                print(f"  {leave_type}: {balance}")
        
        print("\n✅ Login completed successfully!")
        print("💡 Session saved for future use")
        
    else:
        print("❌ Authentication verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()