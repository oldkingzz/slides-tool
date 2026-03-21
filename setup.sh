#!/bin/bash
# One-command setup. Works on any machine with uv (or installs it).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv sync

echo ""
echo "=== Setup complete ==="
echo ""
echo "If you haven't deployed the Apps Script yet:"
echo "  1. Open your Google Slides"
echo "  2. Extensions > Apps Script"
echo "  3. Paste the contents of appscript.js"
echo "  4. Deploy > New Deployment > Web app"
echo "     - Execute as: Me"
echo "     - Who has access: Anyone"
echo "  5. Copy the URL into config.json"
echo ""
echo "Then test with:  uv run edit_slides.py list"
