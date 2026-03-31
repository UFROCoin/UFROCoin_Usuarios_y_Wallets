import hashlib
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import ping_db, collection

# Manejador asíncrono avanzado para el ciclo de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar el servidor: validamos que Mongo esté activo
    await ping_db()
    yield
    # Al detener el servidor: Aquí cerraríamos el entorno si requiriéramos

app = FastAPI(title="UFROCoin Backend API", lifespan=lifespan)

# CORS: Permitir comunicación cruzada porque nuestro UI (Vue) estará en otro puerto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Por simplicidad del test. En producción sería ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo Pydantic para validar entradas por POST
class HashRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {
        "status": "ok", 
        "message": "UFROCoin Backend funcionando a la perfección."
    }

@app.post("/hash")
async def generate_hash(payload: HashRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="El texto está vacío o en blanco.")

    # 1. El cálculo matemático - Hashing (SHA-256)
    sha256_hash = hashlib.sha256(payload.text.encode('utf-8')).hexdigest()

    # 2. Preparar el log (documento que será la pista de auditoría en Mongo)
    log_document = {
        "original_text": payload.text,
        "hash": sha256_hash,
        "created_at": datetime.now(timezone.utc)
    }

    # 3. Persistiendo el log asíncronamente
    try:
        result = await collection.insert_one(log_document)
        
        # Devolvemos la confirmación de Frontend
        return {
            "message": "Hash guardado como log en la Blockchain (Mongo)",
            "hash_generated": sha256_hash,
            "db_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando en MongoDB: {e}")
