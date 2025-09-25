"""Automation script to: 
- Download Nordic nrf-ble-driver Windows x64 release
- Extract SD API v3 DLL and copy to current Python's pc_ble_driver_py site-packages
- Download and silently install VC++ redistributable (optional, requires admin)
- Test importing the native module

Run with the same Python interpreter used by your project (Python 3.10)."""
import sys
import os
import shutil
import zipfile
import urllib.request
import tempfile
import subprocess
import site

RELEASE_URL = "https://github.com/NordicSemiconductor/pc-ble-driver/releases/download/v4.1.4/nrf-ble-driver-4.1.4-win_x86_64.zip"
VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


def log(msg):
    print("[install_pc_ble_driver]", msg)


def download(url, dest):
    log(f"Downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)


def find_site_packages_for_current_python():
    # Use site.getsitepackages() when available, fallback to sys.prefix
    paths = []
    try:
        paths = site.getsitepackages()
    except Exception:
        paths = [os.path.join(sys.prefix, 'Lib', 'site-packages')]
    # pick the first writable path
    for p in paths:
        if os.path.isdir(p):
            return p
    # fallback
    return paths[0]


def main():
    tmp = tempfile.mkdtemp(prefix='pc_ble_driver_')
    try:
        zip_path = os.path.join(tmp, 'nrf-ble-driver.zip')
        download(RELEASE_URL, zip_path)
        extract_dir = os.path.join(tmp, 'extracted')
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        # locate sd_api_v3 dll under bin
        dll_candidates = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith('.dll') and 'sd_api_v3' in f.lower():
                    dll_candidates.append(os.path.join(root, f))
        if not dll_candidates:
            log('No sd_api_v3 DLL found in the archive')
            return 2
        dll_path = dll_candidates[0]
        log(f'Found DLL: {dll_path}')

        site_pkgs = find_site_packages_for_current_python()
        target_dir = os.path.join(site_pkgs, 'pc_ble_driver_py', 'lib', 'win', 'x86_64')
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(dll_path, target_dir)
        log(f'Copied {os.path.basename(dll_path)} -> {target_dir}')

        # download VC redist
        vc_path = os.path.join(tmp, 'vc_redist.x64.exe')
        download(VC_REDIST_URL, vc_path)
        log('VC redist downloaded. Launching silent install (requires admin privileges).')
        # silent install: /install /quiet /norestart
        try:
            subprocess.check_call([vc_path, '/install', '/quiet', '/norestart'])
            log('VC redistributable installed (exit code 0)')
        except subprocess.CalledProcessError as e:
            log(f'VC redistributable installer returned {e.returncode}. You may need to run it manually.')

        # test import
        log('Testing import of native module _pc_ble_driver_sd_api_v3')
        try:
            import importlib
            importlib.import_module('_pc_ble_driver_sd_api_v3')
            log('Native module import succeeded')
        except Exception as e:
            log('Native import failed: ' + repr(e))
            # try higher-level import
            try:
                from pc_ble_driver_py.ble_driver import BLEDriver
                log('High-level import pc_ble_driver_py.ble_driver succeeded')
            except Exception as e2:
                log('High-level import failed: ' + repr(e2))
                return 3

        return 0
    finally:
        # keep tmp for debugging, do not delete automatically
        log(f'temporary files kept at {tmp} (delete manually if desired)')


if __name__ == '__main__':
    sys.exit(main())
