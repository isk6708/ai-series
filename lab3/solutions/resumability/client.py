# client.py - calls the resumable server's tool and prints the streamed events
# (MCP Python SDK v2)
# v1 -> v2 changes:
#   streamablehttp_client  -> streamable_http_client
#   it yields (read, write) - the 3rd "session_callback" value is gone
#   message_handler now receives only notifications or exceptions
#   tool name fixed: the server's tool is "process-files" (was "process_files")
# Run the server first (python server.py), then: python client.py
# To see the actual resume (Last-Event-ID) in action, run: python resume_demo.py
from mcp.client.streamable_http import streamable_http_client
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

port = 3000

# I get notifications and exceptions
async def message_handler(
        message: types.ServerNotification | Exception,
    ) -> None:
        if isinstance(message, Exception):
            raise message
        print("NOTIFICATION:", message.method)

async def main():
    print("Starting client...")
    # Connect to a streamable HTTP server
    async with streamable_http_client(f"http://localhost:{port}/mcp") as (
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

            # Call a tool
            tool_result = await session.call_tool("process-files", {})

            print("Tool result:", tool_result.content[0].text)


asyncio.run(main())
