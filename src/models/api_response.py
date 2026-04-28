from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        default="",
        description="Codigo de error interno de la API.",
    )
    details: str = Field(
        ...,
        description="Detalle tecnico o funcional del error.",
    )


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Datos invalidos o contrasena debil.",
                "data": {},
                "error": {
                    "code": "VALIDATION_ERROR",
                    "details": "No fue posible generar la wallet o proteger la contrasena.",
                },
            }
        },
    )

    success: bool = Field(default=False, description="Indica si la operacion fue exitosa.")
    message: str = Field(
        ...,
        description="Mensaje legible para el cliente.",
        examples=["Datos invalidos o contrasena debil."],
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Carga util de respuesta. Vacia cuando ocurre error.",
    )
    error: ApiErrorDetail


class RegisterUserResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(
        ...,
        description="Identificador unico del usuario creado.",
        examples=["67f7d1d2f2a80f2f9f2d1a12"],
    )
    wallet_address: str = Field(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion de wallet asociada al usuario.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    )
    initial_balance: float = Field(
        ...,
        ge=0,
        description="Saldo inicial asignado a la wallet.",
        examples=[100.0],
    )


class LoginResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(..., description="Token JWT de acceso.")
    token_type: str = Field(default="Bearer", description="Tipo de token.")
    expires_in: int = Field(..., description="Tiempo de expiracion en segundos.")


class ApiSuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operacion exitosa.",
                "data": {},
                "error": {
                    "code": "",
                    "details": "",
                },
            }
        },
    )

    success: bool = Field(default=True, description="Indica si la operacion fue exitosa.")
    message: str = Field(
        ...,
        description="Mensaje legible para el cliente.",
    )
    data: T
    error: ApiErrorDetail = Field(
        default_factory=lambda: ApiErrorDetail(code="", details="")
    )
