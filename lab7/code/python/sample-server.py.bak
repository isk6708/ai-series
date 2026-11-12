# sample-server.py - SAMPLING demo: the server asks the CLIENT's LLM to write
# a product description. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   from mcp.server.fastmcp import Context, FastMCP
#   -> from mcp.server import MCPServer / from mcp.server.mcpserver import Context
#   - startup message goes to stderr (stdout is reserved for MCP messages)
#   - max_tokens 100 -> 300 so descriptions aren't cut off mid-sentence
#   - Product model: id is optional so get_products' output can be validated
#
# Note: sampling (ctx.session.create_message) is deprecated as of MCP protocol
# 2026-07-28 but still works with clients on earlier protocol versions, like
# sample-client.py. The deprecation warning is hidden below.
import json
import sys
import warnings
from typing import List, Optional

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import SamplingMessage, TextContent

warnings.filterwarnings("ignore", message="The sampling capability is deprecated")

mcp = MCPServer(name="Sampling Example")

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str

products: List[Product] = []

@mcp.tool()
def get_products() -> list[Product]:
    """List all products."""
    return products

# @mcp.tool()
# def get_products() -> [Product]:
#     """List all products."""
#     return [{"type": "text", "name": f"ID: {item.id}, product: {item.name}, description: {item.description}"} for item in products]

@mcp.tool()
async def create_product(product_name: str, keywords: str, ctx: Context) -> str:
    """Create a product and generate a product description using LLM sampling."""

    product = Product(id=len(products) + 1, name=product_name, description="")

    prompt = f"Create a product description about {product_name} described by as {keywords}"

    # Ask the client's LLM to write the description (this is "sampling")
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=300,
    )


    product.description = result.content.text

    products.append(product)

    # return the complete product
    return json.dumps({
        "id": product.id,
        "name": product.name,
        "description": product.description
    })

if __name__ == "__main__":
    print("Starting server...", file=sys.stderr)
    mcp.run()
