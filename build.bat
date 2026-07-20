@echo off
REM ============================================
REM  Bluetooth Scanner - Windows Builder
REM  Draai dit script op een Windows PC
REM ============================================

echo === Bluetooth Scanner Windows Builder ===
echo.

REM Controleer Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python niet gevonden!
    echo Download vanaf: https://www.python.org/downloads/
    echo Vink "Add Python to PATH" aan tijdens installatie!
    pause
    exit /b 1
)

REM Contoleer pip
python -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo pip installeren...
    python -m ensurepip --upgrade
)

REM Installeer dependencies
echo Dependencies installeren...
python -m pip install bleak pyinstaller --quiet

REM Bouw de app
echo.
echo App bouwen (dit duurt even)...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "BluetoothScanner" ^
    --clean ^
    --noconfirm ^
    bluetooth_scanner.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    #  BUILD SUCCESVOL!
    echo ========================================
    echo.
    echo Bestand: dist\BluetoothScanner.exe
    echo.
    echo Je kan BluetoothScanner.exe nu gebruiken!
    echo Kopieer hem naar je bureaublad of startmenu.
    echo.
) else (
    echo.
    echo BUILD MISLUKT! Bekijk de foutmeldingen hierboven.
)

pause
