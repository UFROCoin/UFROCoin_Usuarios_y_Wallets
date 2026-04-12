from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = ""
    details: str


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = False
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: ApiErrorDetail


class RegisterUserResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    wallet_address: str = Field(..., pattern=r"^[a-f0-9]{40}$")
    initial_balance: float = Field(..., ge=0)


class ApiSuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    data: RegisterUserResponseData
    error: ApiErrorDetail
