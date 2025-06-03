#!/usr/bin/env python3
"""
MCP Entry Point for EchoVault Memory Service

Allows running the EchoVault MCP server as a Python module:
    python -m src.mcp_memory_service

This provides a standardized way to start the MCP server for integration
with MCP clients like Claude Desktop.
"""

import sys
import asyncio

try:
    from .mcp_server import main
except ImportError:
    print("Error: Could not import MCP server. Ensure dependencies are installed.")
    print("Run: pip install mcp")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 