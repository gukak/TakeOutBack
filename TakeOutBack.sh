#!/bin/bash
# Script lanceur de TakeOutBack
# À placer à la racine du disque externe

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/TakeOutBack"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERREUR: Dossier TakeOutBack introuvable dans $SCRIPT_DIR"
    echo "Installez TakeOutBack avec: bash $SCRIPT_DIR/install.sh"
    exit 1
fi

cd "$PROJECT_DIR"

if [ "$1" = "import" ]; then
    echo "Import des exports Takeout..."
    python3 src/main.py --import
elif [ "$1" = "search" ]; then
    if [ -z "$2" ]; then
        echo "Usage: $0 search <nom_de_fichier>"
        exit 1
    fi
    python3 src/main.py --search "$2"
elif [ "$1" = "verify" ]; then
    echo "Vérification d'intégrité..."
    python3 src/main.py --verify
elif [ "$1" = "stats" ]; then
    python3 src/main.py --stats
elif [ "$1" = "update-tools" ]; then
    echo "Mise à jour des outils..."
    python3 src/main.py --update-tools
else
    echo "=== TakeOutBack ==="
    echo ""
    echo "Usage: $0 [commande]"
    echo ""
    echo "Commandes:"
    echo "  import              Importer les exports Takeout"
    echo "  search <nom>        Rechercher un fichier"
    echo "  verify              Vérifier l'intégrité"
    echo "  stats               Afficher les statistiques"
    echo "  update-tools        Mettre à jour les outils"
    echo "  (sans argument)     Lancer l'interface interactive"
    echo ""
    python3 src/main.py
fi
