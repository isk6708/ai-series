# server.py - low-level MCP server over SSE (MCP Python SDK v2)
#
# v1 -> v2 changes:
#   - Handlers are passed to Server(...) as on_list_tools= / on_call_tool= /
#     on_list_prompts= / on_get_prompt= instead of @server.list_tools() etc.
#   - Handlers receive (ctx, params) and return result objects
#     (ListToolsResult, CallToolResult, ListPromptsResult, GetPromptResult)
#   - types.Tool(inputSchema=...) -> types.Tool(input_schema=...)
#   - model_cls.schema() -> model_cls.model_json_schema() (Pydantic v2)
#   - Tool errors are returned as CallToolResult(is_error=True) so the client
#     sees the message instead of a generic failure
#   - uvicorn.run(...) moved under if __name__ == "__main__":
#
# The SSE plumbing (SseServerTransport, /sse + /messages/) is unchanged.
#
# Start with:  python server.py        -> http://127.0.0.1:8000/sse
import mcp.types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

import tools


def pydantic_to_json(model_cls: type) -> dict:
    schema = model_cls.model_json_schema()
    properties = {}
    required = schema.get("required", [])
    for prop, details in schema.get("properties", {}).items():
        properties[prop] = {"type": details.get("type", "string")}
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }

async def handle_list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    tool_list = []
    print(tools)

    for tool in tools.tools.values():
        tool_list.append(
            types.Tool(
                name=tool["name"],
                description=tool["description"],
                input_schema=pydantic_to_json(tool["input_schema"]),
            )
        )
    return types.ListToolsResult(tools=tool_list)

async def handle_call_tool(
    ctx: ServerRequestContext, params: types.CallToolRequestParams
) -> types.CallToolResult:
    name = params.name
    arguments = params.arguments or {}

    # tools is a dictionary with tool names as keys
    if name not in tools.tools:
        return error_result(f"Unknown tool: {name}")

    tool = tools.tools[name]

    result = "default"
    try:
        result = await tool["handler"](arguments)
    except Exception as e:
        return error_result(f"Error calling tool {name}: {str(e)}")

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=str(result))]
    )

def error_result(message: str) -> types.CallToolResult:
    """A tool error the client (and the LLM) can read."""
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)],
        is_error=True,
    )

async def handle_list_prompts(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListPromptsResult:
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


async def handle_get_prompt(
    ctx: ServerRequestContext, params: types.GetPromptRequestParams
) -> types.GetPromptResult:
    if params.name != "example-prompt":
        raise ValueError(f"Unknown prompt: {params.name}")

    arg1 = (params.arguments or {}).get("arg1", "")

    return types.GetPromptResult(
        description="Example prompt",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=f"Example prompt text {arg1}".strip()),
            )
        ],
    )

# Create a server instance (handlers are passed in, not decorated)
server = Server(
    "low-level-server",
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

port = 8000

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

# start with python server.py

# test with: npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --transport sse --method tools/list

# npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --transport sse --method tools/call --tool-name add --tool-arg a=1 --tool-arg b=2
