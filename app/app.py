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
    q = request.args.get("q", "").strip()
    if q:
        return redirect(url_for("search_view", q=q))
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
    )


@app.route("/search")
def search_view():
    query = request.args.get("q", "").strip()
    games = models.list_games(console=None, search=query) if query else []
    catalog_total = models.stats().get("total", 0)
    return render_template(
        "search.html",
        query=query,
        games=games,
        catalog_total=catalog_total,
    )


@app.route("/console/<console>")
def console_view(console):
    search = request.args.get("q", "").strip() or None
    games = models.list_games(console=console, search=search)
    return render_template("console.html", console=console, games=games, search=search or "")


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

        # Substituição opcional da capa por URL
        cover_url = request.form.get("cover_url", "").strip()
        if cover_url:
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


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
