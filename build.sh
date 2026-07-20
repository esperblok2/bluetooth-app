#!/bin/bash
# Build script - Maakt een echte app van Bluetooth Scanner
# Op Manjaro/Arch Linux

echo "=== Bluetooth Scanner Builder ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Activeer venv
source "$VENV_DIR/bin/activate"

# Installeer PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller installeren..."
    pip install pyinstaller
fi

# Bouw de app
echo "App bouwen..."
cd "$SCRIPT_DIR"

pyinstaller \
    --onefile \
    --windowed \
    --name "BluetoothScanner" \
    --icon=NONE \
    --add-data "bluetooth_scanner.py:." \
    --hidden-import tkinter \
    --hidden-import bleak \
    --noconfirm \
    bluetooth_scanner.py

# Kopieer de .desktop file
echo "Desktop entry aanmaken..."
chmod +x "$SCRIPT_DIR/dist/BluetoothScanner"

# Maak .desktop bestand
DESKTOP_FILE="$HOME/.local/share/applications/bluetooth-scanner.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Bluetooth Scanner
Comment=Zoek Bluetooth apparaten en bekijk info & batterij
Exec=$SCRIPT_DIR/dist/BluetoothScanner
Icon=bluetooth
Terminal=false
Type=Application
Categories=Utility;System;Bluetooth;
Keywords=bluetooth;scanner;battery;
EOF

# Maak ook een symlink in /usr/local/bin zodat je het vanuit terminal kan starten
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ] 2>/dev/null; then
    ln -sf "$SCRIPT_DIR/dist/BluetoothScanner" /usr/local/bin/bluetooth-scanner 2>/dev/null
fi

echo ""
echo "================================"
echo "  App gebouwd!"
echo "================================"
echo ""
echo "  Bestand: $SCRIPT_DIR/dist/BluetoothScanner"
echo "  Menu:    Zoek naar 'Bluetooth Scanner'"
echo "  Terminal: $SCRIPT_DIR/dist/BluetoothScanner"
echo ""
echo "  De app staat nu in je applicatie-menu!"
echo "  Je kan hem ook kopiëren naar een andere locatie."
echo ""
