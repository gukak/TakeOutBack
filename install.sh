#!/bin/bash
# TakeOutBack installation script
# Downloads and installs TakeOutBack on the system

set -e

INSTALL_DIR="${INSTALL_DIR:-$(pwd)}"
REPO_URL="https://github.com/gukak/TakeOutBack"
ZIP_URL="https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip"

echo "=== TakeOutBack Installation ==="
echo ""

if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERROR: Installation directory does not exist: $INSTALL_DIR"
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: Do not run this script as root."
    exit 1
fi

cd "$INSTALL_DIR"

echo "Installation directory: $INSTALL_DIR"
echo ""

if [ -d "TakeOutBack" ]; then
    echo "TakeOutBack directory already exists."
    read -p "Do you want to reinstall? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "Removing old version..."
    rm -rf TakeOutBack
fi

echo "Downloading TakeOutBack..."
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -fsSL -o takeoutback.zip"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -q -O takeoutback.zip"
else
    echo "ERROR: curl or wget is required for download."
    exit 1
fi

$DOWNLOAD_CMD "$ZIP_URL"

if [ ! -f "takeoutback.zip" ]; then
    echo "ERROR: Download failed."
    exit 1
fi

echo "Extracting..."
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
    echo "ERROR: Decompression failed."
    exit 1
fi

# Make all scripts executable
chmod +x TakeOutBack/TakeOutBack.sh
chmod +x TakeOutBack/src/main.py 2>/dev/null || true

echo ""
echo "=== Installation complete ==="
echo ""
echo "Created structure:"
echo "  $INSTALL_DIR/TakeOutBack/    - Software"
echo "  $INSTALL_DIR/Incoming/       - Exports to process"
echo "  $INSTALL_DIR/Archive/        - Archives"
echo ""
echo "Run TakeOutBack with:"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh"
echo ""
echo "Or in non-interactive mode:"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh import"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh search <name>"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh verify"
echo "  $INSTALL_DIR/TakeOutBack/TakeOutBack.sh stats"
