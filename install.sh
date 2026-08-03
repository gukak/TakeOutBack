#!/bin/bash
# Script d'installation de TakeOutBack
# Télécharge et installe TakeOutBack sur le système

set -e

INSTALL_DIR="${INSTALL_DIR:-$(pwd)}"
REPO_URL="https://github.com/gukak/TakeOutBack"
ZIP_URL="https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip"

echo "=== Installation de TakeOutBack ==="
echo ""

if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERREUR: Le dossier d'installation n'existe pas: $INSTALL_DIR"
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    echo "ERREUR: Ne pas exécuter ce script en tant que root."
    exit 1
fi

cd "$INSTALL_DIR"

echo "Dossier d'installation: $INSTALL_DIR"
echo ""

if [ -d "TakeOutBack" ]; then
    echo "Un dossier TakeOutBack existe déjà."
    read -p "Voulez-vous le réinstaller ? (o/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        echo "Installation annulée."
        exit 0
    fi
    echo "Suppression de l'ancienne version..."
    rm -rf TakeOutBack
fi

echo "Téléchargement de TakeOutBack..."
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -fsSL -o takeoutback.zip"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -q -O takeoutback.zip"
else
    echo "ERREUR: curl ou wget est requis pour le téléchargement."
    exit 1
fi

$DOWNLOAD_CMD "$ZIP_URL"

if [ ! -f "takeoutback.zip" ]; then
    echo "ERREUR: Échec du téléchargement."
    exit 1
fi

echo "Décompression..."
if command -v unzip &> /dev/null; then
    unzip -q takeoutback.zip
    mv TakeOutBack-main TakeOutBack
    rm -f takeoutback.zip
elif command -v 7z &> /dev/null; then
    7z x -o. takeoutback.zip > /dev/null
    mv TakeOutBack-main TakeOutBack
    rm -f takeoutback.zip
else
    python3 -c "import zipfile; zipfile.ZipFile('takeoutback.zip').extractall('.')"
    mv TakeOutBack-main TakeOutBack
    rm -f takeoutback.zip
fi

if [ ! -d "TakeOutBack" ]; then
    echo "ERREUR: Échec de la décompression."
    exit 1
fi

chmod +x TakeOutBack/TakeOutBack.sh 2>/dev/null || true

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Structure créée :"
echo "  $INSTALL_DIR/TakeOutBack/    - Logiciel"
echo "  $INSTALL_DIR/Incoming/       - Exports à traiter"
echo "  $INSTALL_DIR/Archive/        - Archives"
echo ""
echo "Lancez TakeOutBack avec:"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh"
echo ""
echo "Ou en mode non-interactive:"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh import"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh search <nom>"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh verify"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh stats"
