"""Single demo account auth - SPEC.md section 38. No signup, no user table.

Password hashing uses stdlib `hashlib.scrypt` rather than the spec-suggested Argon2:
this dev machine's Application Control policy blocks argon2-cffi's compiled DLL from
loading (other native deps - psycopg, pymupdf, cryptography - are unaffected, so this
is specific to that package, not a general native-extension ban). scrypt is a
comparably memory-hard KDF and a legitimate password-hashing choice; see
docs/decisions.md. The interface below (hash_password/verify_password) is what the
rest of the app depends on, so swapping back to argon2-cffi in an unrestricted
environment is a one-file change.
"""

import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

_ALGORITHM = "HS256"
_COOKIE_NAME = "policylens_session"

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_LENGTH = 32


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_KEY_LENGTH
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        scheme, n, r, p, salt_hex, hash_hex = password_hash.split("$")
        if scheme != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(hash_hex) // 2,
        )
        return hmac.compare_digest(derived.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(username: str, secret: str, ttl_minutes: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
    payload = {"sub": username, "exp": expires_at}
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> str | None:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
