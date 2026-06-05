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