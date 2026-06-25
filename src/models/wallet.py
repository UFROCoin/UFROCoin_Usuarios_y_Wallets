from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str = Field(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion publica de la wallet.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    )
    balance: float = Field(
        ...,
        description="Saldo actual confirmado de la wallet.",
        examples=[100.0],
    )
    created_at: datetime = Field(
        ...,
        description="Fecha de creacion de la wallet en formato ISO 8601.",
        examples=["2026-03-30T12:00:00Z"],
    )


class WalletExistsResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exists: bool = Field(
        ...,
        description="Indica si la wallet existe en Usuarios y Wallets.",
        examples=[True],
    )
    address: str = Field(
        ...,
        pattern=r"^[a-f0-9]{40}$",
        description="Direccion publica consultada.",
        examples=["a3f5e2c9d1b84f76a0c91d4e7b3f8a2d5c6e9f10"],
    )
