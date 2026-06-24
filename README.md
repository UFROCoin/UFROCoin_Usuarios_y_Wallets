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

### 🎯 Funcionalidades Implementadas (Sprint 1)
* [x] **US-01/02:** Registro de usuario con Hashing SHA-256 + Salt.
* [x] **US-03/04:** Generación de dirección de Wallet y vinculación automática.
* [x] **US-05/06:** Autenticación de usuario y entrega de Token JWT en `/api/users/login`.
* [x] **US-07:** Emisión de Transacción Génesis (Welcome Reward).
* [x] **US-08:** Endpoint de consulta de Wallet con cálculo de saldo real en `/api/wallet/{address}`.
* [x] **TECH-04/05:** Refactor de respuestas genéricas y alineación de contrato Apidog.

### 📦 Justificación de Nuevas Dependencias
* **`httpx`**: Se agregó esta dependencia exclusivamente para habilitar las pruebas de integración asíncronas (`TestClient` de FastAPI requiere `httpx` para los endpoints asíncronos en los tests del pipeline de CI/CD).

### ⚙️ Desarrollo Local con uv
* Al clonar el repositorio por primera vez, instalar dependencias con: `python -m uv sync --all-extras`
* Si cambian `pyproject.toml` o `uv.lock`, volver a ejecutar: `python -m uv sync --all-extras`
* Levantar API en desarrollo: `python -m uv run uvicorn src.main:app --reload --port 8001`
* Documentacion API (Swagger): `http://localhost:8001/docs`
* Ejecutar tests: `python -m uv run pytest -q`

### 🧪 Pruebas agregadas y cobertura
La suite combina pruebas black-box y white-box para buscar defectos, no solo confirmar casos felices.

* **Black-box / use case coverage:** `tests/test_password_reset.py` cubre los flujos US-13/US-14 de recuperacion y reset de contrasena, incluyendo usuario inexistente, token invalido, token expirado, token de un solo uso y errores controlados del proveedor Resend.
* **Black-box / equivalence partitioning:** `tests/test_authentication_and_security.py` valida entradas validas e invalidas para login, emails, contrasenas, campos extra, hashes y generacion de wallet.
* **Black-box / boundary value analysis:** se prueban fronteras de contrasena de 7 y 8 caracteres y formato de wallet de 40 caracteres hexadecimales.
* **White-box / branch coverage:** `tests/test_wallet_service.py` fuerza ramas de saldo con ingresos, egresos, transacciones pendientes, saldo cero, saldo negativo, wallet inexistente y usuario no autorizado.
* **White-box / branch coverage:** `tests/test_authentication_and_security.py` fuerza ramas de JWT valido, token sin `user_id`, firma invalida y token expirado en `get_current_user()`.
* **White-box / branch coverage:** `tests/test_user_registration.py` cubre registro exitoso, email duplicado, password invalida y rollback transaccional cuando falla la insercion de wallet.
* **Contract/config coverage:** `tests/test_auth_openapi.py` y `tests/test_docker_runtime_config.py` previenen regresiones en Swagger, `.env.example`, Docker Compose y variables Resend usadas por TECH-07.

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

### 🔁 Probar recuperacion de contrasena US-13/US-14 (Docker + Swagger)
1. Levantar API + MongoDB:
```bash
docker compose up --build
```

2. Abrir Swagger en `http://localhost:8001/docs`.

3. Registrar un usuario con `POST /api/users/register` si aun no existe:
```json
{
  "nombre": "Ana Perez",
  "email": "ana.perez@ufrontera.cl",
  "password": "Segura123!"
}
```

4. Solicitar recuperacion con `POST /api/users/forgot-password`:
```json
{
  "email": "ana.perez@ufrontera.cl"
}
```

La respuesta no incluye el token; siempre retorna un mensaje generico para evitar enumeracion de usuarios.

5. Revisar la bandeja de entrada del correo registrado y abrir el enlace recibido.

6. TECH-07 usa Resend como proveedor transaccional con dominio remitente verificado; Docker pasa estas variables desde `.env` al contenedor API. Para ambiente local puedes configurar:
```bash
RESEND_API_KEY=<tu_api_key_real>
RESEND_FROM_EMAIL="UFROCoin <no-reply@ufrocoin.email>"
RESEND_RESET_SUBJECT=Recuperacion de contrasena UFROCoin
PASSWORD_RESET_BASE_URL=http://localhost:5173/reset-password
RESEND_TIMEOUT_SECONDS=10
```

En ambientes desplegados, ajustar `PASSWORD_RESET_BASE_URL` al frontend real.
Si Resend no esta configurado, falla o expira, `POST /api/users/forgot-password` responde `500` con codigos controlados (`EMAIL_PROVIDER_NOT_CONFIGURED`, `EMAIL_DELIVERY_ERROR` o `EMAIL_DELIVERY_TIMEOUT`) sin exponer credenciales.

7. Si necesitas probar manualmente `POST /api/users/reset-password`, usa el `token` del enlace recibido:
```json
{
  "token": "<TOKEN>",
  "new_password": "Nueva123!"
}
```

8. Verificar que responde `200 OK` y luego iniciar sesion con la nueva contrasena. El token es de un solo uso; reutilizarlo debe responder `401 INVALID_OR_EXPIRED_TOKEN`.

---
*Desarrollado por el Equipo A/1*
