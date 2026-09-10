"""Suite de testes unitários para o Catálogo de Jogos (sem dependências externas)."""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import config, database, logos, metadata, models, scanner
from app.metadata import is_safe_url


class TestMetadata(unittest.TestCase):
    def test_clean_title(self):
        cases = [
            ("Super_Mario_Odyssey (USA) [En].nsp", "Super Mario Odyssey"),
            ("The_Legend_of_Zelda_-_Breath_of_the_Wild_(Rev 1).xci", "The Legend of Zelda - Breath of the Wild"),
            ("Metal_Gear_Solid_[v1.1].iso", "Metal Gear Solid"),
            ("Halo_3.zip", "Halo 3"),
            ("SimpleGame.bin", "SimpleGame"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(metadata.clean_title(raw), expected)


class TestScannerFilters(unittest.TestCase):
    def test_cue_bin_deduplication(self):
        def make_entry(name, is_dir=False):
            return SimpleNamespace(
                name=name,
                is_dir=lambda: is_dir,
                is_file=lambda: not is_dir,
                path=f"/fake/{name}",
            )

        entries = [
            make_entry("Crash Bandicoot.cue"),
            make_entry("Crash Bandicoot.bin"),
            make_entry("Crash Bandicoot (Track 1).bin"),
            make_entry("Crash Bandicoot (Track 2).bin"),
            make_entry("Tekken 3.iso"),
            make_entry("Standalone.bin"),
            make_entry(".DS_Store"),
            make_entry("Halo 3", is_dir=True),
        ]

        filtered = scanner.filter_game_entries(entries)
        names = [e.name for e in filtered]

        self.assertIn("Crash Bandicoot.cue", names)
        self.assertIn("Tekken 3.iso", names)
        self.assertIn("Standalone.bin", names)
        self.assertIn("Halo 3", names)

        # Ficheiros redundantes devem ser removidos
        self.assertNotIn("Crash Bandicoot.bin", names)
        self.assertNotIn("Crash Bandicoot (Track 1).bin", names)
        self.assertNotIn("Crash Bandicoot (Track 2).bin", names)
        self.assertNotIn(".DS_Store", names)


class TestLogos(unittest.TestCase):
    def test_safe_name(self):
        self.assertEqual(logos.safe_name("Nintendo Switch"), "Nintendo Switch")
        self.assertEqual(logos.safe_name("PlayStation 2 / Pro"), "PlayStation 2 _ Pro")

    def test_initials_for(self):
        self.assertEqual(logos.initials_for("PlayStation 2"), "P2")
        self.assertEqual(logos.initials_for("Switch"), "SW")
        self.assertEqual(logos.initials_for(""), "?")

    def test_accent_for_deterministic(self):
        accent1 = logos.accent_for("Xbox 360")
        accent2 = logos.accent_for("Xbox 360")
        self.assertEqual(accent1, accent2)
        self.assertTrue(accent1.startswith("hsl("))


class TestSecurity(unittest.TestCase):
    def test_is_safe_url(self):
        unsafe_urls = [
            "http://localhost:8080/image.jpg",
            "http://127.0.0.1:5000/test.png",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/test.jpg",
            "ftp://example.com/image.png",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "http://myrouter.local/cover.jpg",
            "http://192.168.1.1/secret.png",
            "http://10.0.0.5/thumb.jpg",
        ]
        for u in unsafe_urls:
            with self.subTest(url=u):
                self.assertFalse(is_safe_url(u))

        safe_urls = [
            "https://images.igdb.com/igdb/image/upload/t_cover_big/co1r7f.png",
            "http://cdn.steamgriddb.com/grid/test.jpg",
            "https://example.com/cover.png",
        ]
        for u in safe_urls:
            with self.subTest(url=u):
                self.assertTrue(is_safe_url(u))


class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_catalog.db")
        self.patcher_db = patch.object(config, "DB_PATH", self.db_path)
        self.patcher_dir = patch.object(config, "DATA_DIR", self.temp_dir.name)
        self.patcher_thumbs = patch.object(config, "THUMBS_DIR", os.path.join(self.temp_dir.name, "thumbs"))
        self.patcher_logos = patch.object(config, "LOGOS_DIR", os.path.join(self.temp_dir.name, "logos"))
        self.patcher_db.start()
        self.patcher_dir.start()
        self.patcher_thumbs.start()
        self.patcher_logos.start()
        database.init_db()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_dir.stop()
        self.patcher_thumbs.stop()
        self.patcher_logos.stop()
        self.temp_dir.cleanup()

    def test_crud_games(self):
        # Inserir um jogo
        with database.get_conn() as conn:
            conn.execute(
                "INSERT INTO games (id, title, console, path, size_bytes) VALUES (?,?,?,?,?)",
                ("id123", "Super Mario Odyssey", "Nintendo Switch", "/games/switch/smo.nsp", 5000000),
            )

        # Listar consolas
        consoles = models.list_consoles()
        self.assertEqual(len(consoles), 1)
        self.assertEqual(consoles[0]["console"], "Nintendo Switch")
        self.assertEqual(consoles[0]["total"], 1)

        # Obter jogo
        g = models.get_game("id123")
        self.assertIsNotNone(g)
        self.assertEqual(g["title"], "Super Mario Odyssey")

        # Atualizar jogo
        models.update_game("id123", {"genre": "Platformer", "year": 2017})
        g_updated = models.get_game("id123")
        self.assertEqual(g_updated["genre"], "Platformer")
        self.assertEqual(g_updated["year"], 2017)

        # Pesquisar jogo globalmente
        results = models.list_games(console=None, search="Mario")
        self.assertEqual(len(results), 1)

        results_empty = models.list_games(console=None, search="Zelda")
        self.assertEqual(len(results_empty), 0)

        # Eliminar jogo
        deleted = models.delete_game("id123")
        self.assertTrue(deleted)
        self.assertIsNone(models.get_game("id123"))

    def test_advanced_search(self):
        with database.get_conn() as conn:
            conn.executemany(
                "INSERT INTO games (id, title, console, genre, path, size_bytes) VALUES (?,?,?,?,?,?)",
                [
                    ("g1", "Pokémon: Edição Esmeralda", "Game Boy Advance", "RPG", "/games/gba/pkmn.gba", 16000000),
                    ("g2", "The Legend of Zelda: Breath of the Wild", "Nintendo Switch", "Ação e Aventura", "/games/switch/botw.nsp", 14000000000),
                    ("g3", "Super Mario Odyssey", "Nintendo Switch", "Plataformas", "/games/switch/smo.nsp", 6000000000),
                ],
            )

        # 1. Insensibilidade a acentos
        self.assertEqual(len(models.list_games(search="pokemon")), 1)
        self.assertEqual(len(models.list_games(search="POKÉMON")), 1)
        self.assertEqual(len(models.list_games(search="esmeralda")), 1)
        self.assertEqual(len(models.list_games(search="acao")), 1)

        # 2. Pesquisa multi-palavra / tokens não contíguos
        self.assertEqual(len(models.list_games(search="zelda breath")), 1)
        self.assertEqual(len(models.list_games(search="mario odyssey")), 1)

        # 3. Pesquisa cruzada por consola e título
        self.assertEqual(len(models.list_games(search="switch mario")), 1)
        self.assertEqual(len(models.list_games(search="gba pokemon")), 1)

        # 4. Pesquisa por género e extensão/caminho
        self.assertEqual(len(models.list_games(search="rpg")), 1)
        self.assertEqual(len(models.list_games(search="nsp")), 2)

        # 5. Termo inexistente
        self.assertEqual(len(models.list_games(search="metroid")), 0)

    def test_favorites_and_random(self):
        with database.get_conn() as conn:
            conn.executemany(
                "INSERT INTO games (id, title, console, path, size_bytes) VALUES (?,?,?,?,?)",
                [
                    ("fav1", "Chrono Trigger", "SNES", "/games/snes/ct.sfc", 4000000),
                    ("fav2", "Super Mario World", "SNES", "/games/snes/smw.sfc", 1000000),
                    ("other1", "Sonic The Hedgehog", "Mega Drive", "/games/md/sonic.md", 1000000),
                ],
            )

        # Inicialmente nenhum é favorito
        st = models.stats()
        self.assertEqual(st["favorites"], 0)
        self.assertEqual(len(models.list_games(favorites_only=True)), 0)

        # Alternar fav1 para favorito
        res = models.toggle_favorite("fav1")
        self.assertTrue(res)
        g = models.get_game("fav1")
        self.assertEqual(g["favorite"], 1)

        # Stats e listagem
        st = models.stats()
        self.assertEqual(st["favorites"], 1)
        fav_list = models.list_games(favorites_only=True)
        self.assertEqual(len(fav_list), 1)
        self.assertEqual(fav_list[0]["id"], "fav1")

        # Alternar fav2
        models.toggle_favorite("fav2")
        self.assertEqual(models.stats()["favorites"], 2)

        # Filtro de favoritos com consola
        snes_favs = models.list_games(console="SNES", favorites_only=True)
        self.assertEqual(len(snes_favs), 2)
        md_favs = models.list_games(console="Mega Drive", favorites_only=True)
        self.assertEqual(len(md_favs), 0)

        # Jogo aleatório
        rnd = models.get_random_game()
        self.assertIsNotNone(rnd)
        self.assertIn(rnd["id"], ["fav1", "fav2", "other1"])

        rnd_md = models.get_random_game(console="Mega Drive")
        self.assertIsNotNone(rnd_md)
        self.assertEqual(rnd_md["id"], "other1")

        rnd_fav = models.get_random_game(favorites_only=True)
        self.assertIn(rnd_fav["id"], ["fav1", "fav2"])

        # Remover favorito
        res_off = models.toggle_favorite("fav1")
        self.assertFalse(res_off)
        self.assertEqual(models.stats()["favorites"], 1)

        # Alternar jogo inexistente
        self.assertFalse(models.toggle_favorite("nao_existe"))

    def test_database_migration(self):
        db_legacy = os.path.join(self.temp_dir.name, "legacy.db")
        with patch.object(config, "DB_PATH", db_legacy):
            with database.get_conn() as conn:
                conn.execute(
                    """
                    CREATE TABLE games (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        console TEXT NOT NULL,
                        path TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO games (id, title, console, path) VALUES ('leg1', 'Legacy Game', 'NES', '/leg.nes')"
                )
            # Ao inicializar a BD, a coluna favorite deve ser adicionada sem apagar os dados existentes
            database.init_db()
            with database.get_conn() as conn:
                cols = [r["name"] for r in conn.execute("PRAGMA table_info(games)").fetchall()]
                self.assertIn("favorite", cols)
                row = conn.execute("SELECT id, title, favorite FROM games WHERE id = 'leg1'").fetchone()
                self.assertEqual(row["title"], "Legacy Game")
                self.assertEqual(row["favorite"], 0)


if __name__ == "__main__":
    unittest.main()
