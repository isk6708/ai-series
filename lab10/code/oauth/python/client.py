# client.py - walks through the OAuth 2.1 authorization code flow with PKCE,
# then calls the resource server with the access token.
#
# Changes from the original:
#   - real PKCE: a random code_verifier per run, sent as an S256 code_challenge
#     (the original used the fixed string "123" with method "plain")
#   - a random state, checked when the code comes back (protects against CSRF)
#   - stops with a clear message if a step fails, instead of carrying on with None
#   - TODO 1a: reuses a saved token if /introspect says it's still valid (see below)
import base64
import hashlib
import json
import secrets
import sys
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

# Configuration
AUTH_SERVER = "http://localhost:5000"
RESOURCE_SERVER = "http://localhost:5001"
CLIENT_ID = "abc"
REDIRECT_URI = "http://localhost:3000/callback"
SCOPE = "read"
TOKEN_CACHE = Path(__file__).with_name(".token-cache.json")   # ignored by git


def fail(message: str):
    print(f"ERROR: {message}")
    sys.exit(1)


def make_pkce_pair() -> tuple[str, str]:
    """PKCE: a secret verifier, and its S256 challenge to send first."""
    code_verifier = secrets.token_urlsafe(64)  # 43-128 chars
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def is_token_active(token: str) -> bool:
    try:
        r = requests.post(f"{AUTH_SERVER}/introspect", data={"token": token}, timeout=5)
        return r.json().get("active", False)
    except requests.RequestException:
        return False


def get_new_token() -> str:
    code_verifier, code_challenge = make_pkce_pair()
    state = secrets.token_urlsafe(16)

    # Step 1: Simulate browser redirect to /authorize
    authorize_url = f"{AUTH_SERVER}/authorize?" + urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    print(f"Requesting authorization: {authorize_url}")
    try:
        response = requests.get(authorize_url, allow_redirects=False, timeout=5)
    except requests.RequestException:
        fail(f"Can't reach the authorization server at {AUTH_SERVER}. Is auth-server.py running?")

    # Step 2: Extract authorization code from redirect
    redirect_location = response.headers.get("Location")
    if not redirect_location:
        fail(f"Authorization server did not redirect ({response.status_code}): {response.text}")

    query_params = parse_qs(urlparse(redirect_location).query)
    if query_params.get("state", [None])[0] != state:
        fail("State mismatch - possible CSRF, stopping.")
    auth_code = query_params.get("code", [None])[0]
    print(f"Received authorization code: {auth_code}")

    # Step 3: Exchange code (+ the PKCE verifier) for an access token
    token_response = requests.post(f"{AUTH_SERVER}/token", data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier,
    }, timeout=5)
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        fail(f"Token request failed: {token_data}")
    print(f"Access token: {access_token}")
    TOKEN_CACHE.write_text(json.dumps({"access_token": access_token}))
    return access_token


# 1a. If we have a saved token, check it with /introspect and reuse it
access_token = None
if TOKEN_CACHE.exists():
    saved = json.loads(TOKEN_CACHE.read_text()).get("access_token")
    if saved and is_token_active(saved):
        print(f"Reusing saved access token: {saved}")
        access_token = saved

# 1b. No valid token: start the journey with /authorize
if not access_token:
    access_token = get_new_token()

# Step 4: Call resource server
try:
    resource_response = requests.get(f"{RESOURCE_SERVER}/userinfo", headers={
        "Authorization": f"Bearer {access_token}"
    }, timeout=5)
except requests.RequestException:
    fail(f"Can't reach the resource server at {RESOURCE_SERVER}. Is resource-server.py running?")
print("User info response:")
print(resource_response.json())
