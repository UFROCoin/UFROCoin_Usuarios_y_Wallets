from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from src.core.config import settings
from src.core.security import get_current_user
from src.models.user import ForgotPasswordRequest, LoginRequest, UserRegister
from src.services.user_service import authenticate_user
from src.utils.security import hash_contrasena, verificar_contrasena
from src.utils.wallet import generar_direccion_wallet


class FakeUsersCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc
        return None


class FakeDB:
    def __init__(self, users=None):
        self.collections = {"users": FakeUsersCollection(users)}

    def __getitem__(self, key):
        return self.collections[key]


@pytest.fixture(autouse=True)
def configure_jwt_settings(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")


def make_credentials(payload, secret="test-secret"):
    token = jwt.encode(payload, secret, algorithm="HS256")
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_authenticate_user_accepts_valid_password_and_rejects_wrong_password():
    password_hash = hash_contrasena("secreta123")["data"]["hash"]
    db = FakeDB(users=[{"email": "ana@ufro.cl", "password_hash": password_hash}])

    assert await authenticate_user("ana@ufro.cl", "secreta123", db) is not False
    assert await authenticate_user("ana@ufro.cl", "incorrecta123", db) is False


@pytest.mark.asyncio
async def test_authenticate_user_rejects_missing_user():
    result = await authenticate_user("nadie@ufro.cl", "secreta123", FakeDB())

    assert result is False


@pytest.mark.asyncio
async def test_get_current_user_accepts_valid_token_with_user_id():
    credentials = make_credentials(
        {"user_id": "user_1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    )

    current_user = await get_current_user(credentials)

    assert current_user == {"id": "user_1"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_token_without_user_id():
    credentials = make_credentials({"exp": datetime.now(timezone.utc) + timedelta(hours=1)})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_signature():
    credentials = make_credentials(
        {"user_id": "user_1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        secret="wrong-secret",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_token():
    credentials = make_credentials(
        {"user_id": "user_1", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


def test_hash_contrasena_rejects_empty_and_blank_passwords():
    assert hash_contrasena("")["code"] == "EMPTY_PASSWORD"
    assert hash_contrasena("   ")["code"] == "EMPTY_PASSWORD"


def test_verificar_contrasena_rejects_invalid_inputs():
    assert verificar_contrasena("", "salt:hash")["code"] == "EMPTY_PASSWORD"
    assert verificar_contrasena("secreta123", "hash_sin_separador")["code"] == "INVALID_HASH"


def test_verificar_contrasena_detects_password_incorrecta():
    stored_hash = hash_contrasena("secreta123")["data"]["hash"]

    result = verificar_contrasena("otra1234", stored_hash)

    assert result == {"status": "ok", "data": {"valid": False}}


def test_generar_direccion_wallet_rejects_empty_required_fields():
    assert generar_direccion_wallet("", "2026-01-01T00:00:00Z")["code"] == "EMPTY_EMAIL"
    assert generar_direccion_wallet("ana@ufro.cl", "")["code"] == "EMPTY_TIMESTAMP"


def test_generar_direccion_wallet_returns_40_lowercase_hex_chars():
    result = generar_direccion_wallet("ana@ufro.cl", "2026-01-01T00:00:00Z")

    address = result["data"]["direccion"]
    assert result["status"] == "ok"
    assert len(address) == 40
    assert address == address.lower()
    int(address, 16)


def test_user_register_password_boundary_and_extra_fields():
    with pytest.raises(ValidationError):
        UserRegister(nombre="Ana", email="ana@ufro.cl", password="1234567")

    valid = UserRegister(nombre="Ana", email="ana@ufro.cl", password="12345678")
    assert valid.password == "12345678"

    with pytest.raises(ValidationError):
        UserRegister(nombre="Ana", email="ana@ufro.cl", password="12345678", rol="admin")


def test_auth_request_models_reject_invalid_email_and_extra_fields():
    with pytest.raises(ValidationError):
        LoginRequest(email="no-es-email", password="secreta123")

    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="ana@ufro.cl", token="unexpected")
