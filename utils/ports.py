"""
Windows COM port auto-detection utilities for nRF52DK.

- Primary source: pyserial (serial.tools.list_ports)
- Fallback: WMIC parsing (legacy)
- Uses config.COM_PORT / COM_PORT_BACKUP as fallbacks
- Controlled by config.AUTO_DETECT_COM
"""
from __future__ import annotations
from typing import List, Tuple
import sys
import subprocess
import re

try:
    # Optional dependency; we'll handle absence gracefully
    from serial.tools import list_ports  # type: ignore
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
                dev = getattr(p, 'device', '') or ''
                desc = getattr(p, 'description', '') or ''
                mfg = getattr(p, 'manufacturer', '') or ''
                if dev and dev.upper().startswith('COM'):
                    ports.append((dev, desc, mfg))
        except Exception:
            pass
    # Fallback to WMIC if nothing found
    if not ports and sys.platform.startswith('win'):
        try:
            out = subprocess.check_output(
                [
                    'wmic', 'path', 'Win32_SerialPort',
                    'get', 'DeviceID,Name,Description,Manufacturer'
                ],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
            for line in out.splitlines():
                line = line.strip()
                if not line or 'DeviceID' in line:
                    continue
                # Heuristic: find token like COM<number>
                m = re.search(r'(COM\d+)', line, re.IGNORECASE)
                if m:
                    dev = m.group(1).upper()
                    # Split description/manufacturer if possible
                    parts = [s.strip() for s in line.split('  ') if s.strip()]
                    desc = parts[0] if parts else ''
                    mfg = parts[-1] if parts else ''
                    ports.append((dev, desc, mfg))
        except Exception:
            pass
    return ports


essential_tags = (
    'j-link', 'segger', 'nordic', 'nrf', 'pca100', 'nrf52', 'dk'
)


def _sort_com(dev: str) -> int:
    m = re.match(r'COM(\d+)$', dev.upper())
    return int(m.group(1)) if m else 10_000


def _probe_port(port: str) -> bool:
    """Try to open/enable/close the BLE driver on a port. Return True if it works.
    This helps choose between multiple COM ports (e.g., COM3/COM4).
    """
    try:
        from pc_ble_driver_py.ble_driver import BLEDriver
        drv = BLEDriver(serial_port=port, baud_rate=1_000_000)
        try:
            drv.open()
            try:
                # If ble_enable succeeds, the connectivity firmware is responsive
                drv.ble_enable(None)
                return True
            finally:
                try:
                    drv.close()
                except Exception:
                    pass
        except Exception:
            # Ensure close in case open succeeded but enable failed
            try:
                drv.close()
            except Exception:
                pass
            return False
    except Exception:
        return False


def autodetect_com_port() -> str:
    """Detect the nRF52DK COM port on Windows using common identifiers.
    Preference order:
    1) Ports matching SEGGER/J-Link/Nordic tokens, probed for responsiveness
    2) Configured COM_PORT/COM_PORT_BACKUP if present and responsive
    3) Any available ports by lowest number, probed
    4) Fallback to configured COM_PORT (no probe) if nothing responsive
    """
    ports = _list_windows_com_ports()
    if not ports:
        # As a last resort, use configured main port
        if getattr(config, 'COM_PORT', None):
            return config.COM_PORT
        raise RuntimeError('No COM ports detected. Connect the nRF52DK and try again.')

    available = [dev for dev, _, _ in ports]

    # Build priority candidate list
    tagged = []
    for dev, desc, mfg in ports:
        text = f"{dev} {desc} {mfg}".lower()
        if any(tag in text for tag in essential_tags):
            tagged.append(dev)
    tagged = sorted(set(tagged), key=_sort_com)

    cfg = []
    if config.COM_PORT in available:
        cfg.append(config.COM_PORT)
    if getattr(config, 'COM_PORT_BACKUP', None) in available:
        cfg.append(config.COM_PORT_BACKUP)

    rest = [d for d in sorted(available, key=_sort_com) if d not in tagged and d not in cfg]

    candidates: List[str] = tagged + cfg + rest

    # Probe candidates
    for port in candidates:
        if _probe_port(port):
            return port

    # Nothing responsive; choose a sane default
    if getattr(config, 'COM_PORT', None) in available:
        return config.COM_PORT
    # otherwise pick lowest-numbered available
    return sorted(available, key=_sort_com)[0]


def get_com_port() -> str:
    """Return cached or auto-detected COM port depending on config.AUTO_DETECT_COM."""
    global _DETECTED_COM_PORT
    if _DETECTED_COM_PORT:
        return _DETECTED_COM_PORT
    if getattr(config, 'AUTO_DETECT_COM', True):
        port = autodetect_com_port()
    else:
        port = config.COM_PORT
    _DETECTED_COM_PORT = port
    return port
