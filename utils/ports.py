"""
Windows COM port auto-detection utilities for nRF52DK.

- Primary source: pyserial (serial.tools.list_ports)
- Fallback: WMIC parsing (legacy)
- Uses config.COM_PORT / COM_PORT_BACKUP as fallbacks
- Controlled by config.AUTO_DETECT_COM
"""
from __future__ import annotations

import subprocess
from typing import List, Tuple

try:
    # Optional dependency; we'll handle absence gracefully
    from serial.tools import list_ports
except Exception:  # pragma: no cover - serial may not be installed in some envs
    list_ports = None  # type: ignore

from config import config

_DETECTED_COM_PORT: str | None = None


def _list_windows_com_ports() -> List[Tuple[str, str, str]]:
    """Return a list of (device, description, manufacturer) for Windows COM ports.
    Tries pyserial first, then WMIC fallback.
    """
    ports: List[Tuple[str, str, str]] = []
    # Try pyserial
    if list_ports is not None:
        try:
            for p in list_ports.comports():
                ports.append((p.device or "", p.description or "", p.manufacturer or ""))
        except Exception:
            pass
    # Fallback to WMIC if nothing found
    if not ports:
        try:
            out = subprocess.check_output(
                ["wmic", "path", "Win32_SerialPort", "get", "DeviceID,Name,Description,Manufacturer"],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
            for line in out.splitlines():
                line = line.strip()
                if not line or line.startswith("DeviceID"):
                    continue
                # Basic split; WMIC output can be irregular, so keep it robust
                parts = [p for p in line.split(" ") if p]
                dev = parts[0] if parts else ""
                desc = " ".join(parts[1:]) if len(parts) > 1 else ""
                ports.append((dev, desc, ""))
        except Exception:
            pass
    return ports


def autodetect_com_port() -> str:
    """Detect the nRF52DK COM port on Windows using common identifiers.
    Preference order: matches (SEGGER/J-Link/Nordic/nRF) else fallbacks in config if present.
    Raises RuntimeError if nothing is found.
    """
    ports = _list_windows_com_ports()
    candidates: List[str] = []
    for dev, desc, mfg in ports:
        text = f"{dev} {desc} {mfg}".lower()
        if any(tag in text for tag in [
            "j-link", "segger", "nordic", "nrf", "pca100", "nrf52", "dk"
        ]):
            candidates.append(dev)
    # If no strong match, accept any COM that equals configured ports
    available = {dev for dev, _, _ in ports}
    if not candidates:
        if config.COM_PORT in available:
            candidates.append(config.COM_PORT)
        if config.COM_PORT_BACKUP in available:
            candidates.append(config.COM_PORT_BACKUP)
    if not candidates:
        # As a last resort, take the first available port (not ideal, but avoids prompts)
        if ports:
            candidates.append(ports[0][0])
    if not candidates:
        raise RuntimeError("No COM ports detected. Connect the nRF52DK and try again.")
    # Prefer the main configured port if present within candidates
    if config.COM_PORT in candidates:
        return config.COM_PORT
    return candidates[0]


def get_com_port() -> str:
    """Return cached or auto-detected COM port depending on config.AUTO_DETECT_COM."""
    global _DETECTED_COM_PORT
    if _DETECTED_COM_PORT:
        return _DETECTED_COM_PORT
    if getattr(config, "AUTO_DETECT_COM", True):
        port = autodetect_com_port()
    else:
        port = config.COM_PORT
    _DETECTED_COM_PORT = port
    return port
