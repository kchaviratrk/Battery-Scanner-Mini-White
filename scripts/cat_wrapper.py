from pathlib import Path
p = Path(r"C:\Users\Funtional2\AppData\Local\Programs\Python\Python310\Lib\site-packages\pc_ble_driver_py\lib\win\x86_64\pc_ble_driver_sd_api_v3.py")
print(p)
print(p.exists())
if p.exists():
    print(p.read_text(encoding='utf-8'))
else:
    print('file not found')
