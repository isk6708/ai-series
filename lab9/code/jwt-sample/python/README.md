# Run sample

Creates a JWT (JSON Web Token), then validates it and prints its claims.

## Set up environment

```sh
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source ./venv/bin/activate
```

## Install dependencies

```sh
pip install PyJWT
```

## Run code

```sh
python app.py
```

You should see output similar to:

```text
Encoded JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlVzZXIgVXNlcnNvbiIsImFkbWluIjp0cnVlLCJpYXQiOjE3NTkxNjgzMDEsImV4cCI6MTc1OTE3MTkwMX0.tz0UYNNtGVC61DWjVDF8xlhpNkp5XBtxmQH3m_RNwe8
✅ Token is valid.
Decoded claims:
  sub: 1234567890
  name: User Userson
  admin: True
  iat: 1759168301
  exp: 1759171901
```

Paste the encoded token into [jwt.io](https://jwt.io) to see its three parts (header, payload, signature).

## Changes from the book's code

The original is kept in [`original_v1/`](./original_v1/).

- `python -m venv` was missing the folder name: it's now `python -m venv venv`.
- `datetime.utcnow()` is deprecated since Python 3.12, so it's now `datetime.now(timezone.utc)`.
- The demo secret is longer, because PyJWT warns about HS256 keys under 32 bytes.
