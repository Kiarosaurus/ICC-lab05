"""Capa de Acceso a Datos: consultas SQL sobre la tabla `predicciones`."""

from contextlib import closing

from app.data.database import get_connection


def guardar(
    partido_id: int,
    usuario: str,
    resultado: str,
    goles_local: int,
    goles_visitante: int,
) -> int:
    """Inserta una predicción y devuelve su id."""
    with closing(get_connection()) as conn, conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO predicciones
                    (partido_id, usuario, resultado, goles_local, goles_visitante)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (partido_id, usuario, resultado, goles_local, goles_visitante),
            )
            return cursor.fetchone()["id"]


def listar() -> list[dict]:
    """Devuelve todas las predicciones con los datos de su partido (JOIN)."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pr.id, pr.usuario, pr.resultado,
                       pr.goles_local, pr.goles_visitante, pr.creado_en,
                       pa.equipo_local, pa.equipo_visitante, pa.ronda, pa.fecha
                FROM predicciones pr
                JOIN partidos pa ON pa.id = pr.partido_id
                ORDER BY pr.id DESC
                """
            )
            return [dict(fila) for fila in cursor.fetchall()]
