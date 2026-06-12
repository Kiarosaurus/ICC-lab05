"""Capa de Acceso a Datos: conexión e inicialización de PostgreSQL.

La configuración se lee desde variables de entorno (definidas en
docker-compose.yml), con valores por defecto para desarrollo local:

    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import time
from contextlib import closing

import psycopg2
from psycopg2.extras import RealDictCursor


def _configuracion() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "mundial"),
        "user": os.getenv("DB_USER", "mundial"),
        "password": os.getenv("DB_PASSWORD", "mundial123"),
    }


def get_connection():
    """Abre una conexión; las filas se devuelven como diccionarios."""
    return psycopg2.connect(cursor_factory=RealDictCursor, **_configuracion())


def esperar_base_de_datos(intentos: int = 30, espera_segundos: float = 2.0) -> None:
    """Espera a que PostgreSQL acepte conexiones antes de continuar.

    En Docker la aplicación puede arrancar antes de que la base de datos
    esté lista, así que se reintenta en lugar de fallar al primer error.
    """
    for intento in range(1, intentos + 1):
        try:
            get_connection().close()
            print(f"[database] PostgreSQL disponible (intento {intento})")
            return
        except psycopg2.OperationalError as error:
            detalle = str(error).strip().splitlines()
            mensaje = detalle[0] if detalle else "sin detalle"
            print(
                f"[database] PostgreSQL aún no responde "
                f"(intento {intento}/{intentos}): {mensaje}"
            )
            time.sleep(espera_segundos)
    raise RuntimeError("No se pudo conectar a PostgreSQL tras varios intentos.")


def init_db() -> None:
    """Crea las tablas si no existen. Se llama al arrancar la aplicación."""
    with closing(get_connection()) as conn, conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS partidos (
                    id               SERIAL PRIMARY KEY,
                    numero           INTEGER UNIQUE NOT NULL,
                    ronda            TEXT NOT NULL,
                    fecha            TEXT NOT NULL,
                    equipo_local     TEXT NOT NULL,
                    equipo_visitante TEXT NOT NULL,
                    goles_local      INTEGER,
                    goles_visitante  INTEGER
                );

                CREATE TABLE IF NOT EXISTS predicciones (
                    id              SERIAL PRIMARY KEY,
                    partido_id      INTEGER NOT NULL REFERENCES partidos(id),
                    usuario         TEXT NOT NULL,
                    resultado       TEXT NOT NULL
                                    CHECK (resultado IN ('local', 'empate', 'visitante')),
                    goles_local     INTEGER NOT NULL CHECK (goles_local >= 0),
                    goles_visitante INTEGER NOT NULL CHECK (goles_visitante >= 0),
                    creado_en       TIMESTAMP(0) NOT NULL DEFAULT now()
                );
                """
            )
            print("[database] Tablas verificadas/creadas en PostgreSQL")
