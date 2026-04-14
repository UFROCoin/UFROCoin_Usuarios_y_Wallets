"""
Módulo de seguridad - Hashing SHA-256 con salt.

Provee funciones para hashear y verificar contraseñas de forma segura.
Utiliza SHA-256 con un salt aleatorio de 16 bytes.
El formato de almacenamiento es ``salt:hash`` (nunca texto plano).
"""

import hashlib
import secrets


def hash_contrasena(contrasena: str) -> dict:
    """
    Genera un hash seguro de la contraseña usando SHA-256 + salt aleatorio.

    Parameters
    ----------
    contrasena : str
        Contraseña en texto plano del usuario.

    Returns
    -------
    dict
        ``{"status": "ok", "data": {"hash": "<salt>:<sha256>"}}``
        o ``{"status": "error", "code": "...", "message": "..."}``
    """
    if not contrasena or not contrasena.strip():
        return {
            "status": "error",
            "code": "EMPTY_PASSWORD",
            "message": "La contraseña no puede estar vacía."
        }

    salt = secrets.token_hex(16)
    hash_pwd = hashlib.sha256(f"{salt}:{contrasena}".encode("utf-8")).hexdigest()
    hash_almacenado = f"{salt}:{hash_pwd}"

    return {
        "status": "ok",
        "data": {
            "hash": hash_almacenado
        }
    }


def verificar_contrasena(contrasena: str, hash_almacenado: str) -> dict:
    """
    Verifica si una contraseña coincide con el hash almacenado.

    Parameters
    ----------
    contrasena : str
        Contraseña ingresada por el usuario.
    hash_almacenado : str
        String con formato ``salt:hash`` guardado en la base de datos.

    Returns
    -------
    dict
        ``{"status": "ok", "data": {"valid": true|false}}``
        o ``{"status": "error", "code": "...", "message": "..."}``
    """
    if not contrasena or not contrasena.strip():
        return {
            "status": "error",
            "code": "EMPTY_PASSWORD",
            "message": "La contraseña no puede estar vacía."
        }

    if not hash_almacenado or ":" not in hash_almacenado:
        return {
            "status": "error",
            "code": "INVALID_HASH",
            "message": "El formato del hash almacenado es inválido."
        }

    salt, hash_esperado = hash_almacenado.split(":", 1)
    hash_calculado = hashlib.sha256(f"{salt}:{contrasena}".encode("utf-8")).hexdigest()
    es_valida = hash_calculado == hash_esperado

    return {
        "status": "ok",
        "data": {
            "valid": es_valida
        }
    }
