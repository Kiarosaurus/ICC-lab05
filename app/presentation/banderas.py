"""Capa de Presentación: banderas emoji para mostrar junto a cada país.

Detalle puramente visual: convierte el nombre del equipo (en inglés si los
datos vienen de la API pública, en español si vienen del mock local) en su
bandera emoji. Si el país no está mapeado se muestra un balón genérico.
"""

# Nombre del país -> código ISO 3166-1 alfa-2.
_PAISES = {
    # Nombres en inglés (API pública openfootball)
    "russia": "RU", "saudi arabia": "SA", "egypt": "EG", "uruguay": "UY",
    "portugal": "PT", "spain": "ES", "morocco": "MA", "iran": "IR",
    "france": "FR", "australia": "AU", "peru": "PE", "denmark": "DK",
    "argentina": "AR", "iceland": "IS", "croatia": "HR", "nigeria": "NG",
    "brazil": "BR", "switzerland": "CH", "costa rica": "CR", "serbia": "RS",
    "germany": "DE", "mexico": "MX", "sweden": "SE", "south korea": "KR",
    "korea republic": "KR", "belgium": "BE", "panama": "PA", "tunisia": "TN",
    "colombia": "CO", "japan": "JP", "poland": "PL", "senegal": "SN",
    "qatar": "QA", "ecuador": "EC", "netherlands": "NL", "ghana": "GH",
    "united states": "US", "usa": "US", "cameroon": "CM", "canada": "CA",
    "wales": "GB",
    # Nombres en español (mock local) que difieren del inglés
    "rusia": "RU", "arabia saudita": "SA", "egipto": "EG", "españa": "ES",
    "marruecos": "MA", "irán": "IR", "francia": "FR", "perú": "PE",
    "dinamarca": "DK", "islandia": "IS", "croacia": "HR", "brasil": "BR",
    "suiza": "CH", "alemania": "DE", "méxico": "MX", "suecia": "SE",
    "corea del sur": "KR", "bélgica": "BE", "panamá": "PA", "túnez": "TN",
    "japón": "JP", "polonia": "PL", "catar": "QA", "países bajos": "NL",
    "estados unidos": "US",
}

# Inglaterra usa una secuencia especial (bandera regional GB-ENG).
_BANDERA_INGLATERRA = (
    "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"
)
_ESPECIALES = {"england": _BANDERA_INGLATERRA, "inglaterra": _BANDERA_INGLATERRA}


def bandera(nombre_pais: str) -> str:
    """Filtro Jinja2: '{{ "Brasil" | bandera }}' -> bandera emoji de Brasil."""
    clave = (nombre_pais or "").strip().lower()
    if clave in _ESPECIALES:
        return _ESPECIALES[clave]
    iso = _PAISES.get(clave)
    if iso is None:
        return "⚽"
    return "".join(chr(0x1F1E6 + ord(letra) - ord("A")) for letra in iso)
