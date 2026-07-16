import os
import json
import anthropic
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_MODEL = "claude-haiku-4-5-20251001"

_CATEGORIES = {"personas", "proyectos", "preferencias", "recordatorios", "otros"}

_EXTRACT_PROMPT = """Analiza este intercambio. ¿El usuario reveló un hecho específico que valdría recordar en futuras conversaciones?

Usuario: {user_msg}
Asistente: {reply}

Hechos memorables: datos sobre personas (nombre, preferencia, hábito), decisiones de proyecto, fechas importantes, precios, medidas, o información explícitamente mencionada.
NO memorable: saludos, preguntas, comandos (abrir web, tiempo, volumen), conversación trivial.

Responde SOLO JSON, sin explicación:
- Si hay hecho: {{"fact": "frase corta del hecho", "category": "personas|proyectos|preferencias|recordatorios|otros"}}
- Si no hay hecho: {{"fact": null}}"""


def extract_fact(user_msg: str, reply: str) -> dict | None:
    try:
        resp = _client.messages.create(
            model=_MODEL,
            max_tokens=80,
            messages=[{"role": "user", "content": _EXTRACT_PROMPT.format(
                user_msg=user_msg[:400], reply=reply[:400]
            )}]
        )
        raw = resp.content[0].text.strip()
        # Extraer JSON aunque venga con texto alrededor
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1:
            return None
        data = json.loads(raw[start:end])
        if not data.get("fact"):
            return None
        category = data.get("category", "otros")
        if category not in _CATEGORIES:
            category = "otros"
        return {
            "fact": data["fact"],
            "category": category,
            "note_path": f"JARVIS/Aprendido/{category}.md",
        }
    except Exception:
        return None


def build_note_content(fact: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"- {ts}: {fact}\n"
