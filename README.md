# Bluetooth Scanner

Zoek Bluetooth apparaten, bekijk info en batterij-status.

## Snel starten (Linux / Manjaro)

```bash
cd ~/bluetooth-app
./start.sh
```

## App bouwen (echte desktop app)

### Linux
```bash
cd ~/bluetooth-app
./build.sh
```
Dan staat de app in je applicatie-menu als "Bluetooth Scanner".

### Windows
1. Kopieer de hele `bluetooth-app` map naar een Windows PC
2. Zorg dat Python geinstalleerd is (met "Add to PATH" aangevinkt)
3. Dubbelklik op `build.bat`
4. De `.exe` staat in `dist/BluetoothScanner.exe`

### Windows .exe bouwen vanaf Linux (met Wine)
```bash
cd ~/bluetooth-app
./build-windows.sh
```

## Vereisten

- Python 3.8+
- tkinter (standaard bij Python)
- bleak (wordt automatisch geinstalleerd)
- Bluetooth adapter

## Bestandsstructuur

```
bluetooth-app/
├── bluetooth_scanner.py    # De app
├── start.sh               # Snel starten (Linux)
├── build.sh               # App bouwen (Linux)
├── build.bat              # App bouwen (Windows)
├── build-windows.sh       # Cross-compile naar Windows
├── requirements.txt       # Dependencies
└── .venv/                 # Virtuele omgeving (automatisch)
```
