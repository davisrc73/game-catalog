"""Logótipos das consolas para o dashboard.

Estratégia sem problemas de direitos de imagem: o utilizador fornece o seu
próprio logótipo (carregado pelo portal ou colocado em LOGOS_DIR). Quando não
há logótipo, mostra-se um monograma com uma cor determinística derivada do nome
da consola — fica sempre com aspeto intencional, e funciona offline.
"""
import glob
import hashlib
import os
import re

from . import config

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def safe_name(console: str) -> str:
    """Nome de ficheiro seguro e estável a partir do nome da consola."""
    s = re.sub(r"[^A-Za-z0-9 _-]", "_", console).strip()
    return s or "console"


def find_logo(console: str) -> str | None:
    """Devolve o nome do ficheiro de logótipo da consola, se existir."""
    base = safe_name(console)
    for ext in ALLOWED_EXT:
        if os.path.isfile(os.path.join(config.LOGOS_DIR, base + ext)):
            return base + ext
    return None


def save_logo(console: str, filename: str, data: bytes) -> str | None:
    """Grava um logótipo carregado. Devolve o nome final ou None se inválido."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT or not data:
        return None
    base = safe_name(console)
    # Remover qualquer logótipo anterior desta consola (qualquer extensão).
    for old in glob.glob(os.path.join(config.LOGOS_DIR, base + ".*")):
        try:
            os.remove(old)
        except OSError:
            pass
    dest_name = base + ext
    with open(os.path.join(config.LOGOS_DIR, dest_name), "wb") as f:
        f.write(data)
    return dest_name


def delete_logo(console: str) -> None:
    base = safe_name(console)
    for old in glob.glob(os.path.join(config.LOGOS_DIR, base + ".*")):
        try:
            os.remove(old)
        except OSError:
            pass


def accent_for(console: str) -> str:
    """Cor determinística (HSL) a partir do nome — igual em cada arranque."""
    h = int(hashlib.sha1(console.encode("utf-8")).hexdigest(), 16) % 360
    return f"hsl({h}, 55%, 58%)"


def initials_for(console: str) -> str:
    words = [w for w in re.split(r"\s+", console.strip()) if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()
