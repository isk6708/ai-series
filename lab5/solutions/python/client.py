# client.py - interactive stdio client (MCP Python SDK v2)
# Changes from the original:
#   - tool.inputSchema -> tool.input_schema (renamed in v2)
#   - starts the server with the current Python (sys.executable server.py)
#     instead of the `mcp` command, so it works without the mcp CLI on PATH
#   - prints the result text instead of raw TextContent objects
# Run: python client.py   (it starts server.py itself - no separate terminal)
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).with_name("server.py"))

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command=sys.executable,  # Executable (same Python / venv as this client)
    args=[SERVER],  # Optional command line arguments
    env=None,  # Optional environment variables
)
# Original (needs the mcp CLI on PATH):
# server_params = StdioServerParameters(command="mcp", args=["run", "server.py"], env=None)

def show_result(result):
    for item in result.content:
        print("Result: ", item.text if hasattr(item, "text") else item)
    if result.is_error:
        print("(the tool reported an error)")

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            mcp_tools = await session.list_tools()
            print("LISTING TOOLS")

            tools = []

            for tool in mcp_tools.tools:
                print("Tool: ", tool.name)
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                })

            while True:
                command = input("Enter command (or 'quit' to exit): ").strip()
                if command == "quit":
                    break
                # Process other commands as needed

                # if command in tools, then call the tool
                if command in [tool["name"] for tool in tools]:
                    # Find the tool
                    tool = next((t for t in tools if t["name"] == command), None)
                    if tool:
                        print(f"Using tool: {tool['name']}")

                        # Prepare the arguments for the tool
                        arguments = {}
                        print("Tool arguments:", tool["parameters"])
                        for param in tool["parameters"].get("properties", {}):
                            print(f"Parameter: {param}")
                            arguments[param] = input(f"Enter {param}: ")

                        result = await session.call_tool(tool["name"], arguments=arguments)

                        show_result(result)
                elif command:
                    print("Unknown command. Tools:", ", ".join(t["name"] for t in tools))




if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
