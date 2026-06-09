from typing import Any

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
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historial de transacciones recientes. En este sprint se retorna vacio.",
        examples=[[]],
    )
