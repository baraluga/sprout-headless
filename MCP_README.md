# ENGIE HR Hub MCP Server

An MCP (Model Context Protocol) server that provides automated access to the ENGIE HR Hub system for time tracking and Certificate of Attendance (COA) applications.

## Features

### 🔧 **Available Tools**

1. **`apply_coa`** - Apply for Certificate of Attendance
   - Flexible time entry (IN-only, OUT-only, or both)
   - Custom date specification
   - Configurable reason and type description

2. **`clock_in`** - Clock in for current or specified time
   - Automatic current time detection
   - Optional custom time/date specification
   - Uses COA system for reliable submission

3. **`clock_out`** - Clock out for current or specified time
   - Automatic current time detection  
   - Optional custom time/date specification
   - Uses COA system for reliable submission

### 🔐 **Authentication & Session Management**
- Automatic session management with persistence
- Handles OpenID Connect authentication flow
- Session renewal on expiry
- Robust error handling and recovery

## Installation

### Prerequisites
```bash
# Install Python dependencies
pip install mcp requests beautifulsoup4 lxml
```

### Setup MCP Server
```bash
# Clone the repository
git clone https://github.com/baraluga/sprout-headless.git
cd sprout-headless

# Install dependencies
pip install -r mcp_requirements.txt

# Make the server executable
chmod +x mcp_server.py
```

## Configuration

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "engie-hr": {
      "command": "python3",
      "args": ["/path/to/sprout-headless/mcp_server.py"],
      "cwd": "/path/to/sprout-headless"
    }
  }
}
```

### Credential Configuration

Update the credentials in `mcp_server.py`:

```python
# Default credentials (update these with your actual credentials)
DEFAULT_USERNAME = "your_username"
DEFAULT_PASSWORD = "your_password"
```

Alternatively, set environment variables:
```bash
export ENGIE_HR_USERNAME="your_username"
export ENGIE_HR_PASSWORD="your_password"
```

## Usage Examples

### Certificate of Attendance (COA) Applications

```python
# Apply COA for both IN and OUT times
apply_coa({
    "date": "2025-07-20",
    "time_in": "09:30",
    "time_out": "17:30",
    "reason": "forgot to clock in/out",
    "type_description": "missed time entry"
})

# Apply COA for IN time only
apply_coa({
    "date": "2025-07-20", 
    "time_in": "09:30",
    "reason": "forgot to clock in"
})

# Apply COA for OUT time only
apply_coa({
    "date": "2025-07-20",
    "time_out": "17:30",
    "reason": "forgot to clock out"
})
```

### Time Tracking

```python
# Clock in with current time
clock_in({})

# Clock in with specific time
clock_in({
    "time": "09:30",
    "date": "2025-07-20"
})

# Clock out with current time
clock_out({})

# Clock out with specific time  
clock_out({
    "time": "17:30",
    "date": "2025-07-20"
})
```

## Tool Specifications

### `apply_coa`

**Description**: Apply for Certificate of Attendance with flexible time options

**Parameters**:
- `date` (required): Date in YYYY-MM-DD format
- `time_in` (optional): Clock-in time in HH:MM format
- `time_out` (optional): Clock-out time in HH:MM format  
- `reason` (optional): Reason for COA application (default: "forgot to in/out")
- `type_description` (optional): Type description (default: "forgot to in/out")

**Returns**: Success/failure message with application details

### `clock_in`

**Description**: Clock in for current or specified date/time

**Parameters**:
- `time` (optional): Specific time in HH:MM format (default: current time)
- `date` (optional): Specific date in YYYY-MM-DD format (default: current date)

**Returns**: Success/failure message with clock-in details

### `clock_out`

**Description**: Clock out for current or specified date/time

**Parameters**:
- `time` (optional): Specific time in HH:MM format (default: current time)
- `date` (optional): Specific date in YYYY-MM-DD format (default: current date)

**Returns**: Success/failure message with clock-out details

## Running the Server

### Command Line
```bash
# Run with stdio transport (default)
python3 mcp_server.py

# Run with specific transport
python3 mcp_server.py --transport stdio
```

### Development Mode
```bash
# Run with debug logging
PYTHONPATH=. python3 -m mcp_server --transport stdio
```

## Session Management

The server automatically handles:
- **Session Creation**: Fresh login on first use
- **Session Persistence**: Saves session to `engie_mcp_session.json`
- **Session Renewal**: Automatic re-authentication on expiry
- **Error Recovery**: Robust handling of network and authentication failures

## Error Handling

The server provides comprehensive error handling for:
- **Network Issues**: Connection timeouts, DNS failures
- **Authentication Problems**: Invalid credentials, expired sessions
- **API Errors**: Validation failures, server errors
- **Input Validation**: Invalid dates, missing parameters

## Security Considerations

- **Credentials**: Store credentials securely, avoid hardcoding in production
- **Session Files**: Protect session files (`engie_mcp_session.json`) - they contain auth tokens
- **Network**: All communication uses HTTPS
- **Logging**: Sensitive information is not logged

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check credentials in `mcp_server.py`
   - Verify network connectivity to `engie.hrhub.ph`
   - Delete session file to force fresh login

2. **COA Application Failed**
   - Verify date format (YYYY-MM-DD)
   - Ensure at least one time (IN or OUT) is provided
   - Check if date is within acceptable range

3. **MCP Connection Issues**
   - Verify MCP client configuration
   - Check server path and permissions
   - Review server logs for errors

### Debug Mode
```bash
# Run with verbose logging
PYTHONUNBUFFERED=1 python3 mcp_server.py --transport stdio
```

### Session Reset
```bash
# Force fresh authentication
rm engie_mcp_session.json
python3 mcp_server.py
```

## Development

### Testing the Server
```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run tests
python3 -m pytest test_comprehensive.py -v

# Test MCP functionality
python3 -c "
import asyncio
from mcp_server import ENGIEHRMCPServer

async def test():
    server = ENGIEHRMCPServer()
    result = await server._ensure_authenticated()
    print('Authentication test:', 'PASS' if result else 'FAIL')

asyncio.run(test())
"
```

### Code Structure
```
mcp_server.py           # Main MCP server implementation
engie_hr_login.py       # Core HR automation logic
test_comprehensive.py   # Comprehensive test suite
integration_test.py     # Integration testing tools
pyproject.toml          # Python project configuration
```

## API Reference

The server implements the MCP protocol with the following capabilities:

- **Tools**: 3 tools (apply_coa, clock_in, clock_out)
- **Resources**: None currently
- **Prompts**: None currently  
- **Notifications**: Standard MCP notifications
- **Transport**: stdio (standard input/output)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see repository for full details

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/baraluga/sprout-headless/issues
- **Documentation**: See README.md and TESTING_REPORT.md

---

**Version**: 1.0.0  
**MCP Protocol**: Compatible with MCP 1.0+  
**Python**: 3.8+ required