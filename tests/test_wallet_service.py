from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from src.api.routes.wallet import consultar_wallet
from src.services.wallet_service import calcular_saldo_real, obtener_detalle_wallet


class FakeAggregateCursor:
    def __init__(self, result):
        self.result = result

    async def to_list(self, length):
        return self.result[:length]


class FakeTransactionsCollection:
    def __init__(self, docs):
        self.docs = docs

    def aggregate(self, pipeline):
        match = pipeline[0]["$match"]
        total = 0.0
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in match.items()):
                total += doc.get("monto", 0.0)
        return FakeAggregateCursor([{"_id": None, "total": total}] if total else [])


class FakeWalletsCollection:
    def __init__(self, docs):
        self.docs = docs

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc
        return None


class FakeDB:
    def __init__(self, wallets=None, transacciones=None):
        self.collections = {
            "wallets": FakeWalletsCollection(wallets or []),
            "transacciones": FakeTransactionsCollection(transacciones or []),
        }

    def __getitem__(self, key):
        return self.collections[key]


@pytest.mark.asyncio
async def test_us09_calcula_saldo_real_ingresos_menos_egresos_e_ignora_pendientes():
    wallet = "a" * 40
    db = FakeDB(
        transacciones=[
            {"hacia": wallet, "desde": "SYSTEM", "monto": 100.0, "estado": "CONFIRMED"},
            {"hacia": wallet, "desde": "b" * 40, "monto": 25.5, "estado": "CONFIRMED"},
            {"desde": wallet, "hacia": "c" * 40, "monto": 40.25, "estado": "CONFIRMED"},
            {"hacia": wallet, "desde": "d" * 40, "monto": 999.0, "estado": "PENDING"},
            {"desde": wallet, "hacia": "e" * 40, "monto": 999.0, "estado": "PENDING"},
        ]
    )

    saldo = await calcular_saldo_real(wallet, db)

    assert saldo == 85.25


@pytest.mark.asyncio
async def test_us09_calcula_saldo_real_sin_transacciones_retorna_cero():
    saldo = await calcular_saldo_real("a" * 40, FakeDB())

    assert saldo == 0.0


@pytest.mark.asyncio
async def test_us09_calcula_saldo_real_permite_saldo_negativo_si_egresos_superan_ingresos():
    wallet = "a" * 40
    db = FakeDB(
        transacciones=[
            {"hacia": wallet, "desde": "SYSTEM", "monto": 10.0, "estado": "CONFIRMED"},
            {"desde": wallet, "hacia": "b" * 40, "monto": 30.0, "estado": "CONFIRMED"},
        ]
    )

    saldo = await calcular_saldo_real(wallet, db)

    assert saldo == -20.0


@pytest.mark.asyncio
async def test_obtener_detalle_wallet_retorna_owner_y_saldo_calculado():
    wallet = "a" * 40
    created_at = datetime.now(timezone.utc)
    db = FakeDB(
        wallets=[{"address": wallet, "user_id": "user_1", "created_at": created_at}],
        transacciones=[{"hacia": wallet, "desde": "SYSTEM", "monto": 100.0, "estado": "CONFIRMED"}],
    )

    detalle = await obtener_detalle_wallet(wallet, db)

    assert detalle == {
        "address": wallet,
        "owner_id": "user_1",
        "balance": 100.0,
        "created_at": created_at,
    }


@pytest.mark.asyncio
async def test_obtener_detalle_wallet_inexistente_retorna_404_controlado():
    with pytest.raises(HTTPException) as exc_info:
        await obtener_detalle_wallet("a" * 40, FakeDB())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "WALLET_NOT_FOUND"


@pytest.mark.asyncio
async def test_consultar_wallet_rechaza_usuario_que_no_es_dueno():
    wallet = "a" * 40
    db = FakeDB(
        wallets=[{"address": wallet, "user_id": "owner_1", "created_at": datetime.now(timezone.utc)}],
        transacciones=[{"hacia": wallet, "desde": "SYSTEM", "monto": 100.0, "estado": "CONFIRMED"}],
    )

    with pytest.raises(HTTPException) as exc_info:
        await consultar_wallet(address=wallet, db=db, current_user={"id": "attacker_1"})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_consultar_wallet_permite_usuario_dueno():
    wallet = "a" * 40
    created_at = datetime.now(timezone.utc)
    db = FakeDB(
        wallets=[{"address": wallet, "user_id": "owner_1", "created_at": created_at}],
        transacciones=[{"hacia": wallet, "desde": "SYSTEM", "monto": 100.0, "estado": "CONFIRMED"}],
    )

    response = await consultar_wallet(address=wallet, db=db, current_user={"id": "owner_1"})

    assert response.success is True
    assert response.data.address == wallet
    assert response.data.balance == 100.0
