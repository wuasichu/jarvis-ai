import re
import json
import hashlib
import threading
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_VAULT = Path("C:/Users/MI PC/Documents/mivault")
_CACHE = Path(__file__).parent.parent.parent / "data" / "vault_index.json"

_model = None
_model_lock = threading.Lock()
_index = {}           # fname -> {hash, embedding, snippet, links}
_matrix = None        # np.array de embeddings
_fnames = []          # lista ordenada de filenames
_ready = False


def _get_model():
    global _model
    with _model_lock:
        if _model is None:
            print("[Semantic] Cargando modelo embeddings...")
            _model = SentenceTransformer(_MODEL_NAME)
            print("[Semantic] Modelo listo")
    return _model


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _parse_links(content: str) -> list[str]:
    return re.findall(r'\[\[([^\]|#]+)[|\]#]', content)


def _load_cache():
    global _index
    if _CACHE.exists():
        try:
            with open(_CACHE, encoding="utf-8") as f:
                _index = json.load(f)
        except Exception:
            _index = {}


def _save_cache():
    _CACHE.parent.mkdir(exist_ok=True)
    with open(_CACHE, "w", encoding="utf-8") as f:
        json.dump(_index, f)


def _read_vault():
    files = {}
    if not _VAULT.exists():
        return files
    for p in _VAULT.rglob("*.md"):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            rel = str(p.relative_to(_VAULT)).replace("\\", "/")
            files[rel] = content
        except Exception:
            pass
    return files


def build_index():
    global _matrix, _fnames, _ready
    _load_cache()
    model = _get_model()
    vault = _read_vault()

    # Detectar notas nuevas o modificadas
    to_embed = [(f, c) for f, c in vault.items()
                if f not in _index or _index[f]["hash"] != _md5(c)]

    if to_embed:
        print(f"[Semantic] Indexando {len(to_embed)} notas...")
        texts = [c[:1200] for _, c in to_embed]
        embs = model.encode(texts, show_progress_bar=False, batch_size=32)
        for (fname, content), emb in zip(to_embed, embs):
            _index[fname] = {
                "hash": _md5(content),
                "embedding": emb.tolist(),
                "snippet": content[:400],
                "links": _parse_links(content),
            }
        _save_cache()

    # Eliminar notas borradas
    for f in list(_index.keys()):
        if f not in vault:
            del _index[f]

    _fnames = list(_index.keys())
    if _fnames:
        _matrix = np.array([_index[f]["embedding"] for f in _fnames], dtype=np.float32)
        norms = np.linalg.norm(_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        _matrix = _matrix / norms  # normalizar una vez

    _ready = True
    print(f"[Semantic] Índice listo: {len(_fnames)} notas")
    return len(_fnames)


def _build_index_bg():
    try:
        build_index()
    except Exception as e:
        print(f"[Semantic] Error indexando: {e}")


def start_indexing():
    t = threading.Thread(target=_build_index_bg, daemon=True)
    t.start()


def semantic_search(query: str, top_k: int = 3) -> list[tuple[str, float, str]]:
    if not _ready or _matrix is None:
        return []
    model = _get_model()
    q = model.encode([query])[0].astype(np.float32)
    q = q / (np.linalg.norm(q) or 1e-10)
    scores = _matrix @ q
    top = np.argsort(scores)[::-1][:top_k]
    return [(_fnames[i], float(scores[i]), _index[_fnames[i]]["snippet"]) for i in top]


def expand_with_graph(fname: str, depth: int = 1) -> list[str]:
    """Devuelve fname + notas enlazadas vía [[wikilinks]]."""
    if fname not in _index:
        return [fname]
    visited = {fname}
    frontier = set(_index[fname].get("links", []))
    for _ in range(depth - 1):
        new = set()
        for link in frontier:
            for f in _fnames:
                if f.endswith(link + ".md") and f not in visited:
                    new.update(_index[f].get("links", []))
        frontier.update(new)
    for link in frontier:
        for f in _fnames:
            if f.endswith(link + ".md"):
                visited.add(f)
    return list(visited)


def embed_text(text: str) -> list[float]:
    model = _get_model()
    return model.encode([text[:500]])[0].tolist()


def semantic_turn_search(query: str, turns: list[dict], top_k: int = 5) -> list[dict]:
    """Filtra los turnos más relevantes semánticamente al query."""
    if not turns:
        return []
    model = _get_model()
    q = model.encode([query[:500]])[0].astype(np.float32)
    q = q / (np.linalg.norm(q) or 1e-10)

    texts = [str(t.get("content", ""))[:300] for t in turns]
    embs = model.encode(texts, show_progress_bar=False).astype(np.float32)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    embs = embs / norms
    scores = embs @ q

    top = np.argsort(scores)[::-1][:top_k]
    # Siempre incluir los 4 más recientes + top semánticos
    recent = set(range(max(0, len(turns) - 4), len(turns)))
    selected = sorted(recent | set(top.tolist()))
    return [turns[i] for i in selected]
