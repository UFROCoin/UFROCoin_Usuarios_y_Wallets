from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.api.routes.auth import router as auth_router
from src.api.routes.wallet import router as wallet_router
from src.core.database import create_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Acciones al iniciar la aplicacion
    await create_indexes()
    yield
    # Acciones al detener la aplicacion (opcional)

app = FastAPI(
    title="UFROCoin API",
    version="0.1.0",
    description=(
        "Modulo A de UFROCoin para gestion de usuarios y wallets. "
        "Incluye registro de usuario con creacion de wallet y consulta segura de billeteras."
    ),
    lifespan=lifespan,
    contact={
        "name": "Equipo A/1",
    },
    openapi_tags=[
        {
            "name": "Auth",
            "description": "Operaciones de registro y autenticacion de usuarios.",
        },
        {
            "name": "Wallet",
            "description": "Operaciones de consulta de billeteras y saldos.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(wallet_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Datos invalidos o contrasena debil.",
            "data": {},
            "error": {
                "code": "VALIDATION_ERROR",
                "details": str(exc.errors()),
            },
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", "Solicitud no procesada.")
        code = detail.get("code", "HTTP_ERROR")
        details = detail.get("details", "")
    else:
        message = str(detail)
        code = "HTTP_ERROR"
        details = str(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message,
            "data": {},
            "error": {
                "code": code,
                "details": details,
            },
        },
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
