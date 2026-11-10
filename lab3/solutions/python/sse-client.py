# sse-client.py - SSE client (MCP Python SDK v2) - legacy transport
# Fixes:
#   sse_client yields (read, write) - the original unpacked 3 values
#   message_handler now receives only notifications or exceptions
# Run the server first (python sse-server.py), then: python sse-client.py
from mcp.client.sse import sse_client
from mcp import ClientSession
import asyncio

import mcp.types as types

from mcp.types import (
    LoggingMessageNotificationParams,
    TextContent,
)

class LoggingCollector:
    def __init__(self):
        self.log_messages: list[LoggingMessageNotificationParams] = []

    async def __call__(self, params: LoggingMessageNotificationParams) -> None:
        self.log_messages.append(params)
        print("LOG:", params.data)

logging_collector = LoggingCollector()

port = 8000

# I get notifications and exceptions
async def message_handler(
        message: types.ServerNotification | Exception,
    ) -> None:
        if isinstance(message, Exception):
            raise message
        print("NOTIFICATION:", message)

async def main():
    print("Starting client...")
    # Connect to the SSE server (/sse)
    async with sse_client(f"http://localhost:{port}/sse") as (
        read_stream,
        write_stream,
    ):
        # Create a session using the client streams
        async with ClientSession(
            read_stream,
            write_stream,
            logging_callback=logging_collector,
            message_handler=message_handler,
        ) as session:

            # Initialize the connection
            await session.initialize()

            print("Session initialized, ready to call tools.")

            # Call a tool - the LOG lines arrive while it runs
            tool_result = await session.call_tool("echo", {"message": "hello"})

            print("Tool result:", tool_result.content[0].text)
            print("Log messages received:", len(logging_collector.log_messages))


asyncio.run(main())
