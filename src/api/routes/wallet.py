from fastapi import APIRouter, Depends, Header, HTTPException, Path, status

from src.core.database import get_database
from src.core.security import get_current_user, verify_internal_wallet_token
from src.models.api_response import ApiErrorResponse, ApiSuccessResponse
from src.models.wallet import WalletExistsResponseData, WalletResponseData
from src.services.wallet_service import obtener_detalle_wallet, wallet_exists

router = APIRouter(tags=["Wallet"])


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not isinstance(authorization, str) or not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token

@router.get(
    "/api/wallet/{address}",
    response_model=ApiSuccessResponse[WalletResponseData],
    summary="Consultar wallet por direccion",
    description=(
        "Obtiene el detalle de una wallet por su direccion. "
        "Requiere token Bearer valido y solo permite consultar wallets del usuario autenticado."
    ),
    operation_id="getWalletByAddress",
    response_description="Wallet consultada correctamente.",
    responses={
        200: {
            "model": ApiSuccessResponse[WalletResponseData],
            "description": "Wallet consultada correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Wallet consultada correctamente.",
                        "data": {
                            "address": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                            "balance": 100.0,
                            "created_at": "2026-03-30T12:00:00Z",
                        },
                        "error": {
                            "code": "",
                            "details": "",
                        },
                    }
                }
            },
        },
        401: {
            "model": ApiErrorResponse,
            "description": "Token invalido o usuario sin permisos sobre la wallet.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No tienes permisos para consultar esta billetera.",
                        "data": {},
                        "error": {
                            "code": "UNAUTHORIZED",
                            "details": "Token invalido o usuario sin permisos sobre la wallet.",
                        },
                    }
                }
            },
        },
        404: {
            "model": ApiErrorResponse,
            "description": "La wallet solicitada no existe.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "La billetera especificada no existe.",
                        "data": {},
                        "error": {
                            "code": "WALLET_NOT_FOUND",
                            "details": "La wallet solicitada no existe.",
                        },
                    }
                }
            },
        },
    },
)
async def consultar_wallet(
    address: str = Path(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion de wallet en formato hexadecimal de 40 caracteres.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    ),
    authorization: str | None = Header(default=None),
    db = Depends(get_database), 
    current_user = Depends(get_current_user)
)-> ApiSuccessResponse[WalletResponseData]:

    wallet_data = await obtener_detalle_wallet(
        address,
        db,
        access_token=_extract_bearer_token(authorization),
    )
    
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
    return ApiSuccessResponse[WalletResponseData](
        success=True,
        message="Wallet consultada correctamente.",
        data=wallet_response_data,
        error={"code": "", "details": ""}
    )


@router.get(
    "/api/internal/wallet/{address}/exists",
    response_model=ApiSuccessResponse[WalletExistsResponseData],
    summary="Verificar existencia de wallet para integraciones internas",
    description=(
        "Endpoint interno para que otros modulos validen si una wallet existe. "
        "No retorna datos sensibles del usuario y requiere token de servicio."
    ),
    operation_id="internalWalletExists",
    responses={
        200: {"model": ApiSuccessResponse[WalletExistsResponseData]},
        401: {"model": ApiErrorResponse},
    },
)
async def consultar_existencia_wallet_interna(
    address: str = Path(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion de wallet en formato hexadecimal de 40 caracteres.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    ),
    db=Depends(get_database),
    _=Depends(verify_internal_wallet_token),
) -> ApiSuccessResponse[WalletExistsResponseData]:
    exists = await wallet_exists(address, db)

    return ApiSuccessResponse[WalletExistsResponseData](
        success=True,
        message="Existencia de wallet consultada correctamente.",
        data=WalletExistsResponseData(exists=exists, address=address),
        error={"code": "", "details": ""},
    )
