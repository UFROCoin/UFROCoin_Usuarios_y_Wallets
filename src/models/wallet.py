from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.api_response import ApiErrorDetail


class WalletResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str = Field(..., pattern=r"^[a-f0-9]{40}$")
    balance: float
    created_at: datetime


class WalletSuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    data: WalletResponseData
    error: ApiErrorDetail
