"""Capa de Presentación: rutas HTTP y renderizado de plantillas.

Esta capa no contiene reglas de negocio ni SQL: recibe la petición,
delega en los servicios de `app.business` y muestra el resultado.
"""

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.business import partido_service, prediccion_service
from app.presentation.banderas import bandera

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent / "templates"
)
templates.env.filters["bandera"] = bandera


def _obtener_partido_o_404(partido_id: int) -> dict:
    try:
        return partido_service.obtener_partido(partido_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/", response_class=HTMLResponse)
def listar_partidos(request: Request):
    """Listado completo de partidos almacenados en la base de datos."""
    partidos = partido_service.listar_partidos()
    return templates.TemplateResponse(
        request, "partidos.html", {"partidos": partidos}
    )


@router.get("/partidos/{partido_id}/predecir", response_class=HTMLResponse)
def formulario_prediccion(request: Request, partido_id: int):
    """Formulario para registrar una predicción sobre un partido."""
    partido = _obtener_partido_o_404(partido_id)
    return templates.TemplateResponse(
        request, "predecir.html", {"partido": partido, "error": None}
    )


@router.post("/partidos/{partido_id}/predicciones")
def crear_prediccion(
    request: Request,
    partido_id: int,
    usuario: str = Form(...),
    resultado: str = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
):
    """Recibe el formulario, delega la validación al negocio y guarda."""
    partido = _obtener_partido_o_404(partido_id)
    try:
        prediccion_service.registrar_prediccion(
            partido_id=partido_id,
            usuario=usuario,
            resultado=resultado,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request,
            "predecir.html",
            {"partido": partido, "error": str(error)},
            status_code=400,
        )
    return RedirectResponse(url="/predicciones", status_code=303)


@router.get("/predicciones", response_class=HTMLResponse)
def listar_predicciones(request: Request):
    """Listado de todas las predicciones registradas."""
    predicciones = prediccion_service.listar_predicciones()
    return templates.TemplateResponse(
        request, "predicciones.html", {"predicciones": predicciones}
    )
