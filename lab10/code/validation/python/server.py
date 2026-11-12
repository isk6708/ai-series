# server.py - shows how Pydantic VALIDATES tool input before your code runs.
# MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - from mcp.server.fastmcp import FastMCP -> from mcp.server import MCPServer
#   - startup message goes to stderr (stdout is reserved for MCP messages)
#   - `id` is optional (the server assigns it), and `email` must look like an
#     email address, so there's a third validation case to try
#   - create_user has a docstring and a return type
#
# Run:  mcp dev server.py      (Inspector, starts the server for you)
import sys
from typing import Optional

from pydantic import BaseModel, Field

from mcp.server import MCPServer

mcp = MCPServer(name="Tool Example")


class User(BaseModel):
    id: Optional[int] = Field(default=None, description="Assigned by the server")
    name: str = Field(min_length=1, description="User's name")
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Email address")

users = []

@mcp.tool()
def create_user(user: User) -> User:
    """Create a user. Input is validated against the User model first."""

    # Create user logic here
    user.id = len(users) + 1
    users.append(user)
    return user

@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    print("Starting MCP server...", file=sys.stderr)
    mcp.run()
