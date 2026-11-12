# server.py - "talk to a character": the server builds a persona prompt and
# asks the CLIENT's LLM to answer in character (sampling). MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - MCPServer / Context imports (mcp.server.fastmcp was removed)
#   - characters.json is found relative to this file, not the current folder
#     (the original only worked when started from solution/python)
#   - unknown character name -> clear ToolError (was a TypeError on None)
#   - startup message goes to stderr (stdout is reserved for MCP messages)
#
# Note: sampling is deprecated as of MCP protocol 2026-07-28 but still works
# with clients on earlier protocol versions, like client.py.
import json
import sys
import warnings
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import SamplingMessage, TextContent

warnings.filterwarnings("ignore", message="The sampling capability is deprecated")

mcp = MCPServer(name="Sampling Example")

# read file characters.json (one folder up from this file)
CHARACTERS_FILE = Path(__file__).resolve().parent.parent / "characters.json"
with open(CHARACTERS_FILE, encoding="utf-8") as f:
    characters = json.load(f)

@mcp.tool()
async def talk_to(name: str, topic: str, ctx: Context) -> str:
    """Talk to a character and get a response."""

    # load character from characters
    # loop characters to find character with property "name" = name
    character = None
    for c in characters:
        if c["name"].lower() == name.strip().lower():
            character = c
            break

    if character is None:
        names = ", ".join(c["name"] for c in characters)
        raise ToolError(f"No character called '{name}'. Available: {names}")

    system_prompt = f" You are {character['name']}, {character['description']}, {character['personality']}"

    prompt = f"Talk to {character['name']}."
    prompt += f" Discuss the topic of {topic}."
    
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        system_prompt=system_prompt,
        temperature=0.9,
        max_tokens=4000,
    )

    return result.content.text

if __name__ == "__main__":
    print("Starting server...", file=sys.stderr)
    mcp.run()
