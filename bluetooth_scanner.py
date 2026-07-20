#!/usr/bin/env python3
"""
Bluetooth Scanner v2 - Coole Edition
Zoek Bluetooth apparaten, bekijk info en batterij-status.
Met gave UI, animaties, slimme features en auto-update.
"""

import sys
import os
import platform
import subprocess
import threading
import json
import time
import colorsys
import math

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, font as tkfont
except ImportError:
    print("tkinter niet gevonden!")
    sys.exit(1)

try:
    import asyncio
    from bleak import BleakScanner, BleakClient
except ImportError:
    print("bleak niet gevonden! Run: pip install bleak")
    sys.exit(1)

# Probeer updater te importeren
try:
    from updater import check_for_updates, get_local_version, install_update, rollback_update
    HAS_UPDATER = True
except ImportError:
    HAS_UPDATER = False

# ─── Thema's ────────────────────────────────────────────────────

THEMES = {
    "Neon Blauw": {
        "bg": "#0a0a1a", "bg2": "#0d1117", "card": "#161b22",
        "border": "#21262d", "accent": "#00d4ff", "accent2": "#0099cc",
        "accent3": "#006699", "green": "#00ff88", "yellow": "#ffcc00",
        "red": "#ff4466", "text": "#e6edf3", "dim": "#7d8590",
        "glow": "#00d4ff",
    },
    "Neon Roze": {
        "bg": "#1a0a1a", "bg2": "#170d17", "card": "#1e1622",
        "border": "#2d2133", "accent": "#ff00ff", "accent2": "#cc00cc",
        "accent3": "#990099", "green": "#00ff88", "yellow": "#ffcc00",
        "red": "#ff4466", "text": "#f3e6f3", "dim": "#857d85",
        "glow": "#ff00ff",
    },
    "Neon Groen": {
        "bg": "#0a1a0a", "bg2": "#0d170d", "card": "#162216",
        "border": "#212d21", "accent": "#00ff44", "accent2": "#00cc33",
        "accent3": "#009922", "green": "#00ff88", "yellow": "#ffcc00",
        "red": "#ff4466", "text": "#e6f3e6", "dim": "#7d857d",
        "glow": "#00ff44",
    },
    "Cyber Paars": {
        "bg": "#0d0a1a", "bg2": "#110d17", "card": "#1a1622",
        "border": "#262133", "accent": "#a855f7", "accent2": "#8b3fd4",
        "accent3": "#6d2db0", "green": "#00ff88", "yellow": "#ffcc00",
        "red": "#ff4466", "text": "#f0e6f3", "dim": "#807d85",
        "glow": "#a855f7",
    },
    "Zonsondergang": {
        "bg": "#1a0f0a", "bg2": "#17110d", "card": "#221a16",
        "border": "#332621", "accent": "#ff6b35", "accent2": "#cc5522",
        "accent3": "#993f11", "green": "#00ff88", "yellow": "#ffcc00",
        "red": "#ff4466", "text": "#f3ede6", "dim": "#857d75",
        "glow": "#ff6b35",
    },
}

# ─── Globale variabelen ────────────────────────────────────────

current_theme_name = "Neon Blauw"
current_theme = THEMES[current_theme_name]

def t(key):
    return current_theme[key]

# ─── Bluetooth Helpers ─────────────────────────────────────────

async def scan_devices(callback, stop_event):
    def detection(device, adv_data):
        if not stop_event.is_set():
            name = device.name or "Onbekend"
            rssi = adv_data.rssi if adv_data else None
            callback({
                "address": device.address,
                "name": name,
                "rssi": rssi,
            })
    scanner = BleakScanner(detection_callback=detection)
    await scanner.start()
    while not stop_event.is_set():
        await asyncio.sleep(0.5)
    await scanner.stop()


def get_battery_info():
    info = {}
    system = platform.system()
    if system == "Linux":
        try:
            result = subprocess.run(
                ["upower", "-e"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if "battery" in line:
                    bat = subprocess.run(
                        ["upower", "-i", line.strip()],
                        capture_output=True, text=True, timeout=5,
                    )
                    data = {}
                    for bline in bat.stdout.strip().split("\n"):
                        if ":" in bline:
                            k, v = bline.split(":", 1)
                            data[k.strip()] = v.strip()
                    percentage = data.get("percentage", None)
                    if percentage:
                        percentage = percentage.replace("%", "").strip()
                    state = data.get("state", "unknown")
                    energy = data.get("energy", None)
                    energy_full = data.get("energy-full", None)
                    info = {
                        "percentage": percentage,
                        "state": state,
                        "energy": energy,
                        "energy_full": energy_full,
                    }
                    break
        except Exception:
            pass
    return info


def get_paired_devices():
    devices = []
    system = platform.system()
    if system == "Linux":
        try:
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True, text=True, timeout=5,
            )
            addresses = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith("Device"):
                    parts = line.split(" ", 2)
                    if len(parts) >= 2:
                        addresses.append((parts[1], parts[2] if len(parts) >= 3 else "Onbekend"))

            for addr, fallback_name in addresses:
                try:
                    info_result = subprocess.run(
                        ["bluetoothctl", "info", addr],
                        capture_output=True, text=True, timeout=5,
                    )
                    info_text = info_result.stdout
                    is_paired = any("Paired: yes" in l for l in info_text.split("\n"))
                    if not is_paired:
                        continue
                    dev_info = {"address": addr, "name": fallback_name}
                    for iline in info_text.split("\n"):
                        iline = iline.strip()
                        if iline.startswith("Name:"):
                            dev_info["name"] = iline.split(":", 1)[1].strip()
                        elif iline.startswith("Alias:"):
                            dev_info["alias"] = iline.split(":", 1)[1].strip()
                        elif iline.startswith("Class:"):
                            dev_info["class"] = iline.split(":", 1)[1].strip()
                            dev_info["type"] = class_to_device_type(iline.split(":", 1)[1].strip())
                        elif iline.startswith("Icon:"):
                            dev_info["icon"] = iline.split(":", 1)[1].strip()
                        elif iline.startswith("Trusted:"):
                            dev_info["trusted"] = iline.split(":", 1)[1].strip()
                        elif iline.startswith("Connected:"):
                            dev_info["connected"] = iline.split(":", 1)[1].strip()
                        elif iline.startswith("UUID:"):
                            uid = iline.split(":", 1)[1].strip()
                            if "uuids" not in dev_info:
                                dev_info["uuids"] = []
                            dev_info["uuids"].append(uid)
                        elif "Battery Percentage:" in iline:
                            try:
                                bat_str = iline.split("(")[1].rstrip(")")
                                dev_info["battery"] = int(bat_str)
                            except Exception:
                                pass
                    devices.append(dev_info)
                except Exception:
                    pass
        except Exception:
            pass
    return devices


def class_to_device_type(class_hex):
    try:
        major = int(class_hex, 16) >> 8 & 0xFF
        type_map = {
            0x20: "Computer", 0x21: "Desktop", 0x22: "Server",
            0x23: "Laptop", 0x24: "Handheld", 0x25: "Palm",
            0x26: "Wearable", 0x40: "Audio", 0x41: "Luidspreker",
            0x42: "Koptelefoon", 0x43: "Headset", 0x44: "Microfoon",
            0x45: "Lavalier", 0x46: "Portable Audio", 0x47: "Auto Audio",
            0x48: "Set-top Box", 0x49: "HiFi", 0x4A: "Telefoon",
            0x4B: "Smartphone", 0x50: "Peripheral", 0x51: "Toetsenbord",
            0x52: "Muis", 0x53: "Joystick", 0x54: "Remote",
            0x55: "Sensor", 0x56: "Bril", 0x57: "Headset",
            0x60: "Imaging", 0x61: "Display", 0x62: "Camera",
            0x63: "Scanner", 0x64: "Printer", 0x70: "Wearable",
            0x72: "Horloge", 0x73: "Jas", 0x74: "Rugzak",
        }
        return type_map.get(major, f"Apparaat (0x{major:02X})")
    except Exception:
        return "Onbekend"


UUID_DESCRIPTIONS = {
    "00001800": "Generic Access", "00001801": "Generic Attribute",
    "0000180a": "Device Information", "0000180f": "Battery Service",
    "00001812": "HID (Keyboard/Mouse)", "00001101": "Serial Port (SPP)",
    "0000110b": "Audio Sink (A2DP)", "0000110c": "Audio Source",
    "0000110e": "Remote Control (AVRCP)", "0000111e": "Handsfree",
    "0000111f": "Handsfree AG", "00001124": "HID over GATT",
    "00001132": "Headset", "00001133": "Headset AG",
    "00001848": "Link Loss", "0000184a": "Immediate Alert",
    "0000184b": "Tx Power",
}

def resolve_uuid(uuid_str):
    uuid_lower = uuid_str.lower()
    for key, desc in UUID_DESCRIPTIONS.items():
        if key in uuid_lower:
            return desc
    if len(uuid_str) <= 8:
        return f"Service {uuid_str}"
    return uuid_str[:40]


def get_device_emoji(name):
    n = name.lower()
    if any(x in n for x in ["airpod", "buds", "headphone", "headset", "ear"]): return "🎧"
    if any(x in n for x in ["speaker", "boombox", "sound"]): return "🔊"
    if any(x in n for x in ["watch", "band", "fit"]): return "⌚"
    if any(x in n for x in ["controller", "gamepad", "dualshock", "xbox"]): return "🎮"
    if any(x in n for x in ["mouse"]): return "🖱️"
    if any(x in n for x in ["keyboard"]): return "⌨️"
    if any(x in n for x in ["phone", "iphone", "galaxy"]): return "📱"
    if any(x in n for x in ["tv", "roku", "chromecast"]): return "📺"
    return "📡"


def get_device_type_text(name):
    n = name.lower()
    if any(x in n for x in ["airpod", "buds", "headphone", "headset", "ear"]): return "Koptelefoon"
    if any(x in n for x in ["speaker", "boombox", "sound"]): return "Luidspreker"
    if any(x in n for x in ["watch", "band", "fit"]): return "Horloge"
    if any(x in n for x in ["controller", "gamepad"]): return "Controller"
    if any(x in n for x in ["mouse"]): return "Muis"
    if any(x in n for x in ["keyboard"]): return "Toetsenbord"
    if any(x in n for x in ["phone"]): return "Telefoon"
    return ""


# ─── Lokale Hardware Detectie ──────────────────────────────────

def get_usb_devices():
    devices = []
    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 5)
            if len(parts) >= 6:
                devices.append({
                    "type": "USB",
                    "name": parts[5],
                    "id": parts[1] + ":" + parts[2],
                    "icon": "🔌",
                })
    except Exception:
        pass
    return devices


def get_pci_devices():
    devices = []
    try:
        result = subprocess.run(
            ["lspci", "-nn"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                name = parts[2] if len(parts) > 2 else parts[1]
                icon = "🖥️"
                nl = name.lower()
                if any(x in nl for x in ["vga", "3d", "display", "gpu"]):
                    icon = "🎮"
                elif any(x in nl for x in ["audio", "sound"]):
                    icon = "🔊"
                elif any(x in nl for x in ["network", "ethernet", "wifi", "wireless"]):
                    icon = "📶"
                elif any(x in nl for x in ["usb"]):
                    icon = "🔌"
                elif any(x in nl for x in ["sata", "nvme", "ahci", "storage"]):
                    icon = "💾"
                devices.append({
                    "type": "PCI",
                    "name": name.split(" [")[0] if " [" in name else name,
                    "id": parts[0],
                    "icon": icon,
                })
    except Exception:
        pass
    return devices


def get_audio_devices():
    devices = []
    try:
        result = subprocess.run(
            ["aplay", "-l"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if "card" in line and "device" in line:
                devices.append({
                    "type": "Audio",
                    "name": line.strip(),
                    "id": "",
                    "icon": "🔊",
                })
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if "card" in line and "device" in line:
                devices.append({
                    "type": "Microfoon",
                    "name": line.strip(),
                    "id": "",
                    "icon": "🎤",
                })
    except Exception:
        pass
    return devices


def get_storage_devices():
    devices = []
    try:
        result = subprocess.run(
            ["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        for line in lines[1:]:
            parts = line.split(None, 3)
            if len(parts) >= 3:
                icon = "💾" if parts[2] == "disk" else "📀" if parts[2] == "rom" else "📦"
                name = parts[3] if len(parts) > 3 else parts[0]
                devices.append({
                    "type": "Opslag",
                    "name": f"{name} ({parts[1]})",
                    "id": parts[0],
                    "icon": icon,
                })
    except Exception:
        pass
    return devices


def get_hdmi_devices():
    devices = []
    try:
        result = subprocess.run(
            ["ls /sys/class/drm/"], capture_output=True, text=True, timeout=5
        )
        for entry in result.stdout.strip().split("\n"):
            if "card" in entry and "-HDMI-" in entry:
                status_file = f"/sys/class/drm/{entry}/status"
                status = "?"
                try:
                    with open(status_file) as f:
                        status = f.read().strip()
                except Exception:
                    pass
                devices.append({
                    "type": "HDMI",
                    "name": entry.replace("card0-", ""),
                    "id": status,
                    "icon": "📺",
                })
    except Exception:
        pass
    return devices


def get_all_local_devices():
    devices = []
    devices.extend(get_usb_devices())
    devices.extend(get_pci_devices())
    devices.extend(get_audio_devices())
    devices.extend(get_storage_devices())
    devices.extend(get_hdmi_devices())
    return devices


# ─── Beveiliging ────────────────────────────────────────────────

SECURITY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "security.json")

def load_security():
    try:
        if os.path.exists(SECURITY_FILE):
            with open(SECURITY_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"pin": None, "whitelist": [], "blocked": []}


def save_security(data):
    try:
        with open(SECURITY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def check_pin(pin):
    sec = load_security()
    if sec["pin"] is None:
        return True
    return sec["pin"] == pin


def set_pin(pin):
    sec = load_security()
    sec["pin"] = pin
    save_security(sec)


def is_device_allowed(address):
    sec = load_security()
    if address in sec["blocked"]:
        return False
    if not sec["whitelist"]:
        return True
    return address in sec["whitelist"]


def add_to_whitelist(address, name=""):
    sec = load_security()
    if address not in sec["whitelist"]:
        sec["whitelist"].append(address)
    if address in sec["blocked"]:
        sec["blocked"].remove(address)
    save_security(sec)


def block_device(address):
    sec = load_security()
    if address not in sec["blocked"]:
        sec["blocked"].append(address)
    if address in sec["whitelist"]:
        sec["whitelist"].remove(address)
    save_security(sec)


# ─── Besturing (Media Controls) ────────────────────────────────

def run_dbus_command(cmd_parts):
    try:
        subprocess.run(cmd_parts, capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def media_play():
    run_dbus_command(["dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
                      "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player.PlayPause"])


def media_next():
    run_dbus_command(["dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
                      "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player.Next"])


def media_prev():
    run_dbus_command(["dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
                      "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player.Previous"])


def media_stop():
    run_dbus_command(["dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
                      "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player.Stop"])


def media_volume_up():
    run_dbus_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])


def media_volume_down():
    run_dbus_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])


def media_mute():
    run_dbus_command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])


def get_media_info():
    try:
        result = subprocess.run(
            ["dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
             "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties.Get",
             "string:org.mpris.MediaPlayer2.Player", "string:Metadata"],
            capture_output=True, text=True, timeout=5
        )
        title = ""
        artist = ""
        for line in result.stdout.split("\n"):
            if "xesam:title" in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    title = parts[-2]
            elif "xesam:artist" in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    artist = parts[-2]
        return {"title": title, "artist": artist}
    except Exception:
        return {"title": "", "artist": ""}


def get_current_volume():
    try:
        result = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True, text=True, timeout=5
        )
        for part in result.stdout.split():
            if "%" in part:
                return part.replace("%", "").strip()
    except Exception:
        pass
    return "?"


# ─── Hoofdvenster ──────────────────────────────────────────────

class BluetoothApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bluetooth Scanner v2")
        self.root.geometry("850x900")
        self.root.minsize(700, 600)
        self.root.configure(bg=t("bg"))

        self.scanning = False
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.found_devices = {}
        self.connected_clients = {}
        self.device_notes = {}
        self.filter_text = ""
        self.glow_phase = 0
        self.anim_running = True
        self.battery_refresh_id = None

        self.load_notes()
        self.build_ui()
        self.start_glow_animation()
        self.schedule_battery_refresh()
        self.root.after(500, self.check_pin_startup)

    def load_notes(self):
        try:
            notes_file = os.path.join(os.path.dirname(__file__), "device_notes.json")
            if os.path.exists(notes_file):
                with open(notes_file) as f:
                    self.device_notes = json.load(f)
        except Exception:
            self.device_notes = {}

    def check_pin_startup(self):
        sec = load_security()
        if sec["pin"] is not None:
            self.ask_pin()

    def ask_pin(self):
        pin_dialog = tk.Toplevel(self.root)
        pin_dialog.title("Pincode vereist")
        pin_dialog.geometry("350x180")
        pin_dialog.configure(bg=t("bg"))
        pin_dialog.resizable(False, False)
        pin_dialog.transient(self.root)
        pin_dialog.grab_set()

        tk.Label(pin_dialog, text="Voer pincode in:", font=("Segoe UI", 12),
                 bg=t("bg"), fg=t("text")).pack(pady=(20, 8))
        pin_entry = tk.Entry(pin_dialog, font=("Consolas", 14), bg=t("card"), fg=t("text"),
                             insertbackground=t("accent"), relief="flat", show="*", justify="center")
        pin_entry.pack(ipady=6, padx=40)
        pin_entry.focus()

        def check():
            if check_pin(pin_entry.get()):
                pin_dialog.destroy()
            else:
                messagebox.showerror("Fout", "Verkeerde pincode!")
                pin_entry.delete(0, tk.END)

        def on_enter(e):
            check()

        pin_entry.bind("<Return>", on_enter)
        tk.Button(pin_dialog, text="OK", font=("Segoe UI", 11, "bold"),
                  bg=t("accent"), fg="#ffffff", relief="flat", cursor="hand2",
                  command=check, padx=20, pady=4).pack(pady=12)

    def save_notes(self):
        try:
            notes_file = os.path.join(os.path.dirname(__file__), "device_notes.json")
            with open(notes_file, "w") as f:
                json.dump(self.device_notes, f, indent=2)
        except Exception:
            pass

    # ─── Glow animatie ─────────────────────────────────────────

    def start_glow_animation(self):
        self.animate_glow()

    def animate_glow(self):
        if not self.anim_running:
            return
        self.glow_phase = (self.glow_phase + 2) % 360
        try:
            glow_color = self.get_glow_color()
            for widget in self.root.winfo_children():
                self.apply_glow_recursive(widget, glow_color)
        except Exception:
            pass
        self.root.after(50, self.animate_glow)

    def get_glow_color(self):
        r, g, b = self.hex_to_rgb(t("glow"))
        phase = math.sin(math.radians(self.glow_phase)) * 0.3 + 0.7
        r = int(r * phase)
        g = int(g * phase)
        b = int(b * phase)
        return f"#{r:02x}{g:02x}{b:02x}"

    def apply_glow_recursive(self, widget, color):
        try:
            if isinstance(widget, tk.Frame):
                if widget.cget("highlightbackground") == t("glow"):
                    widget.configure(highlightbackground=color)
        except Exception:
            pass

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # ─── Batterij auto-refresh ─────────────────────────────────

    def schedule_battery_refresh(self):
        self.refresh_battery_tab()
        self.battery_refresh_id = self.root.after(30000, self.schedule_battery_refresh)

    def refresh_battery_tab(self):
        for w in self.bat_inner.winfo_children():
            w.destroy()
        info = get_battery_info()
        if not info or not info.get("percentage"):
            tk.Label(
                self.bat_inner, text="Geen batterij-info\n(Alleen laptops)",
                font=("Segoe UI", 12), bg=t("bg"), fg=t("dim"), justify="center",
            ).pack(pady=60)
            return
        pct = int(info["percentage"])
        state = info.get("state", "unknown")
        color = t("green") if pct > 60 else t("yellow") if pct > 20 else t("red")

        card = tk.Frame(self.bat_inner, bg=t("card"), highlightbackground=t("border"),
                        highlightthickness=1, bd=0)
        card.pack(fill=tk.X, padx=20, pady=12)

        inner = tk.Frame(card, bg=t("card"))
        inner.pack(fill=tk.X, padx=24, pady=20)

        header_frame = tk.Frame(inner, bg=t("card"))
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Laptop Batterij", font=("Segoe UI", 16, "bold"),
                 bg=t("card"), fg=t("accent")).pack(side=tk.LEFT)

        state_emoji = "⚡" if "charg" in state else "🔋" if "full" in state else "🔌"
        state_text = {"charging": "Aan het opladen", "discharging": "Aan het ontladen",
                      "fully-charged": "Vol", "empty": "Leeg"}.get(state, state.title())
        tk.Label(header_frame, text=f"{state_emoji} {state_text}",
                 font=("Segoe UI", 10), bg=t("card"), fg=t("dim")).pack(side=tk.RIGHT)

        pct_frame = tk.Frame(inner, bg=t("card"))
        pct_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Label(pct_frame, text=f"{pct}%", font=("Segoe UI", 48, "bold"),
                 bg=t("card"), fg=color).pack(side=tk.LEFT)

        bar_frame = tk.Frame(inner, bg=t("card"))
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg=t("border"), height=16)
        bar_bg.pack(fill=tk.X)
        bar_bg.pack_propagate(False)
        bar_width = max(1, int(500 * pct / 100))
        bar_fill = tk.Frame(bar_bg, bg=color, height=16, width=bar_width)
        bar_fill.place(x=0, y=0, relheight=1.0)

        if info.get("energy") and info.get("energy_full"):
            tk.Label(inner, text=f"Capaciteit: {info['energy']} / {info['energy_full']}",
                     font=("Segoe UI", 10), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(12, 0))

        # Laatste update tijd
        tk.Label(inner, text=f"Laatste update: {time.strftime('%H:%M:%S')}  (elke 30s)",
                 font=("Segoe UI", 8), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(8, 0))

    # ─── UI bouwen ─────────────────────────────────────────────

    def build_ui(self):
        main = tk.Frame(self.root, bg=t("bg"))
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Header
        hdr = tk.Frame(main, bg=t("bg"))
        hdr.pack(fill=tk.X, pady=(0, 16))

        title_frame = tk.Frame(hdr, bg=t("bg"))
        title_frame.pack(side=tk.LEFT)

        tk.Label(title_frame, text="Bluetooth Scanner", font=("Segoe UI", 24, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w")
        tk.Label(title_frame, text="Zoek, verbind en beheer je Bluetooth apparaten",
                 font=("Segoe UI", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w")

        # Thema knop
        theme_btn = tk.Button(hdr, text="THEMA", font=("Segoe UI", 9, "bold"),
                              bg=t("accent3"), fg=t("text"), relief="flat",
                              activebackground=t("accent2"), cursor="hand2",
                              command=self.cycle_theme, padx=12, pady=4)
        theme_btn.pack(side=tk.RIGHT)

        # Zoekbalk
        search_frame = tk.Frame(main, bg=t("bg"))
        search_frame.pack(fill=tk.X, pady=(0, 12))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                font=("Segoe UI", 11), bg=t("card"), fg=t("text"),
                                insertbackground=t("accent"), relief="flat",
                                highlightbackground=t("border"), highlightthickness=1)
        search_entry.pack(fill=tk.X, ipady=8, padx=2)
        search_entry.insert(0, "Zoek apparaten...")

        # Scan knop
        self.scan_btn = tk.Button(
            main, text="Zoek Bluetooth Apparaten",
            font=("Segoe UI", 13, "bold"), bg=t("accent"), fg="#ffffff",
            activebackground=t("accent2"), relief="flat", cursor="hand2",
            command=self.toggle_scan, bd=0,
        )
        self.scan_btn.pack(fill=tk.X, ipady=10, pady=(0, 8))

        # Status
        self.status_var = tk.StringVar(value="Klaar om te scannen")
        tk.Label(main, textvariable=self.status_var, font=("Segoe UI", 9),
                 bg=t("bg"), fg=t("dim")).pack(anchor="w", pady=(0, 8))

        # Tabs
        tab_frame = tk.Frame(main, bg=t("bg"))
        tab_frame.pack(fill=tk.BOTH, expand=True)

        # Tab knoppen
        self.tab_buttons = []
        tab_names = ["Live Scan", "Gekoppeld", "Lokaal", "Besturing", "Beveiliging", "Batterij", "Update"]
        self.current_tab = 0

        btn_row = tk.Frame(tab_frame, bg=t("bg"))
        btn_row.pack(fill=tk.X, pady=(0, 8))

        for i, name in enumerate(tab_names):
            btn = tk.Button(btn_row, text=name, font=("Segoe UI", 10, "bold"),
                            bg=t("card") if i != 0 else t("accent3"),
                            fg=t("text"), relief="flat", cursor="hand2",
                            command=lambda idx=i: self.switch_tab(idx), padx=16, pady=6)
            btn.pack(side=tk.LEFT, padx=(0, 4))
            self.tab_buttons.append(btn)

        # Tab content
        self.tab_contents = []

        # Tab 0: Live Scan
        scan_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(scan_frame)

        self.canvas = tk.Canvas(scan_frame, bg=t("bg"), highlightthickness=0)
        self.scrollbar = tk.Scrollbar(scan_frame, orient="vertical", command=self.canvas.yview)
        self.scan_inner = tk.Frame(self.canvas, bg=t("bg"))
        self.scan_inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scan_inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # Tab 1: Gekoppeld
        paired_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(paired_frame)

        self.paired_canvas = tk.Canvas(paired_frame, bg=t("bg"), highlightthickness=0)
        self.paired_scrollbar = tk.Scrollbar(paired_frame, orient="vertical", command=self.paired_canvas.yview)
        self.paired_inner = tk.Frame(self.paired_canvas, bg=t("bg"))
        self.paired_inner.bind("<Configure>", lambda e: self.paired_canvas.configure(scrollregion=self.paired_canvas.bbox("all")))
        self.paired_window = self.paired_canvas.create_window((0, 0), window=self.paired_inner, anchor="nw")
        self.paired_canvas.configure(yscrollcommand=self.paired_scrollbar.set)
        self.paired_canvas.pack(side="left", fill="both", expand=True)
        self.paired_scrollbar.pack(side="right", fill="y")
        self.paired_canvas.bind("<Configure>", lambda e: self.paired_canvas.itemconfig(self.paired_window, width=e.width))

        # Tab 2: Lokaal
        local_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(local_frame)

        self.local_canvas = tk.Canvas(local_frame, bg=t("bg"), highlightthickness=0)
        self.local_scrollbar = tk.Scrollbar(local_frame, orient="vertical", command=self.local_canvas.yview)
        self.local_inner = tk.Frame(self.local_canvas, bg=t("bg"))
        self.local_inner.bind("<Configure>", lambda e: self.local_canvas.configure(scrollregion=self.local_canvas.bbox("all")))
        self.local_window = self.local_canvas.create_window((0, 0), window=self.local_inner, anchor="nw")
        self.local_canvas.configure(yscrollcommand=self.local_scrollbar.set)
        self.local_canvas.pack(side="left", fill="both", expand=True)
        self.local_scrollbar.pack(side="right", fill="y")
        self.local_canvas.bind("<Configure>", lambda e: self.local_canvas.itemconfig(self.local_window, width=e.width))

        # Tab 3: Besturing
        control_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(control_frame)

        self.control_canvas = tk.Canvas(control_frame, bg=t("bg"), highlightthickness=0)
        self.control_scrollbar = tk.Scrollbar(control_frame, orient="vertical", command=self.control_canvas.yview)
        self.control_inner = tk.Frame(self.control_canvas, bg=t("bg"))
        self.control_inner.bind("<Configure>", lambda e: self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all")))
        self.control_window = self.control_canvas.create_window((0, 0), window=self.control_inner, anchor="nw")
        self.control_canvas.configure(yscrollcommand=self.control_scrollbar.set)
        self.control_canvas.pack(side="left", fill="both", expand=True)
        self.control_scrollbar.pack(side="right", fill="y")
        self.control_canvas.bind("<Configure>", lambda e: self.control_canvas.itemconfig(self.control_window, width=e.width))

        # Tab 4: Beveiliging
        security_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(security_frame)

        self.security_canvas = tk.Canvas(security_frame, bg=t("bg"), highlightthickness=0)
        self.security_scrollbar = tk.Scrollbar(security_frame, orient="vertical", command=self.security_canvas.yview)
        self.security_inner = tk.Frame(self.security_canvas, bg=t("bg"))
        self.security_inner.bind("<Configure>", lambda e: self.security_canvas.configure(scrollregion=self.security_canvas.bbox("all")))
        self.security_window = self.security_canvas.create_window((0, 0), window=self.security_inner, anchor="nw")
        self.security_canvas.configure(yscrollcommand=self.security_scrollbar.set)
        self.security_canvas.pack(side="left", fill="both", expand=True)
        self.security_scrollbar.pack(side="right", fill="y")
        self.security_canvas.bind("<Configure>", lambda e: self.security_canvas.itemconfig(self.security_window, width=e.width))

        # Tab 5: Batterij
        bat_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(bat_frame)

        self.bat_canvas = tk.Canvas(bat_frame, bg=t("bg"), highlightthickness=0)
        self.bat_scrollbar = tk.Scrollbar(bat_frame, orient="vertical", command=self.bat_canvas.yview)
        self.bat_inner = tk.Frame(self.bat_canvas, bg=t("bg"))
        self.bat_inner.bind("<Configure>", lambda e: self.bat_canvas.configure(scrollregion=self.bat_canvas.bbox("all")))
        self.bat_window = self.bat_canvas.create_window((0, 0), window=self.bat_inner, anchor="nw")
        self.bat_canvas.configure(yscrollcommand=self.bat_scrollbar.set)
        self.bat_canvas.pack(side="left", fill="both", expand=True)
        self.bat_scrollbar.pack(side="right", fill="y")
        self.bat_canvas.bind("<Configure>", lambda e: self.bat_canvas.itemconfig(self.bat_window, width=e.width))

        # Tab 6: Update
        update_frame = tk.Frame(tab_frame, bg=t("bg"))
        self.tab_contents.append(update_frame)

        self.update_canvas = tk.Canvas(update_frame, bg=t("bg"), highlightthickness=0)
        self.update_scrollbar = tk.Scrollbar(update_frame, orient="vertical", command=self.update_canvas.yview)
        self.update_inner = tk.Frame(self.update_canvas, bg=t("bg"))
        self.update_inner.bind("<Configure>", lambda e: self.update_canvas.configure(scrollregion=self.update_canvas.bbox("all")))
        self.update_window = self.update_canvas.create_window((0, 0), window=self.update_inner, anchor="nw")
        self.update_canvas.configure(yscrollcommand=self.update_scrollbar.set)
        self.update_canvas.pack(side="left", fill="both", expand=True)
        self.update_scrollbar.pack(side="right", fill="y")
        self.update_canvas.bind("<Configure>", lambda e: self.update_canvas.itemconfig(self.update_window, width=e.width))

        # Toon eerste tab
        for i, frame in enumerate(self.tab_contents):
            if i == 0:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

        # Laad data
        self.load_paired_devices()
        self.refresh_battery_tab()

        # Muiswiel scrolling voor alle canvassen
        def on_mousewheel(event):
            for canvas in [self.canvas, self.paired_canvas, self.local_canvas,
                           self.control_canvas, self.security_canvas,
                           self.bat_canvas, self.update_canvas]:
                try:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except Exception:
                    pass

        self.root.bind_all("<MouseWheel>", on_mousewheel)
        self.root.bind_all("<Button-4>", lambda e: self._scroll_all(-1))
        self.root.bind_all("<Button-5>", lambda e: self._scroll_all(1))

    def _scroll_all(self, direction):
        for canvas in [self.canvas, self.paired_canvas, self.local_canvas,
                       self.control_canvas, self.security_canvas,
                       self.bat_canvas, self.update_canvas]:
            try:
                canvas.yview_scroll(direction, "units")
            except Exception:
                pass

    def switch_tab(self, idx):
        self.current_tab = idx
        for i, frame in enumerate(self.tab_contents):
            if i == idx:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()
        for i, btn in enumerate(self.tab_buttons):
            btn.configure(bg=t("accent3") if i == idx else t("card"))

        if idx == 1:
            self.load_paired_devices()
        elif idx == 2:
            self.load_local_devices()
        elif idx == 3:
            self.load_controls()
        elif idx == 4:
            self.load_security()
        elif idx == 5:
            self.refresh_battery_tab()
        elif idx == 6:
            self.load_update_tab()

    def cycle_theme(self):
        names = list(THEMES.keys())
        idx = names.index(current_theme_name)
        new_name = names[(idx + 1) % len(names)]
        self.set_theme(new_name)

    def set_theme(self, name):
        global current_theme_name, current_theme
        current_theme_name = name
        current_theme = THEMES[name]
        self.root.configure(bg=t("bg"))
        self.save_notes()
        self.root.after(100, self.rebuild_ui)

    def rebuild_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.build_ui()

    def on_search(self, *args):
        self.filter_text = self.search_var.get().lower()
        self.filter_devices()

    def filter_devices(self):
        for card in self.scan_inner.winfo_children():
            name = card.device_name.lower() if hasattr(card, "device_name") else ""
            addr = card.device_addr if hasattr(card, "device_addr") else ""
            if self.filter_text in name or self.filter_text in addr:
                card.pack(fill=tk.X, pady=6, padx=4)
            else:
                card.pack_forget()

    # ─── Scan ──────────────────────────────────────────────────

    def toggle_scan(self):
        if self.scanning:
            self.stop_scan()
        else:
            self.start_scan()

    def start_scan(self):
        self.scanning = True
        self.scan_btn.configure(text="Stop Scannen", bg=t("red"))
        self.status_var.set("Scannen naar Bluetooth apparaten...")
        self.found_devices.clear()
        for w in self.scan_inner.winfo_children():
            w.destroy()
        self.stop_event.clear()
        self.scan_thread = threading.Thread(target=self._run_scan, daemon=True)
        self.scan_thread.start()

    def stop_scan(self):
        self.scanning = False
        self.stop_event.set()
        self.scan_btn.configure(text="Zoek Bluetooth Apparaten", bg=t("accent"))
        self.status_var.set(f"{len(self.found_devices)} appara(a)ten gevonden")

    def _run_scan(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scan_devices(self._on_device_found, self.stop_event))

    def _on_device_found(self, info):
        addr = info["address"]
        if addr not in self.found_devices:
            self.found_devices[addr] = info
            self.root.after(0, self._add_device_card, info)

    def _add_device_card(self, info):
        addr = info["address"]
        name = info["name"]
        rssi = info.get("rssi")

        card = tk.Frame(self.scan_inner, bg=t("card"), highlightbackground=t("border"),
                        highlightthickness=1, bd=0)
        card.device_name = name
        card.device_addr = addr

        inner = tk.Frame(card, bg=t("card"))
        inner.pack(fill=tk.X, padx=16, pady=12)

        hdr = tk.Frame(inner, bg=t("card"))
        hdr.pack(fill=tk.X)

        emoji = get_device_emoji(name)
        icon_frame = tk.Frame(hdr, bg=t("accent3"), width=50, height=50)
        icon_frame.pack(side=tk.LEFT, padx=(0, 12))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=emoji, font=("Segoe UI", 18),
                 bg=t("accent3"), fg=t("text")).place(relx=0.5, rely=0.5, anchor="center")

        info_frame = tk.Frame(hdr, bg=t("card"))
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(info_frame, text=name, font=("Segoe UI", 13, "bold"),
                 bg=t("card"), fg=t("text")).pack(anchor="w")
        tk.Label(info_frame, text=addr, font=("Consolas", 9),
                 bg=t("card"), fg=t("dim")).pack(anchor="w")

        if rssi is not None:
            color = t("green") if rssi > -50 else t("yellow") if rssi > -70 else t("red")
            bars = "█" * max(1, min(6, (rssi + 100) // 10))
            tk.Label(info_frame, text=f"{bars}  {rssi} dBm",
                     font=("Consolas", 9), bg=t("card"), fg=color).pack(anchor="w")

        type_text = get_device_type_text(name)
        if type_text:
            tk.Label(info_frame, text=type_text, font=("Segoe UI", 9),
                     bg=t("card"), fg=t("accent")).pack(anchor="w")

        connect_btn = tk.Button(
            hdr, text="Verbind", font=("Segoe UI", 10, "bold"),
            bg=t("accent2"), fg="#ffffff", activebackground=t("accent"),
            relief="flat", cursor="hand2", bd=0,
            command=lambda a=addr, n=name: self.connect_device(a, n),
        )
        connect_btn.pack(side=tk.RIGHT, padx=(12, 0))

        card.pack(fill=tk.X, pady=6, padx=4)

    def connect_device(self, address, name):
        threading.Thread(
            target=lambda: asyncio.run(self._connect_device(address, name)),
            daemon=True,
        ).start()

    async def _connect_device(self, address, name):
        try:
            self.root.after(0, self.status_var.set, f"Verbinden met {name}...")
            async with BleakClient(address) as client:
                self.connected_clients[address] = client
                info = {"name": name, "address": address, "services": []}
                for service in client.services:
                    svc_info = {"uuid": str(service.uuid), "description": service.description or str(service.uuid), "characteristics": []}
                    for char in service.characteristics:
                        char_info = {"uuid": str(char.uuid), "properties": list(char.properties)}
                        if "read" in char.properties:
                            try:
                                val = await client.read_gatt_char(char.uuid)
                                try:
                                    decoded = val.decode("utf-8").strip()
                                except Exception:
                                    decoded = val.hex()
                                char_info["value"] = decoded
                            except Exception:
                                pass
                        svc_info["characteristics"].append(char_info)
                    info["services"].append(svc_info)

                battery_level = None
                try:
                    val = await client.read_gatt_char("00002a19-0000-1000-8000-00805f9b34fb")
                    battery_level = val[0]
                except Exception:
                    pass

                self.root.after(0, self._show_device_details, info, battery_level)

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self.status_var.set, f"Fout: {error_msg}")
            def show_error(msg=error_msg, dev=name):
                messagebox.showerror("Fout", f"Kan niet verbinden met {dev}:\n{msg}")
            self.root.after(0, show_error)

    def _show_device_details(self, info, battery_level):
        win = tk.Toplevel(self.root)
        win.title(f"{info['name']}")
        win.geometry("650x750")
        win.configure(bg=t("bg"))

        canvas = tk.Canvas(win, bg=t("bg"), highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=t("bg"))
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        # Header
        emoji = get_device_emoji(info["name"])
        hdr_frame = tk.Frame(inner, bg=t("bg"))
        hdr_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        tk.Label(hdr_frame, text=emoji, font=("Segoe UI", 32), bg=t("bg"), fg=t("accent")).pack(side=tk.LEFT, padx=(0, 12))
        name_frame = tk.Frame(hdr_frame, bg=t("bg"))
        name_frame.pack(side=tk.LEFT)
        tk.Label(name_frame, text=info["name"], font=("Segoe UI", 18, "bold"), bg=t("bg"), fg=t("text")).pack(anchor="w")
        tk.Label(name_frame, text=info["address"], font=("Consolas", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w")

        # Notitie
        note_frame = tk.Frame(inner, bg=t("card"), highlightbackground=t("border"), highlightthickness=1)
        note_frame.pack(fill=tk.X, padx=20, pady=12)
        tk.Label(note_frame, text="Notitie:", font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", padx=12, pady=(8, 0))
        note_entry = tk.Entry(note_frame, font=("Segoe UI", 10), bg=t("bg"), fg=t("text"),
                              insertbackground=t("accent"), relief="flat")
        note_entry.pack(fill=tk.X, padx=12, pady=(0, 8), ipady=4)
        addr = info["address"]
        if addr in self.device_notes:
            note_entry.insert(0, self.device_notes[addr])

        def save_note():
            self.device_notes[addr] = note_entry.get()
            self.save_notes()
        tk.Button(note_frame, text="Opslaan", font=("Segoe UI", 8), bg=t("accent3"),
                  fg=t("text"), relief="flat", cursor="hand2", command=save_note).pack(anchor="e", padx=12, pady=(0, 8))

        # Batterij
        if battery_level is not None:
            bat_frame = tk.Frame(inner, bg=t("card"), highlightbackground=t("glow"), highlightthickness=1)
            bat_frame.pack(fill=tk.X, padx=20, pady=8)
            color = t("green") if battery_level > 60 else t("yellow") if battery_level > 20 else t("red")
            tk.Label(bat_frame, text=f"Batterij: {battery_level}%", font=("Segoe UI", 14, "bold"),
                     bg=t("card"), fg=color).pack(anchor="w", padx=16, pady=(12, 0))
            bar_bg = tk.Frame(bat_frame, bg=t("border"), height=12)
            bar_bg.pack(fill=tk.X, padx=16, pady=(4, 12))
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=color, height=12, width=max(1, int(560 * battery_level / 100))).place(x=0, y=0, relheight=1.0)

        # Services
        tk.Label(inner, text="Services & Eigenschappen", font=("Segoe UI", 14, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=20, pady=(12, 8))

        for service in info["services"]:
            svc_frame = tk.Frame(inner, bg=t("card"), highlightbackground=t("border"), highlightthickness=1)
            svc_frame.pack(fill=tk.X, padx=20, pady=4)
            tk.Label(svc_frame, text=service["description"], font=("Segoe UI", 11, "bold"),
                     bg=t("card"), fg=t("accent")).pack(anchor="w", padx=12, pady=(8, 0))
            tk.Label(svc_frame, text=service["uuid"], font=("Consolas", 8),
                     bg=t("card"), fg=t("dim")).pack(anchor="w", padx=12)
            for char in service["characteristics"]:
                props = ", ".join(char["properties"])
                txt = f"  {char['uuid'][:8]}...  [{props}]"
                if "value" in char:
                    txt += f"  = {char['value']}"
                color = t("green") if "value" in char else t("dim")
                tk.Label(svc_frame, text=txt, font=("Consolas", 9),
                         bg=t("card"), fg=color).pack(anchor="w", padx=16)

        tk.Label(inner, text="", bg=t("bg")).pack(pady=20)

    # ─── Gekoppelde apparaten ───────────────────────────────────

    def load_paired_devices(self):
        for w in self.paired_inner.winfo_children():
            w.destroy()
        devices = get_paired_devices()
        sec = load_security()
        if not devices:
            tk.Label(self.paired_inner, text="Geen gekoppelde apparaten",
                     font=("Segoe UI", 12), bg=t("bg"), fg=t("dim")).pack(pady=40)
            return

        for dev in devices:
            card = tk.Frame(self.paired_inner, bg=t("card"), highlightbackground=t("border"), highlightthickness=1)
            card.pack(fill=tk.X, pady=6, padx=4)

            inner = tk.Frame(card, bg=t("card"))
            inner.pack(fill=tk.X, padx=16, pady=12)

            hdr = tk.Frame(inner, bg=t("card"))
            hdr.pack(fill=tk.X)

            emoji = get_device_emoji(dev.get("name", ""))
            icon_frame = tk.Frame(hdr, bg=t("accent3"), width=50, height=50)
            icon_frame.pack(side=tk.LEFT, padx=(0, 12))
            icon_frame.pack_propagate(False)
            tk.Label(icon_frame, text=emoji, font=("Segoe UI", 18),
                     bg=t("accent3"), fg=t("text")).place(relx=0.5, rely=0.5, anchor="center")

            name_frame = tk.Frame(hdr, bg=t("card"))
            name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            display_name = dev.get("alias") or dev.get("name", "Onbekend")
            tk.Label(name_frame, text=display_name, font=("Segoe UI", 13, "bold"),
                     bg=t("card"), fg=t("text")).pack(anchor="w")
            tk.Label(name_frame, text=dev["address"], font=("Consolas", 9),
                     bg=t("card"), fg=t("dim")).pack(anchor="w")

            connect_btn = tk.Button(
                hdr, text="Verbind", font=("Segoe UI", 10, "bold"),
                bg=t("accent2"), fg="#ffffff", activebackground=t("accent"),
                relief="flat", cursor="hand2", bd=0,
                command=lambda a=dev["address"], n=display_name: self.connect_device(a, n),
            )
            connect_btn.pack(side=tk.RIGHT, padx=(12, 0))

            # Info pills
            info_frame = tk.Frame(inner, bg=t("card"))
            info_frame.pack(fill=tk.X, pady=(8, 0))

            dev_type = dev.get("type", "") or get_device_type_text(dev.get("name", ""))
            if dev_type:
                self._add_pill(info_frame, "Type", dev_type)

            connected = dev.get("connected", "no")
            status_color = t("green") if connected == "yes" else t("dim")
            status_text = "Verbonden" if connected == "yes" else "Niet verbonden"
            self._add_pill(info_frame, "Status", status_text, status_color)

            trusted = dev.get("trusted", "")
            if trusted:
                self._add_pill(info_frame, "Vertrouwd", trusted.title())

            battery = dev.get("battery")
            if battery is not None:
                bat_color = t("green") if battery > 60 else t("yellow") if battery > 20 else t("red")
                self._add_pill(info_frame, "Batterij", f"{battery}%", bat_color)

            # Beveiligingsstatus
            addr = dev["address"]
            if addr in sec["blocked"]:
                self._add_pill(info_frame, "Beveiliging", "Geblokkeerd", t("red"))
            elif sec["whitelist"] and addr in sec["whitelist"]:
                self._add_pill(info_frame, "Beveiliging", "Toegestaan", t("green"))
            elif sec["whitelist"]:
                self._add_pill(info_frame, "Beveiliging", "Niet op whitelist", t("yellow"))
            else:
                self._add_pill(info_frame, "Beveiliging", "Geen restricties", t("dim"))

            uuids = dev.get("uuids", [])
            if uuids:
                uuid_frame = tk.Frame(inner, bg=t("card"))
                uuid_frame.pack(fill=tk.X, pady=(6, 0))
                tk.Label(uuid_frame, text="Profielen:", font=("Segoe UI", 9),
                         bg=t("card"), fg=t("dim")).pack(anchor="w")
                for uid in uuids[:6]:
                    desc = resolve_uuid(uid)
                    tk.Label(uuid_frame, text=f"  {desc}", font=("Segoe UI", 9),
                             bg=t("card"), fg=t("text")).pack(anchor="w")

            # ─── Besturing (Media Controls) ─────────────────────
            has_audio = any("audio" in str(uid).lower() or "110b" in str(uid).lower() for uid in uuids)
            is_connected = connected == "yes"

            if is_connected:
                ctrl_card = tk.Frame(inner, bg=t("bg2"), highlightbackground=t("accent"), highlightthickness=1)
                ctrl_card.pack(fill=tk.X, pady=(8, 0))
                ctrl_inner = tk.Frame(ctrl_card, bg=t("bg2"))
                ctrl_inner.pack(fill=tk.X, padx=12, pady=8)

                tk.Label(ctrl_inner, text="Besturing", font=("Segoe UI", 9, "bold"),
                         bg=t("bg2"), fg=t("accent")).pack(anchor="w", pady=(0, 4))

                btn_row = tk.Frame(ctrl_inner, bg=t("bg2"))
                btn_row.pack(fill=tk.X)

                small_btn = {"font": ("Segoe UI", 10), "bg": t("accent3"), "fg": t("text"),
                             "relief": "flat", "cursor": "hand2", "bd": 0, "padx": 10, "pady": 3}

                tk.Button(btn_row, text="⏮", command=media_prev, **small_btn).pack(side=tk.LEFT, padx=(0, 3))
                tk.Button(btn_row, text="⏯", command=media_play, **small_btn).pack(side=tk.LEFT, padx=(0, 3))
                tk.Button(btn_row, text="⏭", command=media_next, **small_btn).pack(side=tk.LEFT, padx=(0, 3))

                vol_row = tk.Frame(ctrl_inner, bg=t("bg2"))
                vol_row.pack(fill=tk.X, pady=(4, 0))
                tk.Button(vol_row, text="-", command=media_volume_down, **small_btn).pack(side=tk.LEFT, padx=(0, 3))
                tk.Button(vol_row, text="🔊", command=media_mute, **small_btn).pack(side=tk.LEFT, padx=(0, 3))
                tk.Button(vol_row, text="+", command=media_volume_up, **small_btn).pack(side=tk.LEFT)

            # ─── Beveiligingsacties per apparaat ────────────────
            sec_card = tk.Frame(inner, bg=t("bg2"), highlightbackground=t("border"), highlightthickness=1)
            sec_card.pack(fill=tk.X, pady=(8, 0))
            sec_inner = tk.Frame(sec_card, bg=t("bg2"))
            sec_inner.pack(fill=tk.X, padx=12, pady=8)

            tk.Label(sec_inner, text="Beveiliging", font=("Segoe UI", 9, "bold"),
                     bg=t("bg2"), fg=t("yellow")).pack(anchor="w", pady=(0, 4))

            sec_btn_row = tk.Frame(sec_inner, bg=t("bg2"))
            sec_btn_row.pack(fill=tk.X)

            if addr in sec["blocked"]:
                def unblock_cmd(a=addr):
                    block_device.__wrapped__ = None
                    s = load_security()
                    if a in s["blocked"]:
                        s["blocked"].remove(a)
                        save_security(s)
                    self.load_paired_devices()
                tk.Button(sec_btn_row, text="Deblokkeer", font=("Segoe UI", 9),
                          bg=t("green"), fg="#000", relief="flat", cursor="hand2",
                          command=unblock_cmd, padx=10, pady=2).pack(side=tk.LEFT, padx=(0, 4))
            else:
                def block_cmd(a=addr):
                    block_device(a)
                    self.load_paired_devices()
                tk.Button(sec_btn_row, text="Blokkeer", font=("Segoe UI", 9),
                          bg=t("red"), fg="#ffffff", relief="flat", cursor="hand2",
                          command=block_cmd, padx=10, pady=2).pack(side=tk.LEFT, padx=(0, 4))

            if sec["whitelist"] and addr not in sec["whitelist"]:
                def allow_cmd(a=addr):
                    add_to_whitelist(a)
                    self.load_paired_devices()
                tk.Button(sec_btn_row, text="Toestaan", font=("Segoe UI", 9),
                          bg=t("green"), fg="#000", relief="flat", cursor="hand2",
                          command=allow_cmd, padx=10, pady=2).pack(side=tk.LEFT, padx=(0, 4))
            elif sec["whitelist"] and addr in sec["whitelist"]:
                def remove_allow_cmd(a=addr):
                    s = load_security()
                    if a in s["whitelist"]:
                        s["whitelist"].remove(a)
                        save_security(s)
                    self.load_paired_devices()
                tk.Button(sec_btn_row, text="Van whitelist", font=("Segoe UI", 9),
                          bg=t("yellow"), fg="#000", relief="flat", cursor="hand2",
                          command=remove_allow_cmd, padx=10, pady=2).pack(side=tk.LEFT, padx=(0, 4))

    def _add_pill(self, parent, label, value, color=None):
        if color is None:
            color = t("text")
        pill = tk.Frame(parent, bg=t("card"))
        pill.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        tk.Label(pill, text=label + ":", font=("Segoe UI", 8),
                 bg=t("card"), fg=t("dim")).pack(side=tk.LEFT)
        tk.Label(pill, text=" " + value, font=("Segoe UI", 9, "bold"),
                 bg=t("card"), fg=color).pack(side=tk.LEFT)

    # ─── Lokale Hardware Tab ────────────────────────────────────

    def load_local_devices(self):
        for w in self.local_inner.winfo_children():
            w.destroy()

        tk.Label(self.local_inner, text="Lokale Hardware", font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(self.local_inner, text="Alle hardware in je PC/laptop",
                 font=("Segoe UI", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w", padx=16, pady=(0, 12))

        # ─── Beveiliging Overzicht ──────────────────────────────
        sec = load_security()
        sec_card = tk.Frame(self.local_inner, bg=t("card"),
                            highlightbackground=t("glow"), highlightthickness=1)
        sec_card.pack(fill=tk.X, padx=16, pady=(0, 12))
        sec_inner = tk.Frame(sec_card, bg=t("card"))
        sec_inner.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(sec_inner, text="Beveiliging Overzicht", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("yellow")).pack(anchor="w")

        pin_status = "Actief" if sec["pin"] else "Niet ingesteld"
        pin_color = t("green") if sec["pin"] else t("dim")
        tk.Label(sec_inner, text=f"  PIN: {pin_status}", font=("Segoe UI", 9),
                 bg=t("card"), fg=pin_color).pack(anchor="w")

        wl_count = len(sec["whitelist"])
        bl_count = len(sec["blocked"])
        if wl_count:
            tk.Label(sec_inner, text=f"  Whitelist: {wl_count} appara(a)ten toegestaan",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("green")).pack(anchor="w")
        else:
            tk.Label(sec_inner, text="  Whitelist: uit (alle apparaten toegestaan)",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w")

        if bl_count:
            tk.Label(sec_inner, text=f"  Geblokkeerd: {bl_count} appara(a)ten",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("red")).pack(anchor="w")
        else:
            tk.Label(sec_inner, text="  Geen apparaten geblokkeerd",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w")

        # USB Beveiliging
        usb_devices = get_usb_devices()
        if usb_devices:
            usb_card = tk.Frame(self.local_inner, bg=t("card"),
                                highlightbackground=t("border"), highlightthickness=1)
            usb_card.pack(fill=tk.X, padx=16, pady=(0, 8))
            usb_inner = tk.Frame(usb_card, bg=t("card"))
            usb_inner.pack(fill=tk.X, padx=12, pady=10)

            tk.Label(usb_inner, text="USB Beveiliging", font=("Segoe UI", 10, "bold"),
                     bg=t("card"), fg=t("accent")).pack(anchor="w")
            tk.Label(usb_inner, text="USB apparaten worden automatisch gedetecteerd",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(2, 4))

            usb_sec_frame = tk.Frame(usb_inner, bg=t("card"))
            usb_sec_frame.pack(fill=tk.X)

            tk.Label(usb_sec_frame, text=f"  {len(usb_devices)} USB appara(a)ten gedetecteerd",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("text")).pack(anchor="w")

            for dev in usb_devices[:5]:
                tk.Label(usb_sec_frame, text=f"    {dev['icon']} {dev['name']}",
                         font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w")

        # Ververs knop
        refresh_btn = tk.Button(self.local_inner, text="Ververs", font=("Segoe UI", 9),
                                bg=t("accent3"), fg=t("text"), relief="flat", cursor="hand2",
                                command=self.load_local_devices, padx=12, pady=4)
        refresh_btn.pack(anchor="w", padx=16, pady=(8, 12))

        devices = get_all_local_devices()

        # Groepeer per type
        groups = {}
        for dev in devices:
            gtype = dev["type"]
            if gtype not in groups:
                groups[gtype] = []
            groups[gtype].append(dev)

        type_order = ["USB", "PCI", "HDMI", "Audio", "Microfoon", "Opslag"]
        type_emojis = {
            "USB": "🔌", "PCI": "🖥️", "HDMI": "📺",
            "Audio": "🔊", "Microfoon": "🎤", "Opslag": "💾"
        }

        for gtype in type_order:
            if gtype not in groups:
                continue
            grp = groups[gtype]

            grp_frame = tk.Frame(self.local_inner, bg=t("card"),
                                 highlightbackground=t("glow"), highlightthickness=1)
            grp_frame.pack(fill=tk.X, padx=16, pady=6)

            hdr = tk.Frame(grp_frame, bg=t("card"))
            hdr.pack(fill=tk.X, padx=12, pady=(10, 4))
            emoji = type_emojis.get(gtype, "📦")
            tk.Label(hdr, text=f"{emoji}  {gtype}", font=("Segoe UI", 12, "bold"),
                     bg=t("card"), fg=t("accent")).pack(side=tk.LEFT)
            tk.Label(hdr, text=f"({len(grp)})", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(side=tk.LEFT, padx=(8, 0))

            for dev in grp:
                dev_frame = tk.Frame(grp_frame, bg=t("card"))
                dev_frame.pack(fill=tk.X, padx=12, pady=2)
                tk.Label(dev_frame, text=f"  {dev['icon']}", font=("Segoe UI", 11),
                         bg=t("card"), fg=t("text")).pack(side=tk.LEFT)
                tk.Label(dev_frame, text=f"  {dev['name']}", font=("Segoe UI", 10),
                         bg=t("card"), fg=t("text")).pack(side=tk.LEFT, padx=(0, 8))
                if dev.get("id"):
                    tk.Label(dev_frame, text=dev["id"], font=("Consolas", 8),
                             bg=t("card"), fg=t("dim")).pack(side=tk.LEFT)

                # Beveiligingsindicator per apparaat
                if gtype == "USB":
                    tk.Label(dev_frame, text="✓", font=("Segoe UI", 9),
                             bg=t("card"), fg=t("green")).pack(side=tk.RIGHT)

            tk.Frame(grp_frame, bg=t("card"), height=6).pack()

        if not devices:
            tk.Label(self.local_inner, text="Geen hardware gevonden",
                     font=("Segoe UI", 11), bg=t("bg"), fg=t("dim")).pack(pady=40)

    # ─── Besturing Tab ──────────────────────────────────────────

    def load_controls(self):
        for w in self.control_inner.winfo_children():
            w.destroy()

        tk.Label(self.control_inner, text="Media Besturing", font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=20, pady=(20, 4))
        tk.Label(self.control_inner, text="Bestuur je muziek en volume",
                 font=("Segoe UI", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w", padx=20, pady=(0, 16))

        # Muziek info
        media_info = get_media_info()
        info_card = tk.Frame(self.control_inner, bg=t("card"),
                             highlightbackground=t("border"), highlightthickness=1)
        info_card.pack(fill=tk.X, padx=20, pady=(0, 12))
        info_inner = tk.Frame(info_card, bg=t("card"))
        info_inner.pack(fill=tk.X, padx=16, pady=12)
        tk.Label(info_inner, text="Nu aan het afspelen:", font=("Segoe UI", 9),
                 bg=t("card"), fg=t("dim")).pack(anchor="w")
        title = media_info.get("title", "") or "Geen muziek"
        artist = media_info.get("artist", "") or ""
        tk.Label(info_inner, text=title, font=("Segoe UI", 14, "bold"),
                 bg=t("card"), fg=t("text")).pack(anchor="w")
        if artist:
            tk.Label(info_inner, text=artist, font=("Segoe UI", 11),
                     bg=t("card"), fg=t("accent")).pack(anchor="w")

        # Media controls
        ctrl_card = tk.Frame(self.control_inner, bg=t("card"),
                             highlightbackground=t("border"), highlightthickness=1)
        ctrl_card.pack(fill=tk.X, padx=20, pady=(0, 12))
        ctrl_inner = tk.Frame(ctrl_card, bg=t("card"))
        ctrl_inner.pack(fill=tk.X, padx=16, pady=16)

        tk.Label(ctrl_inner, text="Muziek", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(ctrl_inner, bg=t("card"))
        btn_row.pack(fill=tk.X)

        btn_style = {"font": ("Segoe UI", 12), "bg": t("accent3"), "fg": t("text"),
                     "relief": "flat", "cursor": "hand2", "bd": 0, "padx": 16, "pady": 8}

        tk.Button(btn_row, text="⏮", command=media_prev, **btn_style).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_row, text="⏯", command=media_play, **btn_style).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_row, text="⏭", command=media_next, **btn_style).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_row, text="⏹", command=media_stop, **btn_style).pack(side=tk.LEFT, padx=(0, 4))

        # Volume controls
        vol_card = tk.Frame(self.control_inner, bg=t("card"),
                            highlightbackground=t("border"), highlightthickness=1)
        vol_card.pack(fill=tk.X, padx=20, pady=(0, 12))
        vol_inner = tk.Frame(vol_card, bg=t("card"))
        vol_inner.pack(fill=tk.X, padx=16, pady=16)

        tk.Label(vol_inner, text="Volume", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w", pady=(0, 8))

        vol_row = tk.Frame(vol_inner, bg=t("card"))
        vol_row.pack(fill=tk.X)

        tk.Button(vol_row, text="-", command=media_volume_down, **btn_style).pack(side=tk.LEFT, padx=(0, 4))
        current_vol = get_current_volume()
        self.vol_label = tk.Label(vol_row, text=f"{current_vol}%", font=("Segoe UI", 14, "bold"),
                                  bg=t("card"), fg=t("text"))
        self.vol_label.pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(vol_row, text="+", command=media_volume_up, **btn_style).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(vol_row, text="🔇", command=media_mute, **btn_style).pack(side=tk.LEFT, padx=(12, 0))

        # Ververs knop
        tk.Button(self.control_inner, text="Ververs Info", font=("Segoe UI", 9),
                  bg=t("accent3"), fg=t("text"), relief="flat", cursor="hand2",
                  command=self.load_controls, padx=12, pady=4).pack(anchor="w", padx=20, pady=(8, 0))

        # ─── Toetsenbord & Muis ─────────────────────────────────
        tk.Label(self.control_inner, text="Toetsenbord & Muis (HID)",
                 font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=20, pady=(20, 4))
        tk.Label(self.control_inner, text="Bestuur verbonden HID apparaten (toetsenbord/muis)",
                 font=("Segoe UI", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w", padx=20, pady=(0, 12))

        # Apparaat selectie
        paired = get_paired_devices()
        hid_devices = [d for d in paired if d.get("connected") == "yes"]

        if not hid_devices:
            info_card = tk.Frame(self.control_inner, bg=t("card"),
                                 highlightbackground=t("border"), highlightthickness=1)
            info_card.pack(fill=tk.X, padx=20, pady=6)
            tk.Label(info_card, text="Geen verbonden apparaten gevonden",
                     font=("Segoe UI", 11), bg=t("card"), fg=t("dim")).pack(pady=16)
            tk.Label(info_card, text="Verbind eerst een apparaat via de Gekoppeld tab",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(pady=(0, 16))
        else:
            # Apparaat kiezer
            sel_card = tk.Frame(self.control_inner, bg=t("card"),
                                highlightbackground=t("glow"), highlightthickness=1)
            sel_card.pack(fill=tk.X, padx=20, pady=6)
            sel_inner = tk.Frame(sel_card, bg=t("card"))
            sel_inner.pack(fill=tk.X, padx=12, pady=10)

            tk.Label(sel_inner, text="Kies apparaat:", font=("Segoe UI", 10, "bold"),
                     bg=t("card"), fg=t("accent")).pack(anchor="w", pady=(0, 4))

            self.hid_device_var = tk.StringVar(value=hid_devices[0]["address"] if hid_devices else "")
            for dev in hid_devices:
                addr = dev["address"]
                name = dev.get("alias") or dev.get("name", addr)
                emoji = get_device_emoji(name)
                rb = tk.Radiobutton(sel_inner, text=f"{emoji} {name} ({addr})",
                                    variable=self.hid_device_var, value=addr,
                                    bg=t("card"), fg=t("text"), selectcolor=t("bg2"),
                                    activebackground=t("card"), activeforeground=t("accent"),
                                    font=("Segoe UI", 10))
                rb.pack(anchor="w", pady=1)

            # Toetsenbord sectie
            kb_card = tk.Frame(self.control_inner, bg=t("card"),
                               highlightbackground=t("border"), highlightthickness=1)
            kb_card.pack(fill=tk.X, padx=20, pady=6)
            kb_inner = tk.Frame(kb_card, bg=t("card"))
            kb_inner.pack(fill=tk.X, padx=12, pady=10)

            tk.Label(kb_inner, text="Toetsenbord", font=("Segoe UI", 11, "bold"),
                     bg=t("card"), fg=t("accent")).pack(anchor="w", pady=(0, 8))

            # Sneltoetsen
            shortcut_row = tk.Frame(kb_inner, bg=t("card"))
            shortcut_row.pack(fill=tk.X, pady=(0, 8))

            small_btn = {"font": ("Segoe UI", 9), "bg": t("accent3"), "fg": t("text"),
                         "relief": "flat", "cursor": "hand2", "bd": 0, "padx": 8, "pady": 3}

            shortcuts = [
                ("Ctrl+C", ["ctrl", "c"]), ("Ctrl+V", ["ctrl", "v"]),
                ("Ctrl+Z", ["ctrl", "z"]), ("Ctrl+A", ["ctrl", "a"]),
                ("Ctrl+S", ["ctrl", "s"]), ("Ctrl+X", ["ctrl", "x"]),
                ("Tab", ["tab"]), ("Esc", ["esc"]),
            ]
            for label, keys in shortcuts:
                def cmd(k=keys):
                    self._hid_send_combo(k)
                tk.Button(shortcut_row, text=label, command=cmd, **small_btn).pack(side=tk.LEFT, padx=(0, 3))

            # Enter / Backspace / Spatie
            nav_row = tk.Frame(kb_inner, bg=t("card"))
            nav_row.pack(fill=tk.X, pady=(0, 8))
            tk.Button(nav_row, text="Enter", command=lambda: self._hid_send_key("enter"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Backspace", command=lambda: self._hid_send_key("backspace"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Spatie", command=lambda: self._hid_send_key("space"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Pijl ↑", command=lambda: self._hid_send_key("up"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Pijl ↓", command=lambda: self._hid_send_key("down"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Pijl ←", command=lambda: self._hid_send_key("left"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))
            tk.Button(nav_row, text="Pijl →", command=lambda: self._hid_send_key("right"), **small_btn).pack(side=tk.LEFT, padx=(0, 3))

            # Tekst typen
            type_frame = tk.Frame(kb_inner, bg=t("card"))
            type_frame.pack(fill=tk.X, pady=(4, 0))
            tk.Label(type_frame, text="Tekst typen:", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(side=tk.LEFT)
            self.hid_text_entry = tk.Entry(type_frame, font=("Segoe UI", 10), bg=t("bg"), fg=t("text"),
                                          insertbackground=t("accent"), relief="flat")
            self.hid_text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8), ipady=3)
            tk.Button(type_frame, text="Typ", command=self._hid_send_text,
                      font=("Segoe UI", 9, "bold"), bg=t("accent"), fg="#fff",
                      relief="flat", cursor="hand2", padx=12).pack(side=tk.LEFT)

            # Muis sectie
            mouse_card = tk.Frame(self.control_inner, bg=t("card"),
                                  highlightbackground=t("border"), highlightthickness=1)
            mouse_card.pack(fill=tk.X, padx=20, pady=6)
            mouse_inner = tk.Frame(mouse_card, bg=t("card"))
            mouse_inner.pack(fill=tk.X, padx=12, pady=10)

            tk.Label(mouse_inner, text="Muis", font=("Segoe UI", 11, "bold"),
                     bg=t("card"), fg=t("accent")).pack(anchor="w", pady=(0, 8))

            # Klik knoppen
            click_row = tk.Frame(mouse_inner, bg=t("card"))
            click_row.pack(fill=tk.X, pady=(0, 8))

            tk.Button(click_row, text="Linker Klik", command=lambda: self._hid_mouse_click("left"),
                      font=("Segoe UI", 10, "bold"), bg=t("accent3"), fg=t("text"),
                      relief="flat", cursor="hand2", padx=16, pady=6).pack(side=tk.LEFT, padx=(0, 4))
            tk.Button(click_row, text="Rechter Klik", command=lambda: self._hid_mouse_click("right"),
                      font=("Segoe UI", 10, "bold"), bg=t("accent3"), fg=t("text"),
                      relief="flat", cursor="hand2", padx=16, pady=6).pack(side=tk.LEFT, padx=(0, 4))
            tk.Button(click_row, text="Middel Klik", command=lambda: self._hid_mouse_click("middle"),
                      font=("Segoe UI", 10), bg=t("accent3"), fg=t("text"),
                      relief="flat", cursor="hand2", padx=12, pady=6).pack(side=tk.LEFT)

            # Beweeg muis
            move_frame = tk.Frame(mouse_inner, bg=t("card"))
            move_frame.pack(fill=tk.X, pady=(0, 8))
            tk.Label(move_frame, text="Beweeg:", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(side=tk.LEFT)

            tk.Button(move_frame, text="←", command=lambda: self._hid_mouse_move(-50, 0), **small_btn).pack(side=tk.LEFT, padx=2)
            tk.Button(move_frame, text="→", command=lambda: self._hid_mouse_move(50, 0), **small_btn).pack(side=tk.LEFT, padx=2)
            tk.Button(move_frame, text="↑", command=lambda: self._hid_mouse_move(0, -50), **small_btn).pack(side=tk.LEFT, padx=2)
            tk.Button(move_frame, text="↓", command=lambda: self._hid_mouse_move(0, 50), **small_btn).pack(side=tk.LEFT, padx=2)

            # Scroll
            scroll_frame = tk.Frame(mouse_inner, bg=t("card"))
            scroll_frame.pack(fill=tk.X)
            tk.Label(scroll_frame, text="Scroll:", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(side=tk.LEFT)
            tk.Button(scroll_frame, text="Scroll ↑", command=lambda: self._hid_mouse_scroll(3), **small_btn).pack(side=tk.LEFT, padx=(8, 2))
            tk.Button(scroll_frame, text="Scroll ↓", command=lambda: self._hid_mouse_scroll(-3), **small_btn).pack(side=tk.LEFT, padx=2)

    def _hid_get_address(self):
        if hasattr(self, "hid_device_var"):
            return self.hid_device_var.get()
        paired = get_paired_devices()
        for d in paired:
            if d.get("connected") == "yes":
                return d["address"]
        return None

    def _hid_send_key(self, key):
        addr = self._hid_get_address()
        if not addr:
            messagebox.showwarning("Let op", "Selecteer eerst een apparaat!")
            return
        try:
            from hid_controller import quick_key
            threading.Thread(target=lambda: asyncio.run(quick_key(addr, key)), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Fout", f"Kon niet versturen: {e}")

    def _hid_send_combo(self, keys):
        addr = self._hid_get_address()
        if not addr:
            messagebox.showwarning("Let op", "Selecteer eerst een apparaat!")
            return
        try:
            from hid_controller import quick_key, SPECIAL_KEYS
            modifier = 0
            key = None
            for k in keys:
                k_lower = k.lower()
                if k_lower in SPECIAL_KEYS:
                    modifier |= SPECIAL_KEYS[k_lower][1]
                else:
                    key = k_lower
            def _do():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(quick_key(addr, key or "a", modifier if modifier else None))
            threading.Thread(target=_do, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Fout", f"Kon niet versturen: {e}")

    def _hid_send_text(self):
        addr = self._hid_get_address()
        text = self.hid_text_entry.get() if hasattr(self, "hid_text_entry") else ""
        if not addr:
            messagebox.showwarning("Let op", "Selecteer eerst een apparaat!")
            return
        if not text:
            return
        try:
            from hid_controller import quick_type
            threading.Thread(target=lambda: asyncio.run(quick_type(addr, text)), daemon=True).start()
            self.hid_text_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Fout", f"Kon niet typen: {e}")

    def _hid_mouse_click(self, button):
        addr = self._hid_get_address()
        if not addr:
            messagebox.showwarning("Let op", "Selecteer eerst een apparaat!")
            return
        try:
            from hid_controller import quick_click
            threading.Thread(target=lambda: asyncio.run(quick_click(addr, button)), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Fout", f"Kon niet klikken: {e}")

    def _hid_mouse_move(self, dx, dy):
        addr = self._hid_get_address()
        if not addr:
            return
        try:
            from hid_controller import quick_move
            threading.Thread(target=lambda: asyncio.run(quick_move(addr, dx, dy)), daemon=True).start()
        except Exception:
            pass

    def _hid_mouse_scroll(self, amount):
        addr = self._hid_get_address()
        if not addr:
            return
        try:
            from hid_controller import HIDController, get_controller
            def _do():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ctrl = loop.run_until_complete(get_controller(addr))
                loop.run_until_complete(ctrl.mouse_scroll(amount))
            threading.Thread(target=_do, daemon=True).start()
        except Exception:
            pass

    # ─── Beveiliging Tab ────────────────────────────────────────

    def load_security(self):
        for w in self.security_inner.winfo_children():
            w.destroy()

        sec = load_security()

        tk.Label(self.security_inner, text="Beveiliging", font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(self.security_inner, text="Beheer welke Bluetooth apparaten toegang hebben tot jouw PC",
                 font=("Segoe UI", 10), bg=t("bg"), fg=t("dim")).pack(anchor="w", padx=16, pady=(0, 12))

        # Uitleg
        info_box = tk.Frame(self.security_inner, bg=t("bg2"), highlightbackground=t("accent"), highlightthickness=1)
        info_box.pack(fill=tk.X, padx=16, pady=(0, 8))
        info_box_inner = tk.Frame(info_box, bg=t("bg2"))
        info_box_inner.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(info_box_inner, text="Hoe werkt het?", font=("Segoe UI", 10, "bold"),
                 bg=t("bg2"), fg=t("accent")).pack(anchor="w")
        for line in [
            "1. Het MAC-adres is van het BLUETOOTH APPARAAT (niet je PC)",
            "2. Vind het MAC-adres bij: Gekoppeld tab → onder de naam",
            "3. Whitelist = alleen deze apparaten mogen verbinden",
            "4. Blokkeer = deze apparaten worden altijd geweigerd",
            "5. Geen whitelist = iedereen mag verbinden (behalve geblokkeerde)",
        ]:
            tk.Label(info_box_inner, text=f"  {line}", font=("Segoe UI", 9),
                     bg=t("bg2"), fg=t("dim")).pack(anchor="w")

        # PIN instellingen
        pin_card = tk.Frame(self.security_inner, bg=t("card"),
                            highlightbackground=t("glow"), highlightthickness=1)
        pin_card.pack(fill=tk.X, padx=16, pady=6)
        pin_inner = tk.Frame(pin_card, bg=t("card"))
        pin_inner.pack(fill=tk.X, padx=12, pady=12)

        tk.Label(pin_inner, text="PIN Code", font=("Segoe UI", 12, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w")

        has_pin = sec["pin"] is not None
        pin_status = "Actief" if has_pin else "Niet ingesteld"
        pin_color = t("green") if has_pin else t("dim")
        tk.Label(pin_inner, text=f"Status: {pin_status}", font=("Segoe UI", 10),
                 bg=t("card"), fg=pin_color).pack(anchor="w", pady=(4, 8))

        pin_frame = tk.Frame(pin_inner, bg=t("card"))
        pin_frame.pack(fill=tk.X)

        self.pin_entry = tk.Entry(pin_frame, font=("Consolas", 12), bg=t("bg"), fg=t("text"),
                                  insertbackground=t("accent"), relief="flat", show="*")
        self.pin_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def set_pin_action():
            pin = self.pin_entry.get().strip()
            if pin:
                set_pin(pin)
                self.load_security()
            else:
                messagebox.showwarning("Let op", "Voer een PIN in!")

        def clear_pin_action():
            set_pin(None)
            self.pin_entry.delete(0, tk.END)
            self.load_security()

        tk.Button(pin_frame, text="Instellen", font=("Segoe UI", 9),
                  bg=t("accent"), fg="#ffffff", relief="flat", cursor="hand2",
                  command=set_pin_action, padx=12).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(pin_frame, text="Verwijder", font=("Segoe UI", 9),
                  bg=t("red"), fg="#ffffff", relief="flat", cursor="hand2",
                  command=clear_pin_action, padx=12).pack(side=tk.LEFT, padx=(4, 0))

        # Whitelist
        wl_card = tk.Frame(self.security_inner, bg=t("card"),
                           highlightbackground=t("border"), highlightthickness=1)
        wl_card.pack(fill=tk.X, padx=16, pady=6)
        wl_inner = tk.Frame(wl_card, bg=t("card"))
        wl_inner.pack(fill=tk.X, padx=12, pady=12)

        tk.Label(wl_inner, text="Toegestane Apparaten (Whitelist)", font=("Segoe UI", 12, "bold"),
                 bg=t("card"), fg=t("green")).pack(anchor="w")
        tk.Label(wl_inner, text="Alleen deze Bluetooth apparaten mogen met je PC verbinden",
                 font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(0, 4))

        if sec["whitelist"]:
            for addr in sec["whitelist"]:
                row = tk.Frame(wl_inner, bg=t("card"))
                row.pack(fill=tk.X, pady=2)
                # Zoek naam bij dit adres
                dev_name = ""
                for d in get_paired_devices():
                    if d["address"] == addr:
                        dev_name = d.get("name", "")
                        break
                display = f"  {addr}"
                if dev_name:
                    display += f"  ({dev_name})"
                tk.Label(row, text=display, font=("Consolas", 9),
                         bg=t("card"), fg=t("text")).pack(side=tk.LEFT)
                tk.Button(row, text="Verwijder", font=("Segoe UI", 8),
                          bg=t("red"), fg="#ffffff", relief="flat", cursor="hand2",
                          command=lambda a=addr: self.remove_from_whitelist(a),
                          padx=8).pack(side=tk.RIGHT)
        else:
            tk.Label(wl_inner, text="  Geen apparaten op whitelist (iedereen mag verbinden)",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=4)

        # Kies uit gekoppelde apparaten
        paired = get_paired_devices()
        if paired:
            tk.Label(wl_inner, text="Kies een gekoppeld apparaat:", font=("Segoe UI", 9, "bold"),
                     bg=t("card"), fg=t("text")).pack(anchor="w", pady=(8, 4))

            self.wl_device_var = tk.StringVar()
            for dev in paired:
                addr = dev["address"]
                name = dev.get("name", "Onbekend")
                emoji = get_device_emoji(name)
                is_in_wl = addr in sec["whitelist"]
                prefix = "✓ " if is_in_wl else "  "
                rb = tk.Radiobutton(wl_inner, text=f"{prefix}{emoji} {name} ({addr})",
                                    variable=self.wl_device_var, value=addr,
                                    bg=t("card"), fg=t("text"), selectcolor=t("bg2"),
                                    activebackground=t("card"), activeforeground=t("accent"),
                                    font=("Segoe UI", 9))
                rb.pack(anchor="w", pady=1)

            def add_selected():
                addr = self.wl_device_var.get() if hasattr(self, "wl_device_var") else ""
                if addr:
                    add_to_whitelist(addr)
                    self.load_security()
                else:
                    messagebox.showwarning("Let op", "Selecteer eerst een apparaat!")

            tk.Button(wl_inner, text="Geselecteerd Toestaan", font=("Segoe UI", 9, "bold"),
                      bg=t("green"), fg="#000000", relief="flat", cursor="hand2",
                      command=add_selected, padx=12, pady=4).pack(anchor="w", pady=(8, 0))
        else:
            # Handmatig invoeren
            tk.Label(wl_inner, text="Of voer MAC-adres handmatig in:", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(8, 4))
            add_frame = tk.Frame(wl_inner, bg=t("card"))
            add_frame.pack(fill=tk.X)
            self.wl_entry = tk.Entry(add_frame, font=("Consolas", 9), bg=t("bg"), fg=t("text"),
                                     insertbackground=t("accent"), relief="flat",
                                     placeholder="bv 89:7E:2C:69:BC:EB")
            self.wl_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
            tk.Button(add_frame, text="Toestaan", font=("Segoe UI", 9),
                      bg=t("green"), fg="#000000", relief="flat", cursor="hand2",
                      command=self.add_to_whitelist_action, padx=12).pack(side=tk.LEFT, padx=(8, 0))

        # Blokkeringen
        bl_card = tk.Frame(self.security_inner, bg=t("card"),
                           highlightbackground=t("border"), highlightthickness=1)
        bl_card.pack(fill=tk.X, padx=16, pady=6)
        bl_inner = tk.Frame(bl_card, bg=t("card"))
        bl_inner.pack(fill=tk.X, padx=12, pady=12)

        tk.Label(bl_inner, text="Geblokkeerde Apparaten", font=("Segoe UI", 12, "bold"),
                 bg=t("card"), fg=t("red")).pack(anchor="w")

        if sec["blocked"]:
            for addr in sec["blocked"]:
                row = tk.Frame(bl_inner, bg=t("card"))
                row.pack(fill=tk.X, pady=2)
                tk.Label(row, text=f"  {addr}", font=("Consolas", 9),
                         bg=t("card"), fg=t("text")).pack(side=tk.LEFT)
                tk.Button(row, text="Deblokkeer", font=("Segoe UI", 8),
                          bg=t("green"), fg="#000000", relief="flat", cursor="hand2",
                          command=lambda a=addr: self.unblock_device(a),
                          padx=8).pack(side=tk.RIGHT)
        else:
            tk.Label(bl_inner, text="  Geen apparaten geblokkeerd",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=4)

        # Blokkeer nieuw
        bl_add = tk.Frame(bl_inner, bg=t("card"))
        bl_add.pack(fill=tk.X, pady=(8, 0))
        self.bl_entry = tk.Entry(bl_add, font=("Consolas", 9), bg=t("bg"), fg=t("text"),
                                 insertbackground=t("accent"), relief="flat")
        self.bl_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        tk.Button(bl_add, text="Blokkeer", font=("Segoe UI", 9),
                  bg=t("red"), fg="#ffffff", relief="flat", cursor="hand2",
                  command=self.block_device_action, padx=12).pack(side=tk.LEFT, padx=(8, 0))

        # Info
        info_card = tk.Frame(self.security_inner, bg=t("card"),
                             highlightbackground=t("border"), highlightthickness=1)
        info_card.pack(fill=tk.X, padx=16, pady=6)
        info_inner = tk.Frame(info_card, bg=t("card"))
        info_inner.pack(fill=tk.X, padx=12, pady=12)
        tk.Label(info_inner, text="Hoe werkt het?", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w")
        info_lines = [
            "PIN: Voer een PIN in om de app te beveiligen.",
            "Whitelist: Alleen deze apparaten mogen verbinden.",
            "Blokkeer: Deze apparaten worden geweigerd.",
            "Geen whitelist = alle apparaten toegestaan (behalve geblokkeerde).",
        ]
        for line in info_lines:
            tk.Label(info_inner, text=f"  {line}", font=("Segoe UI", 9),
                     bg=t("card"), fg=t("dim")).pack(anchor="w")

    def add_to_whitelist_action(self):
        addr = self.wl_entry.get().strip()
        if addr:
            add_to_whitelist(addr)
            self.wl_entry.delete(0, tk.END)
            self.load_security()

    def block_device_action(self):
        addr = self.bl_entry.get().strip()
        if addr:
            block_device(addr)
            self.bl_entry.delete(0, tk.END)
            self.load_security()

    def remove_from_whitelist(self, address):
        sec = load_security()
        if address in sec["whitelist"]:
            sec["whitelist"].remove(address)
            save_security(sec)
        self.load_security()

    def unblock_device(self, address):
        sec = load_security()
        if address in sec["blocked"]:
            sec["blocked"].remove(address)
            save_security(sec)
        self.load_security()

    # ─── Update Tab ─────────────────────────────────────────────

    def load_update_tab(self):
        for w in self.update_inner.winfo_children():
            w.destroy()

        tk.Label(self.update_inner, text="Updates & Systeem", font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(anchor="w", padx=20, pady=(20, 4))

        # ─── Batterij Info ──────────────────────────────────────
        bat_info = get_battery_info()
        paired = get_paired_devices()

        sys_card = tk.Frame(self.update_inner, bg=t("card"),
                            highlightbackground=t("glow"), highlightthickness=1)
        sys_card.pack(fill=tk.X, padx=20, pady=8)
        sys_inner = tk.Frame(sys_card, bg=t("card"))
        sys_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(sys_inner, text="Systeem Info", font=("Segoe UI", 12, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w")

        # Laptop batterij
        if bat_info and bat_info.get("percentage"):
            pct = int(bat_info["percentage"])
            state = bat_info.get("state", "unknown")
            color = t("green") if pct > 60 else t("yellow") if pct > 20 else t("red")
            state_text = {"charging": "Opladen", "discharging": "Ontladen",
                          "fully-charged": "Vol"}.get(state, state.title())

            bat_frame = tk.Frame(sys_inner, bg=t("bg2"))
            bat_frame.pack(fill=tk.X, pady=(8, 0))
            tk.Label(bat_frame, text="Laptop Batterij:", font=("Segoe UI", 9),
                     bg=t("bg2"), fg=t("dim")).pack(side=tk.LEFT)
            tk.Label(bat_frame, text=f"{pct}%", font=("Segoe UI", 11, "bold"),
                     bg=t("bg2"), fg=color).pack(side=tk.LEFT, padx=(4, 8))
            tk.Label(bat_frame, text=state_text, font=("Segoe UI", 9),
                     bg=t("bg2"), fg=t("text")).pack(side=tk.LEFT)

            bar_frame = tk.Frame(sys_inner, bg=t("bg2"))
            bar_frame.pack(fill=tk.X, pady=(4, 0))
            bar_bg = tk.Frame(bar_frame, bg=t("border"), height=8)
            bar_bg.pack(fill=tk.X)
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=color, height=8,
                     width=max(1, int(400 * pct / 100))).place(x=0, y=0, relheight=1.0)
        else:
            tk.Label(sys_inner, text="  Laptop batterij: niet beschikbaar",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(8, 0))

        # BT apparaten batterij
        bt_with_battery = [d for d in paired if d.get("battery") is not None]
        if bt_with_battery:
            tk.Label(sys_inner, text="Bluetooth Apparaten Batterij:",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(8, 2))
            for dev in bt_with_battery:
                bat = dev["battery"]
                bat_color = t("green") if bat > 60 else t("yellow") if bat > 20 else t("red")
                row = tk.Frame(sys_inner, bg=t("bg2"))
                row.pack(fill=tk.X, pady=1)
                emoji = get_device_emoji(dev.get("name", ""))
                tk.Label(row, text=f"  {emoji} {dev.get('name', '?')}", font=("Segoe UI", 9),
                         bg=t("bg2"), fg=t("text")).pack(side=tk.LEFT)
                tk.Label(row, text=f"{bat}%", font=("Segoe UI", 9, "bold"),
                         bg=t("bg2"), fg=bat_color).pack(side=tk.RIGHT)
        else:
            tk.Label(sys_inner, text="  Geen BT apparaten met batterij-info",
                     font=("Segoe UI", 9), bg=t("card"), fg=t("dim")).pack(anchor="w", pady=(4, 0))

        # ─── Versie Info ────────────────────────────────────────
        local_ver = get_local_version() if HAS_UPDATER else "2.1.0"
        ver_card = tk.Frame(self.update_inner, bg=t("card"),
                            highlightbackground=t("border"), highlightthickness=1)
        ver_card.pack(fill=tk.X, padx=20, pady=6)
        ver_inner = tk.Frame(ver_card, bg=t("card"))
        ver_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(ver_inner, text="App Versie", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w")
        tk.Label(ver_inner, text=f"v{local_ver}", font=("Segoe UI", 18, "bold"),
                 bg=t("card"), fg=t("text")).pack(anchor="w", pady=(4, 0))

        self.update_status_var = tk.StringVar(value="")

        def do_check():
            self.update_status_var.set("Controleren...")
            def _check():
                if HAS_UPDATER:
                    has_update, remote, changelog = check_for_updates(silent=True)
                    if has_update:
                        self.root.after(0, lambda: self.update_status_var.set(
                            f"Update: v{remote} beschikbaar!"))
                        self.root.after(0, lambda: self._show_update_available(remote, changelog))
                    else:
                        self.root.after(0, lambda: self.update_status_var.set("Up-to-date!"))
                else:
                    self.root.after(0, lambda: self.update_status_var.set(
                        "Update-systeem niet actief"))
            threading.Thread(target=_check, daemon=True).start()

        tk.Button(ver_inner, text="Controleren op Updates",
                  font=("Segoe UI", 11, "bold"), bg=t("accent"), fg="#ffffff",
                  relief="flat", cursor="hand2", command=do_check, bd=0,
                  padx=16, pady=6).pack(anchor="w", pady=(12, 0))

        tk.Label(ver_inner, textvariable=self.update_status_var, font=("Segoe UI", 10),
                 bg=t("card"), fg=t("text")).pack(anchor="w", pady=(8, 0))

        # ─── Changelog ──────────────────────────────────────────
        hist_card = tk.Frame(self.update_inner, bg=t("card"),
                             highlightbackground=t("border"), highlightthickness=1)
        hist_card.pack(fill=tk.X, padx=20, pady=6)
        hist_inner = tk.Frame(hist_card, bg=t("card"))
        hist_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(hist_inner, text="Wat is er nieuw", font=("Segoe UI", 12, "bold"),
                 bg=t("card"), fg=t("accent")).pack(anchor="w")
        for feat in [
            "Lokaal tab: USB, HDMI, audio, opslag",
            "Besturing: Media controls in Gekoppeld",
            "Beveiliging: Blokkeren/whitelist per apparaat",
            "Update tab met batterij info",
            "Auto-update systeem",
            "5 neon thema's",
            "Zoekbalk & notities",
        ]:
            tk.Label(hist_inner, text=f"  {feat}", font=("Segoe UI", 10),
                     bg=t("card"), fg=t("text")).pack(anchor="w", pady=1)

        # ─── Rollback ───────────────────────────────────────────
        rollback_card = tk.Frame(self.update_inner, bg=t("card"),
                                 highlightbackground=t("border"), highlightthickness=1)
        rollback_card.pack(fill=tk.X, padx=20, pady=6)
        rollback_inner = tk.Frame(rollback_card, bg=t("card"))
        rollback_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(rollback_inner, text="Terug naar vorige versie", font=("Segoe UI", 11, "bold"),
                 bg=t("card"), fg=t("yellow")).pack(anchor="w")

        def do_rollback():
            if HAS_UPDATER:
                success, msg = rollback_update()
                messagebox.showinfo("Rollback", msg)
                self.load_update_tab()
            else:
                messagebox.showwarning("Let op", "Update-systeem niet beschikbaar")

        tk.Button(rollback_inner, text="Terugzetten", font=("Segoe UI", 10),
                  bg=t("yellow"), fg="#000000", relief="flat", cursor="hand2",
                  command=do_rollback, padx=16, pady=4).pack(anchor="w", pady=(4, 0))

    def _show_update_available(self, version, changelog):
        win = tk.Toplevel(self.root)
        win.title(f"Update v{version}")
        win.geometry("400x350")
        win.configure(bg=t("bg"))

        tk.Label(win, text="Update Beschikbaar!", font=("Segoe UI", 16, "bold"),
                 bg=t("bg"), fg=t("green")).pack(pady=(20, 8))
        tk.Label(win, text=f"v{version}", font=("Segoe UI", 24, "bold"),
                 bg=t("bg"), fg=t("accent")).pack(pady=(0, 12))

        tk.Label(win, text="Wijzigingen:", font=("Segoe UI", 11, "bold"),
                 bg=t("bg"), fg=t("text")).pack(anchor="w", padx=20)
        for item in changelog:
            tk.Label(win, text=f"  {item}", font=("Segoe UI", 10),
                     bg=t("bg"), fg=t("dim")).pack(anchor="w", padx=20)

        def do_install():
            def _install():
                def progress(msg):
                    self.root.after(0, lambda m=msg: self.update_status_var.set(m))
                success, msg = install_update(progress_callback=progress)
                self.root.after(0, lambda: messagebox.showinfo("Update", msg))
            threading.Thread(target=_install, daemon=True).start()
            win.destroy()

        tk.Button(win, text="Nu Installeren", font=("Segoe UI", 12, "bold"),
                  bg=t("green"), fg="#000000", relief="flat", cursor="hand2",
                  command=do_install, padx=20, pady=8).pack(pady=20)
        tk.Button(win, text="Later", font=("Segoe UI", 10),
                  bg=t("card"), fg=t("dim"), relief="flat", cursor="hand2",
                  command=win.destroy, padx=12, pady=4).pack()


def main():
    root = tk.Tk()
    app = BluetoothApp(root)
    def on_close():
        app.anim_running = False
        app.stop_event.set()
        if app.battery_refresh_id:
            root.after_cancel(app.battery_refresh_id)
        app.save_notes()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
