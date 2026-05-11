from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.core.config import settings
from src.models.user import ResetPasswordRequest
from src.services.user_service import reset_user_password
from src.utils.security import hash_contrasena, verificar_contrasena


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self):
        self.docs = []
        self.fail_on_update = False

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    async def update_one(self, query, update):
        if self.fail_on_update:
            raise PyMongoError("forced update error")

        doc = await self.find_one(query)
        if doc is None:
            return FakeUpdateResult(0)

        doc.update(update.get("$set", {}))
        return FakeUpdateResult(1)


class FakeDB:
    def __init__(self):
        self.collections = {"users": FakeCollection()}

    def __getitem__(self, key):
        return self.collections[key]


def make_password_hash(password="actual123"):
    return hash_contrasena(password)["data"]["hash"]


def make_recovery_token(user_id, password_hash, expires_delta=timedelta(hours=1)):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key + password_hash, algorithm=settings.jwt_algorithm)


@pytest.fixture(autouse=True)
def configure_settings(monkeypatch):
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")


@pytest.mark.asyncio
async def test_us14_reset_password_success_updates_hash():
    db = FakeDB()
    current_hash = make_password_hash()
    db["users"].docs.append({"_id": "id_1", "password_hash": current_hash})
    token = make_recovery_token("id_1", current_hash)

    response = await reset_user_password(token=token, new_password="nueva123", db=db)

    assert response["success"] is True
    assert response["message"] == "Contrasena restablecida correctamente."
    assert response["data"] == {}
    assert response["error"] == {"code": "", "details": ""}
    assert db["users"].docs[0]["password_hash"] != current_hash
    assert verificar_contrasena("nueva123", db["users"].docs[0]["password_hash"])["data"]["valid"] is True


@pytest.mark.asyncio
async def test_us14_recovery_token_is_single_use():
    db = FakeDB()
    current_hash = make_password_hash()
    db["users"].docs.append({"_id": "id_1", "password_hash": current_hash})
    token = make_recovery_token("id_1", current_hash)

    await reset_user_password(token=token, new_password="nueva123", db=db)

    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(token=token, new_password="otra1234", db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_OR_EXPIRED_TOKEN"


@pytest.mark.asyncio
async def test_us14_invalid_signature_returns_401():
    db = FakeDB()
    current_hash = make_password_hash()
    db["users"].docs.append({"_id": "id_1", "password_hash": current_hash})
    token = jwt.encode(
        {"user_id": "id_1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(token=token, new_password="nueva123", db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_OR_EXPIRED_TOKEN"


@pytest.mark.asyncio
async def test_us14_expired_token_returns_401():
    db = FakeDB()
    current_hash = make_password_hash()
    db["users"].docs.append({"_id": "id_1", "password_hash": current_hash})
    token = make_recovery_token("id_1", current_hash, expires_delta=timedelta(seconds=-1))

    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(token=token, new_password="nueva123", db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_OR_EXPIRED_TOKEN"


def test_us14_model_validates_new_password_length():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="token", new_password="1234567")


@pytest.mark.asyncio
async def test_us14_database_error_returns_500():
    db = FakeDB()
    current_hash = make_password_hash()
    db["users"].docs.append({"_id": "id_1", "password_hash": current_hash})
    db["users"].fail_on_update = True
    token = make_recovery_token("id_1", current_hash)

    with pytest.raises(HTTPException) as exc_info:
        await reset_user_password(token=token, new_password="nueva123", db=db)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["code"] == "DATABASE_ERROR"
