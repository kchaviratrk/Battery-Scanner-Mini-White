"""Diagnóstico y ejecución del BLE scanner usando solo Python.
- Lista archivos en pc_ble_driver_py
- Añade su carpeta x86_64 al search path de DLLs con os.add_dll_directory
- Intenta importar el módulo nativo y el paquete
- Si la importación falla, muestra errores detallados
- Ejecuta `ble_scanner.py` y responde 'y' automáticamente

Ejecutar con: python scripts\diagnose_and_run_scanner.py
"""
import os
import sys
import importlib
import traceback
import subprocess

SITE_PKG = os.path.join(sys.prefix, 'Lib', 'site-packages')
PKG_PATH = os.path.join(SITE_PKG, 'pc_ble_driver_py')
DLL_DIR = os.path.join(PKG_PATH, 'lib', 'win', 'x86_64')

print('Python executable:', sys.executable)
print('Python version:', sys.version)
print('Site-packages:', SITE_PKG)
print('pc_ble_driver_py path:', PKG_PATH)
print('DLL dir:', DLL_DIR)
print('\nListing pc_ble_driver_py contents:')
try:
    for p in sorted(os.listdir(PKG_PATH)):
        print('  ', p)
except Exception as e:
    print('  cannot list package path:', e)

# Try adding DLL dir to process search path (Windows 3.8+)
if os.name == 'nt' and os.path.isdir(DLL_DIR):
    try:
        print('\nCalling os.add_dll_directory(%r)' % DLL_DIR)
        dll_ctx = os.add_dll_directory(DLL_DIR)
    except Exception as e:
        print('  add_dll_directory failed:', e)
else:
    print('\nNo DLL dir to add or not Windows')

print('\nAttempt native import _pc_ble_driver_sd_api_v3')
try:
    importlib.import_module('_pc_ble_driver_sd_api_v3')
    print('  native import ok')
except Exception:
    print('  native import failed:')
    traceback.print_exc()

print('\nAttempt high-level import pc_ble_driver_py.ble_driver')
try:
    importlib.import_module('pc_ble_driver_py.ble_driver')
    print('  high-level import ok')
except Exception:
    print('  high-level import failed:')
    traceback.print_exc()

# Try to run the ble_scanner and send 'y' to stdin
SCANNER = os.path.join(os.getcwd(), 'ble_scanner.py')
if os.path.exists(SCANNER):
    print('\nRunning ble_scanner.py and sending "y" to stdin (will run until scanner stops)')
    try:
        proc = subprocess.Popen([sys.executable, SCANNER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out, _ = proc.communicate('y\n', timeout=30)
        print('\n--- ble_scanner.py output (first 2000 chars) ---\n')
        print(out[:2000])
        print('\n--- end output ---')
    except subprocess.TimeoutExpired:
        proc.kill()
        print('\nScanner timed out (killed)')
    except Exception:
        print('\nFailed to run scanner:')
        traceback.print_exc()
else:
    print('\nble_scanner.py not found in cwd:', os.getcwd())

# If we added a dll ctx, keep it alive until script exit. We'll not close it explicitly.
print('\nDone')
