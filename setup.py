"""
Script d'installation initiale de TakeOutBack.
Crée l'arborescence, télécharge les outils portables, initialise la base.
"""
import sys
import os
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import run_setup


if __name__ == "__main__":
    print("=" * 60)
    print("  TakeOutBack - Installation initiale")
    print("=" * 60)
    print()

    run_setup()

    print()
    print("=" * 60)
    print("  Installation terminée!")
    print("=" * 60)
    print()
    print("Pour lancer TakeOutBack:")
    print("  python src/main.py")
    print()
