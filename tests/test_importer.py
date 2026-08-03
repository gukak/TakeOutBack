"""
Tests unitaires pour le module importer.
"""
import os
import sys
import tempfile
import zipfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.importer import TakeoutImporter
from src.core.database import Database


class TestImporter(unittest.TestCase):
    """Tests pour le module d'import."""

    def setUp(self):
        """Crée une base de données temporaire et un dossier Incoming."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test.db"
        self.incoming_dir = Path(self.test_dir) / "incoming"
        self.incoming_dir.mkdir()

        self.db = Database(db_path=self.db_path)
        self.db.initialize()

        self.importer = TakeoutImporter(database=self.db)

    def tearDown(self):
        """Nettoie les fichiers temporaires."""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def _create_test_zip(self, filename: str, content: bytes) -> Path:
        """Crée un fichier ZIP de test."""
        zip_path = self.incoming_dir / filename
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test_file.txt", content)
        return zip_path

    def test_detect_exports(self):
        """Test la détection des exports."""
        # Créer un ZIP dans le dossier Incoming réel du projet
        import shutil
        real_incoming = Path(__file__).parent.parent / "incoming"
        real_incoming.mkdir(exist_ok=True)
        zip_path = real_incoming / "test_takeout.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test_file.txt", b"test content")

        exports = self.importer.detect_exports()
        self.assertGreaterEqual(len(exports), 1)

        # Nettoyer
        zip_path.unlink()

    def test_import_simple_zip(self):
        """Test l'import d'un ZIP simple."""
        zip_path = self._create_test_zip("takeout.zip", b"test content")

        result = self.importer.import_takeout(zip_path)
        self.assertEqual(result.total_files, 1)
        self.assertEqual(len(result.errors), 0)


if __name__ == "__main__":
    unittest.main()
