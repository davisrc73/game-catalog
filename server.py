#!/usr/bin/env python3
"""Servidor de produção usando waitress (puro Python, leve, ideal para ARM).

Uso:
    python3 server.py
"""
from waitress import serve

from app import config
from app.app import app

if __name__ == "__main__":
    print(f"Catálogo a correr em http://{config.HOST}:{config.PORT}")
    # 2 threads chegam para uso doméstico e poupam RAM no DS220+.
    serve(app, host=config.HOST, port=config.PORT, threads=2)
