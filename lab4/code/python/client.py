# client.py - SSE client for server.py (MCP Python SDK v2)
# Changes from the original:
#   - get_prompt now passes the prompt's required "arg1" argument
#   - results are printed readably; an error result is shown too
# Start the server first (python server.py), then: python client.py
from mcp import ClientSession, types
from mcp.client.sse import sse_client



async def run():
    async with sse_client(url="http://127.0.0.1:8000/sse") as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            print("Session initialized")

            # # List available resources
            # resources = await session.list_resources()

            # List available tools
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name} - {tool.description} - input: {tool.input_schema}")

            result = await session.call_tool("add", arguments={"a": 1, "b": 2})
            print("Tool result:", result.content[0].text)

            # Bad input -> the server returns an error result
            result = await session.call_tool("add", arguments={"a": "one", "b": 2})
            print("Tool error:", result.is_error, "-", result.content[0].text)

            prompts = await session.list_prompts()
            print("Available prompts:", [p.name for p in prompts.prompts])

            # "example-prompt" declares arg1 as required, so pass it
            prompt = await session.get_prompt(
                "example-prompt", arguments={"arg1": "value"}
            )

            print("Prompt:", prompt.messages[0].content.text)

            # # Read a resource
            # content, mime_type = await session.read_resource("file://some/path")

            # # Call a tool
            # result = await session.call_tool("tool-name", arguments={"arg1": "value"})


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
