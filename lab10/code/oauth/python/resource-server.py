# resource-server.py - a RESOURCE SERVER with a protected /userinfo endpoint.
# It asks the authorization server whether a token is valid (/introspect). (port 5001)
#
# Changes from the original:
#   - removed dead code after app.run() that tried to `from auth_server import
#     access_tokens` (it never ran, and the file is called auth-server.py)
#   - checks the token has the "read" scope
#   - a clear 503 if the authorization server isn't running
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

AUTH_SERVER = "http://localhost:5000"
REQUIRED_SCOPE = "read"

@app.route("/userinfo")
def userinfo():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing_token"}), 401

    token = auth_header.split(" ")[1]

    # check validity of token with /introspect
    try:
        token_response = requests.post(f"{AUTH_SERVER}/introspect", data={
          "token": token
        }, timeout=5)
    except requests.RequestException:
        return jsonify({"error": "auth_server_unavailable"}), 503

    token_data = token_response.json()
    is_active = token_data.get("active", False)

    if not is_active:
        return jsonify({"error": "invalid_token"}), 403

    if REQUIRED_SCOPE not in token_data.get("scope", "").split():
        return jsonify({"error": "insufficient_scope"}), 403

    return jsonify({
        "sub": "user123",
        "name": "Chris",
        "email": "chris@example.com"
    })

if __name__ == "__main__":
    PORT = 5001
    print(f"Resource server started on {PORT}")
    app.run(port=PORT)
