from fastapi import APIRouter, Depends, status

from src.core.database import get_database
from src.models.api_response import ApiErrorResponse, ApiSuccessResponse
from src.models.user import UserRegister
from src.services.user_service import register_user_with_wallet


router = APIRouter(tags=["Auth"])


@router.post(
    "/api/users/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiSuccessResponse,
    responses={
        400: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def register(payload: UserRegister, db=Depends(get_database)):
    return await register_user_with_wallet(payload=payload, db=db)
