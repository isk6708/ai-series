# Run sample

The solution protects the MCP server with a **JWT**. The middleware checks, in order:

1. The token is present (else **401**).
2. Its signature is valid and it hasn't expired (else **403**).
3. The user exists (`User Userson` or `Admin Adminson`) (else **403**).
4. It has the `Admin.Write` scope (else **403**).

Updated for the MCP Python SDK **v2** (`mcp>=2`). The original book code (SDK v1) is kept, unchanged,
in [`original_v1/`](./original_v1/).

## Configure environment

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
```

## Install dependencies

```bash
pip install "mcp[cli]>=2" uvicorn PyJWT
```

The book also installed `dotenv`. That's no longer needed, because the client reads `.env` itself
(and `dotenv` was the wrong package anyway; the right one is `python-dotenv`).

## Generate token

We will use a simple script to generate a JWT token for testing.

```bash
python util.py
```

This writes `TOKEN=...` to the `.env` file next to `util.py`, keeping any other lines already there.
The client reads the token from `.env`. `.env` is ignored by git.

## Start server

```bash
python server.py
```

## Start client

In a separate terminal, run:

```bash
python client.py
```

The **server** terminal should show:

```text
Valid token, proceeding...
User exists, proceeding...
User has required scope, proceeding...
```

and the client prints the tool result (the current time).

If you want to see a scenario where the token is invalid, you can change `util.py` and its payload to generate an invalid token, e.g. change the scopes to something else, like so, i.e to "User.Write" instead of "Admin.Write" that the server expects:

```python
payload = {
        "sub": "1234567890",               # Subject (user ID)
        "name": "User Userson",                # Custom claim
        "admin": True,                     # Custom claim
        "iat": now,                        # Issued at
        "exp": now + datetime.timedelta(hours=1),  # Expiry
        "scopes": ["User.Write"]  # Custom claim for scopes/permissions
    }
```

Run `python util.py` again, then `python client.py`. The server prints `-> Missing required scope!` and the client:

```text
... - mcp_client - ERROR - Server rejected the request: HTTP 403 Forbidden (credentials sent but not accepted)
```

Also try changing `"name"` to someone not in `users` (`-> User does not exist!`), or `secret_key` in `util.py`
after starting the server (`-> Invalid token!`).

## What changed from the book's v1 code

| v1 (book) | v2 (this folder) |
|---|---|
| `FastMCP` with `host`/`port` settings; `pydantic_settings` import (crashes on SDK v2) | `MCPServer`; unused imports removed |
| Token decoded three times per request; crashed on a header without `Bearer ` or a token without `scopes` | Decoded once; missing parts are rejected cleanly |
| `streamablehttp_client(url, headers=...)` | `streamable_http_client(url, http_client=create_mcp_http_client(headers=...))` |
| `util.py` overwrote `.env` (in whatever folder you ran it from) | Updates only the `TOKEN` line, in the script's own folder |
| `datetime.utcnow()` (deprecated) | `datetime.now(timezone.utc)` |
| 15-byte demo secret (PyJWT warns) | Longer demo secret |
| `pip install dotenv` (wrong package; should have been `python-dotenv`) | Not needed: the client reads `.env` itself |
