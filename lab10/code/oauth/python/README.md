# Run OAuth sample

Three small Flask apps that walk through the **OAuth 2.1 authorization code flow with PKCE**:

| File | Role | Port |
|---|---|---|
| `auth-server.py` | Authorization server: `/authorize`, `/token`, `/introspect` | 5000 |
| `resource-server.py` | Resource server: protected `/userinfo`, checks tokens via `/introspect` | 5001 |
| `client.py` | Runs the flow, then calls `/userinfo` with the access token | n/a |

The original book code is kept, unchanged, in [`original_v1/`](./original_v1/).

## -0- Set up

Set up a virtual environment and activate it.

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
```

```sh
pip install flask requests
```

## -1- Start auth server

```sh
python auth-server.py
```

## -2- Start resource server

In a second terminal:

```sh
python resource-server.py
```

## -3- Start client

In a third terminal:

```sh
python client.py
```

You should see an output similar to:

```text
Requesting authorization: http://localhost:5000/authorize?response_type=code&client_id=abc&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback&scope=read&state=8u4EazQnXPnRk1KjZEAHRA&code_challenge=Q6u3IcKgxJPjB0BQwTEgc3Xfmog8EnGa0rolciJGXCk&code_challenge_method=S256
Received authorization code: 41dee3d4-bc50-4849-b967-3db4676e8e54
Access token: f327ed13-b2a2-4970-934b-f717db56477c
User info response:
{'email': 'chris@example.com', 'name': 'Chris', 'sub': 'user123'}
```

Run `python client.py` again. It reuses the saved token, after checking it with `/introspect`:

```text
Reusing saved access token: f327ed13-b2a2-4970-934b-f717db56477c
User info response:
{'email': 'chris@example.com', 'name': 'Chris', 'sub': 'user123'}
```

The token is saved in `.token-cache.json` (ignored by git). Delete it, or restart `auth-server.py`, to go through the full flow again.

## How PKCE works here

1. The client makes a random secret, the **code_verifier**, and sends only its hash,
   `code_challenge = BASE64URL(SHA256(code_verifier))`, to `/authorize` with `code_challenge_method=S256`.
2. `/authorize` remembers the challenge and returns an authorization **code**.
3. The client sends the code **plus the original verifier** to `/token`. The server hashes the verifier
   and only issues a token if it matches the challenge.

Someone who steals the code can't use it without the verifier, which never left the client.
The client also checks that the `state` it sent comes back unchanged, which protects against CSRF.

## Try breaking it

| Change | Result |
|---|---|
| In `client.py`, send a different `code_verifier` in step 3 | `400 code_verifier doesn't match` |
| Use the same authorization code twice | `400 unknown or used code` |
| `code_challenge_method=plain` | `400`. OAuth 2.1 requires `S256` |
| Call `/userinfo` with a made-up token | `403 invalid_token` |
| Call `/userinfo` with no token | `401 missing_token` |

## What changed from the book's code

| Book | This folder |
|---|---|
| README ran `auth_server.py` / `resource_server.py` (files don't exist) | `auth-server.py` / `resource-server.py` |
| "PKCE" compared the fixed strings `123` = `123` with method `plain` | Real S256 PKCE, with a random verifier per run |
| Fixed `state=xyz`, never checked | Random state, checked on return |
| Codes reusable; `client_id`/`redirect_uri` not checked at `/token` | One-time codes; both checked |
| `/introspect` always said scope `read`, expiry 9999999999 | Returns the token's real scope and expiry |
| Dead code after `app.run()` importing `auth_server` | Removed |
| TODO "1a: reuse an existing token" | Implemented with `.token-cache.json` + `/introspect` |
| Client carried on with `None` if a step failed | Stops with a clear message |

> **macOS note:** port 5000 is often taken by AirPlay Receiver. If `auth-server.py` won't start, turn AirPlay
> Receiver off in System Settings, or change `PORT` in `auth-server.py` and `AUTH_SERVER` in the other two files.
