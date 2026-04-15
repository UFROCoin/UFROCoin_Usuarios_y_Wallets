# UFROCoin | Módulo A: Usuarios & Wallets 🪙

Este componente es la **puerta de entrada** al ecosistema de UFROCoin. Su función principal es gestionar la identidad de los participantes y proporcionarles las herramientas criptográficas necesarias para interactuar con la blockchain.

### 📝 Descripción del Módulo
El Módulo A se encarga de la capa de identidad y seguridad del proyecto:
* **Gestión de Identidad:** Registro y autenticación de usuarios.
* **Billeteras Digitales (Wallets):** Generación de pares de llaves (pública/privada) para firmar transacciones.
* **Persistencia:** Almacenamiento de perfiles y saldos en MongoDB.
* **Seguridad:** Implementación de hashing SHA-256 para la integridad de los datos.

### 🚀 Estado del Proyecto (Sprint 0)
* [x] Estructura de carpetas inicial.
* [x] Stack tecnológico definido (FastAPI, MongoDB, Vue.js, Docker).
* [x] Pipeline de CI básico configurado.
* [x] Entorno de desarrollo local validado.

### ⚙️ Desarrollo Local con uv
* Al clonar el repositorio por primera vez, instalar dependencias con: `python -m uv sync --all-extras`
* Si cambian `pyproject.toml` o `uv.lock`, volver a ejecutar: `python -m uv sync --all-extras`
* Levantar API en desarrollo: `python -m uv run uvicorn src.main:app --reload --port 8001`
* Documentacion API (Swagger): `http://localhost:8001/docs`
* Ejecutar tests: `python -m uv run pytest -q`

### ▶️ Opciones para correr el proyecto
* Opción 1 (API + MongoDB en Docker): `docker compose up --build`
* Opción 2 (MongoDB en Docker + API local): `docker compose up -d mongo mongo-init` y luego `python -m uv run uvicorn src.main:app --reload --port 8001`

### 🔐 Probar `GET /api/wallet/{address}` (Docker y Local)
1. Registrar un usuario en Swagger con `POST /api/users/register` y guardar `user_id` + `wallet_address`.
2. Generar un JWT con el `user_id` del registro.

**Si corres API en contenedor (Opción 1):**
```bash
docker compose exec api python -c "import os, jwt; print(jwt.encode({'user_id':'<USER_ID>'}, os.getenv('SECRET_KEY'), algorithm='HS256'))"
```

**Si corres API local (Opción 2):**
```bash
python -c "import jwt; print(jwt.encode({'user_id':'<USER_ID>'}, '<SECRET_KEY>', algorithm='HS256'))"
```

Reemplaza `<USER_ID>` por el `user_id` retornado en `POST /api/users/register` y `<SECRET_KEY>` por el valor de `SECRET_KEY` definido en tu `.env`.

3. En Swagger (`/docs`) usar **Authorize** y pegar: `Bearer <TOKEN>`.
4. Ejecutar `GET /api/wallet/{address}` con la `wallet_address` del mismo usuario.

Notas:
- Si no envías token, el endpoint responde `401 Not authenticated`.
- Si el `user_id` del token no coincide con el dueño de la wallet, responde `401 Unauthorized`.

---
*Desarrollado por el Equipo A/1*
