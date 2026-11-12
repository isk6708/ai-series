# sample-server-sse.py - the same sampling demo served over SSE (legacy transport)
# MCP Python SDK v2.
#
# v1 -> v2 changes:
#   - MCPServer / Context imports (mcp.server.fastmcp was removed)
#   - `python sample-server-sse.py` now starts the SSE server on port 8000
#     (the original called mcp.run(), which used stdio, so the SSE app below
#     was never served that way)
#   - added get_products, like sample-server.py
#
# Run:  python sample-server-sse.py           -> http://127.0.0.1:8000/sse
#   or: uvicorn sample-server-sse:app --port 8000
# Test with the Inspector (it can answer sampling requests):
#   npx @modelcontextprotocol/inspector  -> SSE, http://127.0.0.1:8000/sse
import json
import sys
import warnings
from typing import List, Optional

from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import SamplingMessage, TextContent

warnings.filterwarnings("ignore", message="The sampling capability is deprecated")

mcp = MCPServer("My App")

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str

products: List[Product] = []

@mcp.tool()
def get_products() -> list[Product]:
    """List all products."""
    return products

@mcp.tool()
async def create_product(product_name: str, keywords: str, ctx: Context) -> str:
    """Create a product and generate a product description using LLM sampling."""

    product = Product(id=len(products) + 1, name=product_name, description="")

    prompt = f"Create a product description about {product_name} described by as {keywords}"

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


# Mount the SSE server to the existing ASGI server
app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    import uvicorn
    print("Starting SSE server on http://127.0.0.1:8000/sse", file=sys.stderr)
    uvicorn.run(app, host="127.0.0.1", port=8000)
