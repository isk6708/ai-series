## Run sample

Here's the solution for the assignment: a `talk_to` tool that lets you chat with a character from
[`../characters.json`](../characters.json). The **server** builds the character's persona as a system
prompt and asks the **client's** LLM to answer in character (sampling).

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Setup

Make sure you have set up a virtual environment like so:

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
```

## Install

```sh
pip install "mcp[cli]>=2" openai
```

## Choose the LLM

Copy `.env.example` to `.env` and set `LLM_PROVIDER` (`github`, `openai` or `ollama`) and its key,
exactly as in [`../../code/python/README.md`](../../code/python/README.md#choose-the-llm).

## Run

Run it with the following command:

```sh
python client.py
```

You should see a result similar to:

```text
LLM: github / openai/gpt-4o-mini  (https://models.github.ai/inference)
Starting server...
Sampling request: [SamplingMessage(role='user', content=TextContent(type='text', text='Talk to Monsieur Lestrange. Discuss the topic of Tell me about you.', ...))]
result: Ah, bonsoir, my dear interlocutor! It is a pleasure to make your acquaintance. As you may have surmised, I am Monsieur Lestrange, a vampire of some six centuries in age. ...

Ah, the electricity bill! It is a bane of my existence, I assure you. ...
```

The server sends its own system prompt (`You are Monsieur Lestrange, a 600 year old vampire, ...`),
`temperature=0.9` and `max_tokens=4000` with the sampling request, and the client passes all three to the LLM.

## Try it yourself

- Change the topic in `client.py`, e.g. `"topic": "vampire hunters"`, and watch him steer back to his electricity bill.
- Add another character to `../characters.json` and talk to it by name. Names match regardless of case.
  An unknown name returns: `No character called '...'. Available: ...`

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import Context, FastMCP` | `from mcp.server import MCPServer`, `from mcp.server.mcpserver import Context` |
| `open("../characters.json")` only worked when started from `solution/python` | Found relative to `server.py`, from any folder |
| Unknown character crashed with `TypeError: 'NoneType' object is not subscriptable` | Clear error listing the available characters |
| `params.systemPrompt`, `stopReason=` | `params.system_prompt`, `stop_reason=` |
| Client always sent `max_tokens=200`, `temperature=1` (so long answers were cut off) | Uses the server's `max_tokens` and `temperature` |
| `print("Starting server...")` to stdout | Printed to stderr (stdout is reserved for MCP messages) |
| GitHub Models only | `github`, `openai` or `ollama` from `.env` |
