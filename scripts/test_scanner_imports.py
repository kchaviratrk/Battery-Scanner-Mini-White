#!/usr/bin/env python3
"""
Quick test to verify the BLE scanner imports work with SD API v5.
"""
import os
import sys

# Set environment for SD API v5
os.environ['__conn_ic_id__'] = 'NRF52'
os.environ['SD_API_VER'] = '5'

try:
    import pc_ble_driver_py.config as pc_config
    pc_config.__conn_ic_id__ = 'NRF52'
    print("✓ pc_ble_driver_py.config imported successfully")
    
    from pc_ble_driver_py.ble_driver import BLEDriver, BLEEnableParams, BLEGapScanParams
    print("✓ BLE driver imports successful")
    
    from pc_ble_driver_py.observers import BLEDriverObserver
    print("✓ BLE observers imported successfully")
    
    print("\n🎉 SUCCESS: All BLE scanner imports are working!")
    print("The scanner should run without import errors.")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    print("Type:", type(e).__name__)
    import traceback
    traceback.print_exc()