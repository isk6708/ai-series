# Run sample

This sample starts an MCP Server with a middleware that checks for a valid Authorization header.

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Install dependencies

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
pip install "mcp[cli]>=2" uvicorn
```

## Start server

```bash
python server.py
```

It serves `http://localhost:8000/mcp`. Start the client in another terminal:

```bash
python client.py
```

You should see a result similar to:

```text
2026-11-09 16:43:09 - mcp_client - INFO - Tool result: {'current_time': '2026-11-09T16:43:09.655201', 'timezone': 'UTC', 'timestamp': 1794213789.655201, 'formatted': '2026-11-09 16:43:09'}
```

This means the credential being sent through is being allowed.

Try a different credential. You don't need to edit `client.py`; pass it on the command line:

```bash
python client.py secret-token2
```

You should see:

```text
... - httpx2 - INFO - HTTP Request: POST http://localhost:8000/mcp "HTTP/1.1 403 Forbidden"
... - mcp_client - ERROR - Server rejected the request: HTTP 403 Forbidden (credentials sent but not accepted)
```

This means you were authenticated (you had a credential), but it was invalid. With no `Authorization` header at all,
the server returns **401 Unauthorized** instead. Try `curl -X POST http://localhost:8000/mcp` (on Windows: `curl.exe`).

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp.server import FastMCP`, with `host`/`port` settings | `from mcp.server import MCPServer`; uvicorn gets host and port |
| Imported `pydantic_settings`, which SDK v2 doesn't install, so the server crashed on startup | Unused imports removed |
| `streamablehttp_client(url, headers={...})` | `streamable_http_client(url, http_client=create_mcp_http_client(headers={...}))` |
| Client used the session-id callback and `RequestResponder` | Removed in v2 |
| A rejected token ended in a long traceback | One clear line with the HTTP status |
| Edit `client.py` to try another token | `python client.py <token>` |
