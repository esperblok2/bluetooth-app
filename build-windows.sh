#!/bin/bash
# ============================================
#  Bluetooth Scanner - Cross-compile naar Windows
#  Bouwt een .exe vanaf Linux (via Wine)
# ============================================

echo "=== Windows Cross-Builder ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Check of Wine geinstalleerd is
if ! command -v wine &> /dev/null; then
    echo "Wine is niet geinstalleerd."
    echo ""
    echo "Optie 1: Installeer Wine"
    echo "  sudo pacman -S wine"
    echo ""
    echo "Optie 2: Build op een Windows PC"
    echo "  Kopieer deze map naar Windows en draai build.bat"
    echo ""
    echo "Optie 3: Gebruik GitHub Actions (zie build-windows.yml)"
    echo ""
    exit 1
fi

# Activeer venv
source "$VENV_DIR/bin/activate"

# Installeer pyinstaller voor windows via wine
echo "Windows Python + PyInstaller installeren via Wine..."
echo "(Dit kan even duren bij eerste keer)"
echo ""

# Zoek Python voor Windows
WIN_PYTHON=""
for p in \
    "$HOME/.wine/drive_c/users/esper/AppData/Local/Programs/Python/Python312" \
    "$HOME/.wine/drive_c/Python312" \
    "$HOME/.wine/drive_c/Python311" \
    "$HOME/.wine/drive_c/Python313"; do
    if [ -d "$p" ]; then
        WIN_PYTHON="$p"
        break
    fi
done

if [ -z "$WIN_PYTHON" ]; then
    echo "Python voor Windows downloaden..."
    PYTHON_URL="https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    wget -q --show-progress -O /tmp/python-installer.exe "$PYTHON_URL"
    echo "Installeren via Wine (stil)..."
    wine /tmp/python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 2>/dev/null
    rm /tmp/python-installer.exe
    # Zoek opnieuw
    WIN_PYTHON=$(find ~/.wine/drive_c -path "*/Python3*/python.exe" -exec dirname {} \; 2>/dev/null | head -1)
fi

if [ -z "$WIN_PYTHON" ]; then
    echo "FOUT: Kon Windows Python niet vinden in Wine"
    exit 1
fi

echo "Windows Python gevonden: $WIN_PYTHON"

# Installeer bleak + pyinstaller in Wine Python
echo "Dependencies installeren..."
wine "$WIN_PYTHON/python.exe" -m pip install bleak pyinstaller 2>/dev/null

# Zoek pyinstaller
PYINSTALLER=""
for p in \
    "$WIN_PYTHON/Scripts/pyinstaller.exe" \
    "$WIN_PYTHON/Scripts/pyinstaller"; do
    if [ -f "$p" ]; then
        PYINSTALLER="$p"
        break
    fi
done

if [ -z "$PYINSTALLER" ]; then
    echo "PyInstaller niet gevonden, proberen via python -m..."
    PYINSTALLER="$WIN_PYTHON/python.exe"
    PYINSTALLER_ARGS="-m PyInstaller"
else
    PYINSTALLER_ARGS=""
fi

# Bouw de .exe
echo ""
echo "Windows .exe bouwen..."
cd "$SCRIPT_DIR"

if [ -n "$PYINSTALLER_ARGS" ]; then
    wine "$PYINSTALLER" $PYINSTALLER_ARGS \
        --onefile \
        --windowed \
        --name "BluetoothScanner" \
        --clean \
        --noconfirm \
        bluetooth_scanner.py
else
    wine "$PYINSTALLER" \
        --onefile \
        --windowed \
        --name "BluetoothScanner" \
        --clean \
        --noconfirm \
        bluetooth_scanner.py
fi

if [ -f "$SCRIPT_DIR/dist/BluetoothScanner.exe" ]; then
    echo ""
    echo "========================================="
    echo "  BUILD SUCCESVOL!"
    echo "========================================="
    echo ""
    echo "  Bestand: dist/BluetoothScanner.exe"
    echo ""
    echo "  Kopieer deze .exe naar een Windows PC"
    echo "  en hij werkt direct (geen installatie nodig)."
    echo ""
else
    echo ""
    echo "BUILD MISLUKT!"
    echo "Probeer build.bat op een echte Windows PC."
fi
