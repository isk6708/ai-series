# server.py
# Low-level MCP server over Streamable HTTP with RESUMABILITY
# (MCP Python SDK v2: pip install "mcp[cli]>=2" uvicorn)
#
# Resumability: every streamed message gets an event id (stored in the
# InMemoryEventStore). If the client disconnects mid-stream it can reconnect
# with a "Last-Event-ID" header and the server replays what it missed.
#
# v1 -> v2 changes:
#   - Handlers are passed to Server(...) as on_list_tools= / on_call_tool=
#     instead of @app.list_tools() / @app.call_tool() decorators
#   - Handlers receive (ctx, params) and return ListToolsResult / CallToolResult
#   - ctx comes in as an argument (was app.request_context)
#   - Unused v1-only imports removed (FastMCP, Context, ...)
#
# Run:  python server.py   -> http://127.0.0.1:3000/mcp
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

import contextlib
import warnings
import anyio

from collections.abc import AsyncIterator
import mcp.types as types

from mcp.server.context import ServerRequestContext
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import logging
import uvicorn

from mcp.server.lowlevel import Server

from event_store import InMemoryEventStore

# send_log_message still works for clients on older protocol versions, but
# the logging capability is deprecated as of protocol 2026-07-28 - hide the warning
warnings.filterwarnings("ignore", message="The logging capability is deprecated")

# set up logging
logger = logging.getLogger(__name__)
# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

files = [
    "file1.txt",
    "file2.txt",
    "file3.txt"
]

# call tool
async def call_tool(
    ctx: ServerRequestContext, params: types.CallToolRequestParams
) -> types.CallToolResult:
    print("ctx:", ctx.method, "request_id:", ctx.request_id, "tool:", params.name)

    no_of_files = len(files)

    # Send the specified number of notifications with the given interval
    for i in range(no_of_files):
        # Include more detailed message for resumability demonstration
        notification_msg = f"[{i + 1}/{no_of_files}] Event from '{files[i]}' - Use Last-Event-ID to resume if disconnected"

        await ctx.session.send_log_message(
            level="info",
            data=notification_msg,
            logger="notification_stream",
            # Associates this notification with the original request
            # Ensures notifications are sent to the correct response stream
            # Without this, notifications will either go to:
            # - a standalone SSE stream (if GET request is supported)
            # - nowhere (if GET request isn't supported)
            related_request_id=ctx.request_id,
        )
        logger.debug(f"Sent notification {i + 1}/{no_of_files}")
        # pause between events so there is time to disconnect and resume
        await anyio.sleep(1)

    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=(f"Processed {no_of_files} files"),
            )
        ]
    )

# define list tools, what tools we have
async def list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="process-files",
                description=("Process a number of files"),
                input_schema={
                    "type": "object",
                    "required": [],
                    "properties": {},
                },
            )
        ]
    )

# Create an MCP server (handlers are passed in, not decorated)
app = Server(
    "mcp-streamable-http-demo",
    on_list_tools=list_tools,
    on_call_tool=call_tool,
)

# create a store for messages
event_store = InMemoryEventStore()

# Create the session manager with our app and event store
session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=event_store,  # Enable resumability
    json_response=False,      # must stream (SSE) for events/ids to exist
)

# ASGI handler for streamable HTTP connections.
# A class instance (not a plain function) so Starlette's Route passes the raw
# ASGI call through. Route("/mcp") serves /mcp exactly - Mount("/mcp") would
# 307-redirect every request to /mcp/, which plain curl doesn't follow.
class StreamableHTTPEndpoint:
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

handle_streamable_http = StreamableHTTPEndpoint()

@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Context manager for managing session manager lifecycle."""
    async with session_manager.run():
        logger.info("Application started with StreamableHTTP session manager!")
        try:
            yield
        finally:
            logger.info("Application shutting down...")


starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/mcp", endpoint=handle_streamable_http, methods=["GET", "POST", "DELETE"]),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="127.0.0.1", port=3000)
