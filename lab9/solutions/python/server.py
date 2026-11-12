# server.py - MCP server protected by a middleware that validates a JWT:
# valid signature + known user + required scope. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - from mcp.server.fastmcp.server import FastMCP -> from mcp.server import MCPServer
#     (host/port are no longer FastMCP settings; uvicorn gets them directly)
#   - removed unused imports (pydantic_settings isn't installed with SDK v2,
#     so the original crashed on startup; AuthSettings wasn't used)
#   - `app` is now a module-level ASGI app, so `uvicorn server:app` also works
#   - token checks don't crash on a header without "Bearer " or a token
#     without "scopes"; the token is decoded once per request, not three times
#
# Create a token first: python util.py   (the client reads it from .env)
#
# Run:  python server.py   -> http://localhost:8000/mcp
import datetime
import sys
from typing import Any

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from mcp.server import MCPServer

settings = {
    "host": "localhost",
    "port": 8000,
}

from util import validate_token

users = ["User Userson", "Admin Adminson"]
REQUIRED_SCOPE = "Admin.Write"


def decode_bearer(header: str) -> dict | None:
    """Return the token's claims, or None if it's missing or invalid."""
    if not header.startswith("Bearer "):
        return None
    return validate_token(header[7:])

def is_user(claims: dict) -> bool:
    return claims.get("name") in users

def has_scope(claims: dict, scope: str) -> bool:
    # very naive scope check, in real life parse the token and check scopes properly
    return scope in claims.get("scopes", [])


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):

        has_header = request.headers.get("Authorization")
        if not has_header:
            print("-> Missing Authorization header!")
            return Response(status_code=401, content="Unauthorized")

        claims = decode_bearer(has_header)
        if claims is None:
            print("-> Invalid token!")
            return Response(status_code=403, content="Forbidden")

        print("Valid token, proceeding...")

        if not is_user(claims):
            print("-> User does not exist!")
            return Response(status_code=403, content="Forbidden - user does not exist")
        print("User exists, proceeding...")

        if not has_scope(claims, REQUIRED_SCOPE):
            print("-> Missing required scope!")
            return Response(status_code=403, content="Forbidden - insufficient scopes")

        print("User has required scope, proceeding...")

        print(f"-> Received {request.method} {request.url}")
        response = await call_next(request)
        response.headers['Custom'] = 'Example'
        return response


mcp = MCPServer(
    name="MCP Resource Server",
    instructions="Resource Server that validates a JWT in a middleware",
    debug=True,
)

@mcp.tool()
async def get_time() -> dict[str, Any]:
    """
    Get the current server time.

    This tool demonstrates that system information can be protected
    by authentication. User must be authenticated to access it.
    """

    now = datetime.datetime.now()

    return {
        "current_time": now.isoformat(),
        "timezone": "UTC",  # Simplified for demo
        "timestamp": now.timestamp(),
        "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


def create_app():
    """Streamable HTTP app (serves /mcp) wrapped in the auth middleware."""
    starlette_app = mcp.streamable_http_app()
    starlette_app.add_middleware(CustomHeaderMiddleware)
    return starlette_app

app = create_app()


if __name__ == "__main__":
    print("Running MCP Resource Server...", file=sys.stderr)
    print("Adding custom middleware...", file=sys.stderr)
    uvicorn.run(app, host=settings["host"], port=settings["port"])
