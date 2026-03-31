import os
from motor.motor_asyncio import AsyncIOMotorClient

# Obtenemos la variable de entorno MONGO_URI inyectada desde docker-compose.yml
# Si por alguna razón no existe, tomaremos localhost para pruebas nativas
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:secretpassword@localhost:27017/?authSource=admin")

# Cliente asíncrono para comunicarse no bloqueante con la base de datos
client = AsyncIOMotorClient(MONGO_URI)

# Instancia a la base de datos "ufrocoin_db" (se creará al insertar el primer dato)
db = client.ufrocoin_db

# Referencia a la colección (similar a la tabla en SQL) 
collection = db.hash_logs

async def ping_db():
    try:
        await client.admin.command('ping')
        print("¡Ping a MongoDB exitoso! Base de datos lista.")
    except Exception as e:
        print(f"Error en la conexión a MongoDB: {e}")
