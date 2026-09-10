"""Operações de leitura/escrita sobre a tabela de jogos."""
import os
from typing import Optional

from . import config
from .database import get_conn


def list_consoles() -> list[dict]:
    """Devolve as consolas com a contagem de jogos de cada uma."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT console, COUNT(*) AS total "
            "FROM games GROUP BY console ORDER BY console COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]


def list_games(console: Optional[str] = None, search: Optional[str] = None) -> list[dict]:
    sql = "SELECT * FROM games WHERE 1=1"
    params: list = []
    if console:
        sql += " AND console = ?"
        params.append(console)
    if search:
        sql += " AND title LIKE ?"
        params.append(f"%{search}%")
    sql += " ORDER BY title COLLATE NOCASE"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_game(game_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    return dict(row) if row else None


def update_game(game_id: str, fields: dict) -> None:
    """Atualiza campos editáveis manualmente."""
    allowed = {"title", "console", "year", "genre", "description", "cover", "cover_locked"}
    sets, params = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            params.append(v)
    if not sets:
        return
    sets.append("updated_at = datetime('now')")
    params.append(game_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE games SET {', '.join(sets)} WHERE id = ?", params)


def _remove_cover_file(cover: Optional[str]) -> None:
    """Apaga apenas a miniatura gerada por nós. Nunca toca no ficheiro do jogo."""
    if not cover:
        return
    try:
        os.remove(os.path.join(config.THUMBS_DIR, cover))
    except OSError:
        pass


def delete_game(game_id: str) -> bool:
    """Remove um jogo do catálogo (e a sua capa). O ficheiro no NAS fica intacto."""
    game = get_game(game_id)
    if not game:
        return False
    _remove_cover_file(game.get("cover"))
    with get_conn() as conn:
        conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
    return True


def delete_console(console: str) -> int:
    """Remove todos os jogos de uma consola do catálogo. Devolve quantos removeu.

    Útil para limpar entradas de um caminho escaneado por engano.
    Os ficheiros físicos no NAS NÃO são apagados.
    """
    with get_conn() as conn:
        covers = [r["cover"] for r in conn.execute(
            "SELECT cover FROM games WHERE console = ?", (console,)
        ).fetchall()]
        cur = conn.execute("DELETE FROM games WHERE console = ?", (console,))
        removed = cur.rowcount
    for cover in covers:
        _remove_cover_file(cover)
    return removed


def last_scan() -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM scans ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def stats() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        consoles = conn.execute("SELECT COUNT(DISTINCT console) FROM games").fetchone()[0]
        with_cover = conn.execute(
            "SELECT COUNT(*) FROM games WHERE cover IS NOT NULL AND cover != ''"
        ).fetchone()[0]
    return {"total": total, "consoles": consoles, "with_cover": with_cover}
