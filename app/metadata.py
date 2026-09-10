"""Obtenção de capas e metadados online, e limpeza de títulos.

- Capas: SteamGridDB (opcional, via STEAMGRIDDB_API_KEY).
- Metadados (ano, género, descrição): IGDB (opcional, via credenciais Twitch).

Tudo é opcional: sem credenciais, as funções não fazem nada e o scan continua.
"""
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import config

# Etiquetas de região/revisão comuns em nomes de ROM, removidas para a pesquisa
_TAG_RE = re.compile(r"[\(\[][^\)\]]*[\)\]]")          # (USA), [!], (Rev 1)...
_SEP_RE = re.compile(r"[._]+")                          # pontos/underscores -> espaço
_MULTISPACE_RE = re.compile(r"\s{2,}")
_USER_AGENT = "GameCatalog/1.0 (+https://localhost)"


def clean_title(filename: str) -> str:
    """Transforma 'Super_Mario_Odyssey (USA) [En].nsp' em 'Super Mario Odyssey'."""
    name = os.path.splitext(filename)[0]
    name = _TAG_RE.sub(" ", name)
    name = _SEP_RE.sub(" ", name)
    name = _MULTISPACE_RE.sub(" ", name).strip()
    return name or filename


def _http_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        import json
        return json.loads(resp.read().decode("utf-8"))


def _http_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_cover_bytes(title: str) -> tuple[bytes, str] | None:
    """Devolve (conteúdo_da_imagem, extensão) ou None se não encontrar.

    Usa a API do SteamGridDB: procura o jogo por nome e descarrega a primeira
    grelha (capa vertical) disponível.
    """
    if not config.STEAMGRIDDB_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {config.STEAMGRIDDB_API_KEY}",
        "User-Agent": _USER_AGENT,
    }
    try:
        q = urllib.parse.quote(title)
        search = _http_json(
            f"https://www.steamgriddb.com/api/v2/search/autocomplete/{q}", headers
        )
        results = search.get("data") or []
        if not results:
            return None
        game_id = results[0]["id"]

        grids = _http_json(
            f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}"
            "?dimensions=600x900,342x482&types=static&limit=1",
            headers,
        )
        items = grids.get("data") or []
        if not items:
            return None
        img_url = items[0]["url"]
        ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1] or ".png"
        return _http_bytes(img_url), ext
    except Exception:
        # Falha de rede / API: não interromper o scan por causa de uma capa.
        return None


def save_cover(game_id: str, title: str) -> str | None:
    """Procura e grava a capa em THUMBS_DIR. Devolve o nome do ficheiro ou None."""
    result = fetch_cover_bytes(title)
    if not result:
        return None
    data, ext = result
    filename = f"{game_id}{ext.lower()}"
    dest = os.path.join(config.THUMBS_DIR, filename)
    with open(dest, "wb") as f:
        f.write(data)
    return filename


# ---------------------------------------------------------------------------
# IGDB (metadados: ano, género, descrição) — autenticação via Twitch OAuth
# ---------------------------------------------------------------------------
_TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_IGDB_GAMES_URL = "https://api.igdb.com/v4/games"

# Cache do token em memória (partilhado entre threads do servidor).
_token_lock = threading.Lock()
_token_cache = {"value": None, "expires_at": 0.0}


def _http_post(url: str, data: bytes, headers: dict) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_igdb_token() -> str | None:
    """Obtém (e reutiliza) um token de aplicação da Twitch para o IGDB."""
    if not config.IGDB_ENABLED:
        return None
    with _token_lock:
        now = time.time()
        if _token_cache["value"] and now < _token_cache["expires_at"]:
            return _token_cache["value"]
        params = urllib.parse.urlencode({
            "client_id": config.TWITCH_CLIENT_ID,
            "client_secret": config.TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }).encode("utf-8")
        try:
            resp = _http_post(_TWITCH_TOKEN_URL, params,
                              {"User-Agent": _USER_AGENT})
        except Exception:
            return None
        token = resp.get("access_token")
        if not token:
            return None
        # Renovar com margem (a Twitch devolve expires_in em segundos).
        ttl = int(resp.get("expires_in", 3600))
        _token_cache["value"] = token
        _token_cache["expires_at"] = now + max(60, ttl - 300)
        return token


def _igdb_query(token: str, body: str) -> list:
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "text/plain",
        "User-Agent": _USER_AGENT,
    }
    req = urllib.request.Request(_IGDB_GAMES_URL, data=body.encode("utf-8"),
                                headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_metadata(title: str) -> dict | None:
    """Procura no IGDB e devolve {'year', 'genre', 'description'} ou None.

    Só são devolvidos os campos que o IGDB tiver; o chamador decide o que usar.
    """
    token = _get_igdb_token()
    if not token:
        return None

    safe = title.replace('"', " ").strip()
    if not safe:
        return None
    # Linguagem "apicalypse" do IGDB: pesquisa por nome e expande géneros.
    body = (
        f'search "{safe}"; '
        "fields name, summary, first_release_date, genres.name; "
        "limit 1;"
    )
    try:
        results = _igdb_query(token, body)
    except Exception:
        return None
    if not results:
        return None

    g = results[0]
    out: dict = {}

    ts = g.get("first_release_date")
    if isinstance(ts, (int, float)):
        out["year"] = datetime.fromtimestamp(ts, tz=timezone.utc).year

    genres = g.get("genres") or []
    names = [x.get("name") for x in genres if isinstance(x, dict) and x.get("name")]
    if names:
        out["genre"] = ", ".join(names)

    summary = g.get("summary")
    if summary:
        out["description"] = summary.strip()

    return out or None
