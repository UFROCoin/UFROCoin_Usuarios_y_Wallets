# UFROCoin | Módulo A: Usuarios & Wallets 🪙

Este componente gestiona la identidad y seguridad del ecosistema UFROCoin, encargándose del registro de usuarios, autenticación y gestión de billeteras digitales.

### 📝 Descripción del Módulo
El Módulo A implementa la capa base de confianza del proyecto:
* **Gestión de Identidad:** Registro de usuarios con validación de campos y autenticación JWT.
* **Seguridad:** Hashing de contraseñas mediante SHA-256 con salt aleatorio (ADR-002).
* **Billeteras Digitales (Wallets):** Creación automática de wallets (40 caracteres hex) al registrarse, con saldo inicial y transacción génesis.
* **API Estandarizada:** Alineación total con el contrato de [Apidog](https://ufrocoinproposal.apidog.io/).

### 🚀 Funcionalidades Implementadas (Sprint 1)
* [x] **US-01:** Registro de usuario y validación de campos.
* [x] **US-02:** Seguridad mediante Hashing SHA-256 + Salt.
* [x] **US-03/04:** Generación de dirección de Wallet y vinculación automática.
* [x] **US-05/06:** Autenticación de usuario y entrega de Token JWT.
* [x] **US-07:** Emisión de Transacción Génesis (Welcome Reward).
* [x] **US-08:** Endpoint de consulta de Wallet con cálculo de saldo real.
* [x] **TECH-04/05:** Refactor de respuestas genéricas y alineación de contrato.

### ⚙️ Desarrollo Local con uv
* Instalar dependencias: `python -m uv sync --all-extras`
* Levantar API: `python -m uv run uvicorn src.main:app --reload --port 8001`
* Ejecutar tests: `python -m uv run pytest`

### 🛠️ API Endpoints (Contrato Apidog)
Todas las respuestas siguen el formato: `{ "success": bool, "message": string, "data": {}, "error": {...} }`

* `POST /api/users/register`: Registro de nuevo usuario.
* `POST /api/users/login`: Autenticación y obtención de JWT.
* `GET /api/wallet/{address}`: Detalle de wallet y saldo (Requiere JWT).

---
*Desarrollado por el Equipo A/1*
