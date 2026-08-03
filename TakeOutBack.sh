#!/bin/bash
# TakeOutBack launcher script
# Can be called from the drive root or from within TakeOutBack/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If src/ exists in SCRIPT_DIR, we are already inside TakeOutBack/
if [ -d "$SCRIPT_DIR/src" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
else
    PROJECT_DIR="$SCRIPT_DIR/TakeOutBack"
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "ERROR: TakeOutBack folder not found in $SCRIPT_DIR"
        echo "Install TakeOutBack with: bash $SCRIPT_DIR/install.sh"
        exit 1
    fi
fi

cd "$PROJECT_DIR"

if [ "$1" = "import" ]; then
    echo "Importing Takeout exports..."
    python3 src/main.py --import
elif [ "$1" = "search" ]; then
    if [ -z "$2" ]; then
        echo "Usage: $0 search <filename>"
        exit 1
    fi
    python3 src/main.py --search "$2"
elif [ "$1" = "verify" ]; then
    echo "Verifying integrity..."
    python3 src/main.py --verify
elif [ "$1" = "stats" ]; then
    python3 src/main.py --stats
elif [ "$1" = "update-tools" ]; then
    echo "Updating tools..."
    python3 src/main.py --update-tools
else
    echo "=== TakeOutBack ==="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  import              Import Takeout exports"
    echo "  search <name>       Search for a file"
    echo "  verify              Verify integrity"
    echo "  stats               Show statistics"
    echo "  update-tools        Update tools"
    echo "  (no argument)       Launch interactive menu"
    echo ""
    python3 src/main.py
fi
