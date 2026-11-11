import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

import tools
from tool_utils import pydantic_to_json, run_tool

# Create a server instance
server = Server("e-commerce-server")

# pydantic_to_json, no_params_object and the JSON result formatting now live in
# tool_utils.py so server.py (SDK 1.x) and server_v2.py (SDK 2.x) share them.

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    tool_list = []

    for tool in tools.tools.values():
        tool_list.append(
            types.Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=pydantic_to_json(tool["input_schema"]),
            )
        )
    return tool_list

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, str] | None
) -> list[types.TextContent]:
    
    # tools is a dictionary with tool names as keys; run_tool validates the
    # name, calls the handler and returns the result as JSON text
    result = await run_tool(name, arguments)

    return [
        types.TextContent(type="text", text=result)
    ]

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="example-prompt",
            description="An example prompt template",
            arguments=[
                types.PromptArgument(
                    name="arg1", description="Example argument", required=True
                )
            ],
        )
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    if name != "example-prompt":
        raise ValueError(f"Unknown prompt: {name}")

    return types.GetPromptResult(
        description="Example prompt",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text="Example prompt text"),
            )
        ],
    )

sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )
    return Response()

starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    import uvicorn
    port = 8000
    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

# start with python server.py

# requires MCP Python SDK 1.x  ->  pip install -r ../requirements.txt
# (on SDK 2.x use server_v2.py instead)

# test with: npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/list

# npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name add_to_cart --tool-arg cart_id=1 --tool-arg product_id=2 --tool-arg quantity=3
# npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name get_all_categories
