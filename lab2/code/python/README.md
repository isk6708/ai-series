# Run sample

## Set up virtual environment

```bash
python -m venv venv
```

activate virtual environment:

```bash
source venv/bin/activate
```

or on Windows type:

```bash
venv\Scripts\activate
```

## Install dependencies

```bash
pip install "mcp[cli]>=2"
```

> This sample has been updated for MCP SDK 2.x (`MCPServer` replaces `FastMCP`).
> The original 1.x version is kept in `server_v1_original.py`; to run it, install `"mcp[cli]<2"` instead.

## Run code

```bash
mcp run server.py
```

## Run inspector

```bash
mcp dev server.py
```

You should see a web interface open up. Ensure you select:

- transport with value "stdio":
- command: **mcp**
- arguments: **run server.py**

Then select the "Connect" button.
