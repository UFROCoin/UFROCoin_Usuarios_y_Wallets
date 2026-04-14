"""
Módulo de generación de direcciones de wallet.

Genera direcciones únicas usando SHA-256(email + timestamp),
truncadas a 40 caracteres hexadecimales en minúsculas.
"""

import hashlib


def generar_direccion_wallet(email: str, timestamp_registro: str) -> dict:
    """
    Genera una dirección de wallet única a partir del email y timestamp.

    Parameters
    ----------
    email : str
        Email del usuario registrado.
    timestamp_registro : str
        Timestamp del momento de registro en formato ISO 8601.

    Returns
    -------
    dict
        ``{"status": "ok", "data": {"direccion": "<40 hex chars>"}}``
        o ``{"status": "error", "code": "...", "message": "..."}``
    """
    if not email or not email.strip():
        return {
            "status": "error",
            "code": "EMPTY_EMAIL",
            "message": "El email no puede estar vacío."
        }

    if not timestamp_registro or not timestamp_registro.strip():
        return {
            "status": "error",
            "code": "EMPTY_TIMESTAMP",
            "message": "El timestamp de registro no puede estar vacío."
        }

    datos = f"{email}{timestamp_registro}"
    hash_completo = hashlib.sha256(datos.encode("utf-8")).hexdigest()
    direccion = hash_completo[:40]

    return {
        "status": "ok",
        "data": {
            "direccion": direccion
        }
    }
