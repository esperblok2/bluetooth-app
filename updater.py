#!/usr/bin/env python3
"""
Auto-Update Systeem voor Bluetooth Scanner
Controleert op updates en installeert ze automatisch.
"""

import os
import sys
import json
import hashlib
import subprocess
import urllib.request
import urllib.error
import shutil
import tempfile
import time

# ─── Configuratie ───────────────────────────────────────────────

APP_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(APP_DIR, "version.json")
UPDATE_URL = "https://raw.githubusercontent.com/esperblok2/bluetooth-app/main/version.json"
UPDATE_FILES_URL = "https://raw.githubusercontent.com/esperblok2/bluetooth-app/main/"
BACKUP_DIR = os.path.join(APP_DIR, ".backup")
AUTO_CHECK = True
CHECK_INTERVAL = 3600  # 1 uur

# ─── Versie Beheer ─────────────────────────────────────────────

def get_local_version():
    """Lees de lokale versie."""
    try:
        with open(VERSION_FILE) as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def version_to_tuple(v):
    """Converteer versie string naar tuple voor vergelijking."""
    try:
        parts = v.strip().split(".")
        return tuple(int(p) for p in parts)
    except Exception:
        return (0, 0, 0)


def is_newer(remote, local):
    """Check of remote nieuwer is dan local."""
    return version_to_tuple(remote) > version_to_tuple(local)


# ─── Update Checker ─────────────────────────────────────────────

def check_for_updates(silent=True):
    """
    Controleer op updates.
    Retourneert: (has_update, remote_version, changelog)
    """
    try:
        req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": "BluetoothScanner/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        remote_version = data.get("version", "0.0.0")
        local_version = get_local_version()
        changelog = data.get("changelog", [])

        if is_newer(remote_version, local_version):
            return True, remote_version, changelog
        return False, remote_version, changelog

    except urllib.error.URLError:
        if not silent:
            print("Kan geen verbinding maken met update-server")
        return False, None, []
    except Exception as e:
        if not silent:
            print(f"Update-check mislukt: {e}")
        return False, None, []


def check_files_for_update():
    """Haal de lijst van bestanden op die bijgewerkt moeten worden."""
    try:
        url = UPDATE_URL.replace("version.json", "update_manifest.json")
        req = urllib.request.Request(url, headers={"User-Agent": "BluetoothScanner/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("files", [])
    except Exception:
        return []


# ─── Update Downloaden ─────────────────────────────────────────

def download_file(url, dest):
    """Download een bestand."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BluetoothScanner/2.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
        return True
    except Exception:
        return False


def download_update_files(file_list):
    """Download alle bestanden voor een update."""
    downloaded = []
    for file_info in file_list:
        filename = file_info.get("name", "")
        if not filename:
            continue
        url = UPDATE_FILES_URL + filename
        dest = os.path.join(APP_DIR, filename)

        if download_file(url, dest):
            downloaded.append(filename)
    return downloaded


# ─── Backup & Installatie ───────────────────────────────────────

def create_backup():
    """Maak een backup van de huidige bestanden."""
    try:
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)
        os.makedirs(BACKUP_DIR)

        files_to_backup = ["bluetooth_scanner.py", "version.json", "updater.py"]
        for fname in files_to_backup:
            src = os.path.join(APP_DIR, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(BACKUP_DIR, fname))
        return True
    except Exception:
        return False


def restore_backup():
    """Herstel de backup."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return False
        for fname in os.listdir(BACKUP_DIR):
            src = os.path.join(BACKUP_DIR, fname)
            dst = os.path.join(APP_DIR, fname)
            shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def install_update(progress_callback=None):
    """
    Download en installeer de update.
    """
    if progress_callback:
        progress_callback("Controleren op updates...")

    has_update, remote_version, changelog = check_for_updates(silent=False)
    if not has_update:
        return False, "Geen update beschikbaar"

    if progress_callback:
        progress_callback(f"Update gevonden: v{remote_version}")

    # Backup maken
    if progress_callback:
        progress_callback("Backup maken...")
    create_backup()

    # Download update manifest
    if progress_callback:
        progress_callback("Bestanden ophalen...")
    file_list = check_files_for_update()

    if not file_list:
        # Fallback: download alleen de hoofdbestanden
        file_list = [
            {"name": "bluetooth_scanner.py"},
            {"name": "updater.py"},
            {"name": "version.json"},
            {"name": "build.sh"},
            {"name": "build.bat"},
            {"name": "start.sh"},
        ]

    # Download bestanden
    downloaded = []
    for i, file_info in enumerate(file_list):
        fname = file_info.get("name", "")
        if not fname:
            continue
        if progress_callback:
            progress_callback(f"Downloaden: {fname} ({i+1}/{len(file_list)})")
        url = UPDATE_FILES_URL + fname
        dest = os.path.join(APP_DIR, fname)
        if download_file(url, dest):
            downloaded.append(fname)

    if not downloaded:
        return False, "Geen bestanden gedownload"

    # Update versie bestand
    new_version_data = {
        "version": remote_version,
        "name": "Bluetooth Scanner",
        "changelog": changelog
    }
    with open(VERSION_FILE, "w") as f:
        json.dump(new_version_data, f, indent=2)

    if progress_callback:
        progress_callback("Update geinstalleerd!")

    return True, f"Geupdate naar v{remote_version}"


def rollback_update():
    """Herstel naar de vorige versie."""
    if restore_backup():
        return True, "Hersteld naar vorige versie"
    return False, "Geen backup beschikbaar"


# ─── CLI Interface ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bluetooth Scanner Updater")
    parser.add_argument("command", choices=["check", "update", "rollback", "version"],
                        help="Update commando")
    parser.add_argument("--silent", action="store_true", help="Stille modus")
    args = parser.parse_args()

    if args.command == "version":
        print(f"Huidige versie: {get_local_version()}")

    elif args.command == "check":
        has_update, remote, changelog = check_for_updates(silent=args.silent)
        if has_update:
            print(f"Update beschikbaar: v{remote}")
            if changelog:
                print("Wijzigingen:")
                for item in changelog:
                    print(f"  - {item}")
        else:
            print("App is up-to-date!")

    elif args.command == "update":
        def progress(msg):
            if not args.silent:
                print(msg)
        success, msg = install_update(progress_callback=progress)
        print(msg)
        if success:
            print("Start de app opnieuw op om de update te activeren.")

    elif args.command == "rollback":
        success, msg = rollback_update()
        print(msg)


if __name__ == "__main__":
    main()
