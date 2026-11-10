# server.py
# Streamable HTTP MCP server (MCP Python SDK v2: pip install "mcp[cli]>=2")
# v1 -> v2 changes:
#   from mcp.server.fastmcp import FastMCP, Context
#   -> from mcp.server import MCPServer / from mcp.server.mcpserver import Context
# Run:  python server.py        -> http://localhost:8000/mcp
from mcp.server import MCPServer
from mcp.server.mcpserver import Context

# Create an MCP server
mcp = MCPServer("Streamable DEMO")

@mcp.tool(description="A simple tool returning file content")
async def echo(message: str, ctx: Context) -> str:

    # await ctx.debug(f"Processing file 1/3: {message}")
    # Each ctx.info() is sent to the client as a log notification
    # while the tool is still running - that's the "streaming" part.
    await ctx.info(f"Processing file 1/3:")
    await ctx.info(f"Processing file 2/3:")
    await ctx.info(f"Processing file 3/3:")

    # await ctx.log(
    #         level="info",
    #         message="hello there",
    #         logger_name="Obi Wan",
    #     )

    return f"Here's the file content: {message}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
