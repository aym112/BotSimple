from app.auth.service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_correct_password_verifies(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_empty_hash_fails_closed(self):
        assert verify_password("anything", "") is False

    def test_malformed_hash_fails_closed(self):
        assert verify_password("anything", "not-a-real-hash") is False

    def test_two_hashes_of_same_password_differ(self):
        # Random salt per call - hashes must not be comparable/reused directly.
        assert hash_password("same-password") != hash_password("same-password")


class TestAccessToken:
    def test_round_trip(self):
        token = create_access_token("demo", "secret", ttl_minutes=10)
        assert decode_access_token(token, "secret") == "demo"

    def test_wrong_secret_rejected(self):
        token = create_access_token("demo", "secret", ttl_minutes=10)
        assert decode_access_token(token, "wrong-secret") is None

    def test_garbage_token_rejected(self):
        assert decode_access_token("not-a-jwt", "secret") is None
