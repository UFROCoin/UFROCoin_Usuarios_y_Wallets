from datetime import datetime, timedelta, timezone

import jwt

from src.core.config import settings


def generate_token(user_id: str, wallet_address: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def generate_password_recovery_token(user_email: str, password_hash: str) -> str:
    """
    Genera un JWT de recuperacion firmado con clave dinamica:
    SECRET_KEY + password_hash_actual.
    Importante:
    - password_hash NO se incluye en el payload.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "user_email": user_email,
        "exp": expires_at,
    }
    dynamic_secret = settings.secret_key + password_hash
    return jwt.encode(payload, dynamic_secret, algorithm=settings.jwt_algorithm)