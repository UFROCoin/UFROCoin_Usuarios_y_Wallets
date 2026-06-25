from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from src.api.routes.auth import get_me
from src.core.config import settings
from src.core.security import get_current_user
from src.models.user import ForgotPasswordRequest, LoginRequest, UserRegister
from src.services.user_service import authenticate_user, get_my_profile
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


class FakeAggregateCursor:
    def __init__(self, result):
        self.result = result

    async def to_list(self, length):
        return self.result[:length]


class FakeTransactionsCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def aggregate(self, pipeline):
        match = pipeline[0].get("$match", {})
        address = None
        for condition in match.get("$or", []):
            address = condition.get("desde") or condition.get("hacia")
            if address:
                break

        confirmed_docs = [
            doc
            for doc in self.docs
            if doc.get("estado") == "CONFIRMED"
            and (doc.get("desde") == address or doc.get("hacia") == address)
        ]

        if not confirmed_docs:
            return FakeAggregateCursor([])

        total_ingresos = sum(doc.get("monto", 0.0) for doc in confirmed_docs if doc.get("hacia") == address)
        total_egresos = sum(doc.get("monto", 0.0) for doc in confirmed_docs if doc.get("desde") == address)
        return FakeAggregateCursor([{"saldo_disponible": total_ingresos - total_egresos}])


class FakeDB:
    def __init__(self, users=None, transacciones=None):
        self.collections = {
            "users": FakeUsersCollection(users),
            "transacciones": FakeTransactionsCollection(transacciones),
        }

    def __getitem__(self, key):
        return self.collections[key]


@pytest.fixture(autouse=True)
def configure_jwt_settings(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "blockchain_transactions_api_url", "")


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


@pytest.mark.asyncio
async def test_get_my_profile_returns_account_info_and_empty_history():
    wallet_address = "a" * 40
    db = FakeDB(
        users=[
            {
                "_id": "user_1",
                "nombre": "Ana Perez",
                "email": "ana@ufro.cl",
                "wallet_address": wallet_address,
            }
        ],
        transacciones=[
            {"desde": "SYSTEM", "hacia": wallet_address, "monto": 100.0, "estado": "CONFIRMED"},
            {"desde": wallet_address, "hacia": "b" * 40, "monto": 25.0, "estado": "CONFIRMED"},
            {"desde": "c" * 40, "hacia": wallet_address, "monto": 999.0, "estado": "PENDING"},
        ],
    )

    profile = await get_my_profile("user_1", db)

    assert profile.nombre == "Ana Perez"
    assert profile.email == "ana@ufro.cl"
    assert profile.wallet_address == wallet_address
    assert profile.balance == 75.0
    assert profile.history == []


@pytest.mark.asyncio
async def test_get_my_profile_returns_external_history_pending_first(monkeypatch):
    wallet_address = "a" * 40
    db = FakeDB(
        users=[
            {
                "_id": "user_1",
                "nombre": "Ana Perez",
                "email": "ana@ufro.cl",
                "wallet_address": wallet_address,
            }
        ],
        transacciones=[
            {"desde": "SYSTEM", "hacia": wallet_address, "monto": 100.0, "estado": "CONFIRMED"},
        ],
    )

    expected_wallet_address = wallet_address

    async def fake_historial(wallet_address, access_token):
        assert wallet_address == expected_wallet_address
        assert access_token == "jwt-usuario"
        return [
            {
                "_id": "pendiente-antigua",
                "type": "TRANSFER",
                "from": "b" * 40,
                "to": wallet_address,
                "amount": 999.0,
                "timestamp": "2026-06-01T10:00:00+00:00",
                "status": "PENDING",
            },
            {
                "_id": "pendiente-reciente",
                "type": "TRANSFER",
                "from": wallet_address,
                "to": "c" * 40,
                "amount": 5.0,
                "timestamp": "2026-06-03T10:00:00+00:00",
                "status": "PENDING",
            },
            {
                "id": "confirmada-reciente",
                "type": "TRANSFER",
                "from": wallet_address,
                "to": "d" * 40,
                "amount": 25.0,
                "timestamp": "2026-06-04T10:00:00+00:00",
                "status": "CONFIRMED",
                "block_index": 4,
            },
            {
                "id": "confirmada-antigua",
                "type": "TRANSFER",
                "from": "e" * 40,
                "to": wallet_address,
                "amount": 10.0,
                "timestamp": "2026-06-02T10:00:00+00:00",
                "status": "CONFIRMED",
                "block_index": 3,
            },
        ]

    monkeypatch.setattr(settings, "blockchain_transactions_api_url", "http://blockchain:8000/api")
    monkeypatch.setattr("src.services.user_service.obtener_transacciones_blockchain", fake_historial)

    profile = await get_my_profile("user_1", db, access_token="jwt-usuario")

    assert profile.balance == 85.0
    assert [item.id for item in profile.history] == [
        "pendiente-reciente",
        "pendiente-antigua",
        "confirmada-reciente",
        "confirmada-antigua",
    ]
    assert [item.status for item in profile.history] == [
        "PENDING",
        "PENDING",
        "CONFIRMED",
        "CONFIRMED",
    ]
    assert profile.history[0].type == "SEND"
    assert profile.history[1].type == "RECEIVE"


@pytest.mark.asyncio
async def test_get_my_profile_rejects_missing_user():
    with pytest.raises(HTTPException) as exc_info:
        await get_my_profile("missing_user", FakeDB())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_me_endpoint_returns_profile_response_contract():
    wallet_address = "b" * 40
    db = FakeDB(
        users=[
            {
                "_id": "user_2",
                "nombre": "Juan Soto",
                "email": "juan@ufro.cl",
                "wallet_address": wallet_address,
            }
        ],
        transacciones=[
            {"desde": "SYSTEM", "hacia": wallet_address, "monto": 50.0, "estado": "CONFIRMED"},
        ],
    )

    response = await get_me(db=db, current_user={"id": "user_2"})

    assert response.success is True
    assert response.message == "Cuenta consultada correctamente."
    assert response.data.wallet_address == wallet_address
    assert response.data.history == []
