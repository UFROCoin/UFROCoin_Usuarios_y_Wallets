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
