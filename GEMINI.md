# Project: UFROCoin Usuarios y Wallets

Este proyecto es el Módulo A de UFROCoin, encargado de la gestión de usuarios y billeteras.

## Tech Stack

- **Lenguaje**: Python 3.14+
- **Framework**: FastAPI
- **Base de Datos**: MongoDB (Motor/PyMongo)
- **Autenticación**: PyJWT
- **Gestor de Dependencias**: uv

## Testing & Quality

- **Framework**: Pytest
- **Async**: pytest-asyncio
- **E2E**: httpx
- **Comando**: `pytest`

## Standards

- **Lifecycle**: Seguir estrictamente el ciclo Research -> Strategy -> Execution.
- **TDD**: Se prefiere el desarrollo dirigido por pruebas (TDD). Crear pruebas antes de implementar lógica.
- **SDD**: Utilizar los comandos `/sdd-*` para cambios significativos.
- **Arquitectura**: 
  - `src/api/routes/`: Definición de endpoints.
  - `src/services/`: Lógica de negocio.
  - `src/models/`: Modelos de datos (Pydantic/MongoDB).
  - `src/core/`: Configuración y seguridad.

## Persistence

- Este proyecto utiliza **Engram** para la persistencia de artefactos SDD y memoria de sesiones.
