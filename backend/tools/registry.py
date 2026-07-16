import psutil
import pywhatkit
from Automation.open_App import open_App
from Automation.Web_Open import openweb
from Features.set_get_volume import set_volume_windows, get_volume_windows
from Features.set_br import set_brightness_windows
from tools.obsidian import search_vault, read_note, write_note
from tools.weather import get_weather

TOOL_SCHEMAS = [
    {
        "name": "open_app",
        "description": "Abre una aplicación instalada en el sistema",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Nombre de la aplicación a abrir"}
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "open_website",
        "description": "Abre una página web en el navegador. Pasa la URL completa con https:// cuando la conozcas (ej: https://sede.seg-social.gob.es). Si no conoces la URL exacta, pasa el nombre del sitio y se buscará en Google.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "URL completa (https://...) o nombre del sitio web"}
            },
            "required": ["name"],
        },
    },
    {
        "name": "check_battery",
        "description": "Comprueba el nivel de batería y estado de carga",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "set_volume",
        "description": "Ajusta el volumen del sistema",
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Nivel de volumen entre 0 y 100"}
            },
            "required": ["level"],
        },
    },
    {
        "name": "search_google",
        "description": "Realiza una búsqueda en Google",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto a buscar"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_vault",
        "description": "Busca notas en el vault de Obsidian de Jorge",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto a buscar en el vault"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_note",
        "description": "Lee el contenido de una nota de Obsidian por su ruta (ej: 'Proyectos Activos.md')",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_path": {"type": "string", "description": "Ruta relativa de la nota dentro del vault"}
            },
            "required": ["note_path"],
        },
    },
    {
        "name": "write_note",
        "description": "Crea o sobreescribe una nota en el vault de Obsidian",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_path": {"type": "string", "description": "Ruta relativa de la nota a escribir"},
                "content": {"type": "string", "description": "Contenido Markdown de la nota"},
            },
            "required": ["note_path", "content"],
        },
    },
    {
        "name": "get_weather",
        "description": "Obtiene el tiempo actual y previsión del día para una ciudad. Devuelve temperatura, sensación térmica, humedad, viento, máxima y mínima. Úsalo siempre que el usuario pregunte por el tiempo o la temperatura. Jorge vive en España, así que por defecto busca ciudades españolas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Nombre de la ciudad, por ejemplo 'Cartagena' o 'Madrid'"},
                "country": {"type": "string", "description": "Código de país ISO de 2 letras opcional, ej: 'es' para España, 'fr' para Francia. Omitir si no se sabe."},
            },
            "required": ["city"],
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    try:
        if name == "open_app":
            open_App(args["app_name"])
            return f"Aplicación '{args['app_name']}' abierta."

        elif name == "open_website":
            openweb(args["name"])
            return f"Navegando a {args['name']}."

        elif name == "check_battery":
            b = psutil.sensors_battery()
            if b is None:
                return "Sin batería (PC de escritorio)."
            status = "cargando" if b.power_plugged else "descargando"
            return f"Batería al {int(b.percent)}%, {status}."

        elif name == "set_volume":
            set_volume_windows(args["level"])
            return f"Volumen ajustado a {args['level']}%."

        elif name == "search_google":
            pywhatkit.search(args["query"])
            return f"Búsqueda de '{args['query']}' abierta en Google."

        elif name == "search_vault":
            return search_vault(args["query"])

        elif name == "read_note":
            return read_note(args["note_path"])

        elif name == "write_note":
            return write_note(args["note_path"], args["content"])

        elif name == "get_weather":
            return get_weather(args["city"], args.get("country", ""))

        else:
            return f"Herramienta desconocida: {name}"

    except Exception as e:
        return f"Error en {name}: {e}"
