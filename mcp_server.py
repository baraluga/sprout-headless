#!/usr/bin/env python3
"""
MCP Server for ENGIE HR Hub Automation

This MCP server provides three tools for interacting with the ENGIE HR Hub system:
1. apply_coa - Apply for Certificate of Attendance (IN, OUT, or both)
2. clock_in - Clock in for the current time
3. clock_out - Clock out for the current time

The server handles session management automatically and provides robust error handling.
"""

import asyncio
import json
import logging
from datetime import datetime, date
from typing import Any, Dict, Optional, List
from pathlib import Path

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource, 
    LoggingLevel
)
import mcp.types as types

from engie_hr_login import ENGIEHRLogin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("engie-hr-mcp")

# Global HR login instance
hr_login_instance = None
session_file = "engie_mcp_session.json"

# Default credentials (can be overridden via environment variables or config)
DEFAULT_USERNAME = "bperalta"
DEFAULT_PASSWORD = "KKrm7MpdNQijfSM@"

class ENGIEHRMCPServer:
    """MCP Server for ENGIE HR Hub automation."""
    
    def __init__(self):
        self.server = Server("engie-hr-hub")
        self.hr_login = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="apply_coa",
                    description="Apply for Certificate of Attendance (COA) for a specific date with flexible time options",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (e.g., '2025-07-20')"
                            },
                            "time_in": {
                                "type": "string",
                                "description": "Clock-in time in HH:MM format (e.g., '09:30'). Optional if only applying for clock-out."
                            },
                            "time_out": {
                                "type": "string", 
                                "description": "Clock-out time in HH:MM format (e.g., '17:30'). Optional if only applying for clock-in."
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for COA application",
                                "default": "forgot to in/out"
                            },
                            "type_description": {
                                "type": "string",
                                "description": "Type description for the COA",
                                "default": "forgot to in/out"
                            }
                        },
                        "required": ["date"]
                    }
                ),
                Tool(
                    name="clock_in",
                    description="Clock in for the current date and time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "time": {
                                "type": "string",
                                "description": "Optional specific time in HH:MM format. If not provided, uses current time."
                            },
                            "date": {
                                "type": "string", 
                                "description": "Optional specific date in YYYY-MM-DD format. If not provided, uses current date."
                            }
                        }
                    }
                ),
                Tool(
                    name="clock_out",
                    description="Clock out for the current date and time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "time": {
                                "type": "string",
                                "description": "Optional specific time in HH:MM format. If not provided, uses current time."
                            },
                            "date": {
                                "type": "string",
                                "description": "Optional specific date in YYYY-MM-DD format. If not provided, uses current date."
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                # Ensure we have an authenticated session
                if not await self._ensure_authenticated():
                    return [types.TextContent(
                        type="text",
                        text="❌ Failed to authenticate with ENGIE HR Hub. Please check credentials and network connection."
                    )]
                
                if name == "apply_coa":
                    return await self._handle_apply_coa(arguments or {})
                elif name == "clock_in":
                    return await self._handle_clock_in(arguments or {})
                elif name == "clock_out":
                    return await self._handle_clock_out(arguments or {})
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have an authenticated session."""
        if self.hr_login is None:
            self.hr_login = ENGIEHRLogin()
        
        # Try to load existing session
        if self.hr_login.load_session(session_file):
            if self.hr_login.test_authenticated_access():
                logger.info("Using existing valid session")
                return True
            else:
                logger.info("Existing session expired, performing fresh login")
        
        # Perform fresh login
        logger.info("Performing fresh authentication")
        
        if not self.hr_login.get_initial_auth_params():
            logger.error("Failed to get authentication parameters")
            return False
        
        if not self.hr_login.perform_login(DEFAULT_USERNAME, DEFAULT_PASSWORD):
            logger.error("Login failed")
            return False
        
        if not self.hr_login.test_authenticated_access():
            logger.error("Authentication verification failed")
            return False
        
        # Save session for future use
        self.hr_login.save_session(session_file)
        logger.info("Authentication successful, session saved")
        return True
    
    async def _handle_apply_coa(self, arguments: dict) -> list[types.TextContent]:
        """Handle apply_coa tool call."""
        try:
            target_date = arguments.get("date")
            time_in = arguments.get("time_in")
            time_out = arguments.get("time_out")
            reason = arguments.get("reason", "forgot to in/out")
            type_description = arguments.get("type_description", "forgot to in/out")
            
            if not target_date:
                return [types.TextContent(
                    type="text",
                    text="❌ Date parameter is required in YYYY-MM-DD format"
                )]
            
            # Validate that at least one time is provided
            if not time_in and not time_out:
                return [types.TextContent(
                    type="text",
                    text="❌ Either time_in or time_out (or both) must be provided"
                )]
            
            logger.info(f"Applying COA for {target_date} - IN: {time_in}, OUT: {time_out}")
            
            # Apply COA
            result = self.hr_login.apply_coa(
                target_date=target_date,
                time_in=time_in,
                time_out=time_out,
                reason=reason,
                type_other=type_description
            )
            
            if result:
                time_info = []
                if time_in:
                    time_info.append(f"IN: {time_in}")
                if time_out:
                    time_info.append(f"OUT: {time_out}")
                
                return [types.TextContent(
                    type="text",
                    text=f"✅ COA application submitted successfully!\n📅 Date: {target_date}\n⏰ Times: {', '.join(time_info)}\n📝 Reason: {reason}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ COA application failed for {target_date}. Please check the logs for details."
                )]
                
        except Exception as e:
            logger.error(f"Error in apply_coa: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error applying COA: {str(e)}"
            )]
    
    async def _handle_clock_in(self, arguments: dict) -> list[types.TextContent]:
        """Handle clock_in tool call."""
        try:
            # Get current time and date or use provided values
            now = datetime.now()
            target_date = arguments.get("date", now.strftime('%Y-%m-%d'))
            target_time = arguments.get("time", now.strftime('%H:%M'))
            
            logger.info(f"Clock in for {target_date} at {target_time}")
            
            # Use apply_coa with only time_in
            result = self.hr_login.apply_coa(
                target_date=target_date,
                time_in=target_time,
                time_out=None,
                reason="Clock in via MCP",
                type_other="Clock in"
            )
            
            if result:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Clock-in successful!\n📅 Date: {target_date}\n⏰ Time: {target_time}\n📝 Applied via COA system"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Clock-in failed for {target_date} at {target_time}. Please check the logs for details."
                )]
                
        except Exception as e:
            logger.error(f"Error in clock_in: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error during clock-in: {str(e)}"
            )]
    
    async def _handle_clock_out(self, arguments: dict) -> list[types.TextContent]:
        """Handle clock_out tool call."""
        try:
            # Get current time and date or use provided values
            now = datetime.now()
            target_date = arguments.get("date", now.strftime('%Y-%m-%d'))
            target_time = arguments.get("time", now.strftime('%H:%M'))
            
            logger.info(f"Clock out for {target_date} at {target_time}")
            
            # Use apply_coa with only time_out
            result = self.hr_login.apply_coa(
                target_date=target_date,
                time_in=None,
                time_out=target_time,
                reason="Clock out via MCP",
                type_other="Clock out"
            )
            
            if result:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Clock-out successful!\n📅 Date: {target_date}\n⏰ Time: {target_time}\n📝 Applied via COA system"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Clock-out failed for {target_date} at {target_time}. Please check the logs for details."
                )]
                
        except Exception as e:
            logger.error(f"Error in clock_out: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Error during clock-out: {str(e)}"
            )]
    
    async def run(self, transport_type: str = "stdio"):
        """Run the MCP server."""
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="engie-hr-hub",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")


async def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ENGIE HR Hub MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio"], 
        default="stdio",
        help="Transport mechanism (default: stdio)"
    )
    
    args = parser.parse_args()
    
    # Initialize and run server
    server = ENGIEHRMCPServer()
    logger.info(f"Starting ENGIE HR Hub MCP Server with {args.transport} transport")
    
    try:
        await server.run(args.transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())