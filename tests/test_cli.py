"""
Tests unitaires pour le module CLI.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cli.menu import CLI
from src.core.database import Database


class TestCLI(unittest.TestCase):
    """Tests pour l'interface CLI."""

    def setUp(self):
        """Crée une base de données temporaire."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test.db"
        self.db = Database(db_path=self.db_path)
        self.db.initialize()

    def tearDown(self):
        """Nettoie les fichiers temporaires."""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    @patch("builtins.input", return_value="10")
    def test_menu_quit(self, mock_input):
        """Test le quitter du menu."""
        cli = CLI()
        cli.run()
        self.assertFalse(cli.running)

    @patch("builtins.input", side_effect=["1", "10"])
    def test_menu_initialize_and_quit(self, mock_input):
        """Test l'initialisation puis le quitter."""
        cli = CLI()
        cli.run()
        self.assertFalse(cli.running)


if __name__ == "__main__":
    unittest.main()
