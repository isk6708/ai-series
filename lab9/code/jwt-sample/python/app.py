# pip install PyJWT
#
# Changes from the original:
#   - datetime.utcnow() (deprecated since Python 3.12) -> datetime.now(timezone.utc)
#   - longer demo secret: PyJWT warns about HS256 keys under 32 bytes

# create a token
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import datetime

# Secret key used to sign the JWT (demo only - keep real keys out of code)
secret_key = 'your-secret-key-change-me-at-least-32-bytes'

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
    "exp": now + datetime.timedelta(hours=1)  # Expiry
}

# encode it
encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256", headers=header)

print("Encoded JWT:", encoded_jwt) 

# validate a token
try:
    decoded = jwt.decode(encoded_jwt, secret_key, algorithms=["HS256"])
    print("✅ Token is valid.")
    print("Decoded claims:")
    for key, value in decoded.items():
        print(f"  {key}: {value}")
except ExpiredSignatureError:
    print("❌ Token has expired.")
except InvalidTokenError as e:
    print(f"❌ Invalid token: {e}")
