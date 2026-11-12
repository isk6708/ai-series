# server.py - ELICITATION demo: the server asks the user for more input
# (an alternative date) in the middle of a tool call. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   from mcp.server.fastmcp import Context, FastMCP
#   -> from mcp.server import MCPServer / from mcp.server.mcpserver import Context
#   - serves BOTH transports: Streamable HTTP (/mcp, current) and SSE (/sse, legacy)
#   - `python server.py` now starts the HTTP server (it used to start stdio,
#     which client.py can't connect to)
#
# Run:  uvicorn server:app          (or: python server.py)  -> port 8000
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from starlette.applications import Starlette

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

mcp = MCPServer(name="Elicitation Example")


class BookingPreferences(BaseModel):
    """Schema for collecting user preferences."""

    checkAlternative: bool = Field(description="Would you like to check another date?")
    alternativeDate: str = Field(
        default="2024-12-26",
        description="Alternative date (YYYY-MM-DD)",
    )

def not_available_date(date: str) -> bool:
    # Simulate date availability check
    return date != "2024-12-25"


@mcp.tool()
async def book_trip(date: str, ctx: Context) -> str:
    """Book a trip with date availability check."""
    # Check if date is available
    if not_available_date(date):
        # Date unavailable - ask user for alternative
        result = await ctx.elicit(
            message=(f"No trips available on {date}. Would you like to try another date?"),
            schema=BookingPreferences,
        )

        if result.action == "accept" and result.data:
            if result.data.checkAlternative:
                return f"[SUCCESS] Booked for {result.data.alternativeDate}"
            return "[CANCELLED] No booking made"
        return "[CANCELLED] Booking cancelled"

    # Date available
    return f"[SUCCESS] Booked for {date}"


# Streamable HTTP needs its session manager started by the app's lifespan
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
    print("Starting Elicitation Example MCP Server on http://127.0.0.1:8000 (/mcp and /sse)", file=sys.stderr)
    uvicorn.run(app, host="127.0.0.1", port=8000)
