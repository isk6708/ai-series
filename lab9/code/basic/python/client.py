# client.py - calls the protected server with a bearer token. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - streamablehttp_client(url, headers=...) -> streamable_http_client(url, http_client=...)
#     The Authorization header now goes on the HTTP client you pass in.
#   - it yields (read, write); the session-id callback is gone
#   - message_handler receives only notifications or exceptions
#     (RequestResponder / mcp.shared.session were removed)
#   - a rejected token now prints a clear message instead of a long traceback
#   - try another token without editing the code:  python client.py secret-token2
#
# Start the server first: python server.py
import asyncio
import logging
import sys

from mcp import ClientSession
import mcp.types as types
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.shared.exceptions import MCPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mcp_client')

port = 8000
TOKEN = sys.argv[1] if len(sys.argv) > 1 else "secret-token"


class LoggingCollector:
    def __init__(self):
        self.log_messages: list[types.LoggingMessageNotificationParams] = []
    async def __call__(self, params: types.LoggingMessageNotificationParams) -> None:
        self.log_messages.append(params)
        logger.info("MCP Log: %s - %s", params.level, params.data)

logging_collector = LoggingCollector()

# Remember the last HTTP error status, to explain a rejection clearly
last_http_error: dict = {}

async def remember_http_errors(response) -> None:
    if response.status_code >= 400:
        last_http_error["status"] = response.status_code
        last_http_error["reason"] = response.reason_phrase


async def message_handler(message: types.ServerNotification | Exception) -> None:
    if isinstance(message, Exception):
        logger.error("Exception received!")
        raise message
    logger.info("NOTIFICATION: %s", message)


async def main():
    logger.info("Starting client with token: %s", TOKEN)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with create_mcp_http_client(headers=headers) as http_client:
        http_client.event_hooks["response"].append(remember_http_errors)
        async with streamable_http_client(
            f"http://localhost:{port}/mcp", http_client=http_client
        ) as (read_stream, write_stream):
            async with ClientSession(
                read_stream,
                write_stream,
                logging_callback=logging_collector,
                message_handler=message_handler
            ) as session:
                await session.initialize()
                logger.info("Session initialized, ready to call tools.")
                tool_result = await session.call_tool("get_time", {})
                logger.info("Tool result: %s", tool_result.structured_content)


def contains_mcp_error(exc: BaseException) -> bool:
    """True if an MCPError is anywhere inside this exception (or group)."""
    if isinstance(exc, MCPError):
        return True
    return any(contains_mcp_error(e) for e in getattr(exc, "exceptions", []) or [])


if __name__ == "__main__":
    logger.info("Running MCP client...")
    try:
        asyncio.run(main())
    except BaseException as e:
        if not (last_http_error and contains_mcp_error(e)):
            raise
        status = last_http_error["status"]
        meaning = {401: "no credentials sent", 403: "credentials sent but not accepted"}.get(status, "")
        logger.error("Server rejected the request: HTTP %s %s%s", status,
                     last_http_error["reason"], f" ({meaning})" if meaning else "")
        sys.exit(1)
