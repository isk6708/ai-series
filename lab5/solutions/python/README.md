# Running this sample

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/) for reference.

| File | What it is |
|---|---|
| `server.py` | Shop MCP server (`get_products`, `add_product_to_cart`, `list_cart`) over **stdio** |
| `client.py` | Interactive client: you type a tool name, it asks for the arguments and calls the tool |
| `client_llm.py` | LLM client: you type plain English, an LLM picks the tool and arguments. Works with GitHub Models, OpenAI (ChatGPT API) or local Ollama models |
| `.env.example` | Template for `.env`, where `client_llm.py` reads its provider and keys from |

Both clients **start `server.py` themselves** as a subprocess (stdio transport), so you only need one terminal.

You're recommended to install `uv` but it's not a must, see [instructions](https://docs.astral.sh/uv/#highlights)

## -0- Create a virtual environment

```bash
python -m venv venv
```

## -1- Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

## -2- Install the dependencies

```bash
pip install "mcp[cli]>=2"
```

## -3- Run the sample


```bash
python client.py
```

You should see the following output:

```text
LISTING TOOLS
Tool:  add_product_to_cart
Tool:  list_cart
Tool:  get_products
Enter command (or 'quit' to exit):
```

## -4- Test the sample

Test the sample through below input. We assume you have the app running at this point.

1. Type the following command **get_products**, you should see the following output

  ```text
  Using tool: get_products
  Tool arguments: {'properties': {}, 'type': 'object', 'title': 'get_productsArguments'}
  Result:  {
    "id": 1,
    "name": "Product 1",
    "price": 10.0,
    "description": "Description of Product 1",
    "category": "Category 1"
  }
  Result:  {
    "id": 2,
    ...
  }
  Result:  {
    "id": 3,
    ...
  }
  ```

  This tells you that there's a list of products to choose from

1. Add an item to the cart like by typing **add_product_to_cart**. You should see another prompt asking you to "Enter product_name", type **Product 2**. You should see a response like so:

  ```text
  Result:  {
    "cart_id": 0,
    "product_id": 2,
    "quantity": 1
  }
  ```

  Typing a product that doesn't exist (e.g. **Nope**) now returns a clear error:

  ```text
  Result:  Error executing tool add_product_to_cart: Product [Nope] not found. Available: Product 1, Product 2, Product 3
  (the tool reported an error)
  ```

 1. List cart content with the command **list_cart**, you should see the following response:

  ```text
  Using tool: list_cart
  Tool arguments: {'properties': {}, 'type': 'object', 'title': 'list_cartArguments'}
  Result:  {
    "cart_id": 0,
    "product_id": 2,
    "quantity": 1
  }
  ```

  This correctly shows us the item we just added.

## Test the LLm sample

1. Install dependencies (we need to support calling an LLM)

  ```sh
  pip install openai
  ```

1. Create your `.env` file from the template, next to `client_llm.py`:

  ```powershell
  copy .env.example .env        # Windows
  ```

  ```sh
  cp .env.example .env          # macOS / Linux
  ```

1. In `.env`, choose an LLM with `LLM_PROVIDER` and fill in what that provider needs:

  | `LLM_PROVIDER` | Cost | What to put in `.env` | Default model |
  |---|---|---|---|
  | `github` (default) | Free tier | `GITHUB_TOKEN=` a GitHub [fine-grained token](https://github.com/settings/personal-access-tokens) with **Models: read** | `openai/gpt-4o` |
  | `openai` | Paid | `OPENAI_API_KEY=` your key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `gpt-4o-mini` |
  | `ollama` | Free, runs on your PC | Nothing (no key). Install [Ollama](https://ollama.com) and pull a model | `llama3.2` |

  Change the model with `MODEL_NAME`, for example `MODEL_NAME=gpt-4o` (OpenAI) or `MODEL_NAME=qwen2.5` (Ollama).

  **Example: ChatGPT API key**

  ```text
  LLM_PROVIDER=openai
  OPENAI_API_KEY=sk-...
  ```

  **Example: Ollama with Llama 3.2 or Qwen**

  First, once, in a terminal:

  ```sh
  ollama pull llama3.2          # about 2 GB
  ollama pull qwen2.5           # about 4.7 GB; better at picking tools
  ```

  Then in `.env`:

  ```text
  LLM_PROVIDER=ollama
  MODEL_NAME=llama3.2           # or qwen2.5
  ```

  The model must support **tool calling**: `llama3.2`, `qwen2.5` and `qwen3` do; check the model's page on
  [ollama.com/library](https://ollama.com/library) for the **tools** tag before trying others. Small local models
  are less reliable at choosing tools than GPT-4o, so phrase prompts plainly ("add Product 1 to the cart").

  > `.env` is listed in `.gitignore`, so your keys are never committed. Only `.env.example` (no real keys) goes into git.
  > A variable already set in your terminal (e.g. `$env:LLM_PROVIDER`) takes priority over `.env`.

1. Run the LLM client by typing the following:

  ```sh
  python client_llm.py
  ```

  You should see the following output (the first line shows which LLM is in use):

  ```text
  LLM: github / openai/gpt-4o  (https://models.github.ai/inference)
  LISTING TOOLS
  Tool:  add_product_to_cart
  Tool:  list_cart
  Tool:  get_products
  Waiting for input... (type 'quit' to exit)
  Enter prompt:
  ```

1. Type **show me products**, like so:

  ```text
  Enter prompt: show me products
  ```

  You should see the following output:

  ```text
  CALLING LLM
  TOOL NAME:  get_products
  TOOLS result:  {
    "id": 1,
    "name": "Product 1",
    ...
  }
  ...
  Waiting for input... (type 'quit' to exit)
  ```

1. Now add a product by typing the following **Add Product 1 to the cart**, you should see the following output:

  ```text
  CALLING LLM
  TOOL NAME:  add_product_to_cart
  TOOLS result:  {
    "cart_id": 0,
    "product_id": 1,
    "quantity": 1
  }
  Waiting for input... (type 'quit' to exit)
  ```

1. Let's double check by typing **show me cart content**, you should see the following output:

  ```text
  CALLING LLM
  TOOL NAME:  list_cart
  TOOLS result:  {
    "cart_id": 0,
    "product_id": 1,
    "quantity": 1
  }
  Waiting for input... (type 'quit' to exit)
  ```

  As you can see, your added product is in the cart.

  If your prompt doesn't need a tool (e.g. **hi**), the LLM's answer is printed as `LLM:  ...`.

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server import MCPServer` |
| `add_product_to_cart` returned a dict when not found (didn't match `CartItem`, so the call failed) | Raises `ToolError` with the available product names; names match case-insensitively |
| `server.py` had no `__main__` | `mcp.run()` under `if __name__ == "__main__":`, so `python server.py` starts it on stdio |
| Clients started the server with `mcp run server.py` (needs the `mcp` CLI on PATH) | Start it with the same Python: `sys.executable server.py` |
| `tool.inputSchema` | `tool.input_schema` (renamed in v2; the old name raises `AttributeError`) |
| Results printed as raw `TextContent(...)` objects | The text is printed; errors are flagged |
| LLM tool schema had no `required` list and a stray `"type"` key | Includes `required`; stray key removed |
| Model `gpt-4o` | `openai/gpt-4o` (GitHub Models' endpoint uses publisher-prefixed ids); override with `MODEL_NAME` |
| GitHub Models only; token set in the terminal | Choose `github`, `openai` or `ollama` with `LLM_PROVIDER`; settings read from `.env` |
| Missing `GITHUB_TOKEN` gave a `KeyError` traceback | Clear message on startup |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No module named 'mcp.server.fastmcp'` | You're running v1 code (`original_v1/`) on SDK v2. Use the files in this folder |
| `'Tool' object has no attribute 'inputSchema'` | Same: v1 client code. Use the files in this folder |
| `No module named 'openai'` | `pip install openai` |
| `GITHUB_TOKEN is not set` / `OPENAI_API_KEY is not set` | Add the key for your `LLM_PROVIDER` to `.env` (copy `.env.example`) |
| `401` / `Unauthorized` from the LLM | Wrong or expired key. GitHub: token needs **Models: read**. Check `.env` has no leftover spaces or quotes |
| `429` / `insufficient_quota` (OpenAI) | Your OpenAI account has no credit. Add billing, or switch to `github` or `ollama` |
| `Can't reach Ollama` | Start Ollama (open the app, or run `ollama serve`) |
| `Ollama model '…' isn't downloaded yet` | Run the `ollama pull …` command it prints |
| Ollama model answers in text but never calls a tool | The model may not support tools, or is too small. Try `qwen2.5` |
| `Unknown model` / `404` from the LLM | Set `MODEL_NAME` to a model id from the GitHub Models catalog, e.g. `openai/gpt-4o-mini` |
