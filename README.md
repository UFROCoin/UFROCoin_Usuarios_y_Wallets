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

---
*Desarrollado por el Equipo A/1*
