from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from src.core.config import settings
from src.core.database import get_database
from src.models.api_response import (
    ApiErrorResponse,
    ApiSuccessResponse,
    LoginResponseData,
    RegisterUserResponseData,
)
from src.models.user import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    UserRegister,
)
from src.services.token_service import generate_token
from src.services.user_service import (
    authenticate_user,
    register_user_with_wallet,
    request_password_recovery,
    reset_user_password,
)


router = APIRouter(tags=["Auth"])


@router.post(
    "/api/users/login",
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuario",
    description="Autentica al usuario con email y contrasena, retornando un token JWT.",
    operation_id="loginUser",
    response_model=ApiSuccessResponse[LoginResponseData],
    responses={
        200: {"model": ApiSuccessResponse[LoginResponseData]},
        401: {"model": ApiErrorResponse},
    }
)
async def login(payload: LoginRequest, db=Depends(get_database)):
    user = await authenticate_user(payload.email, payload.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Credenciales invalidas.",
                "code": "INVALID_CREDENTIALS",
                "details": "El email o la contrasena son incorrectos."
            }
        )
    
    token = generate_token(str(user["_id"]), user["wallet_address"])
    
    return ApiSuccessResponse[LoginResponseData](
        message="Login exitoso.",
        data=LoginResponseData(
            access_token=token,
            token_type="Bearer",
            expires_in=settings.jwt_expire_hours * 3600
        )
    )


@router.post(
    "/api/users/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description=(
        "Registra un nuevo usuario y crea su wallet asociada con saldo inicial. "
        "El email debe ser unico y la contrasena debe cumplir las reglas minimas de validacion."
    ),
    operation_id="registerUser",
    response_model=ApiSuccessResponse[RegisterUserResponseData],
    response_description="Usuario registrado correctamente junto con su wallet.",
    responses={
        201: {
            "model": ApiSuccessResponse[RegisterUserResponseData],
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

@router.post(
    "/api/users/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperacion de contrasena",
    description=(
        "Solicita recuperacion de contrasena sin revelar si el email existe. "
        "Si existe, genera token JWT con firma dinamica (SECRET_KEY + password_hash actual) "
        "y notifica el enlace por el servicio de notificaciones."
    ),
    operation_id="forgotPassword",
    response_model=ApiSuccessResponse[dict[str, Any]],
    responses={
        200: {
            "description": "Respuesta generica anti-enumeracion.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
                        "data": {},
                        "error": None,
                    }
                }
            },
        }
    },
)
async def forgot_password(payload: ForgotPasswordRequest, db=Depends(get_database)):
    result = await request_password_recovery(email=payload.email, db=db)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)


@router.post(
    "/api/users/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Restablecer contrasena",
    description=(
        "Valida token JWT con firma dinamica (SECRET_KEY + hash actual). "
        "Si es valido, actualiza la contrasena hasheada en MongoDB."
    ),
    operation_id="resetPassword",
    response_model=ApiSuccessResponse[dict],
    responses={
        200: {
            "model": ApiSuccessResponse[dict],
            "description": "Contrasena restablecida correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Contrasena restablecida correctamente.",
                        "data": {},
                        "error": {"code": "", "details": ""},
                    }
                }
            },
        },
        400: {
            "model": ApiErrorResponse,
            "description": "Error de validacion del body.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Datos invalidos o contrasena debil.",
                        "data": {},
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "details": "new_password es obligatorio y debe tener al menos 8 caracteres.",
                        },
                    }
                }
            },
        },
        401: {
            "model": ApiErrorResponse,
            "description": "Token invalido, expirado o firma no coincide.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Token de recuperacion invalido o expirado.",
                        "data": {},
                        "error": {
                            "code": "INVALID_OR_EXPIRED_TOKEN",
                            "details": "El token no es valido, expiro o ya fue invalidado por cambio de contrasena.",
                        },
                    }
                }
            },
        },
        500: {
            "model": ApiErrorResponse,
            "description": "Error interno o de base de datos.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No fue posible restablecer la contrasena.",
                        "data": {},
                        "error": {
                            "code": "DATABASE_ERROR",
                            "details": "Error interno al actualizar la contrasena del usuario en la base de datos.",
                        },
                    }
                }
            },
        },
    },
)
async def reset_password(payload: ResetPasswordRequest, db=Depends(get_database)):
    return await reset_user_password(
        token=payload.token,
        new_password=payload.new_password,
        db=db,
    )
