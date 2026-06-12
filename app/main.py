"""Punto de entrada de la aplicación.

Conecta las tres capas:
- Presentación      -> app/presentation  (rutas HTTP, plantillas, estáticos)
- Lógica de Negocio -> app/business      (servicios y validaciones)
- Acceso a Datos    -> app/data          (SQLite y cliente de la API)

Ejecutar con:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.business import partido_service
from app.data import database
from app.presentation.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Al iniciar: espera la base de datos, crea las tablas y carga los partidos."""
    database.esperar_base_de_datos()
    database.init_db()
    partido_service.sincronizar_partidos()
    yield


app = FastAPI(title="Predicciones del Mundial", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "presentation" / "static"),
    name="static",
)
app.include_router(router)
