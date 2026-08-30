"""python -m app.auth.hash_password <password>  ->  prints an Argon2 hash for .env's
DEMO_PASSWORD_HASH (SPEC.md section 53)."""

import sys

from app.auth.service import hash_password


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m app.auth.hash_password <password>", file=sys.stderr)
        return 1
    print(hash_password(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
