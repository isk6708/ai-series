# server.py - simple stdio MCP server for VS Code (MCP Python SDK v2)
# v1 -> v2 changes:
#   from mcp.server.fastmcp import FastMCP -> from mcp.server import MCPServer
#   the startup message goes to stderr: over stdio, stdout is reserved for
#   MCP messages, so a normal print() there breaks the connection
import sys
from tokenize import String

from mcp.server import MCPServer

# Create an MCP server
mcp = MCPServer("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Add a subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

@mcp.tool()
def ucapan(apaucapannya: str) -> str:
    """Ucapan"""
    return f"Ini ialah ucapan {apaucapannya}"


if __name__ == "__main__":
    print("Starting MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")
