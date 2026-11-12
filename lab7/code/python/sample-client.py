"""
sample-client.py - calls the server's tools and ANSWERS ITS SAMPLING REQUESTS
with an LLM. MCP Python SDK v2.

Run (starts sample-server.py itself):  python sample-client.py
LLM settings: .env (copy .env.example) - see README.md

v1 -> v2 changes:
  - sampling callback receives (context: ClientRequestContext, params)
    (mcp.shared.context.RequestContext was removed)
  - CreateMessageResult(stopReason=...) -> stop_reason=...
  - the LLM call honours the server's max_tokens / temperature, and reports
    the real model name
  - LLM settings moved to llm.py + .env (github / openai / ollama)
  - server started with this Python (sys.executable) and an absolute path
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.context import ClientRequestContext
from mcp.client.stdio import stdio_client

from llm import call_llm, check_settings

SERVER = str(Path(__file__).with_name("sample-server-db.py"))

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command=sys.executable,  # Using this Python (and venv) to run the server
    args=[SERVER]
)

DEFAULT_SYSTEM_PROMPT = ("You're a helpful assistant, keep to the topic, don't make things up "
                         "too much but definitely create a compelling product description")


# The sampling callback: the server calls this when it wants an LLM answer
async def handle_sampling_message(
    context: ClientRequestContext, params: types.CreateMessageRequestParams
) -> types.CreateMessageResult:
    print(f"Sampling request: {params.messages}")

    message = params.messages[0].content.text
    system_prompt = params.system_prompt or DEFAULT_SYSTEM_PROMPT

    response, model = await call_llm(
        message,
        system_prompt,
        max_tokens=params.max_tokens,
        temperature=params.temperature if params.temperature is not None else 1.0,
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=response,
        ),
        model=model,
        stop_reason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            # tools = await session.list_tools()
            # print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool - the server will send us a sampling request
            result = await session.call_tool("create_product", arguments={"product_name": "paprika", "keywords": "red, juicy, vegetable"})
            print("result:", result.content[0].text)

            result = await session.call_tool("get_products", arguments={})
            print("result:", result.content[0].text if result.content else result.structured_content)


def main():
    """Entry point for the client script."""
    check_settings()
    asyncio.run(run())


if __name__ == "__main__":
    main()
