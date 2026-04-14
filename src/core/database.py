from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings


client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
db = client[settings.mongodb_db_name]


def get_database():
    return db
