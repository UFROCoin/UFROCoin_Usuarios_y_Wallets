from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from src.core.config import settings
from src.core.database import get_database
from src.core.security import get_current_user
from src.models.api_response import (
    ApiErrorResponse,
    ApiSuccessResponse,
    LoginResponseData,
    RegisterUserResponseData,
)
from src.models.user import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponseData,
    ResetPasswordRequest,
    UserRegister,
)
from src.services.token_service import generate_token
from src.services.user_service import (
    authenticate_user,
    get_my_profile,
    register_user_with_wallet,
    request_password_recovery,
    reset_user_password,
)


router = APIRouter(tags=["Auth"])


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not isinstance(authorization, str) or not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token


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


@router.get(
    "/api/users/me",
    status_code=status.HTTP_200_OK,
    summary="Obtener cuenta del usuario autenticado",
    description=(
        "Retorna la informacion personal del usuario autenticado, su saldo actual confirmado "
        "y las ultimas transacciones asociadas a su wallet."
    ),
    operation_id="getAuthenticatedUserProfile",
    response_model=ApiSuccessResponse[MeResponseData],
    responses={
        200: {
            "model": ApiSuccessResponse[MeResponseData],
            "description": "Cuenta consultada correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Cuenta consultada correctamente.",
                        "data": {
                            "nombre": "Ana Perez",
                            "email": "ana.perez@ufrontera.cl",
                            "wallet_address": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                            "balance": 100.0,
                            "history": [
                                {
                                    "id": "683f1a2b3c4d5e6f7a8b9c0d",
                                    "type": "SEND",
                                    "from": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                                    "to": "b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11",
                                    "amount": 25.0,
                                    "timestamp": "2026-06-03T22:45:00+00:00",
                                    "status": "PENDING",
                                    "block_index": None,
                                },
                                {
                                    "id": "683f1a2b3c4d5e6f7a8b9c0e",
                                    "type": "RECEIVE",
                                    "from": "b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11",
                                    "to": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                                    "amount": 10.0,
                                    "timestamp": "2026-06-02T10:00:00+00:00",
                                    "status": "CONFIRMED",
                                    "block_index": 3,
                                },
                            ],
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
            "description": "Token invalido o usuario no autenticado.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No fue posible obtener la cuenta del usuario autenticado.",
                        "data": {},
                        "error": {
                            "code": "UNAUTHORIZED",
                            "details": "Token invalido o usuario no encontrado.",
                        },
                    }
                }
            },
        },
    },
)
async def get_me(
    authorization: str | None = Header(default=None),
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    profile_data = await get_my_profile(
        user_id=current_user["id"],
        db=db,
        access_token=_extract_bearer_token(authorization),
    )
    return ApiSuccessResponse[MeResponseData](
        success=True,
        message="Cuenta consultada correctamente.",
        data=profile_data,
        error={"code": "", "details": ""},
    )

@router.post(
    "/api/users/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperacion de contrasena",
    description=(
        "Solicita recuperacion de contrasena sin revelar si el email existe. "
        "Si existe, genera token JWT con firma dinamica (SECRET_KEY + password_hash actual) "
        "y envia el enlace por correo usando Resend como proveedor transaccional."
    ),
    operation_id="forgotPassword",
    response_model=ApiSuccessResponse[dict[str, Any]],
    responses={
        200: {
            "model": ApiSuccessResponse[dict[str, Any]],
            "description": "Respuesta generica anti-enumeracion.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
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
                            "details": "email debe tener formato valido.",
                        },
                    }
                }
            },
        },
        500: {
            "model": ApiErrorResponse,
            "description": (
                "Error controlado al enviar correo de recuperacion con Resend: "
                "proveedor no configurado, timeout o fallo de entrega."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No fue posible enviar el correo de recuperacion.",
                        "data": {},
                        "error": {
                            "code": "EMAIL_DELIVERY_ERROR",
                            "details": "Error interno al enviar el enlace de recuperacion.",
                        },
                    },
                    "examples": {
                        "delivery_error": {
                            "summary": "Fallo de entrega",
                            "value": {
                                "success": False,
                                "message": "No fue posible enviar el correo de recuperacion.",
                                "data": {},
                                "error": {
                                    "code": "EMAIL_DELIVERY_ERROR",
                                    "details": "Error interno al enviar el enlace de recuperacion.",
                                },
                            },
                        },
                        "timeout": {
                            "summary": "Timeout del proveedor",
                            "value": {
                                "success": False,
                                "message": "No fue posible enviar el correo de recuperacion.",
                                "data": {},
                                "error": {
                                    "code": "EMAIL_DELIVERY_TIMEOUT",
                                    "details": "El proveedor de correo no respondio dentro del tiempo esperado.",
                                },
                            },
                        },
                        "provider_not_configured": {
                            "summary": "Proveedor no configurado",
                            "value": {
                                "success": False,
                                "message": "No fue posible enviar el correo de recuperacion.",
                                "data": {},
                                "error": {
                                    "code": "EMAIL_PROVIDER_NOT_CONFIGURED",
                                    "details": "El proveedor de correo no se encuentra configurado correctamente.",
                                },
                            },
                        },
                    },
                }
            },
        },
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
