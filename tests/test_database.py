"""
Tests unitaires pour le module database.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.database import Database


class TestDatabase(unittest.TestCase):
    """Tests pour la classe Database."""

    def setUp(self):
        """Crée une base de données temporaire pour les tests."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test.db"
        self.db = Database(db_path=self.db_path)
        self.db.initialize()

    def tearDown(self):
        """Nettoie les fichiers temporaires."""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def test_initialize(self):
        """Test l'initialisation de la base de données."""
        self.assertTrue(self.db_path.exists())

    def test_add_and_get_file(self):
        """Test l'ajout et la récupération d'un fichier."""
        file_id = self.db.add_file(
            logical_path="Photos/test.jpg",
            filename="test.jpg",
            extension="jpg",
            size=1024,
            crc32=12345,
            discovery_date="2024-01-01",
            last_observed="2024-01-01",
            created_at="2024-01-01",
        )
        self.assertIsNotNone(file_id)

        file_info = self.db.get_file_by_path("Photos/test.jpg")
        self.assertIsNotNone(file_info)
        self.assertEqual(file_info["filename"], "test.jpg")
        self.assertEqual(file_info["size"], 1024)

    def test_add_version(self):
        """Test l'ajout d'une version."""
        file_id = self.db.add_file(
            logical_path="Photos/test.jpg",
            filename="test.jpg",
            extension="jpg",
            size=1024,
            discovery_date="2024-01-01",
            last_observed="2024-01-01",
            created_at="2024-01-01",
        )

        version_id = self.db.add_version(
            file_id=file_id,
            version=1,
            archive_path="Archive/test.jpg",
            logical_path="Photos/test.jpg",
            size=1024,
            is_current=True,
        )
        self.assertIsNotNone(version_id)

        current = self.db.get_current_version(file_id)
        self.assertIsNotNone(current)
        self.assertTrue(current["is_current"])

    def test_search_files(self):
        """Test la recherche de fichiers."""
        self.db.add_file(
            logical_path="Photos/vacation.jpg",
            filename="vacation.jpg",
            extension="jpg",
            size=2048,
            discovery_date="2024-01-01",
            last_observed="2024-01-01",
            created_at="2024-01-01",
        )
        self.db.add_file(
            logical_path="Documents/report.pdf",
            filename="report.pdf",
            extension="pdf",
            size=4096,
            discovery_date="2024-02-01",
            last_observed="2024-02-01",
            created_at="2024-02-01",
        )

        results = self.db.search_files(extension="jpg")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "vacation.jpg")

    def test_get_statistics(self):
        """Test les statistiques."""
        self.db.add_file(
            logical_path="test1.txt",
            filename="test1.txt",
            extension="txt",
            size=100,
            discovery_date="2024-01-01",
            last_observed="2024-01-01",
            created_at="2024-01-01",
        )
        self.db.add_file(
            logical_path="test2.txt",
            filename="test2.txt",
            extension="txt",
            size=200,
            discovery_date="2024-01-02",
            last_observed="2024-01-02",
            created_at="2024-01-02",
        )

        stats = self.db.get_statistics()
        self.assertEqual(stats["total_files"], 2)
        self.assertEqual(stats["total_size"], 300)

    def test_verify_integrity(self):
        """Test la vérification d'intégrité."""
        result = self.db.verify_integrity()
        self.assertTrue(result["database_ok"])


if __name__ == "__main__":
    unittest.main()
