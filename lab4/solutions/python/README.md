# Chapter 06 – E-commerce MCP server (Python, low-level SDK)

An MCP server built with the **low-level** `Server` API of the MCP Python SDK. It exposes a small
in-memory e-commerce store (products, categories, customers, carts and orders) as MCP tools over
**SSE** at `http://localhost:8000/sse`.

## Folder layout

```
python/
├── README.md
├── requirements.txt          # pins the MCP SDK to 1.x for server.py
├── .gitignore
├── tools/                    # earlier exercise: the stand-alone "add" tool (kept for reference,
│   ├── __init__.py           #   not used by the e-commerce server)
│   ├── add.py
│   └── schema.py
└── e-commerce/
    ├── server.py             # MCP server – SDK 1.x (decorator API)
    ├── server_v2.py          # same server – SDK 2.x (constructor on_* handlers)
    ├── tool_utils.py         # shared: Pydantic → JSON Schema, tool dispatch, JSON results
    ├── client.py             # sample Python client
    ├── data.py               # in-memory sample data
    └── tools/
        ├── __init__.py       # registry of all tools
        ├── schema.py         # Pydantic models
        ├── add_to_cart.py
        ├── get_all_categories.py
        ├── get_all_customers.py
        ├── get_all_products.py
        ├── get_cart_items.py
        ├── get_carts.py
        ├── get_order.py
        ├── get_orders.py
        ├── get_product.py
        └── place_order.py
```

## Install dependencies

Create a virtual environment:

```sh
python -m venv venv
# macOS / Linux
source ./venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```sh
pip install -r requirements.txt
```

> **Which server file?** `server.py` uses the SDK 1.x decorators (`@server.list_tools()`), which
> were removed in MCP Python SDK 2.x. A plain `pip install "mcp[cli]"` now installs 2.x, and
> `server.py` then fails with `AttributeError: 'Server' object has no attribute 'list_tools'`.
> Either install from `requirements.txt` (SDK 1.x) and run `server.py`, or keep SDK 2.x and run
> `server_v2.py`. Check your version with `pip show mcp`.

## Run the server

```sh
cd e-commerce
python server.py        # SDK 1.x
# or
python server_v2.py     # SDK 2.x
```

The server listens on `http://127.0.0.1:8000/sse`.

## Tools

| Tool | Arguments | What it does |
|---|---|---|
| `get_all_products` | – | List all products |
| `get_product` | `product_id` | One product (error if not found) |
| `get_all_categories` | – | List product categories |
| `get_all_customers` | – | List customers |
| `add_to_cart` | `cart_id`, `product_id`, `quantity` | Add a product to a cart (adds to the quantity if it is already there) |
| `get_all_cart_items` | `cart_id` (optional, 0 = all) | Items in one cart or in all carts |
| `get_all_carts` | – | Each cart with its item count and total quantity |
| `place_order` | `customer_id`, `quantity`, `total_price` | Create an order; `order_id` is generated |
| `get_orders` | `customer_id` (optional, 0 = all) | Orders for one customer or all orders |
| `get_order` | `order_id` | One order (error if not found) |

Data is in memory, so it resets every time the server restarts. Sample data: customers 1–3,
products 1–3, carts 1–2, orders 1–3.

## Test the server

In a separate terminal (needs Node.js for `npx`):

List tools

```sh
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/list
```

Get all products

```sh
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name get_all_products
```

Add to cart, then view that cart

```sh
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name add_to_cart --tool-arg cart_id=1 --tool-arg product_id=3 --tool-arg quantity=2
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name get_all_cart_items --tool-arg cart_id=1
```

Place order (no `order_id` needed – the server assigns the next one)

```sh
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name place_order --tool-arg customer_id=1 --tool-arg quantity=1 --tool-arg total_price=100
```

Get orders (`customer_id=0` = all orders) and a single order

```sh
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name get_orders --tool-arg customer_id=0
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --method tools/call --tool-name get_order --tool-arg order_id=4
```

Or run the Python client, which lists tools, gets products, adds to cart 1, shows cart 1 and
fetches the example prompt:

```sh
cd e-commerce
python client.py
```

## What was fixed

- **SDK 2.x crash** – added `requirements.txt` pinning SDK 1.x for `server.py`, plus `server_v2.py`
  for SDK 2.x.
- **`add_to_cart` items never appeared** – it wrote to `carts` while `get_all_cart_items` read
  `cart_items`. It now writes to `cart_items`, validates the product, and merges repeat adds.
- **`get_order` and `get_all_carts` were not available** – `get_order.py` had no code and
  `get_carts.py` was never registered. Both are now implemented and registered.
- **`place_order`** – no longer requires a dummy `order_id`; `customer_id=0` no longer slips past
  validation.
- **`get_orders`** – `customer_id` is optional and unknown customers return an error.
  **`get_product`** – returns a clear "not found" error instead of the text `None`.
- **`get_all_cart_items`** – can filter by `cart_id`.
- **Readable results** – tools now return JSON instead of Python object reprs such as
  `[OrderModel(order_id=1, ...)]`.
- **`client.py`** – called an `add` tool this server doesn't have, and omitted the prompt's
  required `arg1`. It now calls real e-commerce tools.
- Replaced the deprecated Pydantic `.schema()` with `.model_json_schema()`.
