import os


class Settings:
    def __init__(self) -> None:
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "ufrocoin")
        self.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
        self.genesis_sender = os.getenv("GENESIS_SENDER", "SYSTEM_REWARD")
        self.initial_wallet_balance = float(os.getenv("INITIAL_WALLET_BALANCE", "100.0"))


settings = Settings()
