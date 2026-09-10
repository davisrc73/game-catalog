import ipaddress
import os
import urllib.parse
import urllib.request

from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)

from . import config, logos, models, scanner
from .database import init_db

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # logótipos até 4 MB
init_db()


@app.context_processor
def inject_globals():
    return {"config_root": config.GAMES_ROOT}


# ----------------------------------------------------------------------------
# Páginas
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    search = request.args.get("q", "").strip() or request.args.get("search", "").strip()
    favorites = request.args.get("favorites") == "1"
    if search or favorites:
        games = models.list_games(console=None, search=search, favorites_only=favorites)
        return render_template(
            "index.html",
            search=search,
            favorites=favorites,
            games=games,
            stats=models.stats(),
            last_scan=models.last_scan(),
            scanning=scanner.is_scanning(),
        )

    consoles = []
    for c in models.list_consoles():
        name = c["console"]
        consoles.append({
            **c,
            "logo": logos.find_logo(name),
            "accent": logos.accent_for(name),
            "initials": logos.initials_for(name),
        })
    return render_template(
        "index.html",
        consoles=consoles,
        stats=models.stats(),
        last_scan=models.last_scan(),
        scanning=scanner.is_scanning(),
        favorites=False,
    )


@app.route("/search")
def search_view():
    query = request.args.get("q", "").strip()
    return redirect(url_for("index", q=query))


@app.route("/random")
def random_game():
    fav = request.args.get("favorites") == "1"
    g = models.get_random_game(console=None, favorites_only=fav)
    if not g:
        return redirect(url_for("index"))
    return redirect(url_for("game_view", game_id=g["id"]))


@app.route("/console/<console>/random")
def random_console_game(console):
    fav = request.args.get("favorites") == "1"
    g = models.get_random_game(console=console, favorites_only=fav)
    if not g:
        return redirect(url_for("console_view", console=console))
    return redirect(url_for("game_view", game_id=g["id"]))


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": [], "total": 0})
    games = models.list_games(console=None, search=q)
    results = []
    for g in games[:8]:
        results.append({
            "id": g["id"],
            "title": g["title"],
            "console": g["console"],
            "year": g.get("year"),
            "url": url_for("game_view", game_id=g["id"]),
            "cover_url": url_for("cover", filename=g["cover"]) if g.get("cover") else None,
        })
    return jsonify({"results": results, "total": len(games)})


@app.route("/console/<console>")
def console_view(console):
    search = request.args.get("q", "").strip() or None
    favorites = request.args.get("favorites") == "1"
    games = models.list_games(console=console, search=search, favorites_only=favorites)
    return render_template(
        "console.html",
        console=console,
        games=games,
        search=search or "",
        favorites=favorites,
    )


@app.route("/game/<game_id>")
def game_view(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    return render_template("game.html", game=game)


@app.route("/game/<game_id>/edit", methods=["GET", "POST"])
def game_edit(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    if request.method == "POST":
        fields = {
            "title": request.form.get("title", "").strip(),
            "console": request.form.get("console", "").strip(),
            "genre": request.form.get("genre", "").strip(),
            "description": request.form.get("description", "").strip(),
        }
        year = request.form.get("year", "").strip()
        fields["year"] = int(year) if year.isdigit() else None
        models.update_game(game_id, fields)

        # 1. Substituição opcional por upload direto de ficheiro
        cover_file = request.files.get("cover_file")
        if cover_file and cover_file.filename:
            raw_ext = os.path.splitext(cover_file.filename)[1].lower()
            if raw_ext in (".png", ".jpg", ".jpeg", ".webp"):
                filename = f"{game_id}{raw_ext}"
                cover_file.save(os.path.join(config.THUMBS_DIR, filename))
                models.update_game(game_id, {"cover": filename, "cover_locked": 1})

        # 2. Substituição alternativa por URL
        cover_url = request.form.get("cover_url", "").strip()
        if cover_url and not (cover_file and cover_file.filename):
            _save_cover_from_url(game_id, cover_url)

        return redirect(url_for("game_view", game_id=game_id))
    return render_template("edit.html", game=game)


# ----------------------------------------------------------------------------
# Capas
# ----------------------------------------------------------------------------
@app.route("/cover/<path:filename>")
def cover(filename):
    return send_from_directory(config.THUMBS_DIR, filename)


# ----------------------------------------------------------------------------
# Eliminação (remove do catálogo; NUNCA apaga ficheiros no NAS)
# ----------------------------------------------------------------------------
@app.route("/game/<game_id>/delete", methods=["POST"])
def game_delete(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    models.delete_game(game_id)
    return redirect(url_for("console_view", console=game["console"]))


@app.route("/console/<console>/delete", methods=["POST"])
def console_delete(console):
    models.delete_console(console)
    logos.delete_logo(console)
    return redirect(url_for("index"))


# ----------------------------------------------------------------------------
# Logótipos das consolas
# ----------------------------------------------------------------------------
@app.route("/logo/<console>")
def logo(console):
    fn = logos.find_logo(console)
    if not fn:
        abort(404)
    return send_from_directory(config.LOGOS_DIR, fn)


@app.route("/console/<console>/logo", methods=["POST"])
def console_logo_upload(console):
    f = request.files.get("logo")
    if f and f.filename:
        logos.save_logo(console, f.filename, f.read())
    return redirect(url_for("console_view", console=console))


def _save_cover_from_url(game_id: str, url: str) -> bool:
    """Descarrega capa de URL externo com streaming, limite de 5MB e proteção anti-SSRF."""
    if not metadata.is_safe_url(url):
        return False
    max_size = 5 * 1024 * 1024  # 5 MB
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameCatalog/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > max_size:
                return False
            chunks = []
            total_size = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size:
                    return False
                chunks.append(chunk)
            data = b"".join(chunks)

        if not data:
            return False

        parsed = urllib.parse.urlparse(url)
        raw_ext = os.path.splitext(parsed.path)[1].lower()
        ext = raw_ext if raw_ext in (".png", ".jpg", ".jpeg", ".webp") else ".jpg"
        filename = f"{game_id}{ext}"
        with open(os.path.join(config.THUMBS_DIR, filename), "wb") as f:
            f.write(data)
        models.update_game(game_id, {"cover": filename, "cover_locked": 1})
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# API / ações
# ----------------------------------------------------------------------------
@app.route("/api/scan", methods=["POST"])
def api_scan():
    started = scanner.scan_async(fetch_covers=True)
    return jsonify({"started": started, "scanning": scanner.is_scanning()})


@app.route("/api/status")
def api_status():
    return jsonify({
        "scanning": scanner.is_scanning(),
        "stats": models.stats(),
        "last_scan": models.last_scan(),
    })


@app.route("/api/game/<game_id>/favorite", methods=["POST"])
def api_toggle_favorite(game_id):
    is_fav = models.toggle_favorite(game_id)
    return jsonify({"success": True, "favorite": is_fav})


# ----------------------------------------------------------------------------
# Definições do Sistema & Diagnóstico
# ----------------------------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
def settings_view():
    if request.method == "POST":
        # 1. Atualizar chaves e extensões
        for key in ("steamgriddb_api_key", "twitch_client_id", "twitch_client_secret", "game_extensions"):
            val = request.form.get(key, "").strip()
            if val:
                models.set_setting(key, val)
            else:
                # Se o utilizador limpar o campo, remove da BD para voltar ao fallback do .env
                models.delete_setting(key)

        # 2. Opções booleanas (checkboxes)
        models.set_setting("auto_fetch_covers", "1" if request.form.get("auto_fetch_covers") else "0")
        models.set_setting("auto_fetch_metadata", "1" if request.form.get("auto_fetch_metadata") else "0")

        return redirect(url_for("settings_view", saved="1"))

    effective = models.get_effective_config()

    # Informações de diagnóstico dos volumes montados
    sources_info = []
    if config.GAME_SOURCES:
        for console, path in config.GAME_SOURCES:
            exists = os.path.isdir(path)
            game_count = len(models.list_games(console=console))
            sources_info.append({
                "console": console,
                "path": path,
                "accessible": exists,
                "games": game_count,
            })
    else:
        root = config.GAMES_ROOT
        if os.path.isdir(root):
            for e in sorted(os.scandir(root), key=lambda x: x.name.lower()):
                if e.is_dir() and e.name.lower() not in config.IGNORE_NAMES:
                    game_count = len(models.list_games(console=e.name))
                    sources_info.append({
                        "console": e.name,
                        "path": e.path,
                        "accessible": True,
                        "games": game_count,
                    })

    # Diagnóstico de armazenamento
    db_size = os.path.getsize(config.DB_PATH) if os.path.exists(config.DB_PATH) else 0
    thumbs_count = len(os.listdir(config.THUMBS_DIR)) if os.path.isdir(config.THUMBS_DIR) else 0
    missing_covers = models.missing_covers_count()

    diagnostics = {
        "sources": sources_info,
        "db_size_mb": round(db_size / (1024 * 1024), 2),
        "thumbs_count": thumbs_count,
        "missing_covers": missing_covers,
        "steamgriddb_active": bool(metadata.get_steamgriddb_key()),
        "igdb_active": metadata.is_igdb_enabled(),
        "games_root": config.GAMES_ROOT,
        "data_dir": config.DATA_DIR,
    }

    return render_template(
        "settings.html",
        config_items=effective,
        diagnostics=diagnostics,
        saved=request.args.get("saved") == "1",
    )


@app.route("/api/settings/test-steamgrid", methods=["POST"])
def api_test_steamgrid():
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip() or metadata.get_steamgriddb_key()
    ok, msg = metadata.test_steamgriddb(key)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/settings/test-igdb", methods=["POST"])
def api_test_igdb():
    data = request.get_json(silent=True) or {}
    cid = data.get("client_id", "").strip()
    csec = data.get("client_secret", "").strip()
    if not (cid and csec):
        default_cid, default_csec = metadata.get_igdb_credentials()
        cid = cid or default_cid
        csec = csec or default_csec
    ok, msg = metadata.test_igdb(cid, csec)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/maintenance/fetch-covers", methods=["POST"])
def api_fetch_covers():
    started = scanner.enrich_missing_async()
    msg = (
        "Procura de capas e metadados em falta iniciada em segundo plano."
        if started
        else "Já existe um scan ou tarefa de enriquecimento a decorrer."
    )
    return jsonify({"started": started, "message": msg})


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
