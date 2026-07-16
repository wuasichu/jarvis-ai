import sqlite3
from pathlib import Path

_DB = Path(__file__).parent.parent.parent / "data" / "memory.db"
_SUMMARIZE_EVERY = 20


def _conn():
    _DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(_DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS messages "
        "(id INTEGER PRIMARY KEY, role TEXT, content TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    c.commit()
    return c


def load_history(limit: int = 20) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    rows.reverse()
    return [{"role": r, "content": m} for r, m in rows]


def save_turn(role: str, content: str):
    with _conn() as c:
        c.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
        c.commit()
        c.execute(
            "DELETE FROM messages WHERE id NOT IN "
            "(SELECT id FROM messages ORDER BY id DESC LIMIT 200)"
        )
        c.commit()


def count_turns() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]


def should_summarize() -> bool:
    return count_turns() % _SUMMARIZE_EVERY == 0


def pop_oldest_block(n: int = 20) -> list[dict]:
    """Devuelve los n turnos más antiguos y los elimina de la BD."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id, role, content FROM messages ORDER BY id ASC LIMIT ?", (n,)
        ).fetchall()
        if not rows:
            return []
        ids = [r[0] for r in rows]
        c.execute(f"DELETE FROM messages WHERE id IN ({','.join('?'*len(ids))})", ids)
        c.commit()
    return [{"role": r, "content": m} for _, r, m in rows]
