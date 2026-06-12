"""Capa de Lógica de Negocio: reglas para registrar y consultar predicciones."""

from app.data import partido_repository, prediccion_repository

RESULTADOS_VALIDOS = ("local", "empate", "visitante")
MAX_GOLES = 20


def registrar_prediccion(
    partido_id: int,
    usuario: str,
    resultado: str,
    goles_local: int,
    goles_visitante: int,
) -> int:
    """Valida la predicción y la guarda asociada a su partido.

    Lanza ValueError con un mensaje claro si alguna regla no se cumple.
    Devuelve el id de la predicción creada.
    """
    usuario = usuario.strip()
    if not usuario:
        raise ValueError("El nombre de usuario es obligatorio.")
    if len(usuario) > 50:
        raise ValueError("El nombre de usuario no puede superar 50 caracteres.")
    if resultado not in RESULTADOS_VALIDOS:
        raise ValueError("El resultado debe ser 'local', 'empate' o 'visitante'.")
    if not (0 <= goles_local <= MAX_GOLES) or not (0 <= goles_visitante <= MAX_GOLES):
        raise ValueError(f"Los goles deben estar entre 0 y {MAX_GOLES}.")

    partido = partido_repository.buscar_por_id(partido_id)
    if partido is None:
        raise ValueError(f"No existe el partido con id {partido_id}.")

    _validar_coherencia(partido, resultado, goles_local, goles_visitante)

    return prediccion_repository.guardar(
        partido_id, usuario, resultado, goles_local, goles_visitante
    )


def listar_predicciones() -> list[dict]:
    """Devuelve todas las predicciones registradas con su partido."""
    return prediccion_repository.listar()


def _validar_coherencia(
    partido: dict, resultado: str, goles_local: int, goles_visitante: int
) -> None:
    """Regla de negocio: el ganador/empate elegido debe coincidir con el marcador."""
    if goles_local > goles_visitante:
        esperado = "local"
    elif goles_local < goles_visitante:
        esperado = "visitante"
    else:
        esperado = "empate"

    if resultado != esperado:
        descripciones = {
            "local": f"victoria de {partido['equipo_local']}",
            "visitante": f"victoria de {partido['equipo_visitante']}",
            "empate": "un empate",
        }
        raise ValueError(
            f"El marcador {goles_local}-{goles_visitante} implica "
            f"{descripciones[esperado]}, pero elegiste {descripciones[resultado]}. "
            "Corrige la predicción."
        )
