# UFROCoin - Test de Arquitectura y Stack (Módulo 1)

Este es un arquetipo validado para **UFROCoin**. Demuestra una comunicación eficiente, asíncrona y orquestada entre los microservicios de nuestra dApp/Proyecto.

## 🚀 Stack Tecnológico Elegido
- **Frontend UI:** Vue.js 3 + Vite. Configurado con `vitejs/plugin-vue` para una compilación relámpago. Puerto local expuesto: `5173`.
- **Backend API:** FastAPI (Python 3.11). Soporta asincronismo nativo de ciclo de vida e integra la librería `motor` (MongoDB async driver). Puerto local expuesto: `8000`.
- **Base de Datos:** MongoDB (`mongo:latest`). Persistencia a nivel de sistema mediante un volumen (Docker Volume). Puerto: `27017`.
- **Orquestación y Redes:** Docker Compose v3 con red virtualizada `bridge` (`ufrocoin_network`) para comunicación DNS interna.

## 🛠 Instalación y Despliegue

### 1. Requisitos Previos
Debes tener instalado y ejecutándose **Docker Desktop** (con Docker Compose incluído). Si ejecutas en Windows, asegúrate de que el motor WSL 2 de Docker esté encendido.

### 2. Arrancar la Infraestructura
Abre tu terminal (PowerShell o CMD) posicionado en esta misma carpeta raíz y escribe:

```bash
docker-compose up --build
```
> **Tip Senior:** Agrega `--build` la primera vez o cuando modifiques dependencias en `requirements.txt` o `package.json` para recrear las capas de compilación. Puedes usar `-d` para que corra en segundo plano.

### 3. Rutas de Validación Oficial

#### A. Estado del Backend y Base de Datos (FastAPI)
- **Ruta de Salud (`Health check`):** [http://localhost:8000/](http://localhost:8000/). El servidor responde JSON. Por detrás se verificó el ciclo de vida de conexión con Mongo mediante un "ping" asíncrono.
- **Swagger / OpenAPI (Auto-generado):** [http://localhost:8000/docs](http://localhost:8000/docs). Puedes probar el endpoint `POST /hash` directamente aquí enviándole un payload.

#### B. Flujo Web (Vue.js + CORS + Endpoints)
- **Interfaz Visual:** Ingresa a [http://localhost:5173/](http://localhost:5173/). 
- Escribe algo en la barra de texto (ejemplo: "bloque semilla inicial") y dale a enviar. Verás cómo Vue envía el POST JSON. FastAPI lo calcula, lo inyecta a MongoDB y el UI actualiza las interfaces reactivamente mostrando éxito.

## ♻ Hot Reload Activo
El entorno orquesta variables pre-inclusas de desarrollo. 
Debido a que hemos montado `volumes: - ./frontend:/app`, si entras a `frontend/src/App.vue` y cambias un título, al instante (10ms) se verá en el navegador gracias al motor `Vite HMR (Polling habilitado)`. Lo mismo pasa si cambias lógicas o prints en `main.py` de FastAPI. No necesitas bajar los contenedores de Docker.
