"""Acesso à base de dados SQLite.

Mantém-se propositadamente simples (sem ORM) para ser leve no DS220+.
Usa-se WAL para melhor concorrência entre o scan e a leitura no browser.
"""
import os
import sqlite3
import unicodedata
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id          TEXT PRIMARY KEY,         -- hash estável (consola + caminho relativo)
    title       TEXT NOT NULL,
    console     TEXT NOT NULL,
    path        TEXT NOT NULL,            -- caminho absoluto no NAS
    cover       TEXT,                     -- nome do ficheiro da capa em THUMBS_DIR
    year        INTEGER,
    genre       TEXT,
    description TEXT,
    size_bytes  INTEGER DEFAULT 0,
    cover_locked INTEGER DEFAULT 0,       -- 1 = capa definida à mão, o scan não substitui
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_games_console ON games(console);
CREATE INDEX IF NOT EXISTS idx_games_title   ON games(title);

CREATE TABLE IF NOT EXISTS scans (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT DEFAULT (datetime('now')),
    ended_at   TEXT,
    added      INTEGER DEFAULT 0,
    updated    INTEGER DEFAULT 0,
    removed    INTEGER DEFAULT 0,
    status     TEXT DEFAULT 'running'
);
"""


def normalize_text(text: str | None) -> str:
    """Normaliza texto removendo acentos e convertendo para minúsculas."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def init_db() -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.THUMBS_DIR, exist_ok=True)
    os.makedirs(config.LOGOS_DIR, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.create_function("norm", 1, normalize_text)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
