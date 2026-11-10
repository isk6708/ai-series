# sse-server.py
# Same echo tool, served over the legacy SSE transport (superseded by
# Streamable HTTP - see server.py). MCP Python SDK v2.
# Run:  python sse-server.py              -> http://localhost:8000/sse
#   or: uvicorn sse-server:app --port 8000
from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import TextContent

# Create an MCP server
mcp = MCPServer("SSE DEMO")

@mcp.tool(description="A simple tool returning file content")
async def echo(message: str, ctx: Context) -> TextContent:

    # await ctx.debug(f"Processing file 1/3: {message}")
    await ctx.info(f"Processing file 1/3:")
    await ctx.info(f"Processing file 2/3:")
    await ctx.info(f"Processing file 3/3:")

    # await ctx.log(
    #         level="info",
    #         message="hello there",
    #         logger_name="Obi Wan",
    #     )

    return TextContent(type="text", text=f"Here's the file content: {message}")

# SSE serves /sse (stream) and /messages/ (client posts).
# No lifespan needed: only Streamable HTTP has a session manager.
app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
