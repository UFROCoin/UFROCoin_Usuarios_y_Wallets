from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
   
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("user_id") 
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "code": "UNAUTHORIZED", "message": "Token inválido"}
            )
        return {"id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "code": "UNAUTHORIZED", "message": "Sesión inválida"}
        )