# client_llm.py - lets an LLM (GitHub Models) decide which MCP tool to call
# (MCP Python SDK v2)
# Changes from the original:
#   - tool.inputSchema -> tool.input_schema (renamed in v2)
#   - tool schema for the LLM now includes "required" (and drops a stray "type"
#     key inside "function")
#   - model id "gpt-4o" -> "openai/gpt-4o": the models.github.ai endpoint needs
#     the publisher prefix. Override with the MODEL_NAME environment variable.
#   - friendly message if GITHUB_TOKEN isn't set
#   - starts the server with sys.executable (no mcp CLI needed)
#   - reads its settings from a .env file next to this script
#     (copy .env.example to .env and fill it in)
#   - choose the LLM with LLM_PROVIDER in .env:
#       github  - GitHub Models (free tier, needs GITHUB_TOKEN)
#       openai  - OpenAI / ChatGPT API (paid, needs OPENAI_API_KEY)
#       ollama  - local models via Ollama, e.g. llama3.2 or qwen2.5 (free, no key)
# Run: python client_llm.py
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from openai import OpenAI

# llm
import os
import json

SERVER = str(Path(__file__).with_name("server.py"))
ENV_FILE = Path(__file__).with_name(".env")


def load_env_file(path: Path) -> None:
    """Load KEY=value lines from .env into os.environ.

    Uses python-dotenv if installed (pip install python-dotenv); otherwise a
    small built-in parser. Variables already set in the shell win over .env.
    """
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=False)
        return
    except ImportError:
        pass
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]      # strip surrounding quotes
        os.environ.setdefault(key, value)


load_env_file(ENV_FILE)


# ---------------------------------------------------------------------------
# LLM providers - all three speak the OpenAI chat-completions API, so the
# same `openai` client works for each; only the URL, key and model differ.
# ---------------------------------------------------------------------------
PROVIDERS = {
    "github": {
        "base_url": "https://models.github.ai/inference",
        "key_env": "GITHUB_TOKEN",
        "model": "openai/gpt-4o",
        "extra": {"temperature": 1., "max_tokens": 1000, "top_p": 1.},
        "max_tokens_param": "max_tokens",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        # max_completion_tokens works for all current OpenAI chat models.
        # temperature/top_p left at the API default: reasoning models
        # (gpt-5, o3, o4-mini...) reject any other value.
        "extra": {"max_completion_tokens": 1000},
        "max_tokens_param": "max_completion_tokens",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,          # local - no key needed
        "model": "llama3.2",
        # small local models pick tools more reliably at temperature 0
        "extra": {"temperature": 0, "max_tokens": 1000},
        "max_tokens_param": "max_tokens",
    },
}

PROVIDER = os.environ.get("LLM_PROVIDER", "github").strip().lower()


def provider_settings():
    """Resolve provider, URL, key and model from .env / environment."""
    if PROVIDER not in PROVIDERS:
        sys.exit(f"Unknown LLM_PROVIDER '{PROVIDER}'. Use one of: {', '.join(PROVIDERS)}")
    p = PROVIDERS[PROVIDER]
    if PROVIDER == "ollama":
        default_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/v1"
    else:
        default_url = p["base_url"]
    base_url = os.environ.get("MODEL_ENDPOINT", default_url)
    model = os.environ.get("MODEL_NAME", p["model"])
    api_key = os.environ.get(p["key_env"]) if p["key_env"] else "ollama"
    return base_url, api_key, model, sampling_params(p)


def sampling_params(p):
    """Provider defaults, overridden by LLM_TEMPERATURE / LLM_MAX_TOKENS / LLM_TOP_P."""
    params = dict(p["extra"])
    overrides = [
        ("LLM_TEMPERATURE", "temperature", float, 0.0, 2.0),
        ("LLM_TOP_P", "top_p", float, 0.0, 1.0),
        ("LLM_MAX_TOKENS", p["max_tokens_param"], int, 1, 100_000),
    ]
    for env_name, param, cast, low, high in overrides:
        raw = os.environ.get(env_name, "").strip()
        if not raw:
            continue
        if raw.lower() == "default":      # remove it: let the API use its default
            params.pop(param, None)
            continue
        try:
            value = cast(raw)
        except ValueError:
            sys.exit(f"{env_name}={raw!r} is not a valid {cast.__name__}")
        if not low <= value <= high:
            sys.exit(f"{env_name}={raw} is out of range ({low}-{high})")
        params[param] = value
    return params


def check_settings():
    """Fail early with a clear message instead of a traceback."""
    base_url, api_key, model, _ = provider_settings()
    key_env = PROVIDERS[PROVIDER]["key_env"]
    if key_env and not api_key:
        hint = {
            "GITHUB_TOKEN": "a GitHub token with 'Models: read' access",
            "OPENAI_API_KEY": "your OpenAI API key (https://platform.openai.com/api-keys)",
        }[key_env]
        sys.exit(f"{key_env} is not set. Put {hint} in .env "
                 f"(copy .env.example) - or change LLM_PROVIDER. See README.md")
    if PROVIDER == "ollama":
        check_ollama(base_url, model)
    _, _, _, params = provider_settings()
    print(f"LLM: {PROVIDER} / {model}  ({base_url})")
    print(f"     {', '.join(f'{k}={v}' for k, v in params.items()) or 'API defaults'}")


def check_ollama(base_url, model):
    """Make sure Ollama is running and the model has been pulled."""
    import urllib.request
    tags_url = base_url.removesuffix("/v1") + "/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as r:
            installed = [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        sys.exit(f"Can't reach Ollama at {tags_url}. Install it from https://ollama.com "
                 f"and make sure it's running (ollama serve).")
    # "llama3.2" matches "llama3.2:latest"
    if not any(name == model or name.split(":")[0] == model for name in installed):
        sys.exit(f"Ollama model '{model}' isn't downloaded yet. Run:  ollama pull {model}\n"
                 f"Installed: {', '.join(installed) or 'none'}")


_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        base_url, api_key, _, _ = provider_settings()
        _llm_client = OpenAI(base_url=base_url, api_key=api_key)
    return _llm_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command=sys.executable,  # Executable (same Python / venv as this client)
    args=[SERVER],  # Optional command line arguments
    env=None,  # Optional environment variables
)

def call_llm(prompt, functions):
    _, _, model_name, extra = provider_settings()
    client = get_llm_client()

    print("CALLING LLM")
    response = client.chat.completions.create(
        messages=[
            {
            "role": "system",
            "content": "You are a helpful shop assistant. Use the provided tools when they help answer the request.",
            },
            {
            "role": "user",
            "content": prompt,
            },
        ],
        model=model_name,
        tools = functions,
        # Optional parameters (per provider - see PROVIDERS above)
        **extra,
    )

    # .content if we want just see the text response 
    response_message = response.choices[0].message
    
    functions_to_call = []

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            # print("TOOL: ", tool_call)
            name = tool_call.function.name
            print("TOOL NAME: ", name)
            raw_args = tool_call.function.arguments
            # some local models send a dict, or an empty string for "no arguments"
            if isinstance(raw_args, dict):
                args = raw_args
            else:
                args = json.loads(raw_args) if raw_args else {}
            functions_to_call.append({ "name": name, "args": args })
    elif response_message.content:
        # The LLM answered directly without needing a tool
        print("LLM: ", response_message.content)

    return functions_to_call

def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.input_schema.get("properties", {}),
                "required": tool.input_schema.get("required", []),
            }
        }
    }

    return tool_schema

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("LISTING TOOLS")

            functions = []

            for tool in tools.tools:
                print("Tool: ", tool.name)
                # print("Tool", tool.input_schema["properties"])
                functions.append(convert_to_llm_tool(tool))
            
            while True:
                print("Waiting for input... (type 'quit' to exit)")
                prompt = input("Enter prompt: ")
                if prompt == "quit":
                    break
            
                # ask LLM what tools to all, if any
                functions_to_call = call_llm(prompt, functions)

                # call suggested functions
                for f in functions_to_call:
                    result = await session.call_tool(f["name"], arguments=f["args"])
                    for item in result.content:
                        print("TOOLS result: ", item.text if hasattr(item, "text") else item)


if __name__ == "__main__":
    import asyncio

    check_settings()

    asyncio.run(run())
