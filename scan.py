#!/usr/bin/env python3
"""Executa um scan completo a partir da linha de comandos.

Pensado para ser chamado pelo cron / Agendador de Tarefas do Synology.

Uso:
    python3 scan.py            # scan com procura de capas
    python3 scan.py --no-cover # scan sem ir à internet buscar capas
"""
import sys

from app import config
from app.database import init_db
from app.scanner import scan


def main() -> int:
    fetch_covers = "--no-cover" not in sys.argv
    print(f"GAMES_ROOT = {config.GAMES_ROOT}")
    print(f"DB_PATH    = {config.DB_PATH}")
    init_db()
    summary = scan(fetch_covers=fetch_covers)
    print(f"Resumo: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
