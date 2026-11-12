# util.py - create and validate the JWT the client sends. (pip install PyJWT)
#
# Changes from the original:
#   - datetime.utcnow() (deprecated) -> datetime.now(timezone.utc)
#   - writes TOKEN into the .env next to this file (from any folder), and keeps
#     any other lines already in .env (e.g. your API keys)
#   - validate_token returns the claims dict (the old hint said str)
#   - longer demo secret (PyJWT warns about keys under 32 bytes)

# create a token
import datetime
from pathlib import Path

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# Secret key used to sign the JWT (demo only - keep real keys out of code).
# HS256 keys should be at least 32 bytes; shorter ones trigger a PyJWT warning.
secret_key = 'your-secret-key-change-me-at-least-32-bytes'

ENV_FILE = Path(__file__).with_name(".env")


def generate_token():
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    now = datetime.datetime.now(datetime.timezone.utc)
    # the user info and its claims and expiry time
    payload = {
        "sub": "1234567890",               # Subject (user ID)
        "name": "User Userson",                # Custom claim
        "admin": True,                     # Custom claim
        "iat": now,                        # Issued at
        "exp": now + datetime.timedelta(hours=1),  # Expiry
        "scopes": ["Admin.Write", "User.Read"]  # Custom claim for scopes/permissions
    }

    # encode it
    encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256", headers=header)
    print("Encoded JWT:", encoded_jwt)
    return encoded_jwt   

def validate_token(token: str) -> dict | None:
    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        return decoded
    except ExpiredSignatureError:
        print("❌ Token has expired.")
    except InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
    return None


def save_token(token: str, path: Path = ENV_FILE) -> None:
    """Set TOKEN=... in .env, keeping any other lines."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [l for l in lines if not l.strip().startswith("TOKEN=")]
    lines.append(f"TOKEN={token}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    token = generate_token()
    save_token(token)
    print(f"Saved to {ENV_FILE}")
