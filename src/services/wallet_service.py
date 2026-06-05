from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status

async def calcular_saldo_real(wallet_address: str, db: AsyncIOMotorDatabase) -> float:
    """
    Calcula el saldo disponible sumando transacciones de entrada y restando las de salida.
    Cumple con los criterios de aceptación usando una sola consulta de agregación.
    Solo considera transacciones con estado 'CONFIRMED' para ignorar el mempool (PENDING).
    """
    pipeline = [
        {
            "$match": {
                "$or": [{"desde": wallet_address}, {"hacia": wallet_address}],
                "estado": "CONFIRMED"
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
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "saldo_disponible": {"$subtract": ["$total_ingresos", "$total_egresos"]}
            }
        }
    ]

    cursor = db["transacciones"].aggregate(pipeline)
    resultado = await cursor.to_list(length=1)

    if not resultado:
        return 0.0

    return float(resultado[0]["saldo_disponible"])


async def obtener_transacciones_recientes(wallet_address: str, db: AsyncIOMotorDatabase, limite: int = 5):
    """
    Obtiene las transacciones mas recientes de una wallet.
    """
    cursor = db["transacciones"].find(
        {"$or": [{"desde": wallet_address}, {"hacia": wallet_address}]}
    ).sort("timestamp", -1).limit(limite)
    
    return await cursor.to_list(limite)


async def obtener_detalle_wallet(address: str, db: AsyncIOMotorDatabase):
    """
    Obtiene los datos básicos de la wallet (dirección e ID del propietario)
    y le adjunta el saldo real calculado.
    Cumple con US-08.
    """
    wallet = await db["wallets"].find_one({"address": address})
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "code": "WALLET_NOT_FOUND",
                "message": "La billetera especificada no existe."
            }
        )

    saldo_actual = await calcular_saldo_real(address, db)

    return {
        "address": wallet["address"],
        "owner_id": str(wallet["user_id"]),
        "balance": saldo_actual,
        "created_at": wallet["created_at"],
    }
