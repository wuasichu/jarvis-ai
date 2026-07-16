import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.brain import process_message
from core.tts import speak_async, stop_tts
from core.learner import build_note_content
from tools.obsidian import read_note, write_note

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _save_memory(note_path: str, fact: str):
    existing = await asyncio.to_thread(read_note, note_path)
    if isinstance(existing, str) and "error" not in existing[:20].lower():
        content = existing + build_note_content(fact)
    else:
        header = f"# {note_path.split('/')[-1].replace('.md','').capitalize()}\n\n"
        content = header + build_note_content(fact)
    await asyncio.to_thread(write_note, note_path, content)
    print(f"[Memory] Guardado en {note_path}: {fact}")


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    tts_task: asyncio.Task | None = None
    try:
        while True:
            raw = await websocket.receive_text()

            # Respuesta de confirmación de memoria (JSON del frontend)
            try:
                msg = json.loads(raw)
                if msg.get("type") == "memory_confirm":
                    if msg.get("confirmed"):
                        await _save_memory(msg["note_path"], msg["fact"])
                    continue
            except (json.JSONDecodeError, KeyError):
                pass

            # Mensaje normal de texto
            text = raw

            # Interrumpir TTS en curso si el usuario habla encima
            if tts_task and not tts_task.done():
                stop_tts()
                tts_task.cancel()
                try:
                    await tts_task
                except asyncio.CancelledError:
                    pass

            reply, proposal = await process_message(text)
            await websocket.send_json({"type": "reply", "text": reply})

            # Propuesta de memoria si se detectó hecho memorable
            if proposal:
                await websocket.send_json({
                    "type": "memory_proposal",
                    "fact": proposal["fact"],
                    "category": proposal["category"],
                    "note_path": proposal["note_path"],
                })

            async def _speak_and_notify(r=reply):
                try:
                    await speak_async(r)
                except Exception as e:
                    print(f"[TTS error] {e}")
                try:
                    await websocket.send_json({"type": "tts_done"})
                except Exception:
                    pass

            tts_task = asyncio.create_task(_speak_and_notify())

    except WebSocketDisconnect:
        if tts_task and not tts_task.done():
            stop_tts()
            tts_task.cancel()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=False)
