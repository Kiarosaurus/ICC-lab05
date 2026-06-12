"""Capa de Acceso a Datos: consumo de la API pública de partidos del Mundial.

Intenta descargar los partidos desde la API pública de openfootball
(JSON del Mundial servido por HTTP). Si no hay conexión a internet,
usa el mock local `mock_partidos.json` para que la aplicación siga
funcionando sin red.

Se soportan los dos formatos de openfootball:
- A (mock):     {"rounds": [{"name": ..., "matches": [...]}]}
                con team1/team2 como objetos y score1/score2 planos.
- B (API real): {"matches": [{"round": ..., "team1": "...", "score": {"ft": [a, b]}}]}
"""

import json
from pathlib import Path

import requests

API_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2018/worldcup.json"
)
MOCK_PATH = Path(__file__).resolve().parent / "mock_partidos.json"


def obtener_partidos() -> list[dict]:
    """Devuelve los partidos ya normalizados al modelo interno."""
    try:
        respuesta = requests.get(API_URL, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        origen = "API pública (openfootball)"
    except (requests.RequestException, ValueError):
        datos = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        origen = "mock local (mock_partidos.json)"

    partidos = _normalizar(datos)
    print(f"[api_client] {len(partidos)} partidos obtenidos desde: {origen}")
    return partidos


def _normalizar(datos: dict) -> list[dict]:
    """Convierte el JSON externo (en cualquiera de sus formatos) al modelo interno."""
    if "rounds" in datos:
        crudos = [
            (ronda["name"], partido)
            for ronda in datos["rounds"]
            for partido in ronda.get("matches", [])
        ]
    else:
        crudos = [
            (partido.get("round", "Sin ronda"), partido)
            for partido in datos.get("matches", [])
        ]

    partidos = []
    for indice, (ronda, partido) in enumerate(crudos, start=1):
        goles_local, goles_visitante = _extraer_marcador(partido)
        partidos.append(
            {
                "numero": partido.get("num") or indice,
                "ronda": ronda,
                "fecha": partido["date"],
                "equipo_local": _nombre_equipo(partido["team1"]),
                "equipo_visitante": _nombre_equipo(partido["team2"]),
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
            }
        )
    return partidos


def _nombre_equipo(equipo) -> str:
    """El equipo puede venir como objeto {"name": ...} o como string."""
    if isinstance(equipo, dict):
        return equipo.get("name") or equipo.get("code") or "Por definir"
    return str(equipo)


def _extraer_marcador(partido: dict) -> tuple:
    """Devuelve (goles_local, goles_visitante); (None, None) si no se jugó."""
    if "score1" in partido or "score2" in partido:
        return partido.get("score1"), partido.get("score2")

    score = partido.get("score") or {}
    # "et" = tras prórroga (resultado final real); si no existe, "ft" = 90 min.
    marcador = score.get("et") or score.get("ft")
    if isinstance(marcador, (list, tuple)) and len(marcador) == 2:
        return marcador[0], marcador[1]
    return None, None
