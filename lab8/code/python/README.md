# Run the code

This sample demonstrates the use of Elicitation: in the middle of a tool call, the **server asks the
user for more information**. Here, `book_trip` finds no trips on your date and asks whether you'd like
another date.

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Set up environment

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
pip install "mcp[cli]>=2" uvicorn
```

## Run server

```sh
uvicorn server:app
```

(or `python server.py`). You should see:

```text
INFO:     Started server process [5016]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

The server listens on port 8000 with two transports:

| Transport | URL |
|---|---|
| Streamable HTTP (current) | `http://localhost:8000/mcp` |
| SSE (legacy, as in the book) | `http://localhost:8000/sse` |

## Test out the server in VS Code

Add an entry like so to *mcp.json*:

```json
"server": {
    "type": "http",
    "url": "http://localhost:8000/mcp"
}
```

(The book's `"type": "sse"` with `"url": "http://localhost:8000/sse"` also works.)

Start the server, then try typing the following prompt in the chat, in **Agent** mode:

```text
Book trip on 2025-02-01
```

This prompt should trigger an Elicitation scenario where you're asked for more input. Typing "2025-01-01" should lead to a successful booking:

![Elicitation example VS Code](../../assets/elicitation.png)

## Run client

In a second terminal (same virtual environment), run the following command:

```sh
python client.py
```

It should start the client and you should see the following output:

```text
Available tools: ['book_trip']
[CLIENT] Received elicitation data: No trips available on 2025-01-02. Would you like to try another date?
[CLIENT]: Selecting alternative date: 2025-01-01
Result:  [SUCCESS] Booked for 2025-01-01
```

### Try the other answers

Instead of editing the code, pass the answer you want on the command line:

| Command | Client's answer | Result |
|---|---|---|
| `python client.py` | accept, alternative date 2025-01-01 | `[SUCCESS] Booked for 2025-01-01` |
| `python client.py no` | accept, but don't check another date | `[CANCELLED] No booking made` |
| `python client.py decline` | decline the whole request | `[CANCELLED] Booking cancelled` |
| `python client.py ask` | you type the answers in the terminal | depends on what you type |

Add `sse` to any of them (e.g. `python client.py sse`) to use the legacy `/sse` endpoint.

The client's elicitation handler, which decides the answer:

```python
async def elicitation_callback_handler(context: ClientRequestContext, params: ElicitRequestParams):
    print(f"[CLIENT] Received elicitation data: {params.message}")
    ...
    # 3. opts to select another date, 2025-01-01 which leads to a booking
    return ElicitResult(action="accept", content={
         "checkAlternative": True,
         "alternativeDate": "2025-01-01"
    })
```

`action` is one of `"accept"` (with `content` matching the server's schema), `"decline"` or `"cancel"`.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import Context, FastMCP` | `from mcp.server import MCPServer`, `from mcp.server.mcpserver import Context` |
| `Context[ServerSession, None]` | `Context` |
| Client callback took `RequestContext[ClientSession, None]` (`mcp.shared.context`) | `ClientRequestContext` (`mcp.client.context`) |
| Served SSE only; `python server.py` started stdio | Serves `/mcp` and `/sse`; `python server.py` starts the HTTP server |
| Answer hard-coded; edit the file to try others | Pick it on the command line, or `ask` to type it yourself |
