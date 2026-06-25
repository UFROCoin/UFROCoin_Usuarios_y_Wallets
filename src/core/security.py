import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from src.core.config import settings

security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingrese el token JWT con el formato: Bearer <token>",
)
internal_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "code": "UNAUTHORIZED", "message": "Token invalido"},
            )

        return {"id": user_id}
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "code": "UNAUTHORIZED", "message": "Sesion invalida"},
        )


async def verify_internal_wallet_token(
    credentials: HTTPAuthorizationCredentials | None = Security(internal_security),
) -> None:
    if not credentials or credentials.credentials != settings.wallet_internal_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token interno invalido.",
                "code": "UNAUTHORIZED",
                "details": "Falta o no coincide el token de servicio entre modulos.",
            },
        )
