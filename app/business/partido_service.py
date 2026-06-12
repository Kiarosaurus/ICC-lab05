"""Capa de Lógica de Negocio: reglas sobre los partidos del Mundial."""

from app.data import api_client, partido_repository


def sincronizar_partidos() -> int:
    """Recupera los partidos (API o mock) y los persiste en la base de datos.

    Se ejecuta al iniciar la aplicación. Es idempotente: los partidos ya
    guardados (mismo número de partido) no se duplican al reiniciar.
    """
    partidos = api_client.obtener_partidos()
    insertados = partido_repository.guardar_todos(partidos)
    print(f"[partido_service] {insertados} partidos nuevos guardados en la BD")
    return insertados


def listar_partidos() -> list[dict]:
    """Devuelve el listado completo de partidos almacenados."""
    return partido_repository.listar()


def obtener_partido(partido_id: int) -> dict:
    """Devuelve un partido por id. Lanza ValueError si no existe."""
    partido = partido_repository.buscar_por_id(partido_id)
    if partido is None:
        raise ValueError(f"No existe el partido con id {partido_id}.")
    return partido
