import pytest
import httpx
import os

BASE_URL = "http://api:8001"

@pytest.mark.asyncio
async def test_e2e_full_flow():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        import uuid
        unique_email = f"test_{uuid.uuid4()}@e2e.com"
        payload = {
            "nombre": "Test User",
            "email": unique_email,
            "password": "password123"
        }
        
        response = await client.post("/api/users/register", json=payload)
        assert response.status_code == 201
        
        data = response.json()["data"]
        user_id = data["user_id"]
        wallet_address = data["wallet_address"]
            
        assert user_id is not None
        assert wallet_address is not None
        
        response_no_auth = await client.get(f"/api/wallet/{wallet_address}")
        assert response_no_auth.status_code == 401
        
        import jwt
        secret = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")
        token = jwt.encode({"user_id": user_id}, secret, algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}"}
        response_auth = await client.get(f"/api/wallet/{wallet_address}", headers=headers)
        
        assert response_auth.status_code == 200
        wallet_data = response_auth.json()["data"]
        assert wallet_data["address"] == wallet_address
        assert wallet_data["balance"] == 100.0
        
        wrong_token = jwt.encode({"user_id": "fake_id"}, secret, algorithm="HS256")
        headers_wrong = {"Authorization": f"Bearer {wrong_token}"}
        response_wrong_auth = await client.get(f"/api/wallet/{wallet_address}", headers=headers_wrong)
        assert response_wrong_auth.status_code == 401
