from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings


client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]


def get_database():
    return db


async def create_indexes():
    """
    Crea los indices necesarios en la base de datos al iniciar la aplicacion.
    Garantiza la unicidad de emails y direcciones de wallet.
    """
    await db["usuarios"].create_index("email", unique=True)
    await db["wallets"].create_index("address", unique=True)
