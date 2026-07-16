import urllib.request
import urllib.parse
import json

_WMO = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "niebla", 48: "niebla con escarcha",
    51: "llovizna ligera", 53: "llovizna moderada", 55: "llovizna densa",
    61: "lluvia ligera", 63: "lluvia moderada", 65: "lluvia intensa",
    71: "nieve ligera", 73: "nieve moderada", 75: "nieve intensa",
    80: "chubascos ligeros", 81: "chubascos moderados", 82: "chubascos intensos",
    95: "tormenta", 96: "tormenta con granizo", 99: "tormenta con granizo intenso",
}

# Países que comparten nombre de ciudad con España — usar countrycode=es por defecto
_ES_CITIES = {
    "cartagena", "valencia", "córdoba", "cordoba", "granada", "almeria", "almería",
    "murcia", "alicante", "castellon", "castellón",
}


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=6) as r:
        return json.loads(r.read())


def get_weather(city: str, country: str = "") -> str:
    try:
        city_lower = city.lower().strip()

        geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {"name": city, "count": 10, "language": "es", "format": "json"}
        )
        geo = _fetch(geo_url)
        if not geo.get("results"):
            return f"No encontré la ciudad '{city}'."

        results = geo["results"]

        # Determinar país preferido
        prefer_country = country.lower()[:2] if country else ""
        if not prefer_country and city_lower in _ES_CITIES:
            prefer_country = "es"

        # Buscar coincidencia por código de país
        place = None
        if prefer_country:
            _CC = {"es": "España", "fr": "Francia", "de": "Alemania", "it": "Italia",
                   "pt": "Portugal", "mx": "México", "ar": "Argentina", "co": "Colombia"}
            country_name_pref = _CC.get(prefer_country, "")
            for r in results:
                if r.get("country_code", "").lower() == prefer_country or \
                   r.get("country", "").lower() == country_name_pref.lower():
                    place = r
                    break
        if place is None:
            place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        name = place.get("name", city)
        region = place.get("admin1", "")
        country_name = place.get("country", "")

        # Tiempo actual + previsión del día
        wx_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto", "forecast_days": 1,
        })
        wx = _fetch(wx_url)
        cur = wx["current"]
        day = wx["daily"]

        code = cur.get("weathercode", 0)
        desc = _WMO.get(code, "condición desconocida")
        location = f"{name}, {region}, {country_name}".strip(", ")

        return (
            f"Tiempo en {location}: {desc}. "
            f"Temperatura {cur['temperature_2m']}°C, sensación {cur['apparent_temperature']}°C. "
            f"Humedad {cur['relative_humidity_2m']}%. "
            f"Viento {cur['wind_speed_10m']} km/h. "
            f"Máxima {day['temperature_2m_max'][0]}°C, mínima {day['temperature_2m_min'][0]}°C. "
            f"Lluvia acumulada hoy: {day['precipitation_sum'][0]} mm."
        )
    except Exception as e:
        return f"Error obteniendo el tiempo: {e}"
