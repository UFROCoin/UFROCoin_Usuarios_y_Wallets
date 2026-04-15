from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status

async def calcular_saldo_real(wallet_address: str, db: AsyncIOMotorDatabase) -> float:
  
    pipeline_ingresos = [
        {"$match": {"hacia": wallet_address, "estado": "CONFIRMED"}},
        {"$group": {"_id": None, "total": {"$sum": "$monto"}}}
    ]
    
    pipeline_egresos = [
        {"$match": {"desde": wallet_address, "estado": "CONFIRMED"}},
        {"$group": {"_id": None, "total": {"$sum": "$monto"}}}
    ]

    ingresos_res = await db["transacciones"].aggregate(pipeline_ingresos).to_list(1)
    egresos_res = await db["transacciones"].aggregate(pipeline_egresos).to_list(1)

    total_ingresos = ingresos_res[0]["total"] if ingresos_res else 0.0
    total_egresos = egresos_res[0]["total"] if egresos_res else 0.0

    return float(total_ingresos - total_egresos)

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
        "balance": saldo_actual
    }