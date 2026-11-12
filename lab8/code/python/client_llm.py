"""
client_llm.py - chat client for the ELICITATION demo server (server.py).
MCP Python SDK v2.

You chat with an LLM (OpenAI or a local Llama via Ollama, chosen in .env).
The LLM decides when to call the server's `book_trip` tool. If the date is not
available, the server ELICITS more input mid-call - this client then asks YOU
(the human) in the terminal and sends your answer back to the server.

Setup:
    pip install openai python-dotenv          (plus the mcp SDK you already have)
    copy .env.example .env                    (then edit it)

Run (server first, in another terminal):
    uvicorn server:app                        -> http://127.0.0.1:8000
    python client_llm.py                      -> chat with the LLM
    python client_llm.py --date 2024-12-20    -> call book_trip directly, no LLM

Try: "Book me a trip on 2024-12-20"  (only 2024-12-25 is available, so the
server will ask you for another date).
"""

import argparse
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from openai import AsyncOpenAI

from mcp import ClientSession, types
from mcp.client.context import ClientRequestContext

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http").strip().lower()      # http | sse
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://127.0.0.1:8000/mcp")
MCP_SSE_URL = os.getenv("MCP_SSE_URL", "http://127.0.0.1:8000/sse")

SYSTEM_PROMPT = (
    "You are a travel booking assistant. Use the book_trip tool to book trips. "
    "The date argument must be in YYYY-MM-DD format; convert other formats yourself. "
    "Do not invent a booking result - always call the tool. "
    "After the tool returns, tell the user the outcome in one or two sentences."
)

MAX_TOOL_ROUNDS = 5   # stop runaway tool-call loops (small local models can loop)


# ------------------------------------------------------------------ LLM setup --

def make_llm() -> tuple[AsyncOpenAI, str]:
    """Return (client, model). Ollama exposes an OpenAI-compatible API, so the
    same OpenAI SDK talks to both."""
    if LLM_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            sys.exit("OPENAI_API_KEY is missing in .env")
        client = AsyncOpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
        return client, os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if LLM_PROVIDER in ("ollama", "llama"):
        client = AsyncOpenAI(
            api_key="ollama",  # Ollama ignores the key, but the SDK requires one
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )
        return client, os.getenv("OLLAMA_MODEL", "llama3.2")

    sys.exit(f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use 'openai' or 'ollama'.")


# ------------------------------------------------------------ MCP transport --

@asynccontextmanager
async def open_transport():
    """Yield (read, write) streams for Streamable HTTP (/mcp) or SSE (/sse)."""
    if MCP_TRANSPORT == "sse":
        from mcp.client.sse import sse_client

        print(f"Connecting to {MCP_SSE_URL} (SSE)...")
        async with sse_client(MCP_SSE_URL) as streams:
            yield streams[0], streams[1]
    else:
        try:  # newer SDK name
            from mcp.client.streamable_http import streamable_http_client as http_client
        except ImportError:  # older SDK name
            from mcp.client.streamable_http import streamablehttp_client as http_client

        print(f"Connecting to {MCP_HTTP_URL} (Streamable HTTP)...")
        async with http_client(MCP_HTTP_URL) as streams:
            yield streams[0], streams[1]


# ------------------------------------------------------ elicitation (human) --

async def ask(prompt: str) -> str:
    """input() without blocking the event loop (the MCP connection keeps running)."""
    return (await asyncio.to_thread(input, prompt)).strip()


async def ask_field(name: str, prop: dict, required: bool):
    """Ask the user for one field of the server's schema, typed correctly."""
    label = prop.get("description") or prop.get("title") or name
    ftype = prop.get("type", "string")
    default = prop.get("default")
    enum = prop.get("enum")
    hint = f" [{default}]" if default is not None else ""

    while True:
        if enum:
            raw = await ask(f"  {label} {enum}{hint}: ")
        elif ftype == "boolean":
            yn = "Y/n" if default is True else "y/N" if default is False else "y/n"
            raw = await ask(f"  {label} ({yn}): ")
        else:
            raw = await ask(f"  {label}{hint}: ")

        if raw == "":
            if default is not None:
                return default
            if not required:
                return None
            print("    This field is required.")
            continue

        if enum:
            if raw in enum:
                return raw
            print(f"    Choose one of {enum}.")
        elif ftype == "boolean":
            if raw.lower() in ("y", "yes", "true", "1"):
                return True
            if raw.lower() in ("n", "no", "false", "0"):
                return False
            print("    Please answer y or n.")
        elif ftype == "integer":
            try:
                return int(raw)
            except ValueError:
                print("    Please enter a whole number.")
        elif ftype == "number":
            try:
                return float(raw)
            except ValueError:
                print("    Please enter a number.")
        else:
            return raw


async def handle_elicitation(
    context: ClientRequestContext, params: types.ElicitRequestParams
) -> types.ElicitResult:
    """Called when the server needs more input from the user mid-tool-call."""
    schema = (
        getattr(params, "requested_schema", None)
        or getattr(params, "requestedSchema", None)
        or {}
    )

    print(f"\n[Server asks] {params.message}")
    choice = (await ask("  Respond? [a]ccept / [d]ecline / [c]ancel (a): ")).lower() or "a"
    if choice.startswith("d"):
        return types.ElicitResult(action="decline")
    if choice.startswith("c"):
        return types.ElicitResult(action="cancel")

    required = set(schema.get("required", []))
    content = {}
    for name, prop in schema.get("properties", {}).items():
        value = await ask_field(name, prop, name in required)
        if value is not None:
            content[name] = value

    return types.ElicitResult(action="accept", content=content)


# --------------------------------------------------------------- tool glue --

def to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to the OpenAI function-calling format."""
    tools = []
    for t in mcp_tools:
        schema = (
            getattr(t, "input_schema", None)
            or getattr(t, "inputSchema", None)
            or {"type": "object", "properties": {}}
        )
        tools.append({
            "type": "function",
            "function": {"name": t.name, "description": t.description or "", "parameters": schema},
        })
    return tools


def result_text(result) -> str:
    texts = [c.text for c in (result.content or []) if getattr(c, "type", "") == "text"]
    if texts:
        return "\n".join(texts)
    structured = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
    return json.dumps(structured, ensure_ascii=False) if structured else "(no output)"


async def call_mcp_tool(session: ClientSession, name: str, args: dict) -> str:
    print(f"\n[Calling tool] {name}({json.dumps(args, ensure_ascii=False)})")
    result = await session.call_tool(name, arguments=args)
    text = result_text(result)
    is_error = getattr(result, "is_error", None) or getattr(result, "isError", False)
    print(f"[Tool {'error' if is_error else 'result'}] {text}")
    return text


# -------------------------------------------------------------------- chat --

async def chat(session: ClientSession, llm: AsyncOpenAI, model: str) -> None:
    tools = to_openai_tools((await session.list_tools()).tools)
    print(f"Tools from server: {[t['function']['name'] for t in tools]}")
    print(f"LLM: {LLM_PROVIDER} / {model}")
    print("Type a request (e.g. 'Book a trip on 2024-12-20'), or 'exit' to quit.")

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user = await ask("\nYou: ")
        if not user:
            continue
        if user.lower() in ("exit", "quit"):
            break
        messages.append({"role": "user", "content": user})

        for _ in range(MAX_TOOL_ROUNDS):
            resp = await llm.chat.completions.create(model=model, messages=messages, tools=tools)
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                print(f"\nAssistant: {msg.content}")
                break

            for call in msg.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    text = await call_mcp_tool(session, call.function.name, args)
                except Exception as exc:  # report tool failures back to the LLM
                    text = f"Tool call failed: {exc}"
                    print(f"[Tool error] {text}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": text})
        else:
            print("\nAssistant: (stopped - too many tool calls in a row)")


# -------------------------------------------------------------------- main --

async def run(direct_date: str | None) -> None:
    llm, model = (None, None) if direct_date else make_llm()

    async with open_transport() as (read, write):
        async with ClientSession(read, write, elicitation_callback=handle_elicitation) as session:
            await session.initialize()

            if direct_date:
                await call_mcp_tool(session, "book_trip", {"date": direct_date})
            else:
                await chat(session, llm, model)


def main() -> None:
    parser = argparse.ArgumentParser(description="Elicitation demo client")
    parser.add_argument("--date", help="call book_trip directly with this date (no LLM)")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.date))
    except KeyboardInterrupt:
        print("\nBye.")
    except Exception as exc:
        print(f"\nError: {exc!r}")
        print("Is the server running?  uvicorn server:app   (port 8000)")
        sys.exit(1)


if __name__ == "__main__":
    main()
