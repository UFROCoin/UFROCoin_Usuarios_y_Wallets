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
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.resend_from_email = os.getenv("RESEND_FROM_EMAIL","UFROCoin <no-reply@ufrocoin.email>")
        self.resend_reset_subject = os.getenv("RESEND_RESET_SUBJECT","Recuperacion de contrasena UFROCoin")
        self.resend_timeout_seconds = float(os.getenv("RESEND_TIMEOUT_SECONDS", "10"))
        self.password_reset_base_url = os.getenv("PASSWORD_RESET_BASE_URL","http://localhost:5173/reset-password")
        self.blockchain_transactions_api_url = os.getenv("BLOCKCHAIN_TRANSACTIONS_API_URL", "").rstrip("/")
        self.blockchain_transactions_timeout_seconds = float(
            os.getenv("BLOCKCHAIN_TRANSACTIONS_TIMEOUT_SECONDS", "5")
        )
        self.wallet_internal_token = os.getenv("WALLET_INTERNAL_TOKEN", "")


settings = Settings()
