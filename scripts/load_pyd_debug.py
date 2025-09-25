import ctypes
from pathlib import Path
import sys

PYD = Path(r"C:\Users\Funtional2\AppData\Local\Programs\Python\Python310\Lib\site-packages\pc_ble_driver_py\lib\win\x86_64\_pc_ble_driver_sd_api_v3.pyd")

print('pyd path:', PYD)
print('exists:', PYD.exists())
if not PYD.exists():
    sys.exit(1)

try:
    ctypes.WinDLL(str(PYD))
    print('Loaded pyd successfully via ctypes.WinDLL')
except OSError as e:
    print('Failed to load pyd via ctypes.WinDLL:')
    print(repr(e))
    # Show Win32 error code if available
    try:
        import ctypes.wintypes as wt
        err = ctypes.get_last_error()
        print('GetLastError:', err)
    except Exception:
        pass
