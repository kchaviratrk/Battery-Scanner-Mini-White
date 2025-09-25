#!/usr/bin/env python3
import importlib, inspect, sys

try:
    mod = importlib.import_module('pc_ble_driver_py.lib.win.x86_64.pc_ble_driver_sd_api_v3')
    print('module file:', mod.__file__)
    import pathlib
    p = pathlib.Path(mod.__file__)
    print('\n--- SOURCE ---\n')
    print(p.read_text(encoding='utf-8'))
except Exception as e:
    print('Failed to load module or read file:', e)
    # fallback: try to locate file manually
    try:
        import pc_ble_driver_py
        p2 = pathlib.Path(pc_ble_driver_py.__file__).resolve().parent / 'lib' / 'win' / 'x86_64' / 'pc_ble_driver_sd_api_v3.py'
        print('fallback path:', p2)
        print(p2.read_text(encoding='utf-8'))
    except Exception as e2:
        print('Fallback also failed:', e2)
