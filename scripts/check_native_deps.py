#!/usr/bin/env python3
"""
Diagnostic helper to check for missing native dependencies that prevent
`_pc_ble_driver_sd_api_v3` from loading. Runs on Windows with Python 3.10.

Usage: python scripts/check_native_deps.py
"""
import ctypes
import importlib
import os
import platform
import sys
from pathlib import Path


def info(msg: str):
    print(msg)


def try_win_dll_load(name: str, paths):
    """Try to load a DLL by name. If paths is provided, try loading from those dirs first."""
    last = None
    for p in paths:
        full = Path(p) / name
        try:
            ctypes.WinDLL(str(full))
            return (True, str(full))
        except OSError as e:
            last = e
    # try system search
    try:
        ctypes.WinDLL(name)
        return (True, name)
    except OSError as e:
        return (False, str(last) if last is not None else str(e))


def main():
    info("Python executable: %s" % sys.executable)
    info("Python version: %s" % platform.python_version())
    info("Architecture: %s" % platform.architecture()[0])

    try:
        import pc_ble_driver_py
        pkg_path = Path(pc_ble_driver_py.__file__).resolve().parent
        info(f"pc_ble_driver_py package path: {pkg_path}")
    except Exception as e:
        info(f"pc_ble_driver_py not importable: {e}")
        # still attempt to find site-packages
        pkg_path = None

    # Candidate DLL directory used by package
    dll_dir = None
    if pkg_path:
        candidate = pkg_path / 'lib' / 'win' / 'x86_64'
        if candidate.exists():
            dll_dir = candidate
            info(f"DLL directory: {dll_dir}")
            for p in sorted(dll_dir.iterdir()):
                info(f"  - {p.name}")
        else:
            info(f"Expected DLL directory not found: {candidate}")

    search_paths = []
    if dll_dir:
        search_paths.append(str(dll_dir))

    # Common MSVC runtime DLLs to check
    runtime_dlls = [
        'vcruntime140_1.dll',
        'vcruntime140.dll',
        'msvcp140.dll',
        'msvcp140_1.dll',
    ]

    info('\nChecking common MSVC runtime DLLs:')
    missing = []
    for d in runtime_dlls:
        ok, path = try_win_dll_load(d, search_paths)
        if ok:
            info(f"FOUND: {d} -> {path}")
        else:
            info(f"MISSING: {d} (last error: {path})")
            missing.append(d)

    # Try loading the Nordic DLL if present
    nordic_names = [
        'nrf-ble-driver-sd_api_v3-mt-4_1_4.dll',
        'nrf-ble-driver-sd_api_v3-mt-4_1_3.dll',
    ]

    info('\nChecking Nordic nrf-ble-driver DLLs:')
    nordic_missing = []
    for n in nordic_names:
        ok, path = try_win_dll_load(n, search_paths)
        if ok:
            info(f"FOUND: {n} -> {path}")
        else:
            info(f"MISSING: {n} (last error: {path})")
            nordic_missing.append(n)

    # Add the DLL dir to the process search path (Python 3.8+)
    if dll_dir:
        try:
            os.add_dll_directory(str(dll_dir))
            info(f"Added {dll_dir} to DLL search directories")
        except Exception as e:
            info(f"os.add_dll_directory failed: {e}")

    info('\nAttempting to import the native SWIG module _pc_ble_driver_sd_api_v3')
    try:
        importlib.import_module('_pc_ble_driver_sd_api_v3')
        info('Import SUCCESS: _pc_ble_driver_sd_api_v3')
    except Exception as e:
        info(f'Import FAILED: _pc_ble_driver_sd_api_v3 -> {e!r}')

    info('\nAttempting high-level import pc_ble_driver_py.ble_driver')
    try:
        import pc_ble_driver_py.ble_driver as bd
        info('Import SUCCESS: pc_ble_driver_py.ble_driver')
    except Exception as e:
        info(f'Import FAILED: pc_ble_driver_py.ble_driver -> {e!r}')

    info('\nSummary:')
    if missing:
        info('Likely missing MSVC runtimes: %s' % ', '.join(missing))
    else:
        info('MSVC runtime DLLs appear available')

    if nordic_missing and dll_dir:
        info('Nordic DLLs missing from DLL dir: %s' % ', '.join(nordic_missing))
    elif nordic_missing:
        info('Nordic DLLs not found in system search path or package')
    else:
        info('Nordic nrf-ble-driver DLLs appear available')

    if missing:
        info('\nNext steps: install the Microsoft Visual C++ Redistributable x64.\n')
    else:
        info('\nIf import still fails, run dependency walker (e.g., "Dependencies" app) on the .pyd to find the missing DLL.\n')


if __name__ == '__main__':
    main()
