# server.py
# MCP SDK 2.x: FastMCP was renamed to MCPServer
from mcp.server.mcpserver import MCPServer

# Create an MCP server
mcp = MCPServer("Demo")


# Add a multiply tool
@mcp.tool()
def multiply(first: int, second: int) -> int:
    """Multiply two numbers"""
    return first * second


# Add a dynamic greeting resource
@mcp.resource("echo://{message}")
def get_greeting(message: str) -> str:
    """Echo out the message"""
    return f"Resource echo, {message}!"

@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"

@mcp.resource("command://ping")
def get_echo() -> str:
    """Send pong"""
    return "Pong"

