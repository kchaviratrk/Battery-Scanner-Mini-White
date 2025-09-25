try:
    import pefile
except Exception:
    print('pefile not installed. Run: python -m pip install pefile')
    raise

from pathlib import Path

PYD = Path(r"C:\Users\Funtional2\AppData\Local\Programs\Python\Python310\Lib\site-packages\pc_ble_driver_py\lib\win\x86_64\_pc_ble_driver_sd_api_v3.pyd")
print('pyd:', PYD)
pe = pefile.PE(str(PYD))
deps = set()
for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    deps.add(entry.dll.decode('utf-8'))

print('Imported DLLs:')
for d in sorted(deps):
    print('  -', d)
