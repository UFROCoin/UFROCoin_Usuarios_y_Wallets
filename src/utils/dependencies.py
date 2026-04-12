import hashlib
import uuid


def hash_password_mock(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_wallet_address_mock() -> str:
    seed = uuid.uuid4().hex
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()
