#!/bin/bash
# Bluetooth Scanner - Start script (Manjaro / Arch Linux)

echo "=== Bluetooth Scanner ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Controleer Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 niet gevonden!"
    echo "Installeer met: sudo pacman -S python"
    exit 1
fi

# Controleer / installeer tk (nodig voor tkinter)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "tkinter niet gevonden, installeren..."
    sudo pacman -S --noconfirm tk
fi

# Controleer / installeer bluez
if ! command -v bluetoothctl &> /dev/null; then
    echo "bluez niet gevonden, installeren..."
    sudo pacman -S --noconfirm bluez bluez-utils
fi

# Bluetooth aan zetten
if command -v bluetoothctl &> /dev/null; then
    if ! bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
        echo "Bluetooth aanzetten..."
        bluetoothctl power on 2>/dev/null
    fi
fi

# Maak venv aan als die niet bestaat
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtuele omgeving aanmaken..."
    python3 -m venv "$VENV_DIR"
fi

# Activeer venv
source "$VENV_DIR/bin/activate"

# Installeer bleak in de venv
if ! python -c "import bleak" 2>/dev/null; then
    echo "bleak installeren..."
    pip install bleak
fi

# Start de app
echo "Starten..."
python "$SCRIPT_DIR/bluetooth_scanner.py"
