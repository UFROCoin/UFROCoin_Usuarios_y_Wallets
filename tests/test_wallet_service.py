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

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from src.services.wallet_service import calcular_saldo_real, obtener_detalle_wallet

@pytest.mark.asyncio
async def test_calcular_saldo_real_con_transacciones():
    mock_db = MagicMock()
    mock_cursor = AsyncMock()
    
    mock_cursor.to_list.return_value = [{"saldo_disponible": 150.0}]
    mock_db["transacciones"].aggregate.return_value = mock_cursor

    wallet_address = "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"
    saldo = await calcular_saldo_real(wallet_address, mock_db)

    assert saldo == 150.0
    mock_db["transacciones"].aggregate.assert_called_once()


@pytest.mark.asyncio
async def test_calcular_saldo_real_sin_transacciones():
    mock_db = MagicMock()
    mock_cursor = AsyncMock()
    
    mock_cursor.to_list.return_value = []
    mock_db["transacciones"].aggregate.return_value = mock_cursor

    wallet_address = "b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11"
    saldo = await calcular_saldo_real(wallet_address, mock_db)

    assert saldo == 0.0


@pytest.mark.asyncio
async def test_obtener_detalle_wallet_exito(monkeypatch):
    mock_db = MagicMock()
    
    mock_db["wallets"].find_one = AsyncMock(return_value={
        "address": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
        "user_id": "67f7d1d2f2a80f2f9f2d1a12",
        "created_at": "2026-06-04T12:00:00Z"
    })

    async def mock_calcular_saldo(*args, **kwargs):
        return 250.0
    
    monkeypatch.setattr("src.services.wallet_service.calcular_saldo_real", mock_calcular_saldo)

    resultado = await obtener_detalle_wallet("a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10", mock_db)

    assert resultado["address"] == "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"
    assert resultado["owner_id"] == "67f7d1d2f2a80f2f9f2d1a12"
    assert resultado["balance"] == 250.0


@pytest.mark.asyncio
async def test_obtener_detalle_wallet_no_encontrada():
    mock_db = MagicMock()
    mock_db["wallets"].find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await obtener_detalle_wallet("wallet_inexistente", mock_db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "WALLET_NOT_FOUND"