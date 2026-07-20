@echo off
REM Bluetooth Scanner - Start script (Windows)

echo === Bluetooth Scanner ===

REM Controleer Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python niet gevonden!
    echo Installeer vanaf https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Installeer dependencies
pip show bleak >nul 2>nul
if %errorlevel% neq 0 (
    echo Installeren van bleak...
    pip install bleak
)

REM Start de app
echo Starten...
python "%~dp0bluetooth_scanner.py"
pause
