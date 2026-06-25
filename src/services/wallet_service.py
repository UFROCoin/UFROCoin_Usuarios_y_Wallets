import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import settings


async def calcular_saldo_real(
    wallet_address: str,
    db: AsyncIOMotorDatabase,
    access_token: str | None = None,
    transacciones_externas: list[dict[str, Any]] | None = None,
) -> float:
    """
    Calcula el saldo real de una wallet.

    Base local:
    - transacciones internas confirmadas, como el saldo inicial de registro.

    Integracion US-10:
    - si BLOCKCHAIN_TRANSACTIONS_API_URL esta configurada y existe JWT de usuario,
      consulta el historial del Modulo 2 y aplica solo transacciones CONFIRMED.
    """
    saldo_local = await _calcular_saldo_local(wallet_address, db)

    if transacciones_externas is None:
        if not settings.blockchain_transactions_api_url or not access_token:
            return saldo_local

        transacciones_externas = await obtener_transacciones_blockchain(
            wallet_address=wallet_address,
            access_token=access_token,
        )
    saldo_externo = calcular_delta_confirmado(wallet_address, transacciones_externas)

    return float(saldo_local + saldo_externo)


async def _calcular_saldo_local(wallet_address: str, db: AsyncIOMotorDatabase) -> float:
    pipeline = [
        {
            "$match": {
                "$or": [{"desde": wallet_address}, {"hacia": wallet_address}],
                "estado": "CONFIRMED",
            }
        },
        {
            "$group": {
                "_id": None,
                "total_ingresos": {
                    "$sum": {"$cond": [{"$eq": ["$hacia", wallet_address]}, "$monto", 0]}
                },
                "total_egresos": {
                    "$sum": {"$cond": [{"$eq": ["$desde", wallet_address]}, "$monto", 0]}
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "saldo_disponible": {"$subtract": ["$total_ingresos", "$total_egresos"]},
            }
        },
    ]

    cursor = db["transacciones"].aggregate(pipeline)
    resultado = await cursor.to_list(length=1)

    if not resultado:
        return 0.0

    return float(resultado[0]["saldo_disponible"])


async def obtener_transacciones_blockchain(
    wallet_address: str,
    access_token: str,
    page_limit: int = 100,
) -> list[dict[str, Any]]:
    transacciones: list[dict[str, Any]] = []
    page = 1

    while True:
        pagina = await asyncio.to_thread(
            _obtener_pagina_historial_blockchain,
            wallet_address,
            access_token,
            page,
            page_limit,
        )
        transacciones.extend(pagina)

        if len(pagina) < page_limit:
            break

        page += 1

    return transacciones


def _obtener_pagina_historial_blockchain(
    wallet_address: str,
    access_token: str,
    page: int,
    limit: int,
) -> list[dict[str, Any]]:
    base_url = settings.blockchain_transactions_api_url.rstrip("/")
    encoded_address = quote(wallet_address, safe="")
    url = f"{base_url}/history/{encoded_address}?page={page}&limit={limit}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=settings.blockchain_transactions_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "No fue posible consultar transacciones externas.",
                "code": "BLOCKCHAIN_TRANSACTIONS_UNAVAILABLE",
                "details": "El modulo de Blockchain y Transacciones no respondio correctamente.",
            },
        ) from exc

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "message": "Respuesta invalida del modulo de transacciones.",
            "code": "INVALID_BLOCKCHAIN_TRANSACTIONS_RESPONSE",
            "details": "El historial externo no tiene el formato esperado.",
        },
    )


def calcular_delta_confirmado(wallet_address: str, transacciones: list[dict[str, Any]]) -> float:
    saldo = 0.0

    for transaccion in transacciones:
        estado = transaccion.get("status") or transaccion.get("estado")
        if estado != "CONFIRMED":
            continue

        origen = transaccion.get("from") or transaccion.get("from_address") or transaccion.get("desde")
        destino = transaccion.get("to") or transaccion.get("to_address") or transaccion.get("hacia")
        monto = float(transaccion.get("amount") or transaccion.get("monto") or 0.0)

        if destino == wallet_address:
            saldo += monto
        if origen == wallet_address:
            saldo -= monto

    return saldo


def normalizar_historial_wallet(
    wallet_address: str,
    transacciones: list[dict[str, Any]],
    limite: int = 10,
) -> list[dict[str, Any]]:
    if limite <= 0:
        return []

    history: list[dict[str, Any]] = []

    for transaccion in transacciones:
        origen = _primer_valor(transaccion, "from", "from_address", "desde")
        destino = _primer_valor(transaccion, "to", "to_address", "hacia")

        if origen != wallet_address and destino != wallet_address:
            continue

        history.append(
            {
                "id": str(_primer_valor(transaccion, "id", "_id", "tx_id") or ""),
                "type": _normalizar_tipo_historial(
                    wallet_address,
                    str(_primer_valor(transaccion, "type", "tipo") or "TRANSFER"),
                    origen,
                    destino,
                ),
                "from": str(origen or ""),
                "to": str(destino or ""),
                "amount": float(_primer_valor(transaccion, "amount", "monto") or 0.0),
                "timestamp": str(_primer_valor(transaccion, "timestamp", "created_at") or ""),
                "status": _normalizar_estado_historial(
                    str(_primer_valor(transaccion, "status", "estado") or "PENDING")
                ),
                "block_index": _normalizar_block_index(
                    _primer_valor(transaccion, "block_index", "blockIndex")
                ),
            }
        )

    history.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    history.sort(key=lambda item: 0 if item["status"] == "PENDING" else 1)
    return history[:limite]


def _primer_valor(transaccion: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = transaccion.get(key)
        if value is not None:
            return value
    return None


def _normalizar_tipo_historial(
    wallet_address: str,
    tipo: str,
    origen: Any,
    destino: Any,
) -> str:
    tipo_normalizado = tipo.upper()

    if tipo_normalizado in {"GENESIS", "GENESIS_ISSUANCE"}:
        return "GENESIS"
    if tipo_normalizado == "MINING_REWARD":
        return "MINING_REWARD"
    if tipo_normalizado in {"SEND", "RECEIVE"}:
        return tipo_normalizado
    if origen == wallet_address:
        return "SEND"
    if destino == wallet_address:
        return "RECEIVE"

    return "RECEIVE"


def _normalizar_estado_historial(estado: str) -> str:
    if estado.upper() == "CONFIRMED":
        return "CONFIRMED"
    return "PENDING"


def _normalizar_block_index(block_index: Any) -> int | None:
    if block_index is None:
        return None

    try:
        return int(block_index)
    except (TypeError, ValueError):
        return None


async def obtener_transacciones_recientes(
    wallet_address: str,
    db: AsyncIOMotorDatabase,
    limite: int = 5,
):
    """
    Obtiene las transacciones locales mas recientes de una wallet.
    """
    cursor = db["transacciones"].find(
        {"$or": [{"desde": wallet_address}, {"hacia": wallet_address}]}
    ).sort("timestamp", -1).limit(limite)

    return await cursor.to_list(limite)


async def obtener_detalle_wallet(
    address: str,
    db: AsyncIOMotorDatabase,
    access_token: str | None = None,
):
    """
    Obtiene los datos basicos de la wallet y adjunta el saldo real calculado.
    """
    wallet = await db["wallets"].find_one({"address": address})

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "code": "WALLET_NOT_FOUND",
                "message": "La billetera especificada no existe.",
            },
        )

    saldo_actual = await calcular_saldo_real(address, db, access_token=access_token)

    return {
        "address": wallet["address"],
        "owner_id": str(wallet["user_id"]),
        "balance": saldo_actual,
        "created_at": wallet["created_at"],
    }


async def wallet_exists(address: str, db: AsyncIOMotorDatabase) -> bool:
    wallet = await db["wallets"].find_one({"address": address})
    return wallet is not None
