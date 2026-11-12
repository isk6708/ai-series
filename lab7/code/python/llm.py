"""
llm.py - the LLM the CLIENT uses to answer the server's sampling requests.

Settings come from a .env file next to this script (copy .env.example to .env):
    LLM_PROVIDER = github | openai | ollama      (default: github)
    GITHUB_TOKEN / OPENAI_API_KEY                 (key for the chosen provider)
    MODEL_NAME, MODEL_ENDPOINT, OLLAMA_HOST       (optional overrides)

All three providers speak the OpenAI chat-completions API, so one `openai`
client works for each (pip install openai).
"""
import asyncio
import os
import sys
from pathlib import Path

ENV_FILE = Path(__file__).with_name(".env")


def load_env_file(path: Path) -> None:
    """Load KEY=value lines into os.environ (shell variables win)."""
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
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env_file(ENV_FILE)

PROVIDERS = {
    "github": {"base_url": "https://models.github.ai/inference", "key_env": "GITHUB_TOKEN",
               "model": "openai/gpt-4o-mini", "max_tokens_param": "max_tokens"},
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY",
               "model": "gpt-4o-mini", "max_tokens_param": "max_completion_tokens"},
    "ollama": {"base_url": None, "key_env": None,
               "model": "llama3.2", "max_tokens_param": "max_tokens"},
}

PROVIDER = os.environ.get("LLM_PROVIDER", "github").strip().lower()


def settings():
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
    return base_url, api_key, model, p


def check_settings() -> None:
    """Fail early with a clear message (call before connecting to the server)."""
    base_url, api_key, model, p = settings()
    if p["key_env"] and not api_key:
        sys.exit(f"{p['key_env']} is not set. Copy .env.example to .env and add it, "
                 f"or change LLM_PROVIDER. See README.md")
    try:
        import openai  # noqa: F401
    except ImportError:
        sys.exit("The 'openai' package is missing: pip install openai")
    print(f"LLM: {PROVIDER} / {model}  ({base_url})")


_client = None


async def call_llm(prompt: str, system_prompt: str,
                   max_tokens: int = 200, temperature: float | None = 1.0) -> tuple[str, str]:
    """Return (text, model_name). Runs the blocking OpenAI call in a thread."""
    global _client
    from openai import OpenAI
    base_url, api_key, model, p = settings()
    if _client is None:
        _client = OpenAI(base_url=base_url, api_key=api_key)

    params = {p["max_tokens_param"]: max_tokens}
    # OpenAI reasoning models reject non-default temperature; others accept it
    if temperature is not None and PROVIDER != "openai":
        params["temperature"] = temperature
    elif temperature is not None and PROVIDER == "openai" and model.startswith("gpt-4"):
        params["temperature"] = temperature

    response = await asyncio.to_thread(
        _client.chat.completions.create,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        model=model,
        **params,
    )
    return response.choices[0].message.content or "", model
