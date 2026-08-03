# TakeOutBack installation script
# Downloads and installs TakeOutBack on the system
#
# Usage:
#   bash install.sh
# or:
#   curl -fsSL https://raw.githubusercontent.com/gukak/TakeOutBack/main/install.sh | bash

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

# Make all scripts executable (ZIP does not preserve permissions)
find . -name "*.sh" -exec chmod +x {} \;
chmod +x TakeOutBack/src/main.py 2>/dev/null || true

# Detect if the filesystem supports executable permissions
if [ -x "$INSTALL_DIR/TakeOutBack/TakeOutBack.sh" ]; then
    SCRIPT_PREFIX=""
    echo ""
    echo "Filesystem supports executable permissions."
else
    SCRIPT_PREFIX="bash "
    echo ""
    echo "WARNING: Filesystem does not support executable permissions"
    echo "(likely FAT32/exFAT). You must use 'bash' to run scripts."
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Created structure:"
echo "  $INSTALL_DIR/TakeOutBack/    - Software"
echo "  $INSTALL_DIR/Incoming/       - Exports to process"
echo "  $INSTALL_DIR/Archive/        - Archives"
echo ""
echo "Run TakeOutBack with:"
echo "  $SCRIPT_PREFIX$INSTALL_DIR/TakeOutBack/TakeOutBack.sh"
echo ""
echo "Non-interactive mode:"
echo "  $SCRIPT_PREFIX$INSTALL_DIR/TakeOutBack/TakeOutBack.sh import"
echo "  $SCRIPT_PREFIX$INSTALL_DIR/TakeOutBack/TakeOutBack.sh search <name>"
echo "  $SCRIPT_PREFIX$INSTALL_DIR/TakeOutBack/TakeOutBack.sh verify"
echo "  $SCRIPT_PREFIX$INSTALL_DIR/TakeOutBack/TakeOutBack.sh stats"
