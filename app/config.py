"""Configuração central da aplicação.

Tudo é lido a partir de variáveis de ambiente para facilitar a execução
em Docker. Existem valores por omissão sensatos para correr em modo nativo.
"""
import os


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Pasta-raiz onde estão as consolas (cada subpasta = uma consola).
# Usada apenas quando GAME_SOURCES não está definido.
GAMES_ROOT = os.environ.get("GAMES_ROOT", "/volume1/jogos")


def _parse_sources(raw: str) -> list[tuple[str, str]]:
    """Lê 'Consola=/caminho' (um par por linha ou separados por ';').

    Exemplo:
        Nintendo Switch=/games/switch
        Xbox 360=/games/xbox360
    """
    sources: list[tuple[str, str]] = []
    for chunk in raw.replace(";", "\n").splitlines():
        chunk = chunk.strip()
        if not chunk or chunk.startswith("#") or "=" not in chunk:
            continue
        name, path = chunk.split("=", 1)
        name, path = name.strip(), path.strip()
        if name and path:
            sources.append((name, path))
    return sources


# Mapeamento explícito de consolas para caminhos arbitrários (volumes diferentes).
# Se estiver definido, tem prioridade sobre GAMES_ROOT.
GAME_SOURCES = _parse_sources(os.environ.get("GAME_SOURCES", ""))

# Onde guardar a base de dados SQLite
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "catalog.db"))

# Onde guardar as miniaturas/capas descarregadas
THUMBS_DIR = os.environ.get("THUMBS_DIR", os.path.join(DATA_DIR, "thumbnails"))

# Onde guardar os logótipos das consolas (carregados pelo utilizador)
LOGOS_DIR = os.environ.get("LOGOS_DIR", os.path.join(DATA_DIR, "logos"))

# Extensões consideradas "jogo" quando o item é um ficheiro.
# Se vazio, qualquer ficheiro conta. Pastas contam sempre como um jogo.
_ext = os.environ.get(
    "GAME_EXTENSIONS",
    ".nsp,.xci,.iso,.cso,.chd,.zip,.7z,.rom,.bin,.cue,.wbfs,.rvz,.nes,.sfc,.smc,.gba,.gb,.gbc,.n64,.z64,.nds,.3ds,.cia,.pkg",
)
GAME_EXTENSIONS = {e.strip().lower() for e in _ext.split(",") if e.strip()}

# Ficheiros a ignorar sempre durante o scan
IGNORE_NAMES = {".ds_store", "thumbs.db", "@eadir", "#recycle", "desktop.ini"}

# API de capas. Atualmente suportado: SteamGridDB (simples, só precisa de chave).
# Obtém uma chave gratuita em https://www.steamgriddb.com/profile/preferences/api
STEAMGRIDDB_API_KEY = os.environ.get("STEAMGRIDDB_API_KEY", "").strip()

# Metadados (ano, género, descrição) via IGDB. Autenticação pela Twitch:
# cria uma app em https://dev.twitch.tv/console/apps para obter Client ID/Secret.
TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "").strip()
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET", "").strip()
IGDB_ENABLED = bool(TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET)

# Servidor web
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8088"))

# Mostrar stack traces no browser (apenas para desenvolvimento)
DEBUG = _bool("DEBUG", False)
