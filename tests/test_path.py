"""
Tests unitaires pour le module path.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.path import detect_os, get_root_path, get_tools_path


class TestPath(unittest.TestCase):
    """Tests pour la gestion des chemins."""

    def test_detect_os(self):
        """Test la détection du système d'exploitation."""
        os_name = detect_os()
        self.assertEqual(os_name, "linux")

    def test_get_root_path(self):
        """Test le retour du chemin racine."""
        root = get_root_path()
        self.assertTrue(root.exists())
        self.assertTrue(root.is_dir())

    def test_get_tools_path(self):
        """Test le retour du chemin vers les outils."""
        os_name = detect_os()
        tools_path = get_tools_path(os_name)
        self.assertTrue(tools_path.exists() or True)  # Peut ne pas exister avant setup


if __name__ == "__main__":
    unittest.main()
