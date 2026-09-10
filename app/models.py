import os
import sqlite3
from typing import Optional

from . import config
from .database import get_conn, normalize_text


def list_consoles() -> list[dict]:
    """Devolve as consolas com a contagem de jogos de cada uma."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT console, COUNT(*) AS total "
            "FROM games GROUP BY console ORDER BY console COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]


def list_games(
    console: Optional[str] = None,
    search: Optional[str] = None,
    favorites_only: bool = False,
) -> list[dict]:
    """Lista jogos com suporte a filtro por consola, favoritos e pesquisa multi-termo insensível a acentos."""
    sql = "SELECT * FROM games WHERE 1=1"
    params: list = []
    if console:
        sql += " AND console = ?"
        params.append(console)
    if favorites_only:
        sql += " AND favorite = 1"
    if search:
        # Divide a pesquisa em palavras para que múltiplos termos coincidam
        # (ex: 'mario switch' encontra Mario na Switch, 'zelda breath' encontra Zelda)
        keywords = [w.strip() for w in search.split() if w.strip()]
        for kw in keywords:
            clean_kw = normalize_text(kw)
            sql += (
                " AND ("
                "norm(title) LIKE ? "
                "OR norm(console) LIKE ? "
                "OR norm(genre) LIKE ? "
                "OR norm(path) LIKE ? "
                "OR norm(description) LIKE ?"
                ")"
            )
            term = f"%{clean_kw}%"
            params.extend([term, term, term, term, term])
    sql += " ORDER BY title COLLATE NOCASE"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_game(game_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    return dict(row) if row else None


def toggle_favorite(game_id: str) -> bool:
    """Alterna o estado de favorito de um jogo e devolve o novo estado (True/False)."""
    with get_conn() as conn:
        row = conn.execute("SELECT favorite FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["favorite"] else 1
        conn.execute(
            "UPDATE games SET favorite = ?, updated_at = datetime('now') WHERE id = ?",
            (new_val, game_id),
        )
        return bool(new_val)


def get_random_game(console: Optional[str] = None, favorites_only: bool = False) -> Optional[dict]:
    """Devolve um jogo aleatório da biblioteca (ou de uma consola específica)."""
    sql = "SELECT * FROM games WHERE 1=1"
    params: list = []
    if console:
        sql += " AND console = ?"
        params.append(console)
    if favorites_only:
        sql += " AND favorite = 1"
    sql += " ORDER BY RANDOM() LIMIT 1"
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def update_game(game_id: str, fields: dict) -> None:
    """Atualiza campos editáveis manualmente."""
    allowed = {"title", "console", "year", "genre", "description", "cover", "cover_locked", "favorite"}
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
        favorites = conn.execute(
            "SELECT COUNT(*) FROM games WHERE favorite = 1"
        ).fetchone()[0]
    return {"total": total, "consoles": consoles, "with_cover": with_cover, "favorites": favorites}


def missing_covers_count() -> int:
    """Devolve o número de jogos sem capa na biblioteca."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM games WHERE cover IS NULL OR cover = ''"
        ).fetchone()
    return row[0] if row else 0


# ---------------------------------------------------------------------------
# Gestão de Definições Dinâmicas (tabela settings)
# ---------------------------------------------------------------------------

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Obtém uma definição persistida na base de dados."""
    try:
        with get_conn() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return default


def set_setting(key: str, value: str) -> None:
    """Grava ou atualiza uma definição na base de dados."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
            """,
            (key, str(value)),
        )


def delete_setting(key: str) -> None:
    """Remove uma definição da base de dados, revertendo para o fallback."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        pass


def get_all_settings() -> dict[str, str]:
    """Devolve todas as definições guardadas na base de dados."""
    try:
        with get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return {}


def get_effective_config() -> dict[str, dict]:
    """Devolve as configurações do sistema com resolução em cascata (UI vs .env)."""
    db_settings = get_all_settings()

    defaults_map = {
        "steamgriddb_api_key": {
            "env": config.STEAMGRIDDB_API_KEY,
            "default": "",
            "label": "Chave API da SteamGridDB",
            "secret": True,
        },
        "twitch_client_id": {
            "env": config.TWITCH_CLIENT_ID,
            "default": "",
            "label": "Twitch Client ID (IGDB)",
            "secret": False,
        },
        "twitch_client_secret": {
            "env": config.TWITCH_CLIENT_SECRET,
            "default": "",
            "label": "Twitch Client Secret (IGDB)",
            "secret": True,
        },
        "auto_fetch_covers": {
            "env": "1",
            "default": "1",
            "label": "Descarregar capas no scan",
            "secret": False,
        },
        "auto_fetch_metadata": {
            "env": "1",
            "default": "1",
            "label": "Descarregar metadados no scan",
            "secret": False,
        },
        "game_extensions": {
            "env": ", ".join(sorted(config.GAME_EXTENSIONS)),
            "default": ", ".join(sorted(config.GAME_EXTENSIONS)),
            "label": "Extensões de ficheiros de jogos",
            "secret": False,
        },
    }

    result = {}
    for k, meta in defaults_map.items():
        db_val = db_settings.get(k)
        if db_val is not None and db_val.strip() != "":
            val = db_val.strip()
            source = "db"
        elif meta["env"]:
            val = meta["env"]
            source = "env"
        else:
            val = meta["default"]
            source = "default"

        result[k] = {
            "value": val,
            "source": source,
            "label": meta["label"],
            "secret": meta["secret"],
            "is_set_in_db": k in db_settings,
        }

    return result

