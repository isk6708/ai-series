# Chapter 08 – Run the MCP server from VS Code (`.vscode/mcp.json`)

This folder has a small **stdio** MCP server in Python (`server.py`) with three tools:

| Tool | Arguments | Returns |
|---|---|---|
| `add` | `a`, `b` (integers) | `a + b` |
| `subtract` | `a`, `b` (integers) | `a - b` |
| `ucapan` | `apaucapannya` (text) | `Ini ialah ucapan <apaucapannya>` |

VS Code starts the server for you using `.vscode/mcp.json`, and GitHub Copilot Chat (Agent mode)
can then call the tools.

```
code/
├── .vscode/
│   └── mcp.json          # tells VS Code how to start the server
├── server.py             # MCP server – Python SDK 2.x (MCPServer)
├── original_v1/
│   └── server.py         # same server for Python SDK 1.x (FastMCP), for reference
├── src/index.ts          # TypeScript version (optional, see the end)
├── package.json
└── tsconfig.json
```

## Prerequisites

- Python 3.10 or newer
- VS Code with the **GitHub Copilot** and **GitHub Copilot Chat** extensions, signed in

## 1. Create the virtual environment

`mcp.json` runs `.venv\Scripts\python.exe` **inside this folder**, so the venv must be named
`.venv` and created here (not in a parent folder).

Windows (PowerShell), from this `code` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "mcp[cli]"
```

> `server.py` uses `from mcp.server import MCPServer`, which needs **MCP Python SDK 2.x**.
> Check with `pip show mcp`. If you have 1.x, run `pip install -U "mcp[cli]"`, or use
> `original_v1/server.py` instead (see Troubleshooting).

Optional – check the server starts (press `Ctrl+C` to stop it):

```powershell
python server.py
```

It prints `Starting MCP server...` and then waits silently. That is correct: a stdio server
talks to VS Code through stdin/stdout, not to you.

## 2. The `mcp.json` file

`.vscode/mcp.json` is already set up:

```json
{
  "servers": {
    "python-server": {
      "type": "stdio",
      "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
      "args": ["${workspaceFolder}\\server.py"]
    }
  }
}
```

- `python-server` – the name VS Code shows for this server
- `type: stdio` – VS Code starts the process and talks to it over stdin/stdout
- `command` – the Python **inside the venv**, so the `mcp` package is found
- `${workspaceFolder}` – the folder you opened in VS Code; it must be this `code` folder

## 3. Start the server in VS Code

1. Open **this folder** in VS Code: **File → Open Folder… →** `Chapter08\code`
   (or `code .` from this folder). If you open a parent folder, `${workspaceFolder}` points to
   the wrong place and the server will not start.
2. Open `.vscode/mcp.json`. Click **Start** in the small link shown above `"python-server"`.
   Or press `Ctrl+Shift+P` → **MCP: List Servers** → `python-server` → **Start Server**.
3. The status above `"python-server"` changes to **Running** and shows **3 tools**.
   If VS Code asks whether you trust the server, choose **Trust**.

## 4. Use the tools in Copilot Chat

1. Open Copilot Chat (`Ctrl+Alt+I`) and switch the mode to **Agent**.
2. Click the **tools** icon in the chat box and check that `add`, `subtract` and `ucapan`
   under `python-server` are ticked.
3. Try:
   - `Use the add tool to add 12 and 30`
   - `Subtract 8 from 20`
   - `Use ucapan with "selamat pagi"` → `Ini ialah ucapan selamat pagi`
4. Copilot asks for permission before running each tool – click **Continue**.

You can also reference a tool directly with `#`, for example `#add 2 and 3`.

## 5. After you change `server.py`

VS Code does not reload the server on its own. After editing `server.py`, restart it:
**Restart** above `"python-server"` in `mcp.json`, or **MCP: List Servers → python-server →
Restart Server**. New tools only appear after a restart.

## Test without VS Code (optional, needs Node.js)

```powershell
npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe server.py
```

This opens the MCP Inspector in your browser, where you can list and call the tools.

## Troubleshooting

To see errors: `Ctrl+Shift+P` → **MCP: List Servers** → `python-server` → **Show Output**.

| Problem | Fix |
|---|---|
| `spawn ...\.venv\Scripts\python.exe ENOENT` | The venv is missing or in the wrong place. Create `.venv` in this folder (step 1) and make sure you opened this folder in VS Code. |
| `ModuleNotFoundError: No module named 'mcp'` | `pip install "mcp[cli]"` was run outside the venv. Activate `.venv` and install again. |
| `ImportError: cannot import name 'MCPServer'` | You have SDK 1.x. Run `pip install -U "mcp[cli]"`, or point `args` in `mcp.json` to `"${workspaceFolder}\\original_v1\\server.py"`. |
| Server starts then stops / "connection closed" | Something printed to **stdout**. In a stdio server use `print(..., file=sys.stderr)` for messages – stdout is reserved for MCP. |
| Tools don't appear in chat | Chat must be in **Agent** mode, the server must show **Running**, and the tools must be ticked in the tools picker. |

## macOS / Linux

The venv layout is different, so use this `mcp.json` instead:

```json
{
  "servers": {
    "python-server": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["${workspaceFolder}/server.py"]
    }
  }
}
```

and create the venv with `python3 -m venv .venv && source .venv/bin/activate && pip install "mcp[cli]"`.

## Optional: TypeScript version (`src/index.ts`)

The same idea in TypeScript (one `add` tool). Build it:

```powershell
npm install
npm run build
```

Then add a second entry inside `"servers"` in `.vscode/mcp.json`:

```json
"ts-server": {
  "type": "stdio",
  "command": "node",
  "args": ["${workspaceFolder}\\build\\index.js"]
}
```

> `src/index.ts` writes `console.log("Starting MCP server...")`, which goes to stdout and can
> break the stdio connection. Change it to `console.error(...)` before building.
