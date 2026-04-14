from fastapi import APIRouter, Depends, HTTPException, status
from src.core.database import get_database
from src.core.security import get_current_user
from src.services.wallet_service import obtener_detalle_wallet

router = APIRouter(tags=["Wallet"])

@router.get("/api/wallet/{address}")
async def consultar_wallet(
    address: str, 
    db = Depends(get_database), 
    current_user = Depends(get_current_user)
):

    wallet_data = await obtener_detalle_wallet(address, db)
    
    if wallet_data["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error", 
                "code": "UNAUTHORIZED", 
                "message": "No tienes permisos para consultar esta billetera."
            }
        )

    return {
        "status": "ok",
        "data": wallet_data
    }