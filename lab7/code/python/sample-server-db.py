# sample-server-db.py - SAMPLING demo: the server asks the CLIENT's LLM to write
# a product description, then saves the product in SQLite. MCP Python SDK v2.
#
# v1 -> v2 changes:
#   from mcp.server.fastmcp import Context, FastMCP
#   -> from mcp.server import MCPServer / from mcp.server.mcpserver import Context
#   - startup message goes to stderr (stdout is reserved for MCP messages)
#   - max_tokens 100 -> 300 so descriptions aren't cut off mid-sentence
#   - Product model: id is optional so get_products' output can be validated
#
# Storage: products are saved in SQLite (products.db next to this script) so
# they survive server restarts. Override the location with PRODUCTS_DB=/path.
# sqlite3 is part of Python's standard library - nothing to pip install.
#
# Note: sampling (ctx.session.create_message) is deprecated as of MCP protocol
# 2026-07-28 but still works with clients on earlier protocol versions, like
# sample-client.py. The deprecation warning is hidden below.
import json
import os
import sqlite3
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import (
    CreateMessageRequest,
    CreateMessageRequestParams,
    InputRequiredResult,
    SamplingMessage,
    TextContent,
)
from mcp_types.version import MODERN_PROTOCOL_VERSIONS

warnings.filterwarnings("ignore", message="The sampling capability is deprecated")

# Absolute path: MCP clients often launch the server from another working dir.
DB_PATH = os.environ.get("PRODUCTS_DB", str(Path(__file__).resolve().parent / "products.db"))

mcp = MCPServer(name="Sampling Example (SQLite)")


class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str


# ---------------------------------------------------------------- database --

@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_product(name: str, description: str) -> Product:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, description) VALUES (?, ?)",
            (name, description),
        )
        product_id = cur.lastrowid
    return Product(id=product_id, name=name, description=description)


def row_to_product(row: sqlite3.Row) -> Product:
    return Product(id=row["id"], name=row["name"], description=row["description"])


# ------------------------------------------------------------------- tools --

@mcp.tool()
def get_products() -> list[Product]:
    """List all products stored in the database."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, description FROM products ORDER BY id"
        ).fetchall()
    return [row_to_product(r) for r in rows]


@mcp.tool()
def get_product(product_id: int) -> Product:
    """Get one product by its id."""
    with db() as conn:
        row = conn.execute(
            "SELECT id, name, description FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    if row is None:
        # The SDK turns this into a tool result with isError=True.
        raise ValueError(f"Product {product_id} not found")
    return row_to_product(row)


@mcp.tool()
def search_products(query: str) -> list[Product]:
    """Find products whose name or description contains the query text."""
    like = f"%{query}%"
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, description FROM products "
            "WHERE name LIKE ? OR description LIKE ? ORDER BY id",
            (like, like),
        ).fetchall()
    return [row_to_product(r) for r in rows]


@mcp.tool()
def delete_product(product_id: int) -> str:
    """Delete a product by its id."""
    with db() as conn:
        deleted = conn.execute(
            "DELETE FROM products WHERE id = ?", (product_id,)
        ).rowcount
    if not deleted:
        raise ValueError(f"Product {product_id} not found")
    return f"Deleted product {product_id}"


@mcp.tool()
async def create_product(product_name: str, keywords: str, ctx: Context) -> str | InputRequiredResult:
    """Create a product, generate its description using LLM sampling, and save it to the database."""

    prompt = f"Create a product description about {product_name} described by as {keywords}"
    messages = [SamplingMessage(role="user", content=TextContent(type="text", text=prompt))]

    if ctx.protocol_version in MODERN_PROTOCOL_VERSIONS:
        # 2026-07-28 clients (e.g. VS Code): no back-channel. Return the sampling
        # request as "input required"; the client runs it and calls this tool
        # again with the answer in ctx.input_responses.
        responses = ctx.input_responses or {}
        answer = responses.get("description")
        if answer is None:
            # Nothing is written to the DB yet, so the retry won't create duplicates.
            return InputRequiredResult(
                input_requests={
                    "description": CreateMessageRequest(
                        params=CreateMessageRequestParams(messages=messages, max_tokens=300)
                    )
                }
            )
        content = answer.content[0] if isinstance(answer.content, list) else answer.content
        description = content.text
    else:
        # Older handshake clients (e.g. sample-client.py): ask over the back-channel.
        result = await ctx.session.create_message(messages=messages, max_tokens=300)
        description = result.content.text

    product = insert_product(product_name, description)

    # return the complete product
    return json.dumps(
        {"id": product.id, "name": product.name, "description": product.description},
        ensure_ascii=False,
    )


# Create the table on import, so products.db is ready however the server starts.
init_db()

if __name__ == "__main__":
    print(f"Starting server... (database: {DB_PATH})", file=sys.stderr)
    mcp.run()