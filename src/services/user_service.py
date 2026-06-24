from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
import jwt
from bson import ObjectId
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError
from src.core.config import settings
from src.models.api_response import (
    ApiSuccessResponse,
    RegisterUserResponseData,
)
from src.models.user import MeResponseData, UserRegister
from src.services.notification_service import (
    INotificationService,
    NotificationDeliveryError,
    NotificationProviderNotConfiguredError,
    NotificationTimeoutError,
    get_default_notification_service,
)
from src.services.token_service import generate_password_recovery_token
from src.services.wallet_service import calcular_saldo_real
from src.utils.security import hash_contrasena, verificar_contrasena
from src.utils.wallet import generar_direccion_wallet


def _invalid_recovery_token_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "Token de recuperacion invalido o expirado.",
            "code": "INVALID_OR_EXPIRED_TOKEN",
            "details": "El token no es valido, expiro o ya fue invalidado por cambio de contrasena.",
        },
    )


async def authenticate_user(email: str, password: str, db):
    """
    Valida las credenciales de un usuario.
    Retorna el documento del usuario si es valido, False de lo contrario.
    """
    users_collection = db["users"]
    user = await users_collection.find_one({"email": email})
    
    if not user:
        return False
        
    verification = verificar_contrasena(password, user["password_hash"])
    if verification["status"] == "ok" and verification["data"]["valid"]:
        return user
        
    return False


async def get_my_profile(user_id: str, db: AsyncIOMotorDatabase) -> MeResponseData:
    users_collection = db["users"]

    user = None
    if ObjectId.is_valid(user_id):
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        user = await users_collection.find_one({"_id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No fue posible obtener la cuenta del usuario autenticado.",
                "code": "UNAUTHORIZED",
                "details": "Token invalido o usuario no encontrado.",
            },
        )

    wallet_address = user["wallet_address"]
    balance = await calcular_saldo_real(wallet_address, db)

    return MeResponseData(
        nombre=user["nombre"],
        email=user["email"],
        wallet_address=wallet_address,
        balance=balance,
        history=[],
    )

async def request_password_recovery(
    email: str,
    db: AsyncIOMotorDatabase,
    notification_service: INotificationService | None = None,
) -> dict[str, Any]:
    """
    Caso de uso US-13:
    - Siempre responde HTTP 200 con mensaje generico (anti enumeracion).
    - Si el usuario existe, genera token JWT con firma dinamica
      SECRET_KEY + password_hash_actual.
    - El token nunca se retorna en JSON; se notifica por el servicio inyectado.
    """
    users_collection = db["users"]
    user = await users_collection.find_one({"email": email})
    if not user:
        return _forgot_password_response()
    password_hash = user.get("password_hash")
    user_id = user.get("_id")
    if not password_hash or user_id is None:
        return _forgot_password_response()
    token = generate_password_recovery_token(str(user_id), password_hash)
    query = urlencode({"token": token})
    reset_link = f"{settings.password_reset_base_url}?{query}"
    service = notification_service or get_default_notification_service()
    try:
        await service.send_password_reset_link(email=email, reset_link=reset_link)
    except NotificationTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "No fue posible enviar el correo de recuperacion.",
                "code": "EMAIL_DELIVERY_TIMEOUT",
                "details": "El proveedor de correo no respondio dentro del tiempo esperado.",
            },
        ) from exc
    except NotificationProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "No fue posible enviar el correo de recuperacion.",
                "code": "EMAIL_PROVIDER_NOT_CONFIGURED",
                "details": "El proveedor de correo no se encuentra configurado correctamente.",
            },
        ) from exc
    except NotificationDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "No fue posible enviar el correo de recuperacion.",
                "code": "EMAIL_DELIVERY_ERROR",
                "details": "Error interno al enviar el enlace de recuperacion.",
            },
        ) from exc
    return _forgot_password_response()

async def register_user_with_wallet(payload: UserRegister, db):
    users_collection = db["users"]
    wallets_collection = db["wallets"]
    transacciones_collection = db["transacciones"] 

    existing_user = await users_collection.find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "El email ya existe.",
                "code": "EMAIL_ALREADY_EXISTS",
                "details": "Ya existe un usuario registrado con el email proporcionado.",
            },
        )

    now = datetime.now(timezone.utc)
    wallet_address_result = generar_direccion_wallet(
        email=payload.email,
        timestamp_registro=now.isoformat(),
    )
    password_hash_result = hash_contrasena(payload.password)

    if wallet_address_result["status"] != "ok" or password_hash_result["status"] != "ok":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Datos invalidos o contrasena debil.",
                "code": "VALIDATION_ERROR",
                "details": "No fue posible generar la wallet o proteger la contrasena.",
            },
        )

    wallet_address = wallet_address_result["data"]["direccion"]
    password_hash = password_hash_result["data"]["hash"]

    user_document = {
        "nombre": payload.nombre,
        "email": payload.email,
        "password_hash": password_hash,
        "wallet_address": wallet_address,
        "created_at": now,
    }

    wallet_document = {
        "address": wallet_address,
        "balance": settings.initial_wallet_balance,
        "created_at": now,
    }
    
   
    transaccion_genesis = {
        "tipo": "GENESIS",
        "desde": settings.genesis_sender,
        "hacia": wallet_address,
        "monto": settings.initial_wallet_balance,
        "estado": "CONFIRMED",
        "timestamp": now,
    }

    try:
        async with await db.client.start_session() as session:
            async with session.start_transaction():
             
                user_result = await users_collection.insert_one(user_document, session=session)

              
                wallet_document["user_id"] = user_result.inserted_id
                await wallets_collection.insert_one(wallet_document, session=session)
                
              
                await transacciones_collection.insert_one(transaccion_genesis, session=session)

    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "No fue posible completar el registro.",
                "code": "TRANSACTION_ERROR",
                "details": "Fallo en la transaccion de creacion de usuario y wallet.",
            },
        ) from exc

    response_data = RegisterUserResponseData(
        user_id=str(user_result.inserted_id),
        wallet_address=wallet_address,
        initial_balance=settings.initial_wallet_balance,
    )
    return ApiSuccessResponse(
        success=True,
        message="Usuario registrado correctamente.",
        data=response_data,
        error={"code": "", "details": ""},
    ).model_dump()

def _forgot_password_response() -> dict[str, Any]:
    return {
        "success": True,
        "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
        "data": {},
        "error": {"code": "", "details": ""},
    }

async def reset_user_password(token: str, new_password: str, db):
    users_collection = db["users"]

    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        user_id = unverified_payload.get("user_id")
    except InvalidTokenError as exc:
        raise _invalid_recovery_token_error() from exc

    if not user_id:
        raise _invalid_recovery_token_error()

    user = None
    if ObjectId.is_valid(user_id):
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        user = await users_collection.find_one({"_id": user_id})

    if not user or not user.get("password_hash"):
        raise _invalid_recovery_token_error()

    try:
        verified_payload = jwt.decode(
            token,
            settings.secret_key + user["password_hash"],
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise _invalid_recovery_token_error() from exc

    if verified_payload.get("user_id") != user_id:
        raise _invalid_recovery_token_error()

    password_hash_result = hash_contrasena(new_password)
    if password_hash_result["status"] != "ok":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Datos invalidos o contrasena debil.",
                "code": "VALIDATION_ERROR",
                "details": "new_password es obligatorio y debe tener al menos 8 caracteres.",
            },
        )

    try:
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"password_hash": password_hash_result["data"]["hash"]}},
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "No fue posible restablecer la contrasena.",
                "code": "DATABASE_ERROR",
                "details": "Error interno al actualizar la contrasena del usuario en la base de datos.",
            },
        ) from exc

    return ApiSuccessResponse(
        success=True,
        message="Contrasena restablecida correctamente.",
        data={},
        error={"code": "", "details": ""},
    ).model_dump()

