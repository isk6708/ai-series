# Run sample

Shows how MCP tool input is **validated** with a Pydantic model before your tool code runs.

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Set up

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install "mcp[cli]>=2"
```

## Run server and client

Start the Inspector. It starts the server for you, so you don't need `python server.py` first:

```sh
mcp dev server.py
```

or, without the `mcp` CLI:

```sh
npx @modelcontextprotocol/inspector python server.py
```

(The book's `npx @modelcontextprotocol/inspector server.py` doesn't work, because the Inspector needs the command that starts the server, i.e. `python server.py`.)

Connect to the server and run the tool `create_user`.

Try the different tool payloads to see different validation scenarios.

1. Success case (provides all mandatory fields):

   ```json
   {
     "id": 0,
     "name": "chris",
     "email": "chris@example.com"
   }
   ```

   Result: `{"id": 1, "name": "chris", "email": "chris@example.com"}`. The server assigns the id; `id` is optional, so you can leave it out.

2. Validation error (shows that your validation works as we omit the email):

   ```json
   {
     "id": 0,
     "name": "chris"
   }
   ```

   Result: `1 validation error ... user.email  Field required`

3. Validation error (an email that doesn't look like one):

   ```json
   {
     "name": "chris",
     "email": "not-an-email"
   }
   ```

   Result: `1 validation error ... user.email  String should match pattern ...`

In all error cases, `create_user` never runs. Pydantic rejects the input first, and the client gets the
reason back as a tool error.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server import MCPServer` |
| `print("Starting MCP server...")` to stdout (breaks stdio) | Printed to stderr |
| `id` required, although the server overwrites it | Optional |
| Any string accepted as email | Must match an email pattern, which gives a third case to try |
| `npx @modelcontextprotocol/inspector server.py` | `mcp dev server.py` or `npx @modelcontextprotocol/inspector python server.py` |
