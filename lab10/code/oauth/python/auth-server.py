# auth-server.py - a tiny OAuth 2.1 AUTHORIZATION SERVER (demo, no real login).
# Endpoints: /authorize, /token, /introspect, /logout          (port 5000)
#
# Changes from the original:
#   - real PKCE: the client sends code_challenge = BASE64URL(SHA256(code_verifier))
#     with method S256 (OAuth 2.1 requires S256); /token checks the verifier
#     against it. The original compared two fixed strings ("123").
#   - authorization codes can be used only once, and /token checks that the
#     client_id and redirect_uri match the ones used at /authorize
#   - /introspect returns the real scope and expiry stored with the token
import base64
import hashlib
import time
import uuid

from flask import Flask, jsonify, redirect, request

app = Flask(__name__)

# In-memory stores
auth_codes = {}
access_tokens = {}

TOKEN_LIFETIME = 3600  # seconds


def s256(code_verifier: str) -> str:
    """PKCE S256: BASE64URL(SHA256(verifier)) without '=' padding."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


@app.route("/introspect", methods=["POST"])
def introspect():
    token = request.form.get("token")
    token_data = access_tokens.get(token)

    if not token_data or token_data["exp"] < time.time():
        return jsonify({"active": False})

    return jsonify({
        "active": True,
        "scope": token_data["scope"],
        "username": token_data["user"],
        "client_id": token_data["client_id"],
        "token_type": "access_token",
        "exp": token_data["exp"],
        "sub": "user123"
    })


@app.route("/authorize")
def authorize():
    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    state = request.args.get("state")
    code_challenge = request.args.get("code_challenge")
    code_challenge_method = request.args.get("code_challenge_method")
    scope = request.args.get("scope", "read")

    if not code_challenge or code_challenge_method != "S256":
        return jsonify({"error": "invalid_request",
                        "error_description": "PKCE with code_challenge_method=S256 is required"}), 400

    # Simulate login and consent
    code = str(uuid.uuid4())
    auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "scope": scope,
    }

    return redirect(f"{redirect_uri}?code={code}&state={state}")

@app.route("/token", methods=["POST"])
def token():
    code = request.form.get("code")
    code_verifier = request.form.get("code_verifier", "")

    # pop: an authorization code works only once
    code_data = auth_codes.pop(code, None)
    if not code_data:
        return jsonify({"error": "invalid_grant", "error_description": "unknown or used code"}), 400

    if (request.form.get("client_id") != code_data["client_id"]
            or request.form.get("redirect_uri") != code_data["redirect_uri"]):
        return jsonify({"error": "invalid_grant", "error_description": "client_id/redirect_uri mismatch"}), 400

    # PKCE check: hash the verifier and compare with the challenge from /authorize
    if s256(code_verifier) != code_data["code_challenge"]:
        return jsonify({"error": "invalid_grant", "error_description": "code_verifier doesn't match"}), 400

    access_token = str(uuid.uuid4())
    access_tokens[access_token] = {
        "user": "chris",
        "client_id": code_data["client_id"],
        "scope": code_data["scope"],
        "exp": int(time.time()) + TOKEN_LIFETIME,
    }

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": TOKEN_LIFETIME,
        "scope": code_data["scope"],
    })

@app.route("/logout")
def logout():
    return "Logged out (simulated)", 200

if __name__ == "__main__":
    PORT = 5000
    print(f"Auth server started and running on {PORT}")
    app.run(port=PORT)
