from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings


client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]


def get_database():
    return db
