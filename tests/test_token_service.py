from datetime import datetime, timezone

import jwt
import pytest

from src.core.config import settings
from src.services.token_service import generate_token


def test_generate_token_include_claims_and_expiration(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "jwt_expire_hours", 24)

    issued_at = datetime.now(timezone.utc)
    token = generate_token(
        user_id="67f7d1d2f2a80f2f9f2d1a12",
        wallet_address="a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
    )
    decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
    expires_at = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    assert decoded["user_id"] == "67f7d1d2f2a80f2f9f2d1a12"
    assert decoded["wallet_address"] == "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"
    assert 23.9 <= (expires_at - issued_at).total_seconds() / 3600 <= 24.1


def test_generate_token_valid_signature_with_settings_secret(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "settings-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "jwt_expire_hours", 24)

    token = generate_token(
        user_id="id_1",
        wallet_address="b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11",
    )

    decoded = jwt.decode(token, "settings-secret", algorithms=["HS256"])

    assert decoded["user_id"] == "id_1"
    assert decoded["wallet_address"] == "b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11"

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "otra-secret", algorithms=["HS256"])
