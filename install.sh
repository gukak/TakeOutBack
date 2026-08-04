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

# Move launcher script to drive root
if [ -f "TakeOutBack/TakeOutBack.sh" ]; then
    mv "TakeOutBack/TakeOutBack.sh" "."
fi

# Make all scripts executable (ZIP does not preserve permissions)
find . -name "*.sh" -exec chmod +x {} \;
chmod +x TakeOutBack/src/main.py 2>/dev/null || true

# Create Incoming/ and Archive/ at drive root
mkdir -p Incoming Archive

# Download and install portable tools
echo ""
echo "=== Installing portable tools ==="
echo ""

TOOLS_DIR="$INSTALL_DIR/TakeOutBack/tools/linux"
PYTHON_DIR="$TOOLS_DIR/python"
SEVENZIP_DIR="$TOOLS_DIR/7zip"

# Download Python (try multiple versions as fallback)
echo "Downloading Python..."
PYTHON_URLS=(
    "https://www.python.org/ftp/python/3.11.5/Python-3.11.5.tgz"
    "https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz"
    "https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz"
)
PYTHON_DOWNLOADED=0

for url in "${PYTHON_URLS[@]}"; do
    if command -v curl &> /dev/null; then
        curl -fsSL -o python_embed.tar.xz "$url" 2>/dev/null && { PYTHON_DOWNLOADED=1; echo "Python downloaded."; break; }
    elif command -v wget &> /dev/null; then
        wget -q -O python_embed.tar.xz "$url" 2>/dev/null && { PYTHON_DOWNLOADED=1; echo "Python downloaded."; break; }
    fi
done

if [ "$PYTHON_DOWNLOADED" -eq 1 ] && [ -f "python_embed.tar.xz" ]; then
    mkdir -p "$PYTHON_DIR"
    tar -xJf python_embed.tar.xz -C "$PYTHON_DIR"
    rm -f python_embed.tar.xz
    echo "Python installed."
else
    echo "ERROR: Could not download any Python version."
    exit 1
fi

# Download 7-Zip (try multiple versions as fallback)
echo "Downloading 7-Zip..."
SEVENZIP_URLS=(
    "https://www.7-zip.org/a/7z2301-linux-x64.tar.xz"
    "https://www.7-zip.org/a/7z2201-linux-x64.tar.xz"
    "https://www.7-zip.org/a/7z1900-linux-x64.tar.xz"
)
SEVENZIP_DOWNLOADED=0

for url in "${SEVENZIP_URLS[@]}"; do
    if command -v curl &> /dev/null; then
        curl -fsSL -o 7z.tar.xz "$url" 2>/dev/null && { SEVENZIP_DOWNLOADED=1; echo "7-Zip downloaded."; break; }
    elif command -v wget &> /dev/null; then
        wget -q -O 7z.tar.xz "$url" 2>/dev/null && { SEVENZIP_DOWNLOADED=1; echo "7-Zip downloaded."; break; }
    fi
done

if [ "$SEVENZIP_DOWNLOADED" -eq 1 ] && [ -f "7z.tar.xz" ]; then
    mkdir -p "$SEVENZIP_DIR"
    tar -xJf 7z.tar.xz -C "$SEVENZIP_DIR"
    rm -f 7z.tar.xz
    echo "7-Zip installed."
else
    echo "ERROR: Could not download any 7-Zip version."
    exit 1
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Created structure:"
echo "  $INSTALL_DIR/TakeOutBack.sh  - Launcher script"
echo "  $INSTALL_DIR/TakeOutBack/    - Software"
echo "  $INSTALL_DIR/Incoming/       - Drop Takeout exports here"
echo "  $INSTALL_DIR/Archive/        - Compressed archives"
echo ""
echo "Run TakeOutBack with:"
echo "  bash $INSTALL_DIR/TakeOutBack.sh"
echo ""
echo "Non-interactive mode:"
echo "  bash $INSTALL_DIR/TakeOutBack.sh import"
echo "  bash $INSTALL_DIR/TakeOutBack.sh search <name>"
echo "  bash $INSTALL_DIR/TakeOutBack.sh verify"
echo "  bash $INSTALL_DIR/TakeOutBack.sh stats"
