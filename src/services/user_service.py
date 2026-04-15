from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError

from src.core.config import settings
from src.models.api_response import ApiSuccessResponse, RegisterUserResponseData
from src.models.user import UserRegister
from src.utils.security import hash_contrasena
from src.utils.wallet import generar_direccion_wallet


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
