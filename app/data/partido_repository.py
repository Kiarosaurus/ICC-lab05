"""Capa de Acceso a Datos: consultas SQL sobre la tabla `partidos`."""

from contextlib import closing

from app.data.database import get_connection


def guardar_todos(partidos: list[dict]) -> int:
    """Inserta los partidos ignorando los ya existentes (numero es UNIQUE).

    Esto hace la carga inicial idempotente: reiniciar la app no duplica filas.
    Devuelve cuántos partidos nuevos se insertaron.
    """
    with closing(get_connection()) as conn, conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) AS total FROM partidos")
            antes = cursor.fetchone()["total"]
            cursor.executemany(
                """
                INSERT INTO partidos
                    (numero, ronda, fecha, equipo_local, equipo_visitante,
                     goles_local, goles_visitante)
                VALUES
                    (%(numero)s, %(ronda)s, %(fecha)s, %(equipo_local)s,
                     %(equipo_visitante)s, %(goles_local)s, %(goles_visitante)s)
                ON CONFLICT (numero) DO NOTHING
                """,
                partidos,
            )
            cursor.execute("SELECT count(*) AS total FROM partidos")
            return cursor.fetchone()["total"] - antes


def listar() -> list[dict]:
    """Devuelve todos los partidos ordenados por número."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM partidos ORDER BY numero")
            return [dict(fila) for fila in cursor.fetchall()]


def buscar_por_id(partido_id: int) -> dict | None:
    """Devuelve un partido por su id, o None si no existe."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM partidos WHERE id = %s", (partido_id,))
            fila = cursor.fetchone()
    return dict(fila) if fila else None
