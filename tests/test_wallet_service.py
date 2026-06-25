from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from src.api.routes.wallet import consultar_wallet
from src.api.routes.wallet import consultar_existencia_wallet_interna
from src.core.config import settings
from src.core.security import verify_internal_wallet_token
from src.services.wallet_service import (
    calcular_saldo_real,
    normalizar_historial_wallet,
    obtener_detalle_wallet,
)


class FakeAggregateCursor:
    def __init__(self, result):
        self.result = result

    async def to_list(self, length):
        return self.result[:length]


class FakeTransactionsCollection:
    def __init__(self, docs):
        self.docs = docs

    def _matches(self, doc, match):
        for key, value in match.items():
            if key == "$or":
                if not any(self._matches(doc, condition) for condition in value):
                    return False
                continue

            if doc.get(key) != value:
                return False

        return True

    def _extract_wallet_address(self, match):
        or_conditions = match.get("$or", [])
        for condition in or_conditions:
            if "desde" in condition:
                return condition["desde"]
            if "hacia" in condition:
                return condition["hacia"]
        return None

    def aggregate(self, pipeline):
        match = pipeline[0].get("$match", {})
        matched_docs = [doc for doc in self.docs if self._matches(doc, match)]

        has_wallet_balance_projection = any(
            "$project" in stage and "saldo_disponible" in stage["$project"]
            for stage in pipeline
        )

        if has_wallet_balance_projection:
            wallet_address = self._extract_wallet_address(match)

            total_ingresos = sum(
                doc.get("monto", 0.0)
                for doc in matched_docs
                if doc.get("hacia") == wallet_address
            )
            total_egresos = sum(
                doc.get("monto", 0.0)
                for doc in matched_docs
                if doc.get("desde") == wallet_address
            )

            if not matched_docs:
                return FakeAggregateCursor([])

            return FakeAggregateCursor(
                [{"saldo_disponible": total_ingresos - total_egresos}]
            )

        total = sum(doc.get("monto", 0.0) for doc in matched_docs)
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


@pytest.mark.asyncio
async def test_us10_calcula_saldo_con_transacciones_confirmadas_de_blockchain(monkeypatch):
    wallet = "a" * 40
    db = FakeDB(
        transacciones=[
            {"hacia": wallet, "desde": "SYSTEM", "monto": 100.0, "estado": "CONFIRMED"},
        ]
    )

    async def fake_historial(wallet_address, access_token):
        assert wallet_address == wallet
        assert access_token == "jwt-usuario"
        return [
            {"to": wallet, "from": "b" * 40, "amount": 25.5, "status": "CONFIRMED"},
            {"from": wallet, "to": "c" * 40, "amount": 40.25, "status": "CONFIRMED"},
            {"to": wallet, "from": "d" * 40, "amount": 999.0, "status": "PENDING"},
        ]

    monkeypatch.setattr(settings, "blockchain_transactions_api_url", "http://blockchain:8000/api")
    monkeypatch.setattr("src.services.wallet_service.obtener_transacciones_blockchain", fake_historial)

    saldo = await calcular_saldo_real(wallet, db, access_token="jwt-usuario")

    assert saldo == 85.25


def test_normalizar_historial_wallet_mapea_campos_y_ordena_pendientes_primero():
    wallet = "a" * 40

    historial = normalizar_historial_wallet(
        wallet,
        [
            {
                "_id": "pendiente-antigua",
                "type": "TRANSFER",
                "from": "b" * 40,
                "to": wallet,
                "amount": 20.0,
                "timestamp": "2026-06-01T10:00:00+00:00",
                "status": "PENDING",
            },
            {
                "_id": "pendiente-reciente",
                "type": "TRANSFER",
                "from": wallet,
                "to": "c" * 40,
                "amount": 5.0,
                "timestamp": "2026-06-03T10:00:00+00:00",
                "status": "PENDING",
            },
            {
                "tx_id": "genesis-1",
                "type": "GENESIS_ISSUANCE",
                "from_address": "SYSTEM",
                "to_address": wallet,
                "amount": 100.0,
                "timestamp": "2026-06-05T10:00:00+00:00",
                "status": "CONFIRMED",
                "block_index": "0",
            },
            {
                "id": "confirmada-1",
                "type": "TRANSFER",
                "from": "d" * 40,
                "to": wallet,
                "amount": 10.0,
                "timestamp": "2026-06-04T10:00:00+00:00",
                "status": "CONFIRMED",
                "block_index": 4,
            },
            {
                "_id": "no-relacionada",
                "type": "TRANSFER",
                "from": "e" * 40,
                "to": "f" * 40,
                "amount": 99.0,
                "timestamp": "2026-06-06T10:00:00+00:00",
                "status": "PENDING",
            },
        ],
        limite=3,
    )

    assert [item["id"] for item in historial] == [
        "pendiente-reciente",
        "pendiente-antigua",
        "genesis-1",
    ]
    assert [item["status"] for item in historial] == ["PENDING", "PENDING", "CONFIRMED"]
    assert historial[0]["type"] == "SEND"
    assert historial[1]["type"] == "RECEIVE"
    assert historial[2]["type"] == "GENESIS"
    assert historial[2]["from"] == "SYSTEM"
    assert historial[2]["to"] == wallet
    assert historial[2]["block_index"] == 0


@pytest.mark.asyncio
async def test_internal_wallet_exists_retorna_solo_existencia_sin_datos_sensibles():
    wallet = "a" * 40
    db = FakeDB(
        wallets=[
            {
                "address": wallet,
                "user_id": "owner_1",
                "email": "owner@example.com",
                "created_at": datetime.now(timezone.utc),
            }
        ],
    )

    response = await consultar_existencia_wallet_interna(address=wallet, db=db, _=None)
    payload = response.data.model_dump()

    assert response.success is True
    assert payload == {"exists": True, "address": wallet}
    assert "owner_id" not in payload
    assert "email" not in payload


@pytest.mark.asyncio
async def test_internal_wallet_exists_retorna_false_si_no_existe():
    wallet = "a" * 40

    response = await consultar_existencia_wallet_interna(address=wallet, db=FakeDB(), _=None)

    assert response.data.exists is False
    assert response.data.address == wallet


@pytest.mark.asyncio
async def test_internal_wallet_token_rechaza_token_incorrecto(monkeypatch):
    from fastapi.security import HTTPAuthorizationCredentials

    monkeypatch.setattr(settings, "wallet_internal_token", "token-correcto")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-incorrecto")

    with pytest.raises(HTTPException) as exc_info:
        await verify_internal_wallet_token(credentials)

    assert exc_info.value.status_code == 401

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
