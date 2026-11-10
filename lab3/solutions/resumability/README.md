# Run the code

This is the SDK sample on resumeability, updated for the MCP Python SDK **v2** (`mcp>=2`).
The original book code (SDK v1) is kept, unchanged, in [`original_v1/`](./original_v1/) for reference.

## What is resumability?

With Streamable HTTP, a long-running tool streams its progress as events, and each event has an **id**.
The server keeps those events in an **event store**. If the connection drops halfway, the client reconnects
with a `Last-Event-ID` header and the server **replays the events it missed**, so nothing is lost.

| File | What it is |
|---|---|
| `server.py` | Low-level MCP server with a `process-files` tool that sends 3 progress events, 1 second apart |
| `event_store.py` | `InMemoryEventStore`: keeps the events so they can be replayed (demo only; use a database in production) |
| `client.py` | MCP SDK client: calls `process-files` and prints the progress events |
| `resume_demo.py` | Plain HTTP walkthrough: disconnects after the first event, then **resumes** with `Last-Event-ID` |
| `_server.py` | The SDK's fuller example, with options (`--port`, `--log-level`, `--json-response`) and a `start-notification-stream` tool |

## Install

```bash
pip install "mcp[cli]>=2" uvicorn requests
```

## Start the server

```bash
python server.py
```

It listens on `http://127.0.0.1:3000/mcp`. Leave it running and use a second terminal for the steps below.

## Test it with a client

```bash
python client.py
```

```text
Starting client...
Session initialized, ready to call tools.
LOG: [1/3] Event from 'file1.txt' - Use Last-Event-ID to resume if disconnected
NOTIFICATION: notifications/message
LOG: [2/3] Event from 'file2.txt' - Use Last-Event-ID to resume if disconnected
NOTIFICATION: notifications/message
LOG: [3/3] Event from 'file3.txt' - Use Last-Event-ID to resume if disconnected
NOTIFICATION: notifications/message
Tool result: Processed 3 files
```

## See the resume happen

```bash
python resume_demo.py
```

```text
1. Session id: 6275f8b897134a83990908c0578bab05
2. Calling process-files, reading one event, then disconnecting...
   id=78143c99-...  progress: [1/3] Event from 'file1.txt' - Use Last-Event-ID to resume if disconnected
3. Disconnected. Last-Event-ID = 78143c99-...
4. Reconnecting with Last-Event-ID - replaying what we missed:
   id=0ec94b50-...  progress: [2/3] Event from 'file2.txt' - Use Last-Event-ID to resume if disconnected
   id=27c59b9f-...  progress: [3/3] Event from 'file3.txt' - Use Last-Event-ID to resume if disconnected
   id=66badb3a-...  RESULT:   Processed 3 files
Done - no events were lost.
```

The same steps with `curl` are in [`../python/resumeability.md`](../python/resumeability.md). They work against this
server as written: copy the session id from the first response's `mcp-session-id` header, and an `id:` value from
the tool call's output as the `last-event-id`.

## Test it with the Inspector

```bash
npx @modelcontextprotocol/inspector
```

Choose **Streamable HTTP**, enter `http://127.0.0.1:3000/mcp`, click **Connect**, then **Tools → process-files → Run**.

## The fuller SDK example

Stop `server.py` first (both use port 3000), or pick another port:

```bash
python _server.py --port 3001
```

Its `start-notification-stream` tool takes `interval`, `count` and `caller`. Try it in the Inspector with
`http://127.0.0.1:3001/mcp`. Adding `--json-response` turns streaming off, so there are no events to resume.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `@app.call_tool()` / `@app.list_tools()` decorators | Handlers passed in: `Server("…", on_call_tool=call_tool, on_list_tools=list_tools)` |
| Handlers took `(name, arguments)` and returned a list / list of tools | Handlers take `(ctx, params)` and return `CallToolResult` / `ListToolsResult` |
| `ctx = app.request_context` | `ctx` is the handler's first argument |
| `types.Tool(inputSchema=…)` | `types.Tool(input_schema=…)` |
| `server.py`: `json_response=True` | `json_response=False`. JSON replies have no events, so there was nothing to resume |
| `Mount("/mcp", …)` (every request redirected to `/mcp/`) | `Route("/mcp", …)`. No redirect, so plain `curl` works |
| `uvicorn.run(...)` at module level; `_server.py` never called `main()` | Both start under `if __name__ == "__main__":` |
| `event_store.py`: `message: JSONRPCMessage` | `message: JSONRPCMessage | None`. v2 stores "priming" events with no message; they're skipped on replay |
| `client.py`: `streamablehttp_client` → 3 values; called `process_files` | `streamable_http_client` → 2 values; calls `process-files` |

> `send_log_message` is deprecated as of MCP protocol 2026-07-28 (the servers hide that warning). It still works
> for clients on older protocol versions (like these demos). New servers should prefer progress notifications
> (`ctx.report_progress` in `MCPServer`).
