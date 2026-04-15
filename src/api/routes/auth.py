from fastapi import APIRouter, Depends, status

from src.core.database import get_database
from src.models.api_response import ApiErrorResponse, ApiSuccessResponse
from src.models.user import UserRegister
from src.services.user_service import register_user_with_wallet


router = APIRouter(tags=["Auth"])


@router.post(
    "/api/users/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description=(
        "Registra un nuevo usuario y crea su wallet asociada con saldo inicial. "
        "El email debe ser unico y la contrasena debe cumplir las reglas minimas de validacion."
    ),
    operation_id="registerUser",
    response_model=ApiSuccessResponse,
    response_description="Usuario registrado correctamente junto con su wallet.",
    responses={
        201: {
            "description": "Usuario registrado correctamente junto con su wallet.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Usuario registrado correctamente.",
                        "data": {
                            "user_id": "67f7d1d2f2a80f2f9f2d1a12",
                            "wallet_address": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                            "initial_balance": 100.0,
                        },
                        "error": {
                            "code": "",
                            "details": "",
                        },
                    }
                }
            },
        },
        400: {
            "model": ApiErrorResponse,
            "description": "Datos invalidos o contraseña debil.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Datos invalidos o contrasena debil.",
                        "data": {},
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "details": "No fue posible generar la wallet o proteger la contrasena.",
                        },
                    }
                }
            },
        },
        409: {
            "model": ApiErrorResponse,
            "description": "El email ya se encuentra registrado.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "El email ya existe.",
                        "data": {},
                        "error": {
                            "code": "EMAIL_ALREADY_EXISTS",
                            "details": "Ya existe un usuario registrado con el email proporcionado.",
                        },
                    }
                }
            },
        },
        500: {
            "model": ApiErrorResponse,
            "description": "Error interno al ejecutar la transaccion de registro.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No fue posible completar el registro.",
                        "data": {},
                        "error": {
                            "code": "TRANSACTION_ERROR",
                            "details": "Fallo en la transaccion de creacion de usuario y wallet.",
                        },
                    }
                }
            },
        },
    },
)
async def register(payload: UserRegister, db=Depends(get_database)):
    return await register_user_with_wallet(payload=payload, db=db)
