# Run sample

The solution: `book_trip` takes a `member_id`. If you book as `guest`, the server **elicits** whether
you'd like to become a member, and if so your name and email.

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Set up environment

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
pip install "mcp[cli]>=2" uvicorn
```

## Start server

```sh
uvicorn server:app --port 3000
```

(or `python server.py`). It serves `http://localhost:3000/mcp` and the legacy `http://localhost:3000/sse`.

## Run client

In a different terminal, run the following command:

```sh
python client.py
```

You should see output similar to:

```text
Available tools: ['book_trip']
[CLIENT] Received elicitation data: Not a member? Would you like to sign up?
[CLIENT]: Signing up as chris
Result:  [BOOKED] Booked for 2025-01-02, welcome chris as a member!
```

Other answers:

| Command | Result |
|---|---|
| `python client.py no` | `[BOOKED] for 2025-01-02, go to www.example.com to sign up if you change your mind on membership.` |
| `python client.py decline` | `[BOOKED] for 2025-01-02, go to www.example.com to sign up.` |
| `python client.py ask` | type your own name and email |

Add `sse` (e.g. `python client.py sse`) to use `/sse`.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import Context, FastMCP` | `from mcp.server import MCPServer`, `from mcp.server.mcpserver import Context` |
| `name: str = Field(...),`: the trailing comma broke the field's default and dropped its description | Comma removed |
| Client printed "Selecting alternative date" (copied from the code sample) | Prints what it actually does |
| Client callback used `RequestContext` from `mcp.shared.context` | `ClientRequestContext` from `mcp.client.context` |
| SSE only; `python server.py` started stdio | Serves `/mcp` and `/sse`; `python server.py` starts the HTTP server on port 3000 |
