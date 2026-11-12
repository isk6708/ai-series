# server.py - book a trip; if you're not a member, the server ELICITS your
# name and email to sign you up. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - MCPServer / Context imports (mcp.server.fastmcp was removed)
#   - BUG FIX: `name: str = Field(...),` had a trailing comma, which turned
#     the field's default into a tuple: the form lost the "Your name"
#     description and showed a broken default value
#   - serves Streamable HTTP (/mcp) and SSE (/sse); `python server.py` starts
#     it on port 3000 (it used to start stdio)
#
# Run:  uvicorn server:app --port 3000     (or: python server.py)
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from starlette.applications import Starlette

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

mcp = MCPServer(name="Elicitation Example")


class MemberPreferences(BaseModel):
    """Schema for collecting user preferences."""

    become_member: bool = Field(description="Want to be a member to receive discounts?")
    name: str = Field(
        default="",
        description="Your name"
    )
    email: str = Field(
        default="",
        description="Your email address"
    )

@mcp.tool()
async def book_trip(date: str, member_id: str, ctx: Context) -> str:
    """Book a trip check if member is available. If member is not present, ask for sign up."""
    # Check if member is available
    if not member_id or member_id == "guest":
        # Not a member - ask if they want to sign up
        result = await ctx.elicit(
            message=(f"Not a member? Would you like to sign up?"),
            schema=MemberPreferences,
        )

        if result.action == "accept" and result.data:
            if result.data.become_member and result.data.name and result.data.email:
                return f"[BOOKED] Booked for {date}, welcome {result.data.name} as a member!"
            return f"[BOOKED] for {date}, go to www.example.com to sign up if you change your mind on membership."
        return f"[BOOKED] for {date}, go to www.example.com to sign up."

    # Existing member
    return f"[SUCCESS] Booked for {date}, for member {member_id}"


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

streamable_app = mcp.streamable_http_app()   # /mcp
sse_app = mcp.sse_app()                      # /sse and /messages/

app = Starlette(
    routes=[*streamable_app.routes, *sse_app.routes],
    lifespan=lifespan,
)

if __name__ == "__main__":
    import sys
    import uvicorn
    print("Starting Elicitation Example MCP Server on http://127.0.0.1:3000 (/mcp and /sse)", file=sys.stderr)
    uvicorn.run(app, host="127.0.0.1", port=3000)
