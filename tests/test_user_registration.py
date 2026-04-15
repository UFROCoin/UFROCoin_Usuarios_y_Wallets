import copy
import re

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.models.user import UserRegister
from src.services.user_service import register_user_with_wallet


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self):
        self.docs = []
        self.fail_on_insert = False

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    async def insert_one(self, document, session=None):
        if self.fail_on_insert:
            raise PyMongoError("forced insert error")

        new_doc = copy.deepcopy(document)
        new_doc.setdefault("_id", f"id_{len(self.docs) + 1}")
        self.docs.append(new_doc)
        return FakeInsertResult(new_doc["_id"])


class FakeTransaction:
    def __init__(self, db):
        self.db = db
        self.snapshot = None

    async def __aenter__(self):
        self.snapshot = {
            "users": copy.deepcopy(self.db.collections["users"].docs),
            "wallets": copy.deepcopy(self.db.collections["wallets"].docs),
            "transacciones": copy.deepcopy(self.db.collections["transacciones"].docs),
        }
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.db.collections["users"].docs = self.snapshot["users"]
            self.db.collections["wallets"].docs = self.snapshot["wallets"]
            self.db.collections["transacciones"].docs = self.snapshot["transacciones"]
        return False


class FakeSession:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def start_transaction(self):
        return FakeTransaction(self.db)


class FakeClient:
    def __init__(self, db):
        self.db = db

    async def start_session(self):
        return FakeSession(self.db)


class FakeDB:
    def __init__(self):
        self.collections = {
            "users": FakeCollection(),
            "wallets": FakeCollection(),
            "transacciones": FakeCollection(),
        }
        self.client = FakeClient(self)

    def __getitem__(self, key):
        return self.collections[key]


@pytest.mark.asyncio
async def test_us01_and_us04_register_user_and_wallet_success():
    db = FakeDB()
    payload = UserRegister(nombre="Ana", email="ana@ufro.cl", password="secreta123")

    response = await register_user_with_wallet(payload=payload, db=db)

    assert response["success"] is True
    assert response["data"]["user_id"] == "id_1"
    assert response["data"]["initial_balance"] == 100.0
    assert re.fullmatch(r"^[a-f0-9]{40}$", response["data"]["wallet_address"])

    assert len(db["users"].docs) == 1
    assert len(db["wallets"].docs) == 1
    assert len(db["transacciones"].docs) == 1
    assert db["wallets"].docs[0]["user_id"] == db["users"].docs[0]["_id"]
    assert db["wallets"].docs[0]["address"] == db["users"].docs[0]["wallet_address"]
    assert db["users"].docs[0]["password_hash"] != payload.password
    assert ":" in db["users"].docs[0]["password_hash"]


@pytest.mark.asyncio
async def test_us01_duplicate_email_returns_409():
    db = FakeDB()
    db["users"].docs.append(
        {
            "_id": "id_1",
            "nombre": "Ana",
            "email": "ana@ufro.cl",
            "password_hash": "hash",
            "wallet_address": "a" * 40,
        }
    )

    payload = UserRegister(nombre="Ana", email="ana@ufro.cl", password="secreta123")

    with pytest.raises(HTTPException) as exc_info:
        await register_user_with_wallet(payload=payload, db=db)

    assert exc_info.value.status_code == 409


def test_us01_model_validates_min_password_length():
    with pytest.raises(ValidationError):
        UserRegister(nombre="Ana", email="ana@ufro.cl", password="1234567")


@pytest.mark.asyncio
async def test_us04_rolls_back_user_when_wallet_insert_fails():
    db = FakeDB()
    db["wallets"].fail_on_insert = True

    payload = UserRegister(nombre="Ana", email="ana@ufro.cl", password="secreta123")

    with pytest.raises(HTTPException) as exc_info:
        await register_user_with_wallet(payload=payload, db=db)

    assert exc_info.value.status_code == 500
    assert len(db["users"].docs) == 0
    assert len(db["wallets"].docs) == 0
    assert len(db["transacciones"].docs) == 0
