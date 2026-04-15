from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.core.database import get_database
from src.core.security import get_current_user
from src.models.api_response import ApiErrorResponse
from src.models.wallet import WalletResponseData, WalletSuccessResponse
from src.services.wallet_service import obtener_detalle_wallet

router = APIRouter(tags=["Wallet"])

@router.get(
    "/api/wallet/{address}",
    response_model=WalletSuccessResponse,
    responses={
        401: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def consultar_wallet(
    address: str = Path(..., pattern=r"^[a-f0-9]{40}$"),
    db = Depends(get_database), 
    current_user = Depends(get_current_user)
)-> WalletSuccessResponse:

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

    wallet_response_data = WalletResponseData(
        address=wallet_data["address"],
        balance=wallet_data["balance"],
        created_at=wallet_data["created_at"],
    )
    return WalletSuccessResponse(
        success=True,
        message="Wallet consultada correctamente.",
        data=wallet_response_data,
        error={"code": "", "details": ""},
    )
