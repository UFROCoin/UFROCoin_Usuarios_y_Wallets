from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError

from src.models.api_response import ApiSuccessResponse, RegisterUserResponseData
from src.models.user import UserRegister
from src.utils.dependencies import generate_wallet_address_mock, hash_password_mock


async def register_user_with_wallet(payload: UserRegister, db):
    users_collection = db["users"]
    wallets_collection = db["wallets"]

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

    wallet_address = generate_wallet_address_mock()
    password_hash = hash_password_mock(payload.password)
    now = datetime.now(timezone.utc)

    user_document = {
        "nombre": payload.nombre,
        "email": payload.email,
        "password_hash": password_hash,
        "wallet_address": wallet_address,
        "created_at": now,
    }

    wallet_document = {
        "address": wallet_address,
        "balance": 0,
        "created_at": now,
    }

    try:
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                user_result = await users_collection.insert_one(user_document, session=session)

                wallet_document["user_id"] = user_result.inserted_id
                await wallets_collection.insert_one(wallet_document, session=session)

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
        initial_balance=0,
    )
    return ApiSuccessResponse(
        success=True,
        message="Usuario registrado correctamente.",
        data=response_data,
        error={"code": "", "details": ""},
    ).model_dump()
