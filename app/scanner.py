"""Scan das pastas do NAS e sincronização com a base de dados.

Cada subpasta de GAMES_ROOT é tratada como uma consola. Cada item imediato
dentro dessa subpasta (ficheiro com extensão válida OU pasta) é um jogo.

O ID de cada jogo é um hash estável de (consola + caminho relativo), por isso
mover/renomear um jogo conta como remover o antigo e adicionar um novo.
"""
import hashlib
import os
import threading
import time

from . import config, metadata
from .database import get_conn

# Evita dois scans em simultâneo (importante com pouca RAM)
_scan_lock = threading.Lock()


def is_scanning() -> bool:
    locked = _scan_lock.locked()
    return locked


def _game_id(console: str, rel_path: str) -> str:
    raw = f"{console}\x00{rel_path}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _iter_sources(log=print) -> list[tuple[str, str]]:
    """Devolve [(consola, caminho)] a partir da configuração.

    - Se GAME_SOURCES estiver definido, usa esse mapeamento explícito
      (suporta consolas em volumes/caminhos completamente diferentes).
    - Caso contrário, cada subpasta de GAMES_ROOT é uma consola (modo clássico).

    Caminhos inexistentes são ignorados com aviso (p.ex. USB desligado),
    para não apagar do catálogo jogos cujo volume está temporariamente offline.
    """
    sources: list[tuple[str, str]] = []
    if config.GAME_SOURCES:
        for console, path in config.GAME_SOURCES:
            if os.path.isdir(path):
                sources.append((console, path))
            else:
                log(f"  AVISO: origem indisponível, ignorada: {console} -> {path}")
    else:
        root = config.GAMES_ROOT
        if not os.path.isdir(root):
            raise FileNotFoundError(f"GAMES_ROOT não existe: {root}")
        for e in os.scandir(root):
            if e.is_dir() and e.name.lower() not in config.IGNORE_NAMES:
                sources.append((e.name, e.path))
    return sources


def get_active_extensions() -> set[str]:
    """Devolve o conjunto de extensões de ficheiro de jogo ativas."""
    from . import models
    val = models.get_setting("game_extensions")
    if val is not None and val.strip():
        return {e.strip().lower() for e in val.split(",") if e.strip()}
    return config.GAME_EXTENSIONS


def is_auto_fetch_covers_enabled() -> bool:
    """Verifica se o descarregamento automático de capas está ativo."""
    from . import models
    return models.get_setting("auto_fetch_covers", "1") == "1"


def is_auto_fetch_metadata_enabled() -> bool:
    """Verifica se o descarregamento automático de metadados está ativo."""
    from . import models
    return models.get_setting("auto_fetch_metadata", "1") == "1"


def _is_game_entry(entry: os.DirEntry) -> bool:
    name = entry.name.lower()
    if name in config.IGNORE_NAMES or name.startswith("."):
        return False
    if entry.is_dir():
        return True
    exts = get_active_extensions()
    if not exts:
        return True
    ext = os.path.splitext(name)[1]
    return ext in exts


def filter_game_entries(entries: list[os.DirEntry]) -> list[os.DirEntry]:
    """Filtra itens válidos e remove ficheiros .bin redundantes se houver .cue correspondente.

    Exemplo: se existir 'Game.cue', ficheiros como 'Game.bin', 'Game (Track 1).bin',
    'Game (Track 2).bin' são ignorados para não poluir o catálogo com jogos duplicados.
    """
    valid = [e for e in entries if _is_game_entry(e)]
    cue_bases = {
        os.path.splitext(e.name.lower())[0]
        for e in valid
        if not e.is_dir() and e.name.lower().endswith(".cue")
    }
    if not cue_bases:
        return valid

    filtered = []
    for e in valid:
        if not e.is_dir() and e.name.lower().endswith(".bin"):
            bin_base = os.path.splitext(e.name.lower())[0]
            # Se o .bin pertencer a qualquer .cue na mesma pasta, ignorar
            if any(bin_base == cb or bin_base.startswith(cb) for cb in cue_bases):
                continue
        filtered.append(e)
    return filtered


def _entry_size(entry: os.DirEntry) -> int:
    try:
        if entry.is_file():
            return entry.stat().st_size
        total = 0
        for root, _dirs, files in os.walk(entry.path):
            for fn in files:
                try:
                    total += os.path.getsize(os.path.join(root, fn))
                except OSError:
                    pass
        return total
    except OSError:
        return 0


def scan(fetch_covers: bool = True, log=print) -> dict:
    """Executa um scan completo. Devolve um resumo {added, updated, removed}."""
    if not _scan_lock.acquire(blocking=False):
        log("Scan já em curso — ignorado.")
        return {"added": 0, "updated": 0, "removed": 0, "skipped": True}

    summary = {"added": 0, "updated": 0, "removed": 0}
    scan_id = None
    try:
        with get_conn() as conn:
            cur = conn.execute("INSERT INTO scans DEFAULT VALUES")
            scan_id = cur.lastrowid

        seen_ids: set[str] = set()

        # Origens das consolas (mapeamento explícito ou subpastas de GAMES_ROOT)
        sources = _iter_sources(log)
        if not sources:
            log("Nenhuma origem de jogos disponível para analisar.")

        with get_conn() as conn:
            existing = {
                r["id"]: dict(r)
                for r in conn.execute("SELECT * FROM games").fetchall()
            }

            for console, cpath in sources:
                log(f"A analisar consola: {console}  ({cpath})")
                try:
                    raw_entries = list(os.scandir(cpath))
                except OSError as e:
                    log(f"  erro a ler {console}: {e}")
                    continue

                for entry in filter_game_entries(raw_entries):
                    # ID estável por (consola + nome do item): independente do
                    # volume físico, por isso sobreviver a mudanças de volumeUSBx.
                    gid = _game_id(console, entry.name)
                    seen_ids.add(gid)
                    title = metadata.clean_title(entry.name)
                    size = _entry_size(entry)

                    if gid in existing:
                        # Atualizar apenas o que pode ter mudado pelo scan
                        prev = existing[gid]
                        if prev["path"] != entry.path or prev["size_bytes"] != size:
                            conn.execute(
                                "UPDATE games SET path=?, size_bytes=?, "
                                "updated_at=datetime('now') WHERE id=?",
                                (entry.path, size, gid),
                            )
                            summary["updated"] += 1
                    else:
                        conn.execute(
                            "INSERT INTO games (id, title, console, path, size_bytes) "
                            "VALUES (?,?,?,?,?)",
                            (gid, title, console, entry.path, size),
                        )
                        summary["added"] += 1
                        log(f"  + {title}")

            # Remover apenas jogos de consolas que foram REALMENTE analisadas
            # neste scan. Assim, um volume offline (USB desligado) não faz com
            # que os seus jogos desapareçam do catálogo.
            scanned_consoles = {console for console, _ in sources}
            to_remove = [
                gid for gid, g in existing.items()
                if gid not in seen_ids and g["console"] in scanned_consoles
            ]
            for gid in to_remove:
                cover = existing[gid].get("cover")
                if cover:
                    _delete_cover(cover)
                conn.execute("DELETE FROM games WHERE id=?", (gid,))
            summary["removed"] = len(to_remove)
            if to_remove:
                log(f"  - {len(to_remove)} jogo(s) removido(s)")

        # Enriquecer (metadados + capas) fora da transação principal — é lento
        # por causa da rede. O parâmetro fetch_covers mantém o nome por
        # compatibilidade, mas controla todo o enriquecimento online.
        if fetch_covers:
            _enrich_missing(log)

        with get_conn() as conn:
            conn.execute(
                "UPDATE scans SET ended_at=datetime('now'), added=?, updated=?, "
                "removed=?, status='done' WHERE id=?",
                (summary["added"], summary["updated"], summary["removed"], scan_id),
            )
        log(f"Scan concluído: {summary}")
        return summary

    except Exception as e:
        if scan_id is not None:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE scans SET ended_at=datetime('now'), status=? WHERE id=?",
                    (f"error: {e}", scan_id),
                )
        log(f"Erro no scan: {e}")
        raise
    finally:
        _scan_lock.release()


def _enrich_missing(log=print, force_covers: bool = False, force_meta: bool = False) -> None:
    """Preenche capa (SteamGridDB) e metadados (IGDB) nos jogos a que faltam.

    Regra de ouro: os metadados só preenchem campos VAZIOS. Assim, qualquer
    correção manual feita na página de edição nunca é sobreposta pelo scan.
    """
    igdb_on = metadata.is_igdb_enabled() and (force_meta or is_auto_fetch_metadata_enabled())
    sgdb_on = bool(metadata.get_steamgriddb_key()) and (force_covers or is_auto_fetch_covers_enabled())
    if not (igdb_on or sgdb_on):
        return

    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, title, cover, cover_locked, year, genre, description "
            "FROM games WHERE "
            "  (cover IS NULL OR cover = '') "
            "  OR year IS NULL OR genre IS NULL OR genre = '' "
            "  OR description IS NULL OR description = ''"
        ).fetchall()]

    for r in rows:
        updates: dict = {}

        # --- Metadados (IGDB), apenas para campos em falta ---
        need_meta = igdb_on and (
            r["year"] is None or not r["genre"] or not r["description"]
        )
        if need_meta:
            meta = metadata.fetch_metadata(r["title"])
            if meta:
                if r["year"] is None and meta.get("year"):
                    updates["year"] = meta["year"]
                if not r["genre"] and meta.get("genre"):
                    updates["genre"] = meta["genre"]
                if not r["description"] and meta.get("description"):
                    updates["description"] = meta["description"]

        # --- Capa (SteamGridDB), se não existe e não está fixada à mão ---
        if sgdb_on and not r["cover"] and not r["cover_locked"]:
            filename = metadata.save_cover(r["id"], r["title"])
            if filename:
                updates["cover"] = filename

        if updates:
            sets = ", ".join(f"{k}=?" for k in updates)
            params = list(updates.values()) + [r["id"]]
            with get_conn() as conn:
                conn.execute(
                    f"UPDATE games SET {sets}, updated_at=datetime('now') WHERE id=?",
                    params,
                )
            log(f"  enriquecido: {r['title']} ({', '.join(updates.keys())})")

        # Respeitar o limite do IGDB (~4 pedidos/seg).
        if igdb_on:
            time.sleep(0.3)


def _delete_cover(filename: str) -> None:
    try:
        os.remove(os.path.join(config.THUMBS_DIR, filename))
    except OSError:
        pass


def scan_async(fetch_covers: bool = True) -> bool:
    """Lança o scan numa thread. Devolve False se já estiver a decorrer."""
    if is_scanning():
        return False
    t = threading.Thread(target=scan, kwargs={"fetch_covers": fetch_covers}, daemon=True)
    t.start()
    return True


def enrich_missing_async() -> bool:
    """Lança o enriquecimento de capas e metadados numa thread independente.

    Devolve False se já existir um scan ou enriquecimento a decorrer.
    """
    if is_scanning():
        return False

    def _worker():
        if not _scan_lock.acquire(blocking=False):
            return
        try:
            _enrich_missing(log=print, force_covers=True, force_meta=True)
        finally:
            _scan_lock.release()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return True
