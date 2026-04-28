# jarvis-ai

Asistente de IA personal tipo JARVIS (Iron Man). Python backend + React frontend.
Inspirado en el canal NetHyTech. Propiedad de Jorge (wuasichu).

## Stack

- **Backend:** Python, WebSockets, Edge-TTS, automatización del SO
- **Frontend:** React, Three.js (Blob 3D), estética liquid glass futurista
- **LLM:** Groq API (modelos Llama, baja latencia)
- **Voz entrada:** Web Speech API (wake word "Jarvis")
- **Voz salida:** Edge-TTS (voz "Ryan")
- **Comunicación:** WebSockets en tiempo real

## Estructura del proyecto

```
jarvis-ai/
├── backend/          # Python: servidor WebSocket, LLM, TTS, tools
├── frontend/         # React: UI, Blob 3D, widgets
└── CLAUDE.md
```

## Convenciones

- Python virtual env en `backend/.venv`
- Variables de entorno en `backend/.env` (nunca commitear)
- Nunca superar 500 líneas por archivo
- Tests en `/tests/` con pytest

## GitHub Project Board

Project #1 (owner: wuasichu). Status field options:

| Status | Option ID |
|--------|-----------|
| Todo | `f75ad846` |
| In Progress | `47fc9ee4` |
| Done | `98236657` |

Status field ID: `PVTSSF_lAHOAC0d7c4BWCM1zhRZnec`

Priority field options:

| Priority | Option ID |
|----------|-----------|
| Low | `93adb7d9` |
| Medium | `6e6c6aaf` |
| High | `4767b726` |
| Critical | `e47bf167` |

Priority field ID: `PVTSSF_lAHOAC0d7c4BWCM1zhRZnk8`
