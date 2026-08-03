#!/bin/bash
# Script de lancement pour Linux
# TakeOutBack - Archivage Google Takeout

echo "========================================"
echo "  TakeOutBack - Lancement"
echo "========================================"
echo ""

# Vérifier que Python portable existe
if [ ! -f "Tools/linux/python/python3" ]; then
    echo "ERREUR: Python portable introuvable!"
    echo "Exécutez setup.py pour installer les outils portables."
    exit 1
fi

# Lancer le programme avec Python portable
Tools/linux/python/python3 src/main.py "$@"
