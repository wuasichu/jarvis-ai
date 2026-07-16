import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from tools.registry import TOOL_SCHEMAS, execute_tool
from tools.obsidian import fetch_context_semantic, read_note, write_note
from tools.semantic import start_indexing, semantic_turn_search
from core.memory import load_history, save_turn, should_summarize, pop_oldest_block
from core.learner import extract_fact

load_dotenv(Path(__file__).parent.parent.parent / ".env")

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_history = load_history(40)   # cargamos más; semantic filtra los relevantes
start_indexing()              # indexa vault en background al arrancar
_MODEL = "claude-haiku-4-5-20251001"
_BASE_SYSTEM = """Eres JARVIS, el asistente personal de voz de Jorge. Eres una aplicación Python (FastAPI + WebSockets) distinta de Claude Code.

Tus herramientas REALES (lo único que puedes hacer):
- open_app: abrir aplicaciones del sistema
- open_website: abrir páginas web
- check_battery: nivel de batería
- set_volume: ajustar volumen
- search_google: buscar en Google
- search_vault: buscar notas en el vault de Obsidian de Jorge
- read_note: leer una nota de Obsidian por su ruta
- write_note: crear o actualizar una nota de Obsidian

Tu arquitectura real:
- Backend: Python, FastAPI, WebSockets, puerto 8765
- LLM: Claude Haiku (Anthropic API)
- TTS: edge-TTS voz Ryan
- STT: Web Speech API en el navegador
- Memoria: SQLite persistente + semántica (sentence-transformers)
- Obsidian: API REST en 127.0.0.1:27124, conectado y funcional
- Frontend: React + Three.js BlobOrb, puerto 5173

Cuando te pregunten por tus capacidades, cíñete a lo anterior. NO confundas tu identidad con Claude Code, sus skills, MCPs ni memorias — eso es otra herramienta, no tú.

Respuestas cortas y directas. Español siempre. Usa el contexto del vault para respuestas personalizadas."""

# Mapa keyword → nota de Obsidian del proyecto
_PROJECT_MAP = {
    "cota3d":       ("cota3d impresión bambu filamento pedido cliente stl", "Proyectos/ACTIVOS/cota3d.es/Estado del Proyecto.md"),
    "finora":       ("finora finanzas gasto ingreso presupuesto dinero",    "Proyectos/ACTIVOS/Finora/Estado del Proyecto.md"),
    "jarvis":       ("jarvis asistente backend frontend voz tts websocket", "Proyectos/ACTIVOS/JARVIS.md"),
    "marineos":     ("marineos marino barco raspberry cámara esp32",        "Proyectos/ACTIVOS/MarineOS/Estado del Proyecto.md"),
    "ruview":       ("ruview wifi sensing raspberry señal",                 "Proyectos/ACTIVOS/RuView/Estado del Proyecto.md"),
    "stl":          ("stl imagen three.js modelo 3d impresora",            "Proyectos/ACTIVOS/App STL/Estado del Proyecto.md"),
    "fusion360":    ("fusion360 mcp diseño cad modelo",                    "Proyectos/ACTIVOS/Fusion360 MCP/Estado del Proyecto.md"),
}

_active_project: str | None = None
_project_context: str = ""


def _detect_project(text: str) -> str | None:
    lower = text.lower()
    for project, (keywords, _) in _PROJECT_MAP.items():
        if any(kw in lower for kw in keywords.split()):
            return project
    return None


async def _load_project_context(project: str) -> str:
    _, note_path = _PROJECT_MAP[project]
    content = await asyncio.to_thread(read_note, note_path)
    if content and "error" not in content[:30].lower():
        return f"[Proyecto activo: {project}]\n{content[:1200]}"
    return ""


def _trim_history():
    global _history
    if len(_history) <= 20:
        return
    _history[:] = _history[-20:]
    while _history and not (
        _history[0]["role"] == "user" and isinstance(_history[0]["content"], str)
    ):
        _history.pop(0)


async def _summarize_and_archive(block: list[dict]):
    """Comprime un bloque de conversación y lo guarda en Obsidian."""
    turns_text = "\n".join(
        f"{t['role'].upper()}: {t['content']}" for t in block
        if isinstance(t.get("content"), str)
    )
    if not turns_text.strip():
        return

    summary_response = await asyncio.to_thread(
        _client.messages.create,
        model=_MODEL,
        max_tokens=300,
        system=(
            "Eres un archivador de conversaciones. "
            "Resume el siguiente fragmento de conversación entre Jorge y JARVIS en 3-5 puntos clave. "
            "Incluye decisiones tomadas, temas tratados y cualquier dato importante mencionado. "
            "Formato: lista de puntos en español."
        ),
        messages=[{"role": "user", "content": turns_text}],
    )
    summary = summary_response.content[0].text
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    note_path = f"Proyectos/ACTIVOS/JARVIS/Resumenes/sesion_{ts}.md"
    note_content = f"# Resumen de sesión JARVIS — {ts}\n\n{summary}\n\n---\n*Archivado automáticamente*\n"
    await asyncio.to_thread(write_note, note_path, note_content)
    print(f"[Memory] Resumen archivado: {note_path}")


async def process_message(text: str) -> tuple[str, dict | None]:
    global _active_project, _project_context

    save_turn("user", text)
    _history.append({"role": "user", "content": text})
    _trim_history()

    # C: memoria semántica — filtra turnos más relevantes al query actual
    relevant_history = semantic_turn_search(text, _history)

    # Atractor: detectar cambio de proyecto y cargar su nota
    detected = _detect_project(text)
    if detected and detected != _active_project:
        _active_project = detected
        _project_context = await _load_project_context(detected)
        if _project_context:
            print(f"[Attractor] Proyecto activo: {detected}")

    # Contexto reactivo por búsqueda + contexto persistente de proyecto
    # Búsqueda semántica del vault (A+B: embeddings + grafo)
    vault_context = await asyncio.to_thread(fetch_context_semantic, text)
    system = _BASE_SYSTEM
    if _project_context:
        system += f"\n\n{_project_context}"
    if vault_context and vault_context not in _project_context:
        system += f"\n\nContexto del vault:\n{vault_context}"

    response = await asyncio.to_thread(
        _client.messages.create,
        model=_MODEL,
        max_tokens=500,
        system=system,
        tools=TOOL_SCHEMAS,
        messages=relevant_history,
    )

    if response.stop_reason == "tool_use":
        _history.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

        _history.append({"role": "user", "content": tool_results})

        final = await asyncio.to_thread(
            _client.messages.create,
            model=_MODEL,
            max_tokens=300,
            system=system,
            messages=_history,
        )
        reply = final.content[0].text if final.content else ""
    else:
        reply = response.content[0].text

    save_turn("assistant", reply)
    _history.append({"role": "assistant", "content": reply})

    # Olvido gradual: cada 20 turnos comprimir y archivar en Obsidian
    if should_summarize():
        old_block = pop_oldest_block(20)
        if old_block:
            asyncio.create_task(_summarize_and_archive(old_block))

    # Aprendizaje activo: detectar hecho memorable en background
    proposal = await asyncio.to_thread(extract_fact, text, reply)

    return reply, proposal
