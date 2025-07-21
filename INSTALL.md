# ENGIE HR MCP Server Installation

## Installation from Private GitHub Repository

### Method 1: Direct pip install from Git

```bash
pip install git+https://github.com/yourusername/engie-hr-mcp.git
```

### Method 2: With authentication token

```bash
pip install git+https://YOUR_TOKEN@github.com/yourusername/engie-hr-mcp.git
```

### Method 3: For development

```bash
git clone https://github.com/yourusername/engie-hr-mcp.git
cd engie-hr-mcp
pip install -e .
```

## Running the MCP Server

After installation, run the server:

```bash
engie-hr-mcp
```

Or as a module:

```bash
python -m engie_hr_mcp
```

## Claude Desktop Integration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "engie-hr": {
      "command": "engie-hr-mcp",
      "args": []
    }
  }
}
```

## Available Tools

- `apply_coa`: Apply for Certificate of Attendance
- `clock_in`: Clock in for current time
- `clock_out`: Clock out for current time