import os
import ssl
import urllib.request
import urllib.parse
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

_BASE = "https://127.0.0.1:27124"
_TOKEN = os.getenv("OBSIDIAN_TOKEN", "")
_CTX = ssl._create_unverified_context()


def _headers():
    return {"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"}


def _request(method: str, path: str, body: bytes | None = None) -> dict | str:
    url = f"{_BASE}{path}"
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=5) as r:
            raw = r.read().decode()
            try:
                return json.loads(raw)
            except Exception:
                return raw
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def search_vault(query: str) -> str:
    encoded = urllib.parse.quote(query)
    result = _request("POST", f"/search/simple/?query={encoded}&contextLength=100")
    if isinstance(result, dict) and "error" in result:
        return result["error"]
    if not result:
        return "No se encontraron notas."
    lines = []
    for item in result[:5]:
        fname = item.get("filename", "")
        ctx = " | ".join(
            m.get("match", {}).get("context", "") for m in item.get("matches", [])[:2]
        )
        lines.append(f"- {fname}: {ctx}")
    return "\n".join(lines)


def read_note(note_path: str) -> str:
    encoded = urllib.parse.quote(note_path)
    result = _request("GET", f"/vault/{encoded}")
    if isinstance(result, dict) and "error" in result:
        return result["error"]
    if isinstance(result, str):
        return result[:2000]
    return str(result)[:2000]


_STOP_WORDS = {
    "que", "qué", "hay", "sobre", "acerca", "de", "del", "la", "el", "los", "las",
    "en", "lo", "un", "una", "y", "a", "es", "me", "te", "se", "si", "no",
    "busca", "buscar", "mira", "dime", "quiero", "saber", "tengo", "puedo",
    "ultimo", "última", "últimos", "últimas", "hemos", "puesto", "visto",
    "con", "por", "para", "como", "cuando", "donde", "qué", "cuál",
}


def _extract_keywords(text: str) -> list[str]:
    words = text.lower().replace("á","a").replace("é","e").replace("í","i")\
                        .replace("ó","o").replace("ú","u").split()
    return [w for w in words if len(w) > 3 and w not in _STOP_WORDS]


def _search_raw(query: str) -> list:
    encoded = urllib.parse.quote(query)
    result = _request("POST", f"/search/simple/?query={encoded}&contextLength=200")
    if isinstance(result, list):
        return result
    return []


def fetch_context_semantic(query: str) -> str:
    """Búsqueda semántica: usa embeddings + expansión de grafo."""
    try:
        from tools.semantic import semantic_search, expand_with_graph
        results = semantic_search(query, top_k=2)
        if not results:
            return fetch_context(query)
        parts = []
        seen = set()
        for fname, score, _ in results:
            if score < 0.25:
                continue
            expanded = expand_with_graph(fname, depth=1)
            for f in expanded[:3]:
                if f not in seen:
                    seen.add(f)
                    content = read_note(f)
                    if content and "error" not in content[:20].lower():
                        parts.append(f"[{f}]\n{content[:600]}")
        return "\n\n".join(parts) if parts else fetch_context(query)
    except Exception as e:
        return fetch_context(query)


def fetch_context(query: str) -> str:
    """Busca en el vault con estrategia multi-query y devuelve la nota más relevante."""
    # 1. Intentar con la query completa
    results = _search_raw(query)

    # 2. Si no hay resultados, probar con keywords extraídas
    if not results:
        keywords = _extract_keywords(query)
        if keywords:
            # Probar grupos de 3 keywords más significativas (las más largas)
            keywords.sort(key=len, reverse=True)
            kw_query = " ".join(keywords[:3])
            results = _search_raw(kw_query)

    # 3. Si aún nada, probar de a pares
    if not results:
        keywords = _extract_keywords(query)
        for i in range(len(keywords) - 1):
            results = _search_raw(f"{keywords[i]} {keywords[i+1]}")
            if results:
                break

    if not results:
        return ""

    fname = results[0].get("filename", "")
    if not fname:
        return ""
    content = read_note(fname)
    if content and "error" not in content[:30].lower():
        return f"[Nota relevante: {fname}]\n{content[:1000]}"
    return ""


def write_note(note_path: str, content: str) -> str:
    encoded = urllib.parse.quote(note_path)
    body = content.encode()
    result = _request("PUT", f"/vault/{encoded}", body=body)
    if isinstance(result, dict) and "error" in result:
        return result["error"]
    return f"Nota '{note_path}' guardada."
