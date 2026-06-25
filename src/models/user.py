from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre completo del usuario.",
        examples=["Ana Perez"],
    )
    email: EmailStr = Field(
        ...,
        description="Correo electronico del usuario. Debe ser unico.",
        examples=["ana.perez@ufrontera.cl"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña de acceso (minimo 8 caracteres).",
        examples=["Segura123!"],
    )


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Email del usuario.")
    password: str = Field(..., description="Contraseña del usuario.")

class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(
        ...,
        description="Correo electronico para solicitar recuperacion de contrasena.",
        examples=["ana.perez@ufrontera.cl"],
    )

class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., description="JWT de recuperacion.")
    new_password: str = Field(
        ...,
        min_length=8,
        description="Nueva contrasena del usuario.",
        examples=["Segura123!"],
    )


class TransactionHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(..., description="Identificador de la transaccion.")
    type: Literal["SEND", "RECEIVE", "MINING_REWARD", "GENESIS"] = Field(
        ...,
        description="Tipo de movimiento visto desde la wallet del usuario.",
    )
    from_address: str = Field(..., alias="from", description="Wallet de origen.")
    to_address: str = Field(..., alias="to", description="Wallet de destino.")
    amount: float = Field(..., description="Monto de la transaccion.")
    timestamp: str = Field(
        ...,
        description="Fecha-hora ISO 8601 de la transaccion.",
        json_schema_extra={"format": "date-time"},
    )
    status: Literal["PENDING", "CONFIRMED"] = Field(
        ...,
        description="Estado de la transaccion.",
    )
    block_index: int | None = Field(
        default=None,
        ge=0,
        description="Indice del bloque si la transaccion esta confirmada.",
    )


class MeResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre completo del usuario autenticado.",
        examples=["Ana Perez"],
    )
    email: EmailStr = Field(
        ...,
        description="Correo electronico del usuario autenticado.",
        examples=["ana.perez@ufrontera.cl"],
    )
    wallet_address: str = Field(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion de wallet asociada al usuario.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    )
    balance: float = Field(
        ...,
        description="Saldo actual confirmado de la wallet del usuario.",
        examples=[100.0],
    )
    history: list[TransactionHistoryItem] = Field(
        default_factory=list,
        description="Ultimas transacciones asociadas a la wallet.",
        examples=[
            [
                {
                    "id": "683f1a2b3c4d5e6f7a8b9c0d",
                    "type": "SEND",
                    "from": "a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10",
                    "to": "b3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f11",
                    "amount": 25.0,
                    "timestamp": "2026-06-03T22:45:00+00:00",
                    "status": "PENDING",
                    "block_index": None,
                }
            ]
        ],
    )
