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
