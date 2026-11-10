# Running this sample

This sample shows **streaming** in MCP: while a tool runs, the server sends progress
messages ("Processing file 1/3…") to the client before the final result arrives.

It uses the official MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept,
unchanged, in [`original_v1/`](./original_v1/) for reference. It won't run on `mcp>=2`.

| File | What it is | Transport / URL |
|---|---|---|
| `server.py` | MCP server with an `echo` tool that streams progress | Streamable HTTP, `http://localhost:8000/mcp` |
| `client.py` | MCP client for `server.py` (prints the progress messages, then the result) | Streamable HTTP |
| `sse-server.py` | Same `echo` tool over the **legacy** SSE transport | SSE, `http://localhost:8000/sse` |
| `sse-client.py` | MCP client for `sse-server.py` | SSE |
| `_client.py` | No MCP SDK: talks to `server.py` with plain HTTP requests so you can see the raw stream | Streamable HTTP |
| `test_client.py` | No MCP SDK: sends a single raw `initialize` request to `server.py` | Streamable HTTP |
| `main.py` | Notes/stub for building your own server by hand (exercise; not runnable) | none |
| `resumeability.md` | `curl` walkthrough for the [`../resumability`](../resumability/) sample | Streamable HTTP |

> **Streamable HTTP (`/mcp`) is the current transport.** SSE (`/sse`) was replaced by it in the
> MCP spec (2025-03-26); the SDK still supports SSE so older clients keep working.

## Installing dependencies

First, create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Then install the dependencies:

```sh
pip install "mcp[cli]>=2" uvicorn requests
```

`requests` is only needed for `_client.py` and `test_client.py`.

## Starting the server

Start the server by running the following command in the terminal:

```bash
python server.py
```

It listens on `http://localhost:8000/mcp`. Leave it running.

Now run the client in a separate terminal (activate the same virtual environment first):

```bash
python client.py
```

You will see an output similar to this:

```text
Starting client...
Session initialized, ready to call tools.
LOG: Processing file 1/3:
NOTIFICATION: method='notifications/message' params=LoggingMessageNotificationParams(meta=None, level='info', logger=None, data='Processing file 1/3:')
LOG: Processing file 2/3:
NOTIFICATION: method='notifications/message' params=LoggingMessageNotificationParams(meta=None, level='info', logger=None, data='Processing file 2/3:')
LOG: Processing file 3/3:
NOTIFICATION: method='notifications/message' params=LoggingMessageNotificationParams(meta=None, level='info', logger=None, data='Processing file 3/3:')
Tool result: Here's the file content: hello
Log messages received: 3
```

This output shows you all your notifications and the result of the tool call.
Each `Processing file …` line is sent by `await ctx.info(...)` in `server.py` **while the tool is still running**;
the client receives it twice: once in `logging_callback` (the `LOG:` line) and once in `message_handler` (the `NOTIFICATION:` line).

## See the raw stream (no SDK)

With `server.py` still running:

```bash
python _client.py
```

It does the MCP handshake by hand (`initialize` → `notifications/initialized` → `tools/list` → `tools/call`).
The tool call comes back as a stream of server-sent events, one per message:

```text
Calling tool: echo...
event: message
data: {"jsonrpc":"2.0","method":"notifications/message","params":{"level":"info","data":"Processing file 1/3:"}}
event: message
data: {"jsonrpc":"2.0","method":"notifications/message","params":{"level":"info","data":"Processing file 2/3:"}}
event: message
data: {"jsonrpc":"2.0","method":"notifications/message","params":{"level":"info","data":"Processing file 3/3:"}}
event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"text":"Here's the file content: chris","type":"text"}],"isError":false,"structuredContent":{"result":"Here's the file content: chris"}}}
```

For just the first step of the handshake:

```bash
python test_client.py
```

```text
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"capabilities":{...},"protocolVersion":"2024-11-05","serverInfo":{"name":"Streamable DEMO","version":""}}}
```

## Compare with the legacy SSE transport

Stop `server.py` first (Ctrl+C), because both servers use port 8000. Then:

```bash
python sse-server.py
```

(or `uvicorn sse-server:app --port 8000`). In another terminal:

```bash
python sse-client.py
```

The output is the same as `client.py`. The difference is how the messages travel:

| | Streamable HTTP (`server.py`) | SSE (`sse-server.py`) |
|---|---|---|
| URLs | One: `/mcp` | Two: `/sse` (stream) + `/messages/` (client posts) |
| Where progress and result arrive | On the response to the same `POST /mcp` | On the separate, always-open `GET /sse` stream |
| Status | Current | Superseded; kept for older clients |

## Test with the Inspector

With either server running:

```bash
npx @modelcontextprotocol/inspector
```

Choose **Streamable HTTP** + `http://localhost:8000/mcp` (or **SSE** + `http://localhost:8000/sse`), click **Connect**,
then **Tools → echo**. The progress messages appear in the notifications panel.

Or let `mcp dev` start the server itself over stdio (needs Node.js and `uv`):

```bash
mcp dev server.py
```

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import FastMCP, Context` | `from mcp.server import MCPServer` and `from mcp.server.mcpserver import Context` |
| `FastMCP("…")` | `MCPServer("…")` |
| `mcp.run(transport="streamable-http")` at module level | same call, inside `if __name__ == "__main__":` with `port=8000` |
| `streamablehttp_client(url)` → `(read, write, session_callback)` | `streamable_http_client(url)` → `(read, write)`. Newer protocol versions don't need a session id |
| `sse_client(url)` unpacked into 3 values (a bug) | `sse_client(url)` → `(read, write)` |
| `message_handler` received requests, notifications or exceptions | receives only notifications or exceptions |
| `sse-server.py` had no way to run it | `python sse-server.py` or `uvicorn sse-server:app --port 8000` |
| `test_client.py` posted to `/stream` (404) | posts to `/mcp` |

`_client.py` needed no changes. It talks plain HTTP and the v2 server still accepts older protocol versions.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No module named 'mcp.server.fastmcp'` | You're running the v1 code (`original_v1/`) on SDK v2. Use the files in this folder |
| `cannot import name 'MCPServer'` | Your environment has SDK v1: `pip install -U "mcp[cli]>=2"` |
| `address already in use` / `[Errno 10048]` | Another server is on port 8000. Stop it (Ctrl+C) before starting the other one |
| Client: `All connection attempts failed` | The server isn't running, or you started the wrong one (`client.py` needs `server.py`; `sse-client.py` needs `sse-server.py`) |
| `test_client.py` prints `Not Found` | You're running the original from `original_v1/` (it posts to `/stream`) |
