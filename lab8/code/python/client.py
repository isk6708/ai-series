# client.py - calls book_trip and ANSWERS THE SERVER'S ELICITATION REQUEST.
# MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - elicitation callback receives (context: ClientRequestContext, params)
#     (mcp.shared.context.RequestContext was removed)
#   - connects over Streamable HTTP (/mcp) by default; `python client.py sse`
#     uses the legacy SSE endpoint (/sse) like the original
#   - choose the answer from the command line instead of editing the code:
#       python client.py            -> accept, pick 2025-01-01 (default)
#       python client.py no         -> accept, but don't check another date
#       python client.py decline    -> decline the request
#       python client.py ask        -> type the answers yourself
#     (add "sse" to any of these to use /sse)
#
# Start the server first: uvicorn server:app

import asyncio
import sys

from mcp import ClientSession
from mcp.client.context import ClientRequestContext
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import ElicitRequestParams, ElicitResult

BASE_URL = "http://localhost:8000"
args = [a.lower() for a in sys.argv[1:]]
USE_SSE = "sse" in args
MODE = next((a for a in args if a in ("no", "decline", "ask")), "yes")


async def elicitation_callback_handler(context: ClientRequestContext, params: ElicitRequestParams):
    print(f"[CLIENT] Received elicitation data: {params.message}")
 
    # 1. refuses to select another date -> "No booking made"
    if MODE == "no":
        print("[CLIENT]: Not checking another date")
        return ElicitResult(action="accept", content={
            "checkAlternative": False
        })

    # 2. cancels the whole dialogue -> "Booking cancelled"
    if MODE == "decline":
        print("[CLIENT]: Declining")
        return ElicitResult(action="decline")

    # 4. user-driven: ask in the terminal
    if MODE == "ask":
        answer = input("Check another date? (y/n): ").strip().lower()
        if answer != "y":
            return ElicitResult(action="accept", content={"checkAlternative": False})
        date = input("Alternative date (YYYY-MM-DD): ").strip() or "2024-12-26"
        return ElicitResult(action="accept", content={
            "checkAlternative": True,
            "alternativeDate": date
        })

    print("[CLIENT]: Selecting alternative date: 2025-01-01")

    # 3. opts to select another date, 2025-01-01 which leads to a booking
    return ElicitResult(action="accept", content={
         "checkAlternative": True,
         "alternativeDate": "2025-01-01"
    }) # should book 1 jan instead of initial 2nd Jan


async def run_session(read_stream, write_stream):
    # Create a session using the client streams
    async with ClientSession(
        read_stream,
        write_stream,
        elicitation_callback=elicitation_callback_handler) as session:
        # Initialize the connection
        await session.initialize()
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")

        # call tool
        result = await session.call_tool("book_trip", {
            "date": "2025-01-02"
        })
        print("Result: ", result.content[0].text)


async def main():
    if USE_SSE:
        # Connect to a Server-Sent Events (SSE) server
        async with sse_client(url=f"{BASE_URL}/sse") as (read_stream, write_stream):
            await run_session(read_stream, write_stream)
    else:
        async with streamable_http_client(f"{BASE_URL}/mcp") as (read_stream, write_stream):
            await run_session(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
