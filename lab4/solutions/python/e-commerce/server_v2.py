"""E-commerce MCP server for MCP Python SDK 2.x.

Same tools, prompt and SSE endpoint as server.py, but written for SDK 2.x, where
the low-level Server takes on_* handler functions in its constructor instead of
the @server.list_tools() / @server.call_tool() decorators used by SDK 1.x.

Run with:  python server_v2.py   (then connect to http://localhost:8000/sse)
"""
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

import tools
from tool_utils import pydantic_to_json, run_tool


async def handle_list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name=tool["name"],
                description=tool["description"],
                input_schema=pydantic_to_json(tool["input_schema"]),
            )
            for tool in tools.tools.values()
        ]
    )


async def handle_call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    try:
        text = await run_tool(params.name, params.arguments)
    except ValueError as e:
        # report the error to the client/LLM instead of crashing the request
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=str(e))], is_error=True
        )
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)])


async def handle_list_prompts(ctx, params) -> types.ListPromptsResult:
    return types.ListPromptsResult(
        prompts=[
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
    )


async def handle_get_prompt(ctx, params: types.GetPromptRequestParams) -> types.GetPromptResult:
    if params.name != "example-prompt":
        raise ValueError(f"Unknown prompt: {params.name}")

    return types.GetPromptResult(
        description="Example prompt",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text="Example prompt text"),
            )
        ],
    )


server = Server(
    "e-commerce-server",
    on_list_tools=handle_list_tools,
    on_call_tool=handle_call_tool,
    on_list_prompts=handle_list_prompts,
    on_get_prompt=handle_get_prompt,
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
