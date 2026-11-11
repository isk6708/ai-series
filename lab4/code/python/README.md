# Running this sample

A **low-level** MCP server: instead of `MCPServer` decorators, you build the tool list,
JSON schemas and handlers yourself, and wire the SSE transport into Starlette by hand.
Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept,
unchanged, in [`original_v1/`](./original_v1/).

| File / folder | What it is |
|---|---|
| `server.py` | Low-level server with an `add` tool and an `example-prompt` prompt, served over SSE on port 8000 |
| `client.py` | SSE client: lists tools, calls `add` (good and bad input), lists and gets the prompt |
| `tools/` | Tool registry: `schema.py` (Pydantic input model), `add.py` (handler), `__init__.py` (the `tools` dict) |
| `context-manager.py` | Plain Python example of a context manager (`with … as …`), the pattern the SDK uses for connections |
| `learn/` | Empty placeholders for exercises |

## Install

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install "mcp[cli]>=2" uvicorn
```

## Run

Terminal 1:

```bash
python server.py
```

Terminal 2:

```bash
python client.py
```

You should see:

```text
Session initialized
Tool: add - Adds two numbers - input: {'properties': {'a': {'type': 'number'}, 'b': {'type': 'number'}}, 'required': ['a', 'b'], 'type': 'object'}
Tool result: 3.0
Tool error: True - Error calling tool add: Invalid input: 1 validation error for AddInputModel
...
Available prompts: ['example-prompt']
Prompt: Example prompt text value
```

## Test with the Inspector

```bash
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --transport sse --method tools/list
npx @modelcontextprotocol/inspector --cli http://localhost:8000/sse --transport sse --method tools/call --tool-name add --tool-arg a=1 --tool-arg b=2
```

Or run `npx @modelcontextprotocol/inspector`, choose **SSE**, enter `http://localhost:8000/sse` and click **Connect**.

## Add your own tool

1. In `tools/schema.py`, add an input model, e.g. `class MultiplyInputModel(BaseModel): a: float; b: float`.
2. Create `tools/multiply.py` with an `async def multiply_handler(args)` and a `tool_multiply = {"name": …, "description": …, "input_schema": …, "handler": …}` dict (copy `add.py`).
3. Register it in `tools/__init__.py`: `tool_multiply["name"]: tool_multiply`.

`server.py` needs no changes: it builds the tool list and schemas from the `tools` dict.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `@server.list_tools()`, `@server.call_tool()`, `@server.list_prompts()`, `@server.get_prompt()` | Handlers passed in: `Server("…", on_list_tools=…, on_call_tool=…, on_list_prompts=…, on_get_prompt=…)` |
| Handlers took `(name, arguments)` and returned plain lists | Handlers take `(ctx, params)` and return `ListToolsResult`, `CallToolResult`, `ListPromptsResult`, `GetPromptResult` |
| `types.Tool(inputSchema=…)` | `types.Tool(input_schema=…)` |
| `model_cls.schema()` (deprecated in Pydantic v2) | `model_cls.model_json_schema()` |
| Tool errors raised `ValueError` | Returned as `CallToolResult(is_error=True)` so the client sees the actual message |
| `uvicorn.run(...)` ran on import | Under `if __name__ == "__main__":` |
| `client.py` called `get_prompt("example-prompt")` without its required `arg1` | Passes `arguments={"arg1": "value"}` |
| Unused imports `NotificationOptions`, `InitializationOptions` | Removed |

The SSE wiring (`SseServerTransport("/messages/")`, `connect_sse`, `/sse` + `/messages/` routes) is unchanged in v2.
`tools/`, `context-manager.py` and `learn/` needed no changes.

> SSE is the legacy transport. Chapter 5 covers Streamable HTTP (`/mcp`), the current one.
