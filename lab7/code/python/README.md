# Run sample

This sample shows **sampling**: the *server* asks the *client's* LLM to write something for it.
Here, `sample-server.py` has a `create_product` tool that asks the client to write a product
description; `sample-client.py` answers that request by calling an LLM.

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

| File | What it is |
|---|---|
| `sample-server.py` | Server (stdio) with `create_product` (uses sampling) and `get_products` |
| `sample-client.py` | Client: calls the tools and answers the server's sampling requests with an LLM |
| `sample-server-sse.py` | The same server over the legacy SSE transport (port 8000) |
| `llm.py` | Which LLM the client uses: GitHub Models, OpenAI (ChatGPT API) or Ollama, from `.env` |
| `.env.example` | Template for `.env` |

## Set up environment

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
```

## Install dependencies

```sh
pip install "mcp[cli]>=2" openai
```

## Choose the LLM

```sh
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Then edit `.env`:

| `LLM_PROVIDER` | Cost | What to put in `.env` | Default model |
|---|---|---|---|
| `github` (default) | Free tier | `GITHUB_TOKEN=` token with **Models: read** | `openai/gpt-4o-mini` |
| `openai` | Paid | `OPENAI_API_KEY=` your ChatGPT API key | `gpt-4o-mini` |
| `ollama` | Free, local | nothing (run `ollama pull llama3.2` first) | `llama3.2` |

Override the model with `MODEL_NAME`. `.env` is ignored by git.

## Run

```sh
python sample-client.py
```

The client starts `sample-server.py` itself. You should see an output similar to:

```text
LLM: github / openai/gpt-4o-mini  (https://models.github.ai/inference)
Starting server...
Sampling request: [SamplingMessage(role='user', content=TextContent(type='text', text='Create a product description about paprika described by as red, juicy, vegetable', ...))]
result: {"id": 1, "name": "paprika", "description": "**Product Description: Paprika – The Vibrant Touch of Flavor** ..."}
result: {
  "id": 1,
  "name": "paprika",
  "description": "**Product Description: Paprika – The Vibrant Touch of Flavor** ..."
}
```

What happened:

1. The client called the `create_product` tool.
2. Instead of writing the description itself, the server sent a **sampling request** back to the client (`Sampling request: ...`).
3. The client's `handle_sampling_message` called the LLM and returned its text.
4. The server saved the product with that description and returned it. `get_products` then lists it.

## The SSE version

```sh
python sample-server-sse.py
```

It serves `http://127.0.0.1:8000/sse`. To try it, open the Inspector (`npx @modelcontextprotocol/inspector`),
choose **SSE**, connect, and run `create_product`. The Inspector shows the sampling request and lets you
type the reply yourself.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import Context, FastMCP` | `from mcp.server import MCPServer`, `from mcp.server.mcpserver import Context` |
| `Context[ServerSession, None]` | `Context` |
| Client callback took `RequestContext[ClientSession, None]` (`mcp.shared.context`) | `ClientRequestContext` (`mcp.client.context`) |
| `CreateMessageResult(stopReason=...)`, `params.systemPrompt` | `stop_reason=...`, `params.system_prompt` |
| Client ignored the server's `max_tokens` / `temperature` and reported a fake model name | Uses the server's values and reports the real model |
| `max_tokens=100` (descriptions cut off mid-sentence) | `max_tokens=300` |
| `print("Starting server...")` to stdout (corrupts the stdio connection) | Printed to stderr |
| Server started with `python sample-server.py` (relative path, whichever `python` is first) | Same Python as the client, absolute path |
| `Product` had a custom `__init__` that broke `get_products`' output | `id` is an optional field |
| `sample-server-sse.py`: `python ...` ran stdio, not SSE | Starts the SSE server on port 8000 |
| GitHub Models only, `GITHUB_TOKEN` from the terminal | `github`, `openai` or `ollama` from `.env` |

> Sampling is deprecated as of MCP protocol 2026-07-28, but it still works with clients on earlier
> protocol versions, like this one. The servers hide the deprecation warning.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `GITHUB_TOKEN is not set` / `OPENAI_API_KEY is not set` | Create `.env` (copy `.env.example`) and add the key for your `LLM_PROVIDER` |
| `No module named 'openai'` | `pip install openai` |
| `No module named 'mcp.server.fastmcp'` | You're running v1 code (`original_v1/`) on SDK v2 |
| `Sampling not supported` error from the tool | The client has no `sampling_callback`. Use `sample-client.py` or the Inspector |
