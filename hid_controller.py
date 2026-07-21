#!/usr/bin/env python3
"""
HID Controller - Toetsenbord & Muis besturing via Bluetooth
Stuur toetsenbord en muis input naar verbonden HID apparaten.
"""

import asyncio
import struct
import time

try:
    from bleak import BleakClient
except ImportError:
    BleakClient = None

# ─── HID Service UUID's ────────────────────────────────────────

HID_SERVICE = "00001812-0000-1000-8000-00805f9b34fb"
HID_REPORT = "00002a4d-0000-1000-8000-00805f9b34fb"
HID_CONTROL = "00002a4c-0000-1000-8000-00805f9b34fb"

# ─── Keyboard HID Report ───────────────────────────────────────

# Modifier keys
MOD_NONE = 0x00
MOD_LEFT_CTRL = 0x01
MOD_LEFT_SHIFT = 0x02
MOD_LEFT_ALT = 0x04
MOD_LEFT_GUI = 0x08
MOD_RIGHT_CTRL = 0x10
MOD_RIGHT_SHIFT = 0x20
MOD_RIGHT_ALT = 0x40
MOD_RIGHT_GUI = 0x80

# Key codes (USB HID Usage Tables)
KEY_CODES = {
    "a": 0x04, "b": 0x05, "c": 0x06, "d": 0x07, "e": 0x08,
    "f": 0x09, "g": 0x0A, "h": 0x0B, "i": 0x0C, "j": 0x0D,
    "k": 0x0E, "l": 0x0F, "m": 0x10, "n": 0x11, "o": 0x12,
    "p": 0x13, "q": 0x14, "r": 0x15, "s": 0x16, "t": 0x17,
    "u": 0x18, "v": 0x19, "w": 0x1A, "x": 0x1B, "y": 0x1C,
    "z": 0x1D,
    "1": 0x1E, "2": 0x1F, "3": 0x20, "4": 0x21, "5": 0x22,
    "6": 0x23, "7": 0x24, "8": 0x25, "9": 0x26, "0": 0x27,
    "enter": 0x28, "esc": 0x29, "backspace": 0x2A, "tab": 0x2B,
    "space": 0x2C, "-": 0x2D, "=": 0x2E, "[": 0x2F, "]": 0x30,
    "\\": 0x31, ";": 0x33, "'": 0x34, "`": 0x35, ",": 0x36,
    ".": 0x37, "/": 0x38,
    "capslock": 0x39, "f1": 0x3A, "f2": 0x3B, "f3": 0x3C,
    "f4": 0x3D, "f5": 0x3E, "f6": 0x3F, "f7": 0x40,
    "f8": 0x41, "f9": 0x42, "f10": 0x43, "f11": 0x44,
    "f12": 0x45, "printscreen": 0x46, "scrolllock": 0x47,
    "pause": 0x48, "insert": 0x49, "home": 0x4A,
    "pageup": 0x4B, "delete": 0x4C, "end": 0x4D,
    "pagedown": 0x4E, "right": 0x4F, "left": 0x50,
    "down": 0x51, "up": 0x52,
}

SPECIAL_KEYS = {
    "ctrl": ("mod", MOD_LEFT_CTRL),
    "shift": ("mod", MOD_LEFT_SHIFT),
    "alt": ("mod", MOD_LEFT_ALT),
    "super": ("mod", MOD_LEFT_GUI),
    "win": ("mod", MOD_LEFT_GUI),
}

# ─── Mouse HID Report ──────────────────────────────────────────

MOUSE_BUTTON_LEFT = 0x01
MOUSE_BUTTON_RIGHT = 0x02
MOUSE_BUTTON_MIDDLE = 0x04


class HIDController:
    """Verbind met een HID apparaat en verstuur toetsenbord/muis input."""

    def __init__(self, address):
        self.address = address
        self.client = None
        self.connected = False
        self.hid_char = None

    async def connect(self):
        if BleakClient is None:
            raise Exception("bleak niet geinstalleerd")
        self.client = BleakClient(self.address)
        await self.client.connect()
        self.connected = True

        # Zoek HID report characteristic
        for service in self.client.services:
            if str(service.uuid).lower() == HID_SERVICE:
                for char in service.characteristics:
                    if HID_REPORT in str(char.uuid):
                        self.hid_char = char
                        break
                break

    async def disconnect(self):
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False

    async def send_key(self, key, modifier=MOD_NONE):
        """Verstuur een enkele toets."""
        if not self.connected or not self.hid_char:
            return False

        key_code = KEY_CODES.get(key.lower(), 0)
        if key_code == 0:
            return False

        # HID Keyboard report: [modifier, 0, key1, key2, key3, key4, key5, key6]
        report = bytes([modifier, 0x00, key_code, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, report)
        await asyncio.sleep(0.05)

        # Loslaten
        release = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, release)
        return True

    async def send_text(self, text):
        """Verstuur een tekst als toetsaanslagen."""
        for char in text:
            modifier = MOD_NONE
            key = char.lower()

            # Shift nodig voor hoofdletters en speciale tekens
            if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?~':
                modifier = MOD_LEFT_SHIFT

            # Speciale tekens mapping
            special_map = {
                "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
                "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
                "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
                ":": ";", '"': "'", "<": ",", ">": ".", "?": "/",
                "~": "`",
            }
            if char in special_map:
                key = special_map[char]

            await self.send_key(key, modifier)
            await asyncio.sleep(0.03)

    async def send_combo(self, keys):
        """Verstuur een toetscombinatie (bv ctrl+c)."""
        modifier = MOD_NONE
        key = None

        for k in keys:
            k_lower = k.lower()
            if k_lower in SPECIAL_KEYS:
                info = SPECIAL_KEYS[k_lower]
                modifier |= info[1]
            elif k_lower in KEY_CODES:
                key = k_lower

        if key and self.connected and self.hid_char:
            key_code = KEY_CODES[key]
            report = bytes([modifier, 0x00, key_code, 0x00, 0x00, 0x00, 0x00, 0x00])
            await self.client.write_gatt_char(self.hid_char, report)
            await asyncio.sleep(0.05)
            release = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            await self.client.write_gatt_char(self.hid_char, release)
            return True
        return False

    async def mouse_move(self, dx, dy):
        """Beweeg de muis relatief."""
        if not self.connected or not self.hid_char:
            return False

        # Clamp to signed 8-bit
        dx = max(-127, min(127, dx))
        dy = max(-127, min(127, dy))

        report = bytes([0x00, dx & 0xFF, dy & 0xFF, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, report)
        await asyncio.sleep(0.02)

        # Stop
        stop = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, stop)
        return True

    async def mouse_click(self, button=MOUSE_BUTTON_LEFT):
        """Klik met de muis."""
        if not self.connected or not self.hid_char:
            return False

        report = bytes([button, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, report)
        await asyncio.sleep(0.05)

        release = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, release)
        return True

    async def mouse_scroll(self, amount):
        """Scroll met de muis."""
        if not self.connected or not self.hid_char:
            return False

        amount = max(-127, min(127, amount))
        report = bytes([0x00, 0x00, 0x00, amount & 0xFF, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, report)
        await asyncio.sleep(0.05)

        stop = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await self.client.write_gatt_char(self.hid_char, stop)
        return True


# ─── Snelle functies ───────────────────────────────────────────

_controllers = {}

async def get_controller(address):
    if address not in _controllers or not _controllers[address].connected:
        ctrl = HIDController(address)
        await ctrl.connect()
        _controllers[address] = ctrl
    return _controllers[address]


async def quick_type(address, text):
    ctrl = await get_controller(address)
    await ctrl.send_text(text)


async def quick_key(address, key, modifiers=None):
    ctrl = await get_controller(address)
    mod = MOD_NONE
    if modifiers:
        for m in modifiers:
            if m in SPECIAL_KEYS:
                mod |= SPECIAL_KEYS[m][1]
    await ctrl.send_key(key, mod)


async def quick_click(address, button="left"):
    ctrl = await get_controller(address)
    btn = {"left": MOUSE_BUTTON_LEFT, "right": MOUSE_BUTTON_RIGHT,
           "middle": MOUSE_BUTTON_MIDDLE}.get(button, MOUSE_BUTTON_LEFT)
    await ctrl.mouse_click(btn)


async def quick_move(address, dx, dy):
    ctrl = await get_controller(address)
    await ctrl.mouse_move(dx, dy)
