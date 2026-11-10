# _server.py - the MCP SDK's own resumability example (fuller version of server.py)
# with command-line options. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - Handlers are passed to Server(...) as on_list_tools= / on_call_tool=
#     instead of @app.list_tools() / @app.call_tool() decorators
#   - Handlers receive (ctx, params) and return ListToolsResult / CallToolResult
#   - Tool(inputSchema=...) -> Tool(input_schema=...)
#   - Added `if __name__ == "__main__": main()` - the original never called main()
#   - /mcp served by Route (no 307 redirect to /mcp/)
#
# Run:  python _server.py                     -> http://127.0.0.1:3000/mcp
#       python _server.py --port 3001 --log-level DEBUG
import contextlib
import logging
import warnings
from collections.abc import AsyncIterator

import anyio
import click
import mcp.types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from event_store import InMemoryEventStore

# Configure logging
logger = logging.getLogger(__name__)

# send_log_message is deprecated as of protocol 2026-07-28 but still works
# for clients on older protocol versions - hide the warning
warnings.filterwarnings("ignore", message="The logging capability is deprecated")


@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def call_tool(
        ctx: ServerRequestContext, params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        arguments = params.arguments or {}
        interval = arguments.get("interval", 1.0)
        count = int(arguments.get("count", 5))
        caller = arguments.get("caller", "unknown")

        # Send the specified number of notifications with the given interval
        for i in range(count):
            # Include more detailed message for resumability demonstration
            notification_msg = f"[{i + 1}/{count}] Event from '{caller}' - Use Last-Event-ID to resume if disconnected"
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
            logger.debug(f"Sent notification {i + 1}/{count} for caller: {caller}")
            if i < count - 1:  # Don't wait after the last notification
                await anyio.sleep(interval)

        # This will send a resource notificaiton though standalone SSE
        # established by GET request
        await ctx.session.send_resource_updated(uri="http:///test_resource")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=(f"Sent {count} notifications with {interval}s interval for caller: {caller}"),
                )
            ]
        )

    async def list_tools(
        ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name="start-notification-stream",
                    description=("Sends a stream of notifications with configurable count and interval"),
                    input_schema={
                        "type": "object",
                        "required": ["interval", "count", "caller"],
                        "properties": {
                            "interval": {
                                "type": "number",
                                "description": "Interval between notifications in seconds",
                            },
                            "count": {
                                "type": "number",
                                "description": "Number of notifications to send",
                            },
                            "caller": {
                                "type": "string",
                                "description": ("Identifier of the caller to include in notifications"),
                            },
                        },
                    },
                )
            ]
        )

    app = Server(
        "mcp-streamable-http-demo",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )

    # Create event store for resumability
    # The InMemoryEventStore enables resumability support for StreamableHTTP transport.
    # It stores SSE events with unique IDs, allowing clients to:
    #   1. Receive event IDs for each SSE message
    #   2. Resume streams by sending Last-Event-ID in GET requests
    #   3. Replay missed events after reconnection
    # Note: This in-memory implementation is for demonstration ONLY.
    # For production, use a persistent storage solution.
    event_store = InMemoryEventStore()

    # Create the session manager with our app and event store
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=event_store,  # Enable resumability
        json_response=json_response,
    )

    # ASGI handler for streamable HTTP connections
    # (class instance so Route passes the raw ASGI call through)
    class StreamableHTTPEndpoint:
        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application using the transport
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/mcp", endpoint=StreamableHTTPEndpoint(), methods=["GET", "POST", "DELETE"]),
        ],
        lifespan=lifespan,
    )

    # Wrap ASGI application with CORS middleware to expose Mcp-Session-Id header
    # for browser-based clients (ensures 500 errors get proper CORS headers)
    starlette_app = CORSMiddleware(
        starlette_app,
        allow_origins=["*"],  # Allow all origins - adjust as needed for production
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
        expose_headers=["Mcp-Session-Id"],
    )

    import uvicorn

    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    return 0


if __name__ == "__main__":
    main()
