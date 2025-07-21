# Project Cerberus - ENGIE HR Hub Headless Login

🐕 A Python-based headless authentication system for ENGIE's HR Hub portal.

## Overview

This project implements a complete headless login flow for the ENGIE HR Hub system, handling the OpenID Connect authentication process without requiring a browser. It can extract user information, save sessions, and perform authenticated requests.

## Features

- ✅ **Headless Authentication**: Pure HTTP/HTTPS requests, no browser required
- 🔐 **OpenID Connect Flow**: Handles complete OIDC authentication chain
- 💾 **Session Persistence**: Save and reuse authentication sessions
- 📊 **User Data Extraction**: Extract attendance, leave credits, and other HR data
- 🧪 **Testing Suite**: Comprehensive testing functionality
- 🚀 **Easy Integration**: Simple Python API for other applications

## Installation

```bash
# Clone or download the project files
cd project-cerberus

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from engie_hr_login import ENGIEHRLogin

# Initialize login handler
hr_login = ENGIEHRLogin()

# Perform login flow
if hr_login.get_initial_auth_params():
    if hr_login.perform_login("your_username", "your_password"):
        if hr_login.test_authenticated_access():
            # Successfully logged in!
            user_info = hr_login.get_user_info()
            print(user_info)
```

### Command Line Usage

```bash
# Interactive mode
python engie_hr_login.py

# Direct execution
python test_login.py --username your_username --password your_password

# Quiet mode for scripts
python test_login.py -u your_username -p your_password --quiet
```

### Testing

```bash
# Run comprehensive test suite
python test_login.py

# Test with specific credentials
python test_login.py --username testuser --password testpass
```

## How It Works

1. **Initial Redirect Chain**: Follows redirects from HR hub to SSO server
2. **Parameter Extraction**: Extracts OpenID Connect authentication parameters
3. **Form Submission**: Submits credentials to Keycloak authentication server
4. **Token Exchange**: Handles the form_post response with auth tokens
5. **Session Establishment**: Establishes authenticated session with HR system
6. **Data Extraction**: Parses dashboard for user information

## Authentication Flow

```
engie.hrhub.ph → Login.aspx → sso.aspx → sso.sprout.ph/auth
                                                   ↓
engie.hrhub.ph ← SSO.aspx ← form_post ← authenticate
```

## API Reference

### ENGIEHRLogin Class

- `get_initial_auth_params()`: Extract auth parameters from initial requests
- `perform_login(username, password)`: Submit credentials and authenticate
- `test_authenticated_access()`: Verify authentication status
- `get_user_info()`: Extract user data from dashboard
- `save_session(filename)`: Save session cookies for reuse
- `load_session(filename)`: Load previously saved session

## Session Management

Sessions are automatically saved as JSON files containing cookies and headers:

```json
{
  "cookies": {
    "ASP.NET_SessionId": "...",
    "AuthToken": "...",
    "..."
  },
  "headers": {
    "User-Agent": "...",
    "..."
  }
}
```

## Security Considerations

- 🔒 **Credentials**: Never hardcode credentials in scripts
- 🛡️ **Session Files**: Protect session files - they contain authentication tokens
- 🕒 **Session Expiry**: Sessions may expire and require re-authentication
- 🔄 **Rate Limiting**: Respect server rate limits to avoid blocking

## Troubleshooting

### Common Issues

1. **Login Failed**: Check credentials and ensure account isn't locked
2. **Redirect Errors**: Network connectivity or server maintenance
3. **Session Expired**: Delete session file and re-authenticate
4. **Parsing Errors**: Website structure may have changed

### Debug Mode

Enable verbose output to see detailed flow information:

```python
# Add debug prints throughout the flow
hr_login = ENGIEHRLogin()
# ... rest of code with detailed logging
```

## Example Output

```
🚀 ENGIE HR Hub Headless Login
========================================
🔄 Following initial redirect chain...
✅ Redirected to SSO: https://sso.sprout.ph/realms/engie/protocol/...
✅ Found login action URL: https://sso.sprout.ph/realms/engie/login-actions/authenticate...
🔐 Attempting login for user: bperalta
📊 Login response status: 200
📍 Final URL: https://engie.hrhub.ph/EmployeeDashboard.aspx
✅ Login successful! Redirected to dashboard
🧪 Testing authenticated access...
✅ Successfully accessing authenticated dashboard

📊 User Information:
--------------------
📅 Recent Attendance:
  07/21/25 - OUT at 07:21 PM
  07/21/25 - IN at 08:04 AM
  07/18/25 - IN at 09:52 AM

🏖️  Leave Credits:
  Family Care Leave: 2
  Vacation: 11
  Sick: 3.5

✅ Login completed successfully!
💡 Session saved for future use
```

## Contributing

Feel free to submit issues or pull requests if you encounter problems or have improvements!

## License

This project is for educational and authorized testing purposes only.