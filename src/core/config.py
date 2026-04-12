import os


class Settings:
    def __init__(self) -> None:
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "ufrocoin")
        self.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")


settings = Settings()
